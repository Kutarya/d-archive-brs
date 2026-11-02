"""Profile file exchange; the service never receives an arbitrary filesystem path."""

import json
import os
import stat
import tempfile
from pathlib import Path

from ipc_protocol import decode_json
from managers.errors import ProtocolError, ValidationError
from managers.profile_store import MAX_PROFILE_BYTES, validate_profile


def read_profile_file(filename):
    path = Path(filename)
    try:
        initial = path.lstat()
        if not stat.S_ISREG(initial.st_mode) or initial.st_size > MAX_PROFILE_BYTES:
            raise ValidationError("Choose a regular profile file of at most 32 KiB.")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        descriptor = os.open(path, flags)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_PROFILE_BYTES:
                raise ValidationError("Choose a regular profile file of at most 32 KiB.")
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                data = handle.read(MAX_PROFILE_BYTES + 1)
            if len(data) > MAX_PROFILE_BYTES:
                raise ValidationError("Profile file exceeds 32 KiB.")
            if data.startswith(b"\xef\xbb\xbf"):
                data = data[3:]
            return validate_profile(decode_json(data))
        finally:
            os.close(descriptor)
    except (OSError, ProtocolError) as error:
        raise ValidationError(f"Cannot read profile file: {error}") from error


def write_profile_file(filename, profile, overwrite=False):
    validate_profile(profile)
    if type(overwrite) is not bool:
        raise ValidationError("Overwrite must be a boolean.")
    data = json.dumps(profile, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8") + b"\n"
    if len(data) > MAX_PROFILE_BYTES:
        raise ValidationError("Profile file exceeds 32 KiB.")
    path = Path(filename).absolute()
    temporary = None
    try:
        if path.exists() or path.is_symlink():
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValidationError("Export target must be a regular file with one link.")
            if not overwrite:
                raise ValidationError("Export file already exists. Choose another name or use overwrite.")
        descriptor, temporary = tempfile.mkstemp(prefix=".muvv-export-", dir=path.parent)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
        return str(path)
    except OSError as error:
        raise ValidationError(f"Cannot export profile: {error}") from error
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
