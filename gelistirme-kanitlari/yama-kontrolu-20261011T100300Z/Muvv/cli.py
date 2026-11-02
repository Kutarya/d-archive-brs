import argparse
import json
import os
import socket
import stat
import sys
from pathlib import Path

from animations.effect_registry import create_effect, get_effect_class
from ipc_protocol import (
    MAX_REQUEST,
    MAX_RESPONSE,
    PROTOCOL_VERSION,
    private_directory,
    receive_message,
    require_linux,
    send_message,
    socket_path,
    verify_peer,
)
from managers.errors import MuvvError, ProtocolError
from managers.validator import key_code, rgb


def send_command(command, args=None, socket_file=None, timeout=5.0):
    try:
        require_linux()
        path = Path(socket_file) if socket_file is not None else socket_path()
        private_directory(path.parent, create=False)
        metadata = path.lstat()
        if (
            not stat.S_ISSOCK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) & 0o077
        ):
            raise ProtocolError("IPC path must be an owned Unix socket with mode 0600.")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(timeout)
            connection.connect(str(path))
            verify_peer(connection)
            send_message(
                connection,
                {"version": PROTOCOL_VERSION, "command": command, "args": args or {}},
                MAX_REQUEST,
                timeout,
            )
            response = receive_message(connection, MAX_RESPONSE, timeout)
        if response.get("status") not in ("ok", "error"):
            raise ProtocolError("Daemon returned an invalid response.")
        return response
    except MuvvError as error:
        return {"status": "error", "code": error.code, "message": str(error)}
    except OSError as error:
        return {
            "status": "error",
            "code": "connection_error",
            "message": f"Cannot reach Muvv: {error}. Start muvvd first.",
        }


