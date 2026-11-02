"""Version 1: four-byte network-order length followed by UTF-8 JSON."""

import json
import math
import os
import socket
import stat
import struct
import sys
import time
from pathlib import Path

from managers.errors import ProtocolError

PROTOCOL_VERSION = 1
MAX_REQUEST = 16 * 1024
MAX_RESPONSE = 64 * 1024
REQUEST_TIMEOUT = 5.0


def _unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ProtocolError(f"Duplicate JSON key: {key!r}.")
        result[key] = value
    return result


def decode_json(data):
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ProtocolError(f"Invalid JSON number: {value}")
            ),
        )
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ProtocolError("Request must be valid UTF-8 JSON.") from error
    pending = [(value, 0)]
    nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if depth > 16 or nodes > 2048:
            raise ProtocolError("JSON nesting or item limit exceeded.")
        if isinstance(item, float) and not math.isfinite(item):
            raise ProtocolError("JSON numbers must be finite.")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
    if not isinstance(value, dict):
        raise ProtocolError("Request must be a JSON object.")
    return value


def _read_exact(connection, size, deadline):
    chunks = []
    remaining = size
    while remaining:
        timeout = deadline - time.monotonic()
        if timeout <= 0:
            raise ProtocolError("Request timed out.")
        connection.settimeout(timeout)
        try:
            chunk = connection.recv(remaining)
        except TimeoutError as error:
            raise ProtocolError("Request timed out.") from error
        if not chunk:
            raise ProtocolError("Connection closed before the complete message arrived.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def receive_message(connection, limit=MAX_REQUEST, timeout=REQUEST_TIMEOUT):
    deadline = time.monotonic() + timeout
    size = struct.unpack("!I", _read_exact(connection, 4, deadline))[0]
    if not 0 < size <= limit:
        raise ProtocolError(f"Message size must be between 1 and {limit} bytes.")
    return decode_json(_read_exact(connection, size, deadline))


def encode_message(value, limit=MAX_RESPONSE):
    try:
        body = json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise ProtocolError("Message cannot be encoded as JSON.") from error
    if not 0 < len(body) <= limit:
        raise ProtocolError(f"Message exceeds {limit} bytes.")
    return struct.pack("!I", len(body)) + body


def send_message(connection, value, limit=MAX_RESPONSE, timeout=REQUEST_TIMEOUT):
    connection.settimeout(timeout)
    connection.sendall(encode_message(value, limit))


def require_linux():
    if sys.platform != "linux" or not hasattr(socket, "AF_UNIX") or not hasattr(socket, "SO_PEERCRED"):
        raise ProtocolError("Muvv device service requires Linux Unix sockets and SO_PEERCRED.")


def private_directory(path, create=True):
    path = Path(path)
    if not path.is_absolute():
        raise ProtocolError("Private directory must be an absolute path.")
    # Reject symlinks in every existing component, including XDG parent paths.
    for component in reversed((path, *path.parents)):
        try:
            metadata = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode):
            raise ProtocolError(f"Symlink directory is not allowed: {component}")
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise ProtocolError("Private path is not a directory.")
    if os.name == "posix":
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
            raise ProtocolError(f"Directory must belong to the current user and have mode 0700: {path}")
    return path


def runtime_directory():
    require_linux()
    base = os.environ.get("XDG_RUNTIME_DIR")
    if base:
        parent = private_directory(Path(base), create=False)
        return private_directory(parent / "muvv")
    return private_directory(Path("/tmp") / f"muvv-{os.getuid()}")


def socket_path():
    path = runtime_directory() / "muvv.sock"
    if len(os.fsencode(path)) > 107:
        raise ProtocolError("Unix socket path exceeds the Linux length limit.")
    return path


def peer_uid(connection):
    require_linux()
    credentials = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    return struct.unpack("3i", credentials)[1]


def verify_peer(connection):
    if peer_uid(connection) != os.getuid():
        raise ProtocolError("IPC peer belongs to a different user.")
