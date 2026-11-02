"""Exercise device workflows with an in-memory USB transport and temporary profiles."""

import argparse
import json
import logging
import random
import socket
import struct
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app_version import __version__  # noqa: E402
from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse  # noqa: E402
from ipc_protocol import encode_message, receive_message  # noqa: E402
from managers.device_manager import DeviceManager  # noqa: E402
from managers.device_runner import DeviceRunner  # noqa: E402
from managers.errors import TransportError  # noqa: E402
from profile_io import read_profile_file, write_profile_file  # noqa: E402
from ui_client import fetch_snapshot  # noqa: E402


class RecordingHID:
    def __init__(self):
        self.packets = []
        self.closed = False
        self.fail_on = None

    def write(self, packet):
        if self.fail_on == len(self.packets):
            raise OSError("Simulated USB disconnect")
        self.packets.append(bytes(packet))
        return len(packet)

    def close(self):
        self.closed = True


class SimulatedMouse(Rival3Gen2Mouse):
    def connect(self):
        self.device = RecordingHID()
        self.is_connected = True
        self._reset_session()
        self._start_worker()


def framing_checks(server, iterations, rng):
    valid, rejected = 0, 0
    malformed = [
        b"[]",
        b"null",
        b"\xff",
        b'{"command":"list","command":"save"}',
        b'{"command":"set-polling","args":{"hz":NaN}}',
        b'{"command":"list","args":[]}',
        b'{"command":"set-polling","args":{"hz":true}}',
        b'{"version":true,"command":"list"}',
    ]
    for index in range(iterations):
        left, right = socket.socketpair()
        assert server._slots.acquire(blocking=False)
        worker = threading.Thread(target=server._handle_client, args=(right,), name="simulation-ipc")
        with server._clients_lock:
            server._clients[right] = worker
        worker.start()
        try:
            invalid = index % 3 != 0
            if invalid:
                body = malformed[index % len(malformed)]
                frame = struct.pack("!I", len(body)) + body
            else:
                frame = encode_message({"command": "snapshot", "args": {}})
            offset = 0
            while offset < len(frame):
                count = rng.randint(1, 23)
                left.sendall(frame[offset : offset + count])
                offset += count
            result = receive_message(left, limit=65536, timeout=2)
            assert result["status"] == ("error" if invalid else "ok"), result
            rejected += invalid
            valid += not invalid
        finally:
            left.close()
            worker.join(2)
            assert not worker.is_alive()
    assert not server._clients
    acquired = [server._slots.acquire(blocking=False) for _ in range(server.MAX_CLIENTS)]
    assert all(acquired)
    assert not server._slots.acquire(blocking=False)
    for _ in acquired:
        server._slots.release()
    return {
        "fragmented_roundtrips": iterations,
        "valid": valid,
        "rejected": rejected,
        "client_slots_restored": True,
    }


def concurrent_reports(runner, iterations):
    handle = runner.driver.device
    begin = len(handle.packets)

    def producer(identifier):
        for sequence in range(iterations):
            reports = tuple((bytes([0x71, identifier, sequence, part]) + bytes(60), 0) for part in range(3))
            runner.driver.transact(reports)

    with ThreadPoolExecutor(max_workers=8, thread_name_prefix="simulation-producer") as executor:
        futures = [executor.submit(producer, identifier) for identifier in range(8)]
        for future in futures:
            future.result(10)
    packets = handle.packets[begin:]
    assert len(packets) == 8 * iterations * 3
    observed = set()
    for offset in range(0, len(packets), 3):
        batch = packets[offset : offset + 3]
        identity = batch[0][1:3]
        assert all(packet[1:3] == identity for packet in batch)
        assert [packet[3] for packet in batch] == [0, 1, 2]
        observed.add(tuple(identity))
    assert len(observed) == 8 * iterations
    return {
        "producers": 8,
        "transactions": len(observed),
        "reports": len(packets),
        "interleaved_transactions": 0,
    }


