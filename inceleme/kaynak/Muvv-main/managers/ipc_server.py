import socket
import os
import json
import threading
import logging

logger = logging.getLogger(__name__)

class IPCServer:
    """
    Handles Unix Domain Socket (UDS) communication for the Muvv Daemon.
    Receives JSON commands from the CLI and dispatches them.
    """
    def __init__(self, socket_path: str = "/tmp/muvv.sock", device_manager=None):
        self.socket_path = socket_path
        self.device_manager = device_manager # Reference to the DeviceManager
        self.server_socket = None
        self._is_running = False
        self._server_thread = None

    def start(self):
        """Starts the IPC server in a background thread."""
        if self._is_running:
            return

        # Clean up existing socket file if it exists
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(5)
        self._is_running = True

        self._server_thread = threading.Thread(target=self._serve_forever, daemon=True)
        self._server_thread.start()
        logger.info(f"IPC Server started, listening on {self.socket_path}")

    def stop(self):
        """Stops the IPC server and cleans up the socket."""
        self._is_running = False
        if self.server_socket:
            try:
                # To break the accept() blocking call, we connect to it
                dummy_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                dummy_sock.connect(self.socket_path)
                dummy_sock.close()
            except Exception:
                pass
            
            self.server_socket.close()

        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=2.0)

        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
            
        logger.info("IPC Server stopped.")

    def _serve_forever(self):
        """Main loop to accept connections."""
        while self._is_running:
            try:
                client_socket, _ = self.server_socket.accept()
                if not self._is_running:
                    client_socket.close()
                    break
                
                # Handle each client in a new thread so we don't block
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True)
                client_thread.start()
            except Exception as e:
                if self._is_running:
                    logger.error(f"Error accepting connection: {e}")

    def _handle_client(self, client_socket: socket.socket):
        """Handles a single client connection, reads JSON, and sends a response."""
        try:
            data = client_socket.recv(4096)
            if not data:
                return

            try:
                command_data = json.loads(data.decode('utf-8'))
                # Parse JSON string to Python dictionary
                command_data = json.loads(data.decode("utf-8"))
                logger.debug(f"IPC received command: {command_data}")
                
                # Process the command and get a response
                response = self._process_command(command_data)
                
            except json.JSONDecodeError:
                logger.error("IPC received invalid JSON.")
                response = {"status": "error", "message": "Invalid JSON format"}
            
            # Send the response back as JSON (encoded to bytes)
            response_json = json.dumps(response)
            client_socket.sendall(response_json.encode("utf-8"))
            
        except Exception as e:
            logger.error(f"Error handling IPC client: {e}")
        finally:
            client_socket.close()

    def _process_command(self, command_data: dict) -> dict:
        """
        Processes the received command dictionary and interacts with the DeviceManager.
        Returns a response dictionary.
        """
        command = command_data.get("command")
        args = command_data.get("args", {})

        if not command:
            return {"status": "error", "message": "No command specified"}

        if not self.device_manager:
            return {"status": "error", "message": "Device manager not available"}

        try:
            if command == "list":
                devices = self.device_manager.get_active_devices()
                return {"status": "ok", "devices": devices}
                
            elif command == "set-effect":
                device_id = args.get("device")
                effect_name = args.get("effect")
                if not device_id or not effect_name:
                    return {"status": "error", "message": "Missing 'device' or 'effect' arguments"}
                    
                options = {k: v for k, v in args.items() if k not in ("device", "effect") and v is not None}
                if "color" in options and isinstance(options["color"], list):
                    options["color"] = tuple(options["color"])

                success = self.device_manager.set_device_effect(device_id, effect_name, options)
                if success:
                    return {"status": "ok", "message": f"Set effect '{effect_name}' on {device_id}"}
                else:
                    return {"status": "error", "message": f"Device {device_id} not found."}

                
            elif command == "set-color":
                device_id = args.get("device")
                color_hex = args.get("hex")
                if not device_id or not color_hex:
                    return {"status": "error", "message": "Missing 'device' or 'hex' arguments"}
                
                success = self.device_manager.set_device_color(device_id, color_hex)
                if success:
                    return {"status": "ok", "message": f"Set color {color_hex} on {device_id}"}
                else:
                    return {"status": "error", "message": f"Device {device_id} not found."}

            elif command == "set-dpi":
                device_id = args.get("device")
                level = args.get("level")
                if not device_id or level is None:
                    return {"status": "error", "message": "Missing 'device' or 'level' arguments"}
                try:
                    level = int(level)
                except ValueError:
                    return {"status": "error", "message": "'level' must be an integer."}
                
                success, message = self.device_manager.set_device_dpi(device_id, level)
                if success:
                    return {"status": "ok", "message": message}
                else:
                    return {"status": "error", "message": message}

            elif command == "set-polling":
                device_id = args.get("device")
                hz = args.get("hz")
                if not device_id or hz is None:
                    return {"status": "error", "message": "Missing 'device' or 'hz' arguments"}
                try:
                    hz = int(hz)
                except ValueError:
                    return {"status": "error", "message": "'hz' must be an integer."}

                success, message = self.device_manager.set_device_polling(device_id, hz)
                if success:
                    return {"status": "ok", "message": message}
                else:
                    return {"status": "error", "message": message}


            elif command == "bind-key":
                device_id = args.get("device")
                button = args.get("button")
                key_code_val = args.get("key_code")
                if not device_id or not button or key_code_val is None:
                    return {"status": "error", "message": "Missing 'device', 'button', or 'key_code' arguments"}
                
                try:
                    if isinstance(key_code_val, str) and key_code_val.startswith("0x"):
                        key_code = int(key_code_val, 16)
                    else:
                        key_code = int(key_code_val)
                except ValueError:
                    return {"status": "error", "message": "'key_code' must be an integer or hex string (e.g. 0x04)."}

                success = self.device_manager.bind_device_key(device_id, button, key_code)
                if success:
                    return {"status": "ok", "message": f"Bound {button} to key_code {key_code_val} on {device_id}"}
                else:
                    return {"status": "error", "message": f"Failed to bind key or device {device_id} not found."}

            elif command == "save":
                device_id = args.get("device")
                if not device_id:
                    return {"status": "error", "message": "Missing 'device' argument"}

                success = self.device_manager.save_device_profile(device_id)
                if success:
                    return {"status": "ok", "message": f"Saved profile to on-board memory for {device_id}"}
                else:
                    return {"status": "error", "message": f"Failed to save profile or device {device_id} not found."}

            elif command == "info":
                device_id = args.get("device")
                if not device_id:
                    return {"status": "error", "message": "Missing 'device' argument"}

                capabilities = self.device_manager.get_device_capabilities(device_id)
                if capabilities is not None:
                    return {"status": "ok", "capabilities": capabilities, "device": device_id}
                else:
                    return {"status": "error", "message": f"Device {device_id} not found."}

            else:
                return {"status": "error", "message": f"Unknown command: {command}"}


        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Simple logging setup for standalone testing
    logging.basicConfig(level=logging.DEBUG)
    
    server = IPCServer()
    try:
        server.start()
        print("Press Ctrl+C to stop the server...")
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
