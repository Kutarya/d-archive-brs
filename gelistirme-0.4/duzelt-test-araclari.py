"""Convert tool assertions to checks that also execute with python -O."""

import ast
from pathlib import Path

root = Path("D:/BRS/Muvv/tools")
for filename in ("simulation_check.py", "gui_smoke.py"):
    path = root / filename
    content = path.read_bytes()
    lines = content.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    edits = []
    for node in ast.walk(ast.parse(content)):
        if isinstance(node, ast.Assert):
            begin = starts[node.lineno - 1] + node.col_offset
            end = starts[node.end_lineno - 1] + node.end_col_offset
            expression = ast.unparse(node.test)
            message = ast.unparse(node.msg) if node.msg else repr("Check failed: " + expression)
            edits.append((begin, end, f"check({expression}, {message})".encode("utf-8")))
    for begin, end, replacement in sorted(edits, reverse=True):
        content = content[:begin] + replacement + content[end:]
    marker = b"\n\nclass RecordingHID:" if filename == "simulation_check.py" else b"\n\ndef main(argv=None):"
    helper = b'\n\ndef check(condition, message):\n    if not condition:\n        raise RuntimeError(str(message))\n'
    assert content.count(marker) == 1
    content = content.replace(marker, helper + marker, 1)
    path.write_bytes(content.replace(b"\r\n", b"\n"))
