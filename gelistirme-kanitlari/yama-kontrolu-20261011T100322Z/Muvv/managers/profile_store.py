import hashlib
import os
import stat
import tempfile
import threading
import unicodedata
from pathlib import Path

from ipc_protocol import decode_json, private_directory
from managers.errors import ProtocolError, ValidationError
from managers.validator import integer

MAX_PROFILE_BYTES = 32 * 1024
MAX_PROFILES = 128


def profile_name(value):
    if not isinstance(value, str):
        raise ValidationError("Profile name must be a string.")
    value = unicodedata.normalize("NFC", value)
    if not value or value != value.strip() or len(value) > 64:
        raise ValidationError("Profile name must contain 1–64 characters, without surrounding spaces.")
    if any(character in "/\\" or unicodedata.category(character).startswith("C") for character in value):
        raise ValidationError("Profile name contains a slash or a control character.")
    return value


def validate_profile(value):
    expected = {"version", "name", "device", "settings", "effect", "unknown_fields", "readback_verified"}
    if not isinstance(value, dict) or set(value) != expected:
        raise ValidationError("Invalid profile fields.")
    integer(value["version"], "Profile version", 1, 1)
    if profile_name(value["name"]) != value["name"]:
        raise ValidationError("Profile name must use NFC Unicode normalization.")
    device = value["device"]
    if not isinstance(device, dict) or set(device) != {"vendor_id", "product_id"}:
        raise ValidationError("Invalid profile device identity.")
    integer(device["vendor_id"], "Vendor ID", 0, 65535)
    integer(device["product_id"], "Product ID", 0, 65535)
    if not isinstance(value["settings"], dict):
        raise ValidationError("Profile settings must be an object.")
    if value["effect"] is not None:
        effect = value["effect"]
        if (
            not isinstance(effect, dict)
            or set(effect) != {"name", "options"}
            or not isinstance(effect["options"], dict)
        ):
            raise ValidationError("Invalid profile effect.")
        from animations.effect_registry import create_effect

        create_effect(effect["name"], effect["options"])
    unknown = value["unknown_fields"]
    if (
        not isinstance(unknown, list)
        or any(field not in ("dpi", "buttons", "polling_rate", "colors") for field in unknown)
        or len(set(unknown)) != len(unknown)
    ):
        raise ValidationError("Invalid unknown_fields.")
    if value["readback_verified"] is not False:
        raise ValidationError("Hardware readback is not supported; profiles cannot claim verification.")
    if set(value["settings"]) & set(unknown):
        raise ValidationError("Profile marks a known setting as unknown.")
    if not value["settings"] and value["effect"] is None:
        raise ValidationError("No known settings to save. Configure the device first.")
    from managers.device_registry import get_driver_class

    driver_class = get_driver_class(device["vendor_id"], device["product_id"])
    if driver_class is None:
        raise ValidationError("Profile targets an unsupported device model.")
    if value["settings"]:
        driver_class().validate_settings(value["settings"])
    return value


class ProfileStore:
    def __init__(self, directory=None):
        if directory is None:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
            directory = base / "muvv" / "profiles"
        self.directory = Path(directory)
        self._lock = threading.RLock()

    def _path(self, name):
        name = profile_name(name)
        root = private_directory(self.directory)
        digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
        return root / f"{digest}.json", name

    @staticmethod
    def _check_file(metadata):
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValidationError("Profile must be a regular file with one link.")
        if os.name == "posix" and (metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077):
            raise ValidationError("Profile must belong to the current user and have mode 0600.")
        if metadata.st_size > MAX_PROFILE_BYTES:
            raise ValidationError("Profile exceeds the size limit.")

    def _read(self, path):
        self._check_file(path.lstat())
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            self._check_file(os.fstat(descriptor))
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                data = handle.read(MAX_PROFILE_BYTES + 1)
            if len(data) > MAX_PROFILE_BYTES:
                raise ValidationError("Profile exceeds the size limit.")
            try:
                return validate_profile(decode_json(data))
            except ProtocolError as error:
                raise ValidationError(f"Invalid profile JSON: {error}") from error
        finally:
            os.close(descriptor)

    def save(self, profile, overwrite=False):
        import json

        validate_profile(profile)
        if type(overwrite) is not bool:
            raise ValidationError("Overwrite must be a boolean.")
        data = json.dumps(profile, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8") + b"\n"
        if len(data) > MAX_PROFILE_BYTES:
            raise ValidationError("Profile exceeds the size limit.")
        with self._lock:
            path, name = self._path(profile["name"])
            exists = path.exists() or path.is_symlink()
            if exists:
                self._check_file(path.lstat())
                if not overwrite:
                    raise ValidationError(f"Profile {name!r} already exists. Use overwrite explicitly.")
            elif len(self.list()) >= MAX_PROFILES:
                raise ValidationError("Profile count limit reached.")
            descriptor, temporary = tempfile.mkstemp(prefix=".profile-", dir=self.directory)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                if overwrite:
                    os.replace(temporary, path)
                else:
                    os.link(temporary, path)
                    os.unlink(temporary)
                if os.name == "posix":
                    root_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(root_fd)
                    finally:
                        os.close(root_fd)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            return self.load(name)

    def load(self, name):
        with self._lock:
            path, name = self._path(name)
            try:
                profile = self._read(path)
            except FileNotFoundError as error:
                raise ValidationError(f"Profile {name!r} does not exist.") from error
            if profile["name"] != name:
                raise ValidationError("Profile name does not match its file.")
            return profile

    def list(self):
        with self._lock:
            root = private_directory(self.directory)
            profiles = []
            for path in sorted(root.glob("*.json")):
                if len(profiles) >= MAX_PROFILES:
                    raise ValidationError("Profile count limit exceeded.")
                profile = self._read(path)
                expected, _ = self._path(profile["name"])
                if path != expected:
                    raise ValidationError("Profile filename does not match its name.")
                profiles.append(
                    {
                        "name": profile["name"],
                        "device": profile["device"],
                        "unknown_fields": profile["unknown_fields"],
                    }
                )
            return sorted(profiles, key=lambda profile: profile["name"].casefold())

    def delete(self, name):
        with self._lock:
            self.load(name)
            path, _ = self._path(name)
            path.unlink()
