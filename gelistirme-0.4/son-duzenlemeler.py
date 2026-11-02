import ast
from pathlib import Path

root = Path("D:/BRS/Muvv")
messages = {
    "simulation_check.py": [
        "No free IPC client slot.",
        "IPC worker did not finish.",
        "IPC client registry retained a handler.",
        "IPC client slots were not restored.",
        "IPC client slot limit was exceeded.",
        "Unexpected USB report count.",
        "USB transactions were interleaved.",
        "USB reports arrived out of order.",
        "Unexpected transaction count.",
        "Device reconnect failed.",
        "Previous USB handle was not closed.",
        "New connection inherited previous settings.",
        "Reconnect did not change the session.",
        "A stale device command was accepted.",
        "A stale device command wrote to USB.",
        "DPI update failed.",
        "Polling rate update failed.",
        "Button reset failed.",
        "RGB zone update failed.",
        "Profile contents changed during file exchange.",
        "Profile catalog was incomplete.",
        "Snapshot belongs to a different session.",
        "Unexpected profile count.",
        "A device session was reused.",
        "Disconnect occurred at an unexpected report.",
        "Driver remained connected after USB failure.",
        "Failed USB transaction committed settings.",
        "USB reports were sent after failure.",
        "Reconnect retained the old handle or wrote unexpected reports.",
        "Device manager did not shut down.",
        "USB handle remained open after shutdown.",
    ],
    "gui_smoke.py": [
        "Spectrum effect was not applied.",
        "DPI value was not applied.",
        "Animation did not stop.",
        "RGB zone colors were not applied.",
    ],
}
for filename, replacements in messages.items():
    path = root / "tools" / filename
    content = path.read_text(encoding="utf-8")
    nodes = sorted(
        (node for node in ast.walk(ast.parse(content)) if isinstance(node, ast.Constant)
         and isinstance(node.value, str) and node.value.startswith("Check failed:")),
        key=lambda node: (node.lineno, node.col_offset),
    )
    assert len(nodes) == len(replacements), (filename, len(nodes), len(replacements))
    lines = content.encode("utf-8").splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    data = content.encode("utf-8")
    edits = [
        (starts[node.lineno - 1] + node.col_offset,
         starts[node.end_lineno - 1] + node.end_col_offset,
         repr(message).encode("utf-8"))
        for node, message in zip(nodes, replacements, strict=True)
    ]
    for begin, end, replacement in sorted(edits, reverse=True):
        data = data[:begin] + replacement + data[end:]
    path.write_bytes(data)
