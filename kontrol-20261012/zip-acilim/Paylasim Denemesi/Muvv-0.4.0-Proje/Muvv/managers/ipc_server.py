import errno
import logging
import os
import socket
import stat
import threading
import time
from pathlib import Path

from animations.effect_registry import create_effect, list_effects
from ipc_protocol import (
    MAX_REQUEST,
    PROTOCOL_VERSION,
    encode_message,
    private_directory,
    receive_message,
    require_linux,
    send_message,
    socket_path,
    verify_peer,
)
from managers.errors import MuvvError, ProtocolError, TransportError, ValidationError
from managers.validator import integer, key_code, rgb

LOG = logging.getLogger(__name__)


class IPCServer:
    MAX_CLIENTS = 8

    def __init__(self, device_manager, socket_path=None, client_timeout=5.0):
        self.device_manager = device_manager
        self.socket_path = Path(socket_path) if socket_path is not None else None
        self.client_timeout = client_timeout
        self.server_socket = None
        self._lock_fd = None
        self._release_requested = False
        self._socket_identity = None
        self._stop_event = threading.Event()
        self._thread = None
        self._clients = {}
        self._clients_lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(self.MAX_CLIENTS)
        self.is_running = False

    def _acquire_lock(self):
        import fcntl

        flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW
        descriptor = os.open(str(self.socket_path) + ".lock", flags, 0o600)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or metadata.st_nlink != 1:
                raise ProtocolError("Unsafe daemon lock file.")
            if stat.S_IMODE(metadata.st_mode) & 0o077:
                raise ProtocolError("Daemon lock file must have mode 0600.")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ProtocolError("Another Muvv daemon is already running.") from error
            os.ftruncate(descriptor, 0)
            os.write(descriptor, str(os.getpid()).encode("ascii"))
        except Exception:
            os.close(descriptor)
            raise
        self._lock_fd = descriptor

    def _remove_stale_socket(self):
        try:
            metadata = self.socket_path.lstat()
        except FileNotFoundError:
            return
        if not stat.S_ISSOCK(metadata.st_mode) or metadata.st_uid != os.getuid():
            raise ProtocolError("Existing IPC path is not an owned Unix socket.")
        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        probe.settimeout(0.25)
        try:
            probe.connect(str(self.socket_path))
        except OSError as error:
            if error.errno not in (errno.ECONNREFUSED, errno.ENOENT):
                raise ProtocolError("Existing socket could not be checked safely.") from error
        else:
            raise ProtocolError("An active service is already using the IPC path.")
        finally:
            probe.close()
        current = self.socket_path.lstat()
        if (metadata.st_dev, metadata.st_ino) != (current.st_dev, current.st_ino):
            raise ProtocolError("IPC path changed during startup.")
        self.socket_path.unlink()

    def start(self):
        if self.is_running:
            return
        with self._clients_lock:
            if self._clients or (self._thread and self._thread.is_alive()):
                raise ProtocolError("The previous IPC workers are still closing.")
            if self._lock_fd is not None:
                os.close(self._lock_fd)
                self._lock_fd = None
            self._release_requested = False
        require_linux()
        if self.socket_path is None:
            self.socket_path = socket_path()
        if not self.socket_path.is_absolute() or len(os.fsencode(self.socket_path)) > 107:
            raise ProtocolError("IPC path must be absolute and at most 107 bytes.")
        private_directory(self.socket_path.parent)
        try:
            self._acquire_lock()
            self._remove_stale_socket()
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_socket.bind(str(self.socket_path))
            metadata = self.socket_path.lstat()
            self._socket_identity = (metadata.st_dev, metadata.st_ino)
            os.chmod(self.socket_path, 0o600)
            self.server_socket.listen(self.MAX_CLIENTS)
            self.server_socket.settimeout(0.2)
            self._stop_event.clear()
            self._release_requested = False
            self.is_running = True
            self._thread = threading.Thread(target=self._accept_loop, name="muvv-ipc", daemon=True)
            self._thread.start()
        except Exception:
            self.stop()
            raise

    def _accept_loop(self):
        listener = self.server_socket
        while not self._stop_event.is_set():
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            acquired = False
            try:
                verify_peer(connection)
                if not self._slots.acquire(blocking=False):
                    send_message(
                        connection,
                        {"status": "error", "code": "busy", "message": "Too many active IPC clients."},
                        timeout=0.2,
                    )
                    connection.close()
                    continue
                acquired = True
                worker = threading.Thread(
                    target=self._handle_client, args=(connection,), name="muvv-client", daemon=True
                )
                with self._clients_lock:
                    if self._stop_event.is_set():
                        self._slots.release()
                        connection.close()
                        continue
                    self._clients[connection] = worker
                    worker.start()
            except Exception as error:
                LOG.debug("IPC connection rejected: %s", error)
                if acquired:
                    with self._clients_lock:
                        self._clients.pop(connection, None)
                    self._slots.release()
                connection.close()

    def _handle_client(self, connection):
        try:
            try:
                payload = receive_message(connection, MAX_REQUEST, self.client_timeout)
                if self._stop_event.is_set():
                    raise ProtocolError("Device service is stopping.")
                response = self._process_command(payload)
            except MuvvError as error:
                response = self._error(error)
            try:
                encode_message(response)
            except ProtocolError:
                response = {
                    "status": "error",
                    "code": "response_too_large",
                    "message": "The result exceeds the response limit. Use a smaller page.",
                    "operation_completed": response.get("status") == "ok",
                }
            send_message(connection, response, timeout=self.client_timeout)
        except (OSError, MuvvError) as error:
            LOG.debug("IPC client closed: %s", error)
        finally:
            connection.close()
            with self._clients_lock:
                self._clients.pop(connection, None)
            self._slots.release()
            self._try_release_lock()

    @staticmethod
    def _error(error):
        return {"status": "error", "code": error.code, "message": str(error)}

    def stop(self, *, release_lock=True):
        self._stop_event.set()
        listener, self.server_socket = self.server_socket, None
        if listener is not None:
            listener.close()
        with self._clients_lock:
            clients = list(self._clients.items())
        for connection, _ in clients:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        deadline = time.monotonic() + 2
        for worker in [self._thread, *(thread for _, thread in clients)]:
            if worker and worker.is_alive() and worker is not threading.current_thread():
                worker.join(max(0, deadline - time.monotonic()))
        if self.socket_path is not None and self._socket_identity is not None:
            try:
                metadata = self.socket_path.lstat()
                if (
                    stat.S_ISSOCK(metadata.st_mode)
                    and (metadata.st_dev, metadata.st_ino) == self._socket_identity
                ):
                    self.socket_path.unlink()
            except FileNotFoundError:
                pass
            except OSError as error:
                LOG.warning("Cannot remove the IPC socket during shutdown: %s", error)
        self._socket_identity = None
        self.is_running = False
        if release_lock:
            self.release_lock()

    def release_lock(self):
        self._release_requested = True
        return self._try_release_lock()

    def _try_release_lock(self):
        with self._clients_lock:
            if not self._release_requested:
                return False
            if self._clients or self._thread and self._thread.is_alive():
                return False
            if self._lock_fd is not None:
                os.close(self._lock_fd)
                self._lock_fd = None
            return True

    @staticmethod
    def _args(payload):
        if not isinstance(payload, dict) or payload.keys() - {"command", "args", "version"}:
            raise ProtocolError("Request must contain command, args and optional version.")
        if "version" in payload and (
            type(payload["version"]) is not int or payload["version"] != PROTOCOL_VERSION
        ):
            raise ProtocolError("Unsupported IPC protocol version.")
        command = payload.get("command")
        args = payload.get("args", {})
        if not isinstance(command, str) or not command or not isinstance(args, dict):
            raise ProtocolError("Command must be a string and args must be an object.")
        return command, dict(args)

    @staticmethod
    def _check_keys(args, allowed, required=()):
        extra = args.keys() - set(allowed)
        missing = set(required) - args.keys()
        if extra or missing:
            raise ValidationError(
                f"Invalid command arguments. Unknown: {sorted(extra)}; missing: {sorted(missing)}."
            )
        if "device" in args and (not isinstance(args["device"], str) or len(args["device"]) > 1024):
            raise ValidationError("Device identifier must be a string of at most 1024 characters.")
        for flag in ("initialize", "persist", "overwrite"):
            if flag in args and type(args[flag]) is not bool:
                raise ValidationError(f"{flag} must be a boolean.")

    def _process_command(self, payload):
        try:
            command, args = self._args(payload)
            session = {}
            if "expected_session" in args:
                expected = args.pop("expected_session")
                if (
                    not isinstance(expected, str)
                    or len(expected) != 32
                    or any(character not in "0123456789abcdef" for character in expected)
                ):
                    raise ValidationError(
                        "expected_session must be a 32-character lowercase hex connection ID."
                    )
                if command not in {
                    "set-effect",
                    "update-effect",
                    "set-color",
                    "set-colors",
                    "stop-effect",
                    "set-dpi",
                    "set-dpi-stages",
                    "set-polling",
                    "bind-key",
                    "restore-buttons",
                    "set-button",
                    "save",
                    "reconnect",
                    "save-profile",
                    "apply-profile",
                }:
                    raise ValidationError("expected_session is only accepted by device commands.")
                session["expected_session"] = expected
            device = args.get("device", "default")
            manager = self.device_manager
            result = {}
            if command == "list":
                self._check_keys(args, ())
                result["devices"] = manager.get_active_devices()
            elif command == "status":
                self._check_keys(args, ())
                result["daemon"] = manager.status()
            elif command == "snapshot":
                self._check_keys(args, ("device",))
                result = manager.snapshot(args.get("device"))
            elif command == "effects":
                self._check_keys(args, ())
                result["effects"] = list_effects()
            elif command == "info":
                self._check_keys(args, ("device",))
                capabilities = manager.get_device_capabilities(device)
                if capabilities is None:
                    raise ValidationError(f"Device {device!r} not found.")
                result["capabilities"] = capabilities
                if hasattr(manager, "get_device_state"):
                    result["state"] = manager.get_device_state(device)
            elif command in ("set-effect", "update-effect"):
                self._check_keys(
                    args,
                    (
                        "device",
                        "effect",
                        "color",
                        "speed",
                        "direction",
                        "wave_length",
                        "brightness",
                        "enabled",
                    ),
                    ("effect",) if command == "set-effect" else (),
                )
                options = {key: value for key, value in args.items() if key not in ("device", "effect")}
                if command == "set-effect":
                    effect = create_effect(args["effect"], options)
                    normalized = {key: effect.parameters()[key] for key in options}
                    result = self._result(
                        manager.set_device_effect(device, args["effect"], normalized, **session)
                    )
                else:
                    if "effect" in args:
                        raise ValidationError("update-effect changes the current effect; omit effect.")
                    result = self._result(manager.update_device_effect(device, options, **session))
            elif command == "set-color":
                self._check_keys(args, ("device", "color", "hex"))
                if ("color" in args) == ("hex" in args):
                    raise ValidationError("Supply exactly one of color or hex.")
                color = rgb(args.get("color", args.get("hex")))
                result = self._result(
                    manager.set_device_color(
                        device, "#" + "".join(f"{channel:02X}" for channel in color), **session
                    )
                )
            elif command == "set-colors":
                self._check_keys(args, ("device", "colors"), ("colors",))
                result = self._result(manager.set_device_colors(device, args["colors"], **session))
            elif command == "stop-effect":
                self._check_keys(args, ("device",))
                result = self._result(manager.stop_device_effect(device, **session))
            elif command == "set-dpi":
                self._check_keys(args, ("device", "level", "initialize"), ("level",))
                level = integer(args["level"], "DPI stage")
                flags = {"initialize": args["initialize"]} if "initialize" in args else {}
                result = self._result(manager.set_device_dpi(device, level, **flags, **session))
            elif command == "set-dpi-stages":
                self._check_keys(args, ("device", "stages", "active"), ("stages",))
                result = self._result(
                    manager.set_device_dpi_stages(device, args["stages"], args.get("active"), **session)
                )
            elif command == "set-polling":
                self._check_keys(args, ("device", "hz"), ("hz",))
                result = self._result(
                    manager.set_device_polling(device, integer(args["hz"], "Polling rate"), **session)
                )
            elif command == "bind-key":
                self._check_keys(
                    args, ("device", "button", "key_code", "initialize", "persist"), ("button", "key_code")
                )
                result = self._result(
                    manager.bind_device_key(
                        device,
                        args["button"],
                        key_code(args["key_code"]),
                        args.get("initialize", False),
                        args.get("persist", True),
                        **session,
                    )
                )
            elif command == "restore-buttons":
                self._check_keys(args, ("device", "persist"))
                result = self._result(
                    manager.restore_device_buttons(device, args.get("persist", True), **session)
                )
            elif command == "set-button":
                self._check_keys(
                    args,
                    ("device", "button", "assignment", "initialize", "persist"),
                    ("button", "assignment"),
                )
                result = self._result(
                    manager.set_device_button(
                        device,
                        args["button"],
                        args["assignment"],
                        args.get("initialize", False),
                        args.get("persist", False),
                        **session,
                    )
                )
            elif command == "save":
                self._check_keys(args, ("device",))
                result = self._result(manager.save_device_profile(device, **session))
            elif command == "reconnect":
                self._check_keys(args, ("device",))
                result = self._result(manager.reconnect_device(device, **session))
            elif command == "list-profiles":
                self._check_keys(args, ("offset", "limit"))
                result = manager.profile_store.catalog(args.get("offset", 0), args.get("limit", 32))
            elif command == "save-profile":
                self._check_keys(args, ("device", "name", "overwrite"), ("name",))
                result["profile"] = manager.save_host_profile(
                    device, args["name"], args.get("overwrite", False), **session
                )
            elif command in ("show-profile", "delete-profile"):
                self._check_keys(args, ("name",), ("name",))
                if command == "show-profile":
                    result["profile"] = manager.profile_store.load(args["name"])
                else:
                    manager.profile_store.delete(args["name"])
            elif command == "apply-profile":
                self._check_keys(args, ("device", "name", "persist"), ("name",))
                result = self._result(
                    manager.apply_host_profile(device, args["name"], args.get("persist", False), **session)
                )
            elif command == "rename-profile":
                self._check_keys(args, ("name", "new_name"), ("name", "new_name"))
                result["profile"] = manager.profile_store.rename(args["name"], args["new_name"])
            elif command == "import-profile":
                self._check_keys(args, ("profile", "overwrite"), ("profile",))
                result["profile"] = manager.profile_store.save(args["profile"], args.get("overwrite", False))
            else:
                raise ValidationError(f"Unknown command: {command!r}.")
            return {"status": "ok", **result}
        except MuvvError as error:
            return self._error(error)
        except Exception:
            LOG.exception("Command failed")
            return {
                "status": "error",
                "code": "internal_error",
                "message": "Command failed; see the daemon log.",
            }

    @staticmethod
    def _result(result):
        if isinstance(result, tuple):
            success, message = result
            if not success:
                raise ValidationError(message)
            return {"message": message}
        if result is False or result is None:
            raise TransportError("Command did not complete.")
        return result if isinstance(result, dict) else {}