def print_response(response, json_output=False):
    if json_output:
        print(json.dumps(response, ensure_ascii=False, allow_nan=False, indent=2))
    elif response.get("status") == "error":
        print(
            f"Error [{response.get('code', 'unknown')}]: {response.get('message', 'Command failed.')}",
            file=sys.stderr,
        )
    elif "devices" in response:
        devices = response["devices"]
        if not devices:
            print("No supported devices connected.")
        for device in devices:
            print(f"[{device['index']}] {device['name']}  {device['id']!r}")
    elif "effects" in response:
        for effect in response["effects"]:
            print(f"{effect['id']}: {effect['name']} ({', '.join(effect['parameters'])})")
    elif "profiles" in response:
        for profile in response["profiles"]:
            print(profile["name"])
        if not response["profiles"]:
            print("No saved profiles.")
    elif any(key in response for key in ("capabilities", "state", "profile", "daemon")):
        print(
            json.dumps(
                {key: value for key, value in response.items() if key != "status"},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(response.get("message", "Applied."))
        if response.get("transport") == "written":
            print(f"USB: {response['reports']} report(s) written; hardware readback is unavailable.")
        if response.get("persistence_requested"):
            print("On-board save command sent.")


def parse_color_option(value):
    return list(rgb(value))


def normalize_arguments(arguments):
    arguments = list(arguments)
    if len(arguments) < 3:
        return arguments
    command, first, second = arguments[:3]
    if first.startswith("-") or second.startswith("-"):
        return arguments
    if command == "set-effect" and get_effect_class(first) is None and get_effect_class(second) is not None:
        return [command, second, *arguments[3:], "-d", first]
    if command == "set-color":
        try:
            rgb(first)
        except MuvvError:
            try:
                rgb(second)
            except MuvvError:
                return arguments
            return [command, second, first, *arguments[3:]]
    if command in ("set-dpi", "set-polling") and not first.isdecimal() and second.isdecimal():
        return [command, second, first, *arguments[3:]]
    return arguments


def normalize_sys_argv():
    sys.argv[1:] = normalize_arguments(sys.argv[1:])


def _device(parser, positional=True):
    if positional:
        parser.add_argument("device", nargs="?", default="default", help="Device ID or list index")
        parser.add_argument("-d", "--device", dest="device_option")
    else:
        parser.add_argument("-d", "--device", default="default", help="Device ID or list index")


def _effect_options(parser, effect=None):
    if effect is None or effect in ("static", "breathing", "wave"):
        parser.add_argument("--color", type=parse_color_option)
    if effect is None or effect in ("breathing", "wave", "spectrum"):
        parser.add_argument("--speed", type=float)
    if effect is None or effect == "wave":
        parser.add_argument("--direction", choices=("vertical", "horizontal"))
        parser.add_argument("--wave-length", type=float)
    if effect is None or effect == "spectrum":
        parser.add_argument("--brightness", type=float)


def build_parser():
    parser = argparse.ArgumentParser(description="Muvv mouse control client")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable response")
    parser.add_argument("--socket", help="Use a different private Unix socket")
    parser.add_argument("--version", action="version", version="Muvv 0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("list", "List connected devices"),
        ("status", "Show daemon status"),
        ("effects", "List effect parameters"),
        ("list-profiles", "List host profiles"),
    ):
        commands.add_parser(command, help=help_text)
    for command in ("info", "save", "reconnect"):
        _device(commands.add_parser(command))
    effect_parser = commands.add_parser("set-effect", help="Select an RGB effect")
    effects = effect_parser.add_subparsers(dest="effect", required=True)
    for effect in ("static", "breathing", "wave", "spectrum"):
        child = effects.add_parser(effect, aliases=["staticcolor"] if effect == "static" else [])
        _device(child, positional=False)
        _effect_options(child, effect)
    update = commands.add_parser(
        "update-effect", help="Change the active effect without restarting its clock"
    )
    _device(update, positional=False)
    _effect_options(update)
    color = commands.add_parser("set-color")
    color.add_argument("color", type=parse_color_option)
    _device(color)
    dpi = commands.add_parser("set-dpi", help="Select a known DPI slot (0–4)")
    dpi.add_argument("level", type=int)
    dpi.add_argument("--initialize", action="store_true", help="Replace unknown DPI slots with Muvv defaults")
    _device(dpi)
    stages = commands.add_parser("set-dpi-stages", help="Set all five DPI slots explicitly")
    stages.add_argument("stages", nargs=5, type=int)
    stages.add_argument("--active", type=int, default=0)
    _device(stages, positional=False)
    polling = commands.add_parser("set-polling")
    polling.add_argument("hz", type=int, choices=(125, 250, 500, 1000))
    _device(polling)
    bind = commands.add_parser("bind-key")
    bind.add_argument("button")
    bind.add_argument(
        "key_code", type=lambda value: int(value, 0) if value.lower().startswith("0x") else int(value)
    )
    bind.add_argument(
        "--initialize", action="store_true", help="Replace unknown button mappings with Muvv defaults"
    )
    bind.add_argument("--no-persist", action="store_true", help="Apply without an on-board save")
    _device(bind)
    restore = commands.add_parser("restore-buttons", help="Replace all assignments with Muvv defaults")
    restore.add_argument("--no-persist", action="store_true")
    _device(restore)
    save_profile = commands.add_parser("save-profile", help="Save known settings to a host profile")
    save_profile.add_argument("name")
    save_profile.add_argument("--overwrite", action="store_true")
    _device(save_profile, positional=False)
    apply_profile = commands.add_parser("apply-profile", help="Apply a host profile")
    apply_profile.add_argument("name")
    apply_profile.add_argument("--persist", action="store_true", help="Also request on-board persistence")
    _device(apply_profile, positional=False)
    for command in ("show-profile", "delete-profile"):
        commands.add_parser(command).add_argument("name")
    return parser


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    # Accept --json before or after a subcommand.
    json_output = "--json" in arguments
    arguments = [argument for argument in arguments if argument != "--json"]
    parser = build_parser()
    try:
        namespace = parser.parse_args(normalize_arguments(arguments))
        values = vars(namespace)
        command = values.pop("command")
        socket_file = values.pop("socket")
        values.pop("json")
        explicit_device = values.pop("device_option", None)
        if explicit_device is not None:
            values["device"] = explicit_device
        if "no_persist" in values:
            values["persist"] = not values.pop("no_persist")
        values = {key: value for key, value in values.items() if value is not None}
        if command == "set-effect":
            create_effect(
                values["effect"],
                {key: value for key, value in values.items() if key not in ("effect", "device")},
            )
        if command == "bind-key":
            key_code(values["key_code"])
        response = send_command(command, values, socket_file=socket_file)
    except MuvvError as error:
        response = {"status": "error", "code": error.code, "message": str(error)}
    print_response(response, json_output)
    return 0 if response.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