def reconnect_checks(manager, runner, iterations, directory):
    sessions = set()
    server = manager.ipc_server

    def client(command, payload):
        return server._process_command({"command": command, "args": payload})

    for index in range(iterations):
        before = runner.get_state()["session_id"]
        old = runner.driver.device
        assert client("reconnect", {"expected_session": before})["status"] == "ok"
        assert old.closed
        state = runner.get_state()
        assert not state["settings"] and state["effect"] is None
        assert state["session_id"] != before
        sessions.add(state["session_id"])
        stale = client("set-polling", {"hz": 500, "expected_session": before})
        assert stale["code"] == "device_changed"
        assert not runner.driver.device.packets
        current = {"expected_session": state["session_id"]}
        assert (
            client("set-dpi-stages", {"stages": [400 + index % 2 * 100, 800, 1200, 2400, 3200], **current})[
                "status"
            ]
            == "ok"
        )
        assert client("set-polling", {"hz": 500, **current})["status"] == "ok"
        assert client("restore-buttons", {"persist": False, **current})["status"] == "ok"
        assert (
            client(
                "set-colors",
                {"colors": {zone: [index % 256, 22, 33] for zone in runner.zone_map.zone_names}, **current},
            )["status"]
            == "ok"
        )
        profile = manager.save_host_profile("simulated", "Scenario", overwrite=True)
        filename = directory / "exchange.json"
        write_profile_file(filename, profile, overwrite=True)
        assert read_profile_file(filename) == json.loads(json.dumps(profile))
        manager.profile_store.rename("Scenario", "Renamed")
        manager.profile_store.rename("Renamed", "Scenario")
        snapshot = fetch_snapshot(client, "simulated")
        assert snapshot["profiles_complete"]
        assert snapshot["info"]["state"]["session_id"] == state["session_id"]
        assert len(snapshot["profiles"]) == 1
    assert len(sessions) == iterations
    return {
        "cycles": iterations,
        "unique_sessions": len(sessions),
        "stale_writes_blocked": iterations,
        "file_roundtrips": iterations,
        "profile_renames": iterations * 2,
        "closed_old_handles": iterations,
    }


def failure_checks(runner):
    settings = {
        "dpi": {"stages": [400, 800, 1200, 2400, 3200], "active": 1},
        "polling_rate": 500,
        "colors": {zone: [1, 2, 3] for zone in runner.zone_map.zone_names},
    }
    for index in range(4):
        runner.reconnect()
        handle = runner.driver.device
        handle.fail_on = index
        try:
            runner.driver.apply_settings(settings, persist=True)
        except TransportError:
            pass
        else:
            raise AssertionError("Simulated disconnect must not report success")
        assert len(handle.packets) == index
        assert not runner.driver.is_connected
        assert not runner.get_state()["settings"]
        try:
            runner.set_polling(250)
        except TransportError:
            pass
        else:
            raise AssertionError("Writes after failure must be rejected")
        assert len(handle.packets) == index
        runner.reconnect()
        assert handle.closed and not runner.driver.device.packets
    return {"failed_report_positions": 4, "false_successes": 0, "writes_after_failure": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--json", type=Path)
    options = parser.parse_args(argv)
    if not 1 <= options.cycles <= 200:
        parser.error("--cycles must be between 1 and 200")
    logging.basicConfig(level=logging.ERROR)
    started = time.monotonic()
    baseline = {thread.ident for thread in threading.enumerate() if thread.name.startswith("muvv-")}
    with (
        patch.dict("sys.modules", {"hid": None}),
        tempfile.TemporaryDirectory(prefix="muvv-simulation-") as temporary,
    ):
        directory = Path(temporary)
        manager = DeviceManager(enumerate_devices=lambda: [], profile_directory=directory / "profiles")
        runner = DeviceRunner(SimulatedMouse, b"simulated")
        runner.start()
        manager.runners["simulated"] = runner
        try:
            results = {
                "framing": framing_checks(
                    manager.ipc_server, options.cycles * 10, random.Random(options.seed)
                ),
                "concurrency": concurrent_reports(runner, min(options.cycles, 100)),
                "reconnect_and_profiles": reconnect_checks(manager, runner, options.cycles, directory),
                "usb_failures": failure_checks(runner),
            }
        finally:
            assert manager.stop()
        assert runner.driver.device is None
    remaining = [
        thread.name
        for thread in threading.enumerate()
        if thread.name.startswith("muvv-") and thread.ident not in baseline
    ]
    assert not remaining, remaining
    report = {
        "successful": True,
        "version": __version__,
        "platform": sys.platform,
        "python": sys.version,
        "seed": options.seed,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "physical_hid_access": False,
        "linux_peer_credentials_and_permissions_checked": False,
        "remaining_workers": remaining,
        "scenarios": results,
    }
    if options.json:
        options.json.parent.mkdir(parents=True, exist_ok=True)
        options.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
