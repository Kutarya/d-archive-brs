"""Prepare separate validation helpers without changing previous deliveries."""

from pathlib import Path

previous = Path("D:/BRS/gelistirme-0.2")
current = Path("D:/BRS/gelistirme-0.3")
for name in ("paket-dogrulama.py", "kaynak-dogrulama.py", "yama-dogrulama.py"):
    content = (previous / name).read_text(encoding="utf-8")
    content = content.replace("0.2.0", "0.3.0").replace("gelistirme-0.2", "gelistirme-0.3")
    if name == "kaynak-dogrulama.py":
        marker = "    repositories = []\n"
        content = content.replace(marker, '''    prior_deliveries = []
    for directory_name in ("Muvv-0.2.0-20261011", "Muvv-0.2.0-20261011-r2"):
        directory = ROOT / "teslim" / directory_name
        for line in (directory / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            expected, filename = line.split("  ", 1)
            assert (directory / filename).resolve().is_relative_to(directory.resolve())
            assert sha256(directory / filename) == expected, filename
            prior_deliveries.append({"delivery": directory_name, "file": filename, "sha256": expected})
    repositories = []
''')
        content = content.replace('        "repositories": repositories,', '        "previous_0_2_deliveries_unchanged": prior_deliveries,\n        "repositories": repositories,')
    if name == "paket-dogrulama.py":
        content = content.replace("import subprocess\n", "import subprocess\nimport shutil\n")
        marker = '        run([interpreter, "-I", "-c", GUI_CHECK])\n'
        content = content.replace(marker, marker + '''        for directory_name in ("tools", "test/unit", "test/manager"):
            destination = CHECK / directory_name
            destination.mkdir(parents=True, exist_ok=True)
            for source in (SOURCE / directory_name).glob("*.py"):
                if directory_name == "test/manager" and source.name == "test_manager.py":
                    continue
                shutil.copyfile(source, destination / source.name)
        run([interpreter, "-I", CHECK / "tools/check.py", "--json", EVIDENCE / "wheel-test-sonuclari.json"])
        run([interpreter, "-I", CHECK / "tools/simulation_check.py", "--cycles", "200", "--json", EVIDENCE / "sanal-senaryolar.json"])
''')
        content = content.replace("    assert 'hid' not in sys.modules", '''    old_session = app._device_session
    app._replace_entry(app.dpi_entries[0], '700')
    app._mark_dirty('dpi')
    client('reconnect')
    app.refresh()
    pump(lambda: not app._busy)
    assert app._device_session != old_session
    assert app.dpi_entries[0].get() == '400' and not app._dirty
    assert client('set-polling', {'hz': 500, 'expected_session': old_session})['code'] == 'device_changed'
    assert Path(sys.modules['cli'].__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    assert 'hid' not in sys.modules''')
    (current / name).write_text(content, encoding="utf-8", newline="\n")
