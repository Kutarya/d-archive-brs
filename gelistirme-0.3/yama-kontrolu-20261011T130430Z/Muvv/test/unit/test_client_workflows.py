import io
import json
import socket
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import cli
from animations.effect_registry import create_effect
from app_version import __version__
from demo import DemoClient
from diagnostics import environment_report
from ipc_protocol import decode_json, receive_message, send_message
from keyboard_keys import KEY_NAMES, key_label
from managers.errors import ProtocolError, ValidationError
from managers.ipc_server import IPCServer
from ui_client import ServiceError, command_then_snapshot, fetch_snapshot, require_ok


class ClientWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.client = DemoClient()

    def tearDown(self):
        self.client.close()

    def test_successful_write_is_preserved_when_refresh_fails(self):
        commands = []

        def client(command, payload):
            commands.append(command)
            if command == "snapshot":
                return {"status": "error", "message": "refresh unavailable"}
            return self.client(command, payload)

        result = command_then_snapshot(client, "set-polling", {"hz": 500}, "demo-rival-3")
        self.assertEqual(self.client.runner.driver.polling_rate, 500)
        self.assertEqual(result["response"]["transport"], "written")
        self.assertIsNone(result["snapshot"])
        self.assertEqual(result["refresh_error"], "refresh unavailable")
        self.assertEqual(commands, ["set-polling", "snapshot"])

    def test_failed_operation_has_no_automatic_retry_or_refresh(self):
        commands = []

        def client(command, payload):
            commands.append(command)
            return {"status": "error", "code": "operation_uncertain", "message": "USB timeout"}

        with self.assertRaises(ServiceError) as error:
            command_then_snapshot(client, "set-polling", {"hz": 500})
        self.assertEqual(error.exception.code, "operation_uncertain")
        self.assertEqual(commands, ["set-polling"])

    def test_pagination_cycles_and_invalid_offsets_are_rejected(self):
        for offset in (True, 128, -1, 1.5, 32):

            def client(command, payload, offset=offset):
                result = self.client("snapshot") if command == "snapshot" else self.client("list-profiles")
                result["next_offset"] = offset
                return result

            with self.subTest(offset=offset), self.assertRaises(ProtocolError):
                fetch_snapshot(client)

    def test_snapshot_does_not_modify_the_client_response(self):
        original = self.client("snapshot")
        before = deepcopy(original)
        result = fetch_snapshot(lambda *_: original)
        result["profiles"].clear()
        self.assertEqual(original, before)

    def test_later_profile_page_failure_keeps_the_device_snapshot(self):
        original = self.client("snapshot")
        original["next_offset"] = 32

        def client(command, payload):
            if command == "snapshot":
                return original
            return {"status": "error", "code": "connection_error", "message": "page unavailable"}

        result = fetch_snapshot(client)
        self.assertEqual(result["selected_device"], "demo-rival-3")
        self.assertEqual(result["info"], original["info"])
        self.assertFalse(result["profiles_complete"])
        self.assertEqual(result["profile_refresh_error"], "page unavailable")
        self.assertEqual(result["profiles"], original["profiles"])

    def test_profile_catalog_change_is_visible_without_mixing_pages(self):
        original = self.client("snapshot")
        original["next_offset"] = 32
        self.client.manager.save_host_profile("demo-rival-3", "Another")

        def client(command, payload):
            return original if command == "snapshot" else self.client(command, payload)

        result = fetch_snapshot(client)
        self.assertFalse(result["profiles_complete"])
        self.assertIn("değişti", result["profile_refresh_error"])
        self.assertEqual(result["profiles"], original["profiles"])

    def test_malformed_service_response_is_rejected_before_ui_consumes_it(self):
        snapshot = self.client("snapshot")
        for mutate in (
            lambda value: value.update(devices=None),
            lambda value: value.update(selected_device="absent"),
            lambda value: value["devices"].append(value["devices"][0]),
            lambda value: value["info"]["state"].update(transport=[]),
            lambda value: value["devices"][0].update(vendor_id=[]),
            lambda value: value["info"]["state"].update(unknown_fields=["dpi"]),
            lambda value: value["info"]["state"].update(session_id="bad"),
            lambda value: value["info"]["state"]["settings"]["dpi"].update(stages=[400]),
            lambda value: value["info"]["state"].update(effect={"name": "wave", "options": []}),
            lambda value: value["profiles"][0].update(name=[]),
            lambda value: value.update(profile_errors=[{}]),
            lambda value: value.update(profile_count=True),
            lambda value: value.update(profile_limit_exceeded=1),
            lambda value: value.update(catalog_id="invalid"),
        ):
            response = deepcopy(snapshot)
            mutate(response)
            with self.subTest(mutate=mutate), self.assertRaises(ProtocolError):
                fetch_snapshot(lambda *_, response=response: response)

    def test_malformed_later_page_is_not_silently_treated_as_network_failure(self):
        first = self.client("snapshot")
        first["next_offset"] = 32
        with self.assertRaises(ProtocolError):
            fetch_snapshot(
                lambda command, _: first if command == "snapshot" else {"status": "ok", "profiles": "bad"}
            )

    def test_unknown_status_and_non_text_error_are_protocol_errors(self):
        for response in (
            {"status": "maybe"},
            {"status": "error", "message": {}},
            {"status": "error", "code": 1},
        ):
            with self.subTest(response=response), self.assertRaises(ProtocolError):
                require_ok(response)

    def test_zones_and_stop_animation_preserve_usable_colors(self):
        result = self.client("stop-effect")
        self.assertEqual(result["status"], "ok")
        self.assertIsNone(self.client.runner.get_state()["effect"])
        colors = {"wheel": [255, 0, 0], "middle": [0, 255, 0], "underglow": [0, 0, 255]}
        self.assertEqual(self.client("set-colors", {"colors": colors})["status"], "ok")
        state = self.client.runner.get_state()
        self.assertEqual({zone: list(color) for zone, color in state["settings"]["colors"].items()}, colors)
        self.assertIsNone(state["effect"])
        self.assertEqual(self.client("stop-effect")["transport"], "unchanged")
        before = state["settings"]["colors"]
        result = self.client("set-colors", {"colors": {"wheel": [999, 0, 0]}})
        self.assertEqual(result["status"], "error")
        self.assertEqual(self.client.runner.get_state()["settings"]["colors"], before)

    def test_mouse_function_assignment_still_guards_left_click(self):
        self.assertEqual(self.client("set-button", {"button": "button4", "assignment": 0x30})["status"], "ok")
        self.assertEqual(self.client.runner.driver.button_config["button4"], 0x30)
        self.assertEqual(self.client("set-button", {"button": "button1", "assignment": 0})["status"], "error")
        self.assertEqual(self.client.runner.driver.button_config["button1"], 1)

    def test_cli_exchange_pagination_and_new_device_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = str(Path(directory) / "exchange.json")
            with (
                patch("cli.send_command", side_effect=lambda command, args, **_: self.client(command, args)),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(cli.main(["export-profile", "Çalışma", filename]), 0)
                self.assertEqual(cli.main(["import-profile", filename, "--name", "Imported"]), 0)
                self.assertEqual(cli.main(["rename-profile", "Imported", "New name"]), 0)
                self.assertEqual(cli.main(["list-profiles", "--all", "--limit", "1"]), 0)
                self.assertEqual(cli.main(["set-button", "button4", "0x30"]), 0)
                self.assertEqual(
                    cli.main(
                        ["set-colors", "--wheel", "FF0000", "--middle", "00FF00", "--underglow", "0000FF"]
                    ),
                    0,
                )
                self.assertEqual(cli.main(["stop-effect"]), 0)
            self.assertEqual(self.client.manager.profile_store.load("New name")["name"], "New name")

    def test_json_flag_after_separator_can_be_a_literal_profile_name(self):
        with patch("cli.send_command", return_value={"status": "ok"}) as send, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["show-profile", "--", "--json"]), 0)
        self.assertEqual(send.call_args.args, ("show-profile", {"name": "--json"}))

    def test_doctor_has_no_hardware_or_filesystem_side_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            config, runtime = Path(directory) / "config", Path(directory) / "runtime"
            with (
                patch.dict("os.environ", {"XDG_CONFIG_HOME": str(config), "XDG_RUNTIME_DIR": str(runtime)}),
                patch("hid.enumerate") as scan,
            ):
                report = environment_report()
            self.assertEqual(report["version"], __version__)
            self.assertFalse(config.exists())
            self.assertFalse(runtime.exists())
            scan.assert_not_called()

    def test_doctor_prints_failed_checks_and_version_uses_same_source(self):
        failed = {
            "healthy": False,
            "version": __version__,
            "python": "3.12",
            "platform": "test",
            "checks": [{"name": "service", "status": "error", "message": "requires Linux"}],
        }
        with (
            patch("cli.environment_report", return_value=failed),
            patch("cli.send_command") as client,
            redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(cli.main(["doctor"]), 1)
        self.assertIn("requires Linux", output.getvalue())
        client.assert_not_called()
        with redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as result:
            cli.main(["--version"])
        self.assertEqual(result.exception.code, 0)
        self.assertEqual(output.getvalue().strip(), f"Muvv {__version__}")

    def test_protocol_rejects_exponent_overflow_and_non_object_effect_options(self):
        for data in (b'{"value":1e999}', b'{"value":-1e999}'):
            with self.assertRaises(ProtocolError):
                decode_json(data)
        for options in (False, [], ""):
            with self.assertRaises(ValidationError):
                create_effect("static", options)
        with self.assertRaises(ProtocolError):
            require_ok([])
        self.assertEqual(KEY_NAMES["A"], 4)
        self.assertEqual(KEY_NAMES["1"], 0x1E)
        self.assertEqual(KEY_NAMES["0"], 0x27)
        self.assertEqual(KEY_NAMES["F12"], 0x45)
        self.assertEqual(KEY_NAMES["Right Shift"], 0xE5)
        self.assertEqual(key_label(0xA0), "0xA0")

    def test_oversized_response_returns_structured_error_without_repeat(self):
        left, right = socket.socketpair()
        server = IPCServer(None, client_timeout=1)
        self.assertTrue(server._slots.acquire(blocking=False))
        server._process_command = lambda _: {"status": "ok", "value": "x" * 65536}
        worker = threading.Thread(target=server._handle_client, args=(right,))
        worker.start()
        try:
            send_message(left, {"command": "list"})
            result = receive_message(left)
            self.assertEqual(result["code"], "response_too_large")
            self.assertTrue(result["operation_completed"])
            json.dumps(result, allow_nan=False)
        finally:
            left.close()
            worker.join(2)
            self.assertFalse(worker.is_alive())
