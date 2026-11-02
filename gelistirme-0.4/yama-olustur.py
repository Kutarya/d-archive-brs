"""Write review patches against each preserved repository index."""

import subprocess
from pathlib import Path

workspace = Path("D:/BRS")
for name in ("Muvv", "Muvv_development_environment"):
    result = subprocess.run(
        ["git", "diff", "--binary", "--no-ext-diff", "--no-color"],
        cwd=workspace / name, capture_output=True, check=True,
    )
    (workspace / "gelistirme-0.4" / f"{name}.patch").write_bytes(result.stdout)
