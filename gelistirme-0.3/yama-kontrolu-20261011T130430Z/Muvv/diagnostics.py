"""Read-only environment diagnostics; no HID handles, service calls or directory creation."""

import importlib.util
import os
import socket
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from app_version import __version__
from ipc_protocol import private_directory
from managers.errors import ProtocolError


def environment_report():
    checks = []
    supported = sys.platform == "linux" and hasattr(socket, "AF_UNIX") and hasattr(socket, "SO_PEERCRED")
    checks.append(
        {
            "name": "Device service",
            "status": "ok" if supported else "warning",
            "message": "Linux Unix sockets are available."
            if supported
            else "Device control requires Linux; use --demo on this platform.",
        }
    )
    if supported and os.getuid() == 0:
        checks.append(
            {"name": "User", "status": "error", "message": "Run the service as the desktop user, not root."}
        )
    dependencies = {}
    for package in ("hidapi", "customtkinter", "darkdetect", "packaging"):
        try:
            dependencies[package] = version(package)
        except PackageNotFoundError:
            dependencies[package] = None
    for module, label in (("hid", "HID backend"), ("tkinter", "Tk"), ("customtkinter", "Desktop UI")):
        try:
            installed = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            installed = False
        checks.append(
            {
                "name": label,
                "status": "ok" if installed else "warning",
                "message": "Available." if installed else "Missing; see the installation section in README.",
            }
        )
    if supported:
        runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/muvv-{os.getuid()}"))
        if "XDG_RUNTIME_DIR" in os.environ:
            runtime /= "muvv"
        config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "muvv/profiles"
        for label, path in (("Runtime directory", runtime), ("Profile directory", config)):
            try:
                private_directory(path, create=False)
            except FileNotFoundError:
                state, message = "ok", "Not created yet; the service creates it when needed."
            except (ProtocolError, OSError) as error:
                state, message = "error", str(error)
            else:
                state, message = "ok", "Private directory ownership and permissions are valid."
            checks.append({"name": label, "status": state, "message": message, "path": str(path)})
    return {
        "version": __version__,
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "device_service_supported": supported,
        "dependencies": dependencies,
        "checks": checks,
        "hardware_access": False,
        "filesystem_changes": False,
        "healthy": not any(check["status"] == "error" for check in checks),
    }
