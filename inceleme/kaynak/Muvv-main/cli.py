import socket
import json
import argparse
import sys

SOCKET_PATH = "/tmp/muvv.sock"

def send_command(command: str, args: dict = None):
    """Sends a JSON command to the Muvv daemon via UDS."""
    if args is None:
        args = {}
        
    payload = {
        "command": command,
        "args": args
    }
    
    try:
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SOCKET_PATH)
        client_socket.sendall(json.dumps(payload).encode("utf-8"))
        
        response_data = client_socket.recv(4096)
        if response_data:
            response = json.loads(response_data.decode("utf-8"))
            return response
        else:
            return {"status": "error", "message": "No response from daemon."}
            
    except ConnectionRefusedError:
        return {"status": "error", "message": "Daemon is not running or socket is dead. (Connection refused)"}
    except FileNotFoundError:
        return {"status": "error", "message": f"Socket file {SOCKET_PATH} not found. Ensure the daemon is running."}
    except Exception as e:
        return {"status": "error", "message": f"IPC Communication error: {e}"}
    finally:
        try:
            client_socket.close()
        except:
            pass

def print_response(response: dict):
    """Formats and prints the daemon's response cleanly."""
    status = response.get("status")
    
    if status == "ok":
        if "devices" in response:
            print("--- Active Devices ---")
            devices = response["devices"]
            if not devices:
                print("No active devices found.")
            for dev in devices:
                idx = dev.get('index', '1')
                print(f" [{idx}] ID: {dev.get('id', 'N/A')} | Name: {dev.get('name', 'Unknown')}")
            print("----------------------")
            print(" (Tip: You can use '1', 'default', or partial name instead of full Device IDs)")
        elif "capabilities" in response:
            device_id = response.get("device", "Unknown")
            caps = response["capabilities"]
            print(f"=== Device Capabilities & Info [{device_id}] ===")
            dpi_info = caps.get("dpi", {})
            print(f"• DPI Type         : {dpi_info.get('type', 'N/A')}")
            print(f"• Max DPI Stages   : {dpi_info.get('max_stages', 'N/A')}")
            supported_dpi = dpi_info.get("supported_values", [])
            if len(supported_dpi) > 8:
                dpi_preview = f"{supported_dpi[:4]} ... {supported_dpi[-4:]} ({len(supported_dpi)} total values)"
            else:
                dpi_preview = str(supported_dpi)
            print(f"• Supported DPIs   : {dpi_preview}")
            print(f"• Polling Rates    : {caps.get('polling_rates', [])} Hz")
            rgb_info = caps.get("rgb", {})
            print(f"• RGB Supported    : {rgb_info.get('supported', False)}")
            print(f"• RGB Zones        : {', '.join(rgb_info.get('zones', []))}")
            print(f"• RGB Effects      : {', '.join(rgb_info.get('effects', []))}")
            print(f"• Buttons          : {caps.get('programmable_buttons', 0)} programmable")
            print(f"• Macro Support    : {caps.get('macro_support', False)}")
            print("==================================================")
        elif "message" in response:
            print(f"Success: {response['message']}")
        else:
            print("Success")
    else:
        print(f"Error: {response.get('message', 'Unknown error occurred.')}")

def parse_color_option(color_str: str):
    """Helper to parse a hex color string into a list of [R, G, B]."""
    if not color_str:
        return None
    try:
        hex_clean = color_str.lstrip('#')
        if len(hex_clean) != 6:
            raise ValueError
        return [int(hex_clean[i:i+2], 16) for i in (0, 2, 4)]
    except ValueError:
        print("Error: Invalid hex color format. Use e.g. #FF0000 or FF0000.")
        sys.exit(1)

def normalize_sys_argv():
    """
    Normalizes sys.argv so intuitive syntax variations like:
    'cli.py set-effect 1 breathing' or 'cli.py set-color 1 FF0000' or 'cli.py set-dpi 1 2'
    are converted seamlessly to standardized argparse order.
    """
    if len(sys.argv) < 3:
        return

    cmd = sys.argv[1]

    # Case 1: set-effect [device] <effect> -> set-effect <effect> -d [device]
    if cmd == "set-effect":
        known_effects = {"wave", "breathing", "static"}
        first_arg = sys.argv[2]
        if first_arg.lower() not in known_effects and not first_arg.startswith("-"):
            device_token = sys.argv.pop(2)
            sys.argv.extend(["-d", device_token])

    # Case 2: set-color [device] <hex> -> set-color <hex> [device]
    elif cmd == "set-color":
        first_arg = sys.argv[2]
        clean_hex = first_arg.lstrip('#')
        is_hex = (len(clean_hex) == 6 and all(c in "0123456789abcdefABCDEF" for c in clean_hex))
        
        if not is_hex and len(sys.argv) > 3:
            device_token = sys.argv.pop(2)
            sys.argv.insert(3, device_token)

    # Case 3: set-dpi [device] <level> -> set-dpi <level> [device]
    elif cmd == "set-dpi":
        if len(sys.argv) > 3:
            try:
                val1 = int(sys.argv[2])
                val2 = int(sys.argv[3])
                if 0 <= val2 <= 10:
                    device_token = sys.argv.pop(2)
                    sys.argv.insert(3, device_token)
            except ValueError:
                device_token = sys.argv.pop(2)
                sys.argv.insert(3, device_token)

    # Case 4: set-polling [device] <hz> -> set-polling <hz> [device]
    elif cmd == "set-polling":
        if len(sys.argv) > 3:
            try:
                hz = int(sys.argv[3])
                if hz in (125, 250, 500, 1000):
                    device_token = sys.argv.pop(2)
                    sys.argv.insert(3, device_token)
            except ValueError:
                pass

