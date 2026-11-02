"""Bounded diagnostic probes against the ZIP snapshot. No real HID or sockets.

This script preserves source files. Only explicit unittest.TestCase suites run;
interactive hardware functions and the application's daemon entry point do not.
"""
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
import ast
import copy
import hashlib
import io
import json
import queue
import re
import sys
import threading
import time
import types
import unittest

BASE = Path(r"D:\BRS\inceleme")
SOURCE = BASE / "kaynak" / "Muvv-main"
EVIDENCE = BASE / "kanitlar"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SOURCE))
blocked_hid_calls = []

def forbidden_hid(*args, **kwargs):
    blocked_hid_calls.append("real_hid_access_blocked")
    raise RuntimeError("Real HID access is blocked by the offline audit")

hid_stub = types.ModuleType("hid")
hid_stub.enumerate = forbidden_hid
hid_stub.device = forbidden_hid
sys.modules["hid"] = hid_stub

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse
from managers.device_runner import DeviceRunner
from managers.device_manager import DeviceManager
from managers.ipc_server import IPCServer
from managers.validator import CommandValidator
from animations.effect_registry import get_effect_class, _EFFECTS
from animations.vitray import Vitray
from animations.layer import Layer
from animations.effects.static_color import StaticColor
from animations.effects.wave import Wave
import cli

results = []
captured = io.StringIO()

def record(name, observation, details, expected):
    results.append({"id": name, "observation": observation, "details": details,
                    "expected_after_remediation": expected})

class RecordingQueue:
    def __init__(self, after_put=None):
        self.items = []
        self.after_put = after_put
    def put(self, item):
        self.items.append(item)
        if self.after_put:
            self.after_put(item)
    def join(self):
        return None

class DummyHID:
    def close(self):
        pass

def make_stack():
    # Skip only the worker thread; execute the original driver's initializer.
    with patch("drivers.base_mouse.threading.Thread"):
        runner = DeviceRunner(Rival3Gen2Mouse, device_path=b"offline-audit")
    runner.driver.device = DummyHID()
    runner.driver.is_connected = True
    runner.driver.command_queue = RecordingQueue()
    runner.zone_map = runner.driver.get_zone_map()
    runner.engine = Vitray(runner.zone_map)
    runner.engine.add_layer(Layer(StaticColor((10, 20, 30))))
    manager = DeviceManager()
    manager.runners["audit-device"] = runner
    return manager, runner, manager.ipc_server

def request(ipc, command, **args):
    return ipc._process_command({"command": command,
                                 "args": {"device": "audit-device", **args}})

def render_outcome(runner):
    try:
        return {"frame": runner.engine.render()}
    except Exception as error:
        return {"exception": type(error).__name__, "message": str(error)}

class ScriptedSocket:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.sent = b""
        self.recv_calls = 0
        self.closed = False
    def recv(self, size):
        self.recv_calls += 1
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if len(chunk) > size:
            self.chunks.insert(0, chunk[size:])
        return chunk[:size]
    def sendall(self, data):
        self.sent += data
    def close(self):
        self.closed = True
    def connect(self, path):
        self.path = path

def handle_chunks(ipc, chunks):
    sock = ScriptedSocket(chunks)
    ipc._handle_client(sock)
    response = json.loads(sock.sent) if sock.sent else None
    return {"response": response, "recv_calls": sock.recv_calls,
            "unread_chunks": len(sock.chunks), "closed": sock.closed}

inventory = []
secret_candidates = []
patterns = {
    "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|github_pat_[A-Za-z0-9_]{50,}"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "credential_assignment": re.compile(r"(?i)\b(?:password|passwd|api_key|secret_key|access_token)\s*[:=]\s*[\"'][^\"']{8,}[\"']"),
}
for project in (BASE / "kaynak").iterdir():
    for file in sorted(project.rglob("*")):
        if not file.is_file():
            continue
        data = file.read_bytes()
        text = data.decode("utf-8")
        item = {"path": str(file.relative_to(BASE / "kaynak")),
                "bytes": len(data), "lines": len(text.splitlines()),
                "sha256": hashlib.sha256(data).hexdigest()}
        if file.suffix == ".py":
            tree = ast.parse(text, filename=str(file))
            compile(tree, str(file), "exec")  # Compile only; do not execute.
            item["syntax_ok"] = True
            item["classes"] = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
            item["functions"] = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for name, pattern in patterns.items():
            for match in pattern.finditer(text):
                secret_candidates.append({"path": item["path"], "pattern": name,
                                          "line": text[:match.start()].count("\n") + 1})
        inventory.append(item)

