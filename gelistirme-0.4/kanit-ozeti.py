import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

root = Path("D:/BRS")
evidence = root / "gelistirme-0.4"
package = json.loads((evidence / "paket-dogrulama.json").read_text(encoding="utf-8"))
assert package["successful"] and len(package["checks"]) == 13
for entry in package["checks"]:
    names = {Path(argument).name for argument in entry["command"]}
    if "check.py" in names:
        (evidence / "wheel-test-kaydi.log").write_text(entry["stdout"] + entry["stderr"], encoding="utf-8", newline="\n")
    elif "simulation_check.py" in names:
        (evidence / "sanal-senaryolar.log").write_text(entry["stdout"] + entry["stderr"], encoding="utf-8", newline="\n")

baseline = []
for filename in ("regresyon-oncesi.log", "katalog-oncesi.log", "tani-oncesi.log", "katalog-yarisi-oncesi.log", "katalog-arayuz-oncesi.log"):
    content = (evidence / filename).read_text(encoding="utf-8")
    outcomes = re.findall(r"^test_.+?\.\.\. (ok|FAIL|ERROR)$", content, flags=re.M)
    baseline.append({"file": filename, "tests": len(outcomes), "passed": outcomes.count("ok"), "failed": outcomes.count("FAIL"), "errors": outcomes.count("ERROR")})

changed = []
with zipfile.ZipFile(root / "teslim/Muvv-0.3.0-20261011/Muvv-0.3.0-kaynak.zip") as archive:
    before = set(archive.namelist())
    current = set()
    for repository in ("Muvv", "Muvv_development_environment"):
        listing = subprocess.run(["git", "ls-files", "-z"], cwd=root / repository, check=True, capture_output=True)
        for name in {value.decode("utf-8") for value in listing.stdout.split(b"\0") if value}:
            target = f"{repository}/{name}"
            current.add(target)
            data = (root / target).read_bytes()
            if target not in before or archive.read(target) != data:
                changed.append({"file": target, "change": "added" if target not in before else "modified", "sha256": hashlib.sha256(data).hexdigest()})
    assert before.issubset(current)

summary = json.loads((evidence / "test-sonuclari.json").read_text(encoding="utf-8"))
wheel_tests = json.loads((evidence / "wheel-test-sonuclari.json").read_text(encoding="utf-8"))
assert summary["successful"] and wheel_tests["successful"]
assert all(summary[key] == wheel_tests[key] for key in ("tests", "passed", "failures", "errors", "skipped"))
assert summary["tests"] == 176 and summary["passed"] == 162 and len(summary["skipped"]) == 14
assert sum("test_gui.GUITests." in line for line in (evidence / "test-kaydi.log").read_text(encoding="utf-8").splitlines()) == 33
coverage = json.loads((evidence / "coverage.json").read_text(encoding="utf-8"))["totals"]
simulation = json.loads((evidence / "sanal-senaryolar.json").read_text(encoding="utf-8"))
assert simulation["successful"] and simulation["remaining_workers"] == []
optimized = json.loads((evidence / "optimize-senaryolar.json").read_text(encoding="utf-8"))
assert optimized["python_optimization"] == 1 and optimized["checks_active_under_optimization"]
gui = json.loads((evidence / "optimize-arayuz.json").read_text(encoding="utf-8"))
assert gui["status"] == "passed" and gui["python_optimization"] == 1 and gui["callback_errors"] == []
report = {
    "successful": True,
    "new_tests_since_0_3": summary["tests"] - 159,
    "reproduced_failures_before_fixes": sum(entry["failed"] + entry["errors"] for entry in baseline),
    "baseline_runs": baseline,
    "changed_source_files_since_0_3": sorted(changed, key=lambda entry: entry["file"]),
    "source_and_installed_wheel_tests_match": True,
    "tests": {key: summary[key] for key in ("tests", "passed", "failures", "errors")},
    "gui_tests_in_total": 33,
    "coverage_totals": coverage,
    "simulation_scenarios": simulation["scenarios"],
    "package_checks": len(package["checks"]),
}
(evidence / "kanit-ozeti.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"successful": True, "new_tests": report["new_tests_since_0_3"], "baseline_failures": report["reproduced_failures_before_fixes"], "changed_files": len(changed), "tests": report["tests"], "coverage": coverage, "simulations": simulation["scenarios"]}, ensure_ascii=False))