def main():
    normalize_sys_argv()

    parser = argparse.ArgumentParser(description="Muvv CLI - Hardware Independent RGB Sync")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available Commands")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List active and supported devices managed by the daemon.")

    # Command: info
    info_parser = subparsers.add_parser("info", help="Display detailed hardware capabilities and specs of a device.")
    info_parser.add_argument("device", nargs="?", default="default", help="Device ID, index (e.g. 1), or 'default' (default: 1)")

    # Command: set-effect
    effect_parser = subparsers.add_parser("set-effect", help="Set an animation effect on a specific device. Use 'set-effect <effect> --help' for effect-specific help.")
    effect_subparsers = effect_parser.add_subparsers(dest="effect", required=True, help="Available Animation Effects")

    # Effect Subcommand: wave
    wave_parser = effect_subparsers.add_parser("wave", help="Rainbow or custom single-color traveling wave effect.")
    wave_parser.add_argument("-d", "--device", default="default", help="Device ID or index (default: 1)")
    wave_parser.add_argument("--color", help="Hex color code for wave tint (e.g., #FF0000)")
    wave_parser.add_argument("--speed", type=float, help="Speed multiplier (e.g., 1.5, 2.0)")
    wave_parser.add_argument("--direction", choices=["horizontal", "vertical"], help="Wave movement direction")
    wave_parser.add_argument("--wave-length", type=float, help="Wave length parameter (0.1 to 1.0)")

    # Effect Subcommand: breathing
    breathing_parser = effect_subparsers.add_parser("breathing", help="Pulsing brightness breathing animation.")
    breathing_parser.add_argument("-d", "--device", default="default", help="Device ID or index (default: 1)")
    breathing_parser.add_argument("--color", help="Hex color code for breathing (e.g., #00FF00)")
    breathing_parser.add_argument("--speed", type=float, help="Breathing speed multiplier (e.g., 1.5, 2.0)")

    # Effect Subcommand: static
    static_parser = effect_subparsers.add_parser("static", help="Static solid RGB color effect.")
    static_parser.add_argument("-d", "--device", default="default", help="Device ID or index (default: 1)")
    static_parser.add_argument("--color", help="Hex color code (e.g., #0000FF)")

    # Command: set-color
    color_parser = subparsers.add_parser("set-color", help="Set a static RGB color on a specific device.")
    color_parser.add_argument("hex", help="Hex color code (e.g., #FF0000)")
    color_parser.add_argument("device", nargs="?", default="default", help="Device ID or index (default: 1)")

    # Command: set-dpi
    dpi_parser = subparsers.add_parser("set-dpi", help="Set the active DPI stage index on a device.")
    dpi_parser.add_argument("level", type=int, help="The DPI stage index (e.g. 0 to 4)")
    dpi_parser.add_argument("device", nargs="?", default="default", help="Device ID or index (default: 1)")

    # Command: set-polling
    polling_parser = subparsers.add_parser("set-polling", help="Set the polling rate in Hz on a device.")
    polling_parser.add_argument("hz", type=int, choices=[125, 250, 500, 1000], help="Polling rate in Hz (125, 250, 500, 1000)")
    polling_parser.add_argument("device", nargs="?", default="default", help="Device ID or index (default: 1)")

    # Command: bind-key
    bind_parser = subparsers.add_parser("bind-key", help="Bind a keyboard key code to a mouse button.")
    bind_parser.add_argument("button", help="The button name (e.g. button4, button5)")
    bind_parser.add_argument("key_code", help="HID Key code (e.g. 0x04 or 4)")
    bind_parser.add_argument("device", nargs="?", default="default", help="Device ID or index (default: 1)")

    # Command: save
    save_parser = subparsers.add_parser("save", help="Save current settings to the mouse's on-board memory.")
    save_parser.add_argument("device", nargs="?", default="default", help="Device ID or index (default: 1)")

    # Parse args
    args = parser.parse_args()

    # Dispatch to daemon
    if args.command == "list":
        response = send_command("list")
        print_response(response)

    elif args.command == "info":
        response = send_command("info", {
            "device": args.device
        })
        print_response(response)
        
    elif args.command == "set-effect":
        effect_args = {
            "device": getattr(args, "device", "default"),
            "effect": args.effect
        }
        if hasattr(args, "color") and args.color:
            effect_args["color"] = parse_color_option(args.color)
        if hasattr(args, "speed") and args.speed is not None:
            effect_args["speed"] = args.speed
        if hasattr(args, "direction") and args.direction:
            effect_args["direction"] = args.direction
        if hasattr(args, "wave_length") and args.wave_length is not None:
            effect_args["wave_length"] = args.wave_length

        response = send_command("set-effect", effect_args)
        print_response(response)
        
    elif args.command == "set-color":
        response = send_command("set-color", {
            "device": args.device,
            "hex": args.hex
        })
        print_response(response)

    elif args.command == "set-dpi":
        response = send_command("set-dpi", {
            "device": args.device,
            "level": args.level
        })
        print_response(response)

    elif args.command == "set-polling":
        response = send_command("set-polling", {
            "device": args.device,
            "hz": args.hz
        })
        print_response(response)

    elif args.command == "bind-key":
        response = send_command("bind-key", {
            "device": args.device,
            "button": args.button,
            "key_code": args.key_code
        })
        print_response(response)

    elif args.command == "save":
        response = send_command("save", {
            "device": args.device
        })
        print_response(response)

if __name__ == "__main__":
    main()