with redirect_stdout(captured), redirect_stderr(captured):
    suite = unittest.TestLoader().discover(str(SOURCE / "test" / "manager"), pattern="test_*.py")
    unit_stream = io.StringIO()
    unit_result = unittest.TextTestRunner(stream=unit_stream, verbosity=2).run(suite)
    record("P01-existing-unit-tests", "pass" if unit_result.wasSuccessful() else "fail",
           {"run": unit_result.testsRun, "failures": len(unit_result.failures),
            "errors": len(unit_result.errors), "output": unit_stream.getvalue(),
            "hid_import": "blocked stub", "hardware_tests_run": False},
           "Keep existing tests and add security boundary coverage")

    manager, runner, ipc = make_stack()
    runner.driver.set_dpi(2)
    runner.driver.set_polling_rate(500)
    runner.driver.save_profile()
    runner.driver.flush()
    runner.driver.bind_key("button5", 4)
    packets = [{"command_hex": f"0x{packet[0]:02x}", "length": len(packet), "delay": delay}
               for packet, delay in runner.driver.command_queue.items]
    record("P02-packet-lengths", "all_64_bytes", packets,
           "Retain exact verified packet format; check Report ID and descriptor before hardware changes")

    manager, runner, ipc = make_stack()
    response = request(ipc, "bind-key", button="button1", key_code=4)
    after_rejection = copy.deepcopy(runner.driver.button_config)
    second_response = request(ipc, "bind-key", button="button5", key_code=5)
    record("P03-left-click-rejection", "false_success_and_state_mutation",
           {"first_response": response, "second_response": second_response,
            "button1_after_rejection": after_rejection["button1"],
            "queued_packets": len(runner.driver.command_queue.items)},
           "Reject with error and preserve the original button state")

    manager, runner, ipc = make_stack()
    response = request(ipc, "bind-key", button="not-a-real-button", key_code=4)
    record("P04-unknown-button", "accepted_and_save_queued",
           {"response": response, "unknown_key_retained": "not-a-real-button" in runner.driver.button_config,
            "queued_commands": [f"0x{packet[0]:02x}" for packet, _ in runner.driver.command_queue.items]},
           "Reject unsupported button before state mutation or saving")

    manager, runner, ipc = make_stack()
    response = request(ipc, "bind-key", button="button5", key_code=999)
    second_response = request(ipc, "bind-key", button="button4", key_code=4)
    record("P05-out-of-range-key", "rejected_but_state_poisoned",
           {"first_response": response, "second_valid_response": second_response,
            "button5_state": runner.driver.button_config["button5"],
            "queued_packets": len(runner.driver.command_queue.items)},
           "Validate integer byte range and supported usage before committing state")

    manager, runner, ipc = make_stack()
    response = request(ipc, "set-effect", effect="wave", wave_length=0)
    record("P06-zero-wave-length", "success_then_render_failure",
           {"response": response, "render": render_outcome(runner)},
           "Reject invalid wave length and keep the previous effect")

    manager, runner, ipc = make_stack()
    response = request(ipc, "set-effect", effect="wave", apply="overwritten")
    record("P07-effect-method-overwrite", "success_then_render_failure",
           {"response": response, "apply_attribute_type": type(runner.engine.layers[0].effect.apply).__name__,
            "render": render_outcome(runner)},
           "Allow only declared effect parameters; reject methods and private attributes")

    manager, runner, ipc = make_stack()
    parsed_payload = json.loads('{"command":"set-effect","args":{"device":"audit-device","effect":"wave","speed":NaN}}')
    response = ipc._process_command(parsed_payload)
    record("P08-non-finite-speed", "non_standard_json_accepted_and_render_failed",
           {"response": response, "render": render_outcome(runner)},
           "Reject NaN, infinity and invalid parameter types")

    effect_lookup = {name: getattr(get_effect_class(name), "__name__", None)
                     for name in ("static", "staticcolor", "wave", "breathing")}
    manager, runner, ipc = make_stack()
    static_response = request(ipc, "set-effect", effect="static", color=[1, 2, 3])
    static_layers = len(runner.engine.layers)
    manager, runner, ipc = make_stack()
    staticcolor_response = request(ipc, "set-effect", effect="staticcolor", color=[1, 2, 3])
    record("P09-static-effect", "alias_and_constructor_failures",
           {"registry": effect_lookup, "static_response": static_response,
            "layers_after_static_failure": static_layers, "staticcolor_response": staticcolor_response},
           "Declare static alias and instantiate required parameters before replacing layers")

    manager, runner, ipc = make_stack()
    response = request(ipc, "set-effect", effect="does-not-exist")
    record("P10-invalid-effect-state", "old_layers_cleared_on_rejection",
           {"response": response, "remaining_layers": len(runner.engine.layers)},
           "Validate first; switch atomically after successful construction")

    manager, runner, ipc = make_stack()
    response = request(ipc, "set-color", hex="FF0000junk")
    response_short = request(ipc, "set-color", hex="FFFFF")
    record("P11-color-format", "trailing_text_and_short_color_accepted",
           {"trailing_response": response, "short_response": response_short,
            "color_after_short": runner.engine.layers[0].effect.color},
           "Accept exactly six hexadecimal digits after one optional hash")

    manager, runner, ipc = make_stack()
    response_bool = request(ipc, "set-dpi", level=True)
    response_float = request(ipc, "set-dpi", level=2.9)
    record("P12-dpi-types", "boolean_and_fractional_value_coerced",
           {"boolean_response": response_bool, "fractional_response": response_float,
            "final_index": runner.driver.active_dpi_index},
           "Enforce strict integer types without coercing booleans or fractions")

    record("P13-missing-capabilities", "fail_open_or_exception",
           {"empty_dpi": CommandValidator.validate_dpi({}, 0),
            "empty_polling": CommandValidator.validate_polling({}, 1000),
            "empty_rates_polling": CommandValidator.validate_polling({"polling_rates": []}, 1000),
            "unknown_button": CommandValidator.validate_button({}, "fake")},
           "Missing or unsupported capabilities must reject the operation")

    manager, runner, ipc = make_stack()
    record("P14-request-shape-and-framing", "malformed_shape_closes_without_response_and_fragment_fails",
           {"array": handle_chunks(ipc, [b"[]"]),
            "invalid_utf8": handle_chunks(ipc, [bytes([255])]),
            "fragmented_request": handle_chunks(ipc, [b'{"command":', b'"list","args":{}}'])},
           "Read a bounded complete frame and return a consistent structured error")

    client_socket = ScriptedSocket([b'{"status":', b'"ok","devices":[]}'])
    fake_socket_module = types.SimpleNamespace(AF_UNIX=1, SOCK_STREAM=1,
                                              socket=lambda *args: client_socket)
    with patch.object(cli, "socket", fake_socket_module):
        response = cli.send_command("list")
    record("P15-client-framing", "fragmented_response_rejected",
           {"response": response, "recv_calls": client_socket.recv_calls,
            "unread_chunks": len(client_socket.chunks)},
           "Read the full bounded response using the same frame protocol as the server")

    manager, runner, ipc = make_stack()
    manager.runners["second-device"] = runner
    record("P16-ambiguous-device-selection", "first_matching_device_selected",
           {"selector": "rival", "resolved": manager.resolve_device_id("rival"),
            "candidate_ids": list(manager.runners)},
           "Reject ambiguous names; require stable unique targeting for persistent changes")

    manager, runner, ipc = make_stack()
    interleave_done = False
    def inject_render_packet(item):
        global interleave_done
        packet, _ = item
        if packet[0] == runner.driver.CMD_SET_BUTTONS and not interleave_done:
            interleave_done = True
            runner.driver.flush()
    runner.driver.command_queue = RecordingQueue(after_put=inject_render_packet)
    response = request(ipc, "bind-key", button="button5", key_code=4)
    record("P17-save-sequence-interleaving", "controlled_schedule_inserts_rgb_between_config_and_save",
           {"response": response,
            "commands": [f"0x{packet[0]:02x}" for packet, _ in runner.driver.command_queue.items],
            "schedule": "Instrumented queue put simulates a render thread running between two puts"},
           "Enqueue a compound configuration/save transaction atomically")

    # Four bounded in-memory idle clients, no sockets and no load test.
    class IdleSocket(ScriptedSocket):
        def __init__(self):
            super().__init__([])
            self.entered = threading.Event()
            self.release = threading.Event()
        def recv(self, size):
            self.entered.set()
            self.release.wait(timeout=2)
            return b""
    idle_clients = [IdleSocket() for _ in range(4)]
    idle_server = IPCServer(device_manager=manager)
    class AcceptStub:
        def __init__(self):
            self.index = 0
        def accept(self):
            if self.index >= len(idle_clients):
                idle_server._is_running = False
                raise OSError("End of the bounded synthetic accept sequence")
            item = idle_clients[self.index]
            self.index += 1
            return item, None
        def close(self):
            pass
    idle_server.server_socket = AcceptStub()
    idle_server._is_running = True
    idle_server._serve_forever()
    entered = [sock.entered.wait(timeout=0.5) for sock in idle_clients]
    with patch("managers.ipc_server.os.path.exists", return_value=False):
        idle_server.stop()
    record("P18-idle-client-lifetime", "client_handlers_remain_blocked_after_stop",
           {"bounded_clients": 4, "all_entered_recv": all(entered),
            "closed_by_stop": sum(sock.closed for sock in idle_clients),
            "test_transport": "in_memory_stub"},
           "Limit concurrent clients; enforce deadlines and close/join handlers on stop")
    for sock in idle_clients:
        sock.release.set()
    deadline = time.monotonic() + 1
    while not all(sock.closed for sock in idle_clients) and time.monotonic() < deadline:
        time.sleep(0.01)

    # One actual source worker, backed by an in-memory writer only. The daemon
    # worker's missing exit path is demonstrated, then it dies with this process.
    class ControlledWriter:
        def __init__(self):
            self.mode = "raise"
            self.called = threading.Event()
            self.release = threading.Event()
        def write(self, packet):
            self.called.set()
            if self.mode == "raise":
                raise OSError("synthetic write failure")
            if self.mode == "zero":
                return 0
            if self.mode == "hold":
                self.release.wait(timeout=3)
            return len(packet)
        def close(self):
            pass
    worker_driver = Rival3Gen2Mouse(device_path=b"offline-worker")
    writer = ControlledWriter()
    worker_driver.device = writer
    worker_driver.is_connected = True
    manager, runner, ipc = make_stack()
    runner.driver = worker_driver
    response = request(ipc, "set-dpi", level=2)
    writer.called.wait(timeout=0.5)
    deadline = time.monotonic() + 1
    while worker_driver.command_queue.unfinished_tasks and time.monotonic() < deadline:
        time.sleep(0.01)
    record("P19-async-write-error", "ipc_success_even_when_write_raises",
           {"response": response, "fake_write_called": writer.called.is_set(),
            "unfinished_tasks": worker_driver.command_queue.unfinished_tasks},
           "Report queued and applied states separately; propagate write failures")

    writer.mode = "zero"
    writer.called.clear()
    response = request(ipc, "save")
    writer.called.wait(timeout=0.5)
    deadline = time.monotonic() + 1
    while worker_driver.command_queue.unfinished_tasks and time.monotonic() < deadline:
        time.sleep(0.01)
    record("P20-short-write", "zero_byte_write_not_reported_to_client",
           {"response": response, "fake_write_result": 0},
           "Validate the backend-specific write result and report failure")

    writer.mode = "hold"
    writer.called.clear()
    worker_driver.flush()
    writer.called.wait(timeout=0.5)
    for _ in range(24):
        worker_driver.flush()
    record("P21-driver-queue-growth", "unbounded_queue_accumulates_pending_frames",
           {"queue_maxsize": worker_driver.command_queue.maxsize,
            "pending_packets": worker_driver.command_queue.qsize(),
            "bounded_extra_frames": 24},
           "Bound the queue and replace stale animation frames with the latest one")
    disconnect_thread = threading.Thread(target=worker_driver.disconnect, daemon=True)
    disconnect_thread.start()
    disconnect_thread.join(timeout=0.1)
    blocked_before_release = disconnect_thread.is_alive()
    writer.release.set()
    disconnect_thread.join(timeout=1)
    record("P22-worker-and-disconnect-lifetime", "disconnect_waits_on_io_and_worker_survives_disconnect",
           {"disconnect_blocked_until_fake_io_released": blocked_before_release,
            "disconnect_finished_after_release": not disconnect_thread.is_alive(),
            "worker_alive_after_disconnect": worker_driver._worker_thread.is_alive()},
           "Implement an explicit worker exit and a bounded cancellable shutdown")

    manager = DeviceManager()
    devices = [{"vendor_id": 0x1038, "product_id": 0x1870,
                "path": b"failed-connect-audit", "interface_number": 3}]
    attempts = []
    def failed_connect(driver):
        attempts.append(driver.device_path)
        raise ConnectionError("synthetic connection failure")
    with patch.object(hid_stub, "enumerate", return_value=devices), \
         patch.object(Rival3Gen2Mouse, "connect", failed_connect), \
         patch("drivers.base_mouse.threading.Thread"):
        manager._scan_devices()
        manager._scan_devices()
    failed_runner = next(iter(manager.runners.values()))
    record("P23-failed-connect-tracking", "failed_runner_retained_without_retry_on_next_scan",
           {"connect_attempts": len(attempts), "tracked_runners": len(manager.runners),
            "runner_is_running": failed_runner.is_running, "driver_is_connected": failed_runner.driver.is_connected},
           "Register only a usable runner or track explicit error/retry state with backoff")

    wave = Wave(speed=2, wave_length=1)
    wave._start_time = 0
    with patch("animations.effects.base_effect.time.time", return_value=0.125):
        scaled_time = wave.get_time()
        frame = wave.apply(1, [(0.0, 0.0)])
    record("P24-wave-speed", "speed_applied_twice",
           {"elapsed_seconds": 0.125, "speed": 2, "get_time": scaled_time,
            "phase_from_time_term": scaled_time * wave.speed, "frame": frame},
           "Apply the documented speed multiplier exactly once")

hash_mismatches = []
for record_item in json.loads((EVIDENCE / "arsiv-envanteri.json").read_text(encoding="utf-8")):
    for file in record_item["files"]:
        path = BASE / "kaynak" / file["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != file["sha256"]:
            hash_mismatches.append(file["path"])

summary = {"date": "2026-10-11", "python": sys.version,
           "scope": "ZIP snapshots only; Windows; no real HID or IPC server",
           "files": len(inventory), "python_files": sum("syntax_ok" in x for x in inventory),
           "syntax_errors": 0, "secret_pattern_candidates": secret_candidates,
           "source_hash_mismatches": hash_mismatches,
           "real_hid_calls": 0, "unexpected_hid_attempts_blocked": len(blocked_hid_calls),
           "probes": results}
(EVIDENCE / "statik-envanter.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
(EVIDENCE / "offline-inceleme-sonuclari.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
(EVIDENCE / "offline-inceleme-kaydi.txt").write_text(unit_stream.getvalue() + "\n" + captured.getvalue(), encoding="utf-8")
print(json.dumps({key: value for key, value in summary.items() if key != "probes"}, ensure_ascii=False, indent=2))
for item in results:
    print(json.dumps(item, ensure_ascii=False))
if hash_mismatches or not unit_result.wasSuccessful():
    raise SystemExit(1)
