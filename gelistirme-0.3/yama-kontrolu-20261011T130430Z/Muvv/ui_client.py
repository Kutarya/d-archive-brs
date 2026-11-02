"""Client workflows independent from Tk, including partial refresh failures."""

from copy import deepcopy

from animations.effect_registry import create_effect
from managers.device_registry import get_driver_class
from managers.errors import MuvvError, ProtocolError
from managers.profile_store import MAX_PROFILES, PROFILE_FIELDS, profile_name


class ServiceError(ValueError):
    def __init__(self, response):
        self.code = response.get("code", "service_error")
        self.response = response
        super().__init__(response.get("message", "İşlem tamamlanamadı."))


def require_ok(response):
    if not isinstance(response, dict):
        raise ProtocolError("Service returned an invalid response.")
    if response.get("status") not in ("ok", "error"):
        raise ProtocolError("Service returned an invalid response status.")
    if response["status"] == "error":
        if not isinstance(response.get("message", ""), str) or not isinstance(response.get("code", ""), str):
            raise ProtocolError("Service returned an invalid error response.")
        raise ServiceError(response)
    return response


def _hex_id(value, length):
    return (
        isinstance(value, str) and len(value) == length and all(char in "0123456789abcdef" for char in value)
    )


def _fields(value):
    return (
        isinstance(value, list)
        and all(isinstance(field, str) and field in PROFILE_FIELDS for field in value)
        and len(set(value)) == len(value)
    )


def _driver(device):
    if not isinstance(device, dict) or any(
        type(device.get(field)) is not int or not 0 <= device[field] <= 65535
        for field in ("vendor_id", "product_id")
    ):
        raise ProtocolError("Invalid device identity in service response.")
    driver = get_driver_class(device["vendor_id"], device["product_id"])
    if driver is None:
        raise ProtocolError("Unsupported device in service response.")
    return driver


def _profile_page(page):
    profiles, errors = page.get("profiles"), page.get("profile_errors", [])
    if not isinstance(profiles, list) or not isinstance(errors, list) or len(profiles) + len(errors) > 32:
        raise ProtocolError("Invalid profile page size or fields.")
    try:
        for profile in profiles:
            if not isinstance(profile, dict) or profile_name(profile.get("name")) != profile["name"]:
                raise ProtocolError("Invalid profile name in service response.")
            _driver(profile.get("device"))
            if not _fields(profile.get("unknown_fields")):
                raise ProtocolError("Invalid profile unknown fields in service response.")
    except (MuvvError, TypeError) as error:
        raise ProtocolError("Invalid profile page in service response.") from error
    if any(
        not isinstance(error, dict)
        or not isinstance(error.get("file"), str)
        or not isinstance(error.get("message"), str)
        for error in errors
    ):
        raise ProtocolError("Invalid profile error in service response.")
    offset = page.get("next_offset")
    if offset is not None and (type(offset) is not int or not 0 < offset < MAX_PROFILES):
        raise ProtocolError("Invalid profile pagination response.")
    count = page.get("profile_count", len(profiles) + len(errors))
    if type(count) is not int or not 0 <= count <= MAX_PROFILES:
        raise ProtocolError("Invalid profile count in service response.")
    if type(page.get("profile_limit_exceeded", False)) is not bool:
        raise ProtocolError("Invalid profile limit flag in service response.")
    if "catalog_id" in page and not _hex_id(page["catalog_id"], 64):
        raise ProtocolError("Invalid profile catalog ID in service response.")


def _snapshot(result):
    devices, selected, info = result.get("devices"), result.get("selected_device"), result.get("info")
    if not isinstance(devices, list) or len(devices) > MAX_PROFILES:
        raise ProtocolError("Invalid device list in service response.")
    ids, indices = set(), set()
    for device in devices:
        if (
            not isinstance(device, dict)
            or not isinstance(device.get("id"), str)
            or not 1 <= len(device["id"]) <= 1024
            or not isinstance(device.get("name"), str)
            or type(device.get("index")) is not int
            or device["index"] <= 0
            or type(device.get("connected")) is not bool
        ):
            raise ProtocolError("Invalid device fields in service response.")
        if device["id"] in ids or device["index"] in indices:
            raise ProtocolError("Duplicate device in service response.")
        ids.add(device["id"])
        indices.add(device["index"])
        _driver(device)
        if device.get("session_id") is not None and not _hex_id(device["session_id"], 32):
            raise ProtocolError("Invalid device session in service response.")
    if selected is not None and (not isinstance(selected, str) or selected not in ids):
        raise ProtocolError("Selected device is absent from the device list.")
    if info is not None:
        if selected is None or not isinstance(info, dict) or not isinstance(info.get("capabilities"), dict):
            raise ProtocolError("Invalid device info in service response.")
        state = info.get("state")
        if not isinstance(state, dict) or not isinstance(state.get("settings"), dict):
            raise ProtocolError("Invalid device state in service response.")
        if not _fields(state.get("unknown_fields")) or state.get("readback_verified") is not False:
            raise ProtocolError("Invalid device knowledge in service response.")
        transport = state.get("transport")
        if (
            not isinstance(transport, dict)
            or type(transport.get("connected")) is not bool
            or type(transport.get("state_uncertain")) is not bool
            or type(state.get("state_uncertain")) is not bool
            or state.get("render_error") is not None
            and not isinstance(state["render_error"], str)
        ):
            raise ProtocolError("Invalid device transport in service response.")
        if "session_id" in state and not _hex_id(state["session_id"], 32):
            raise ProtocolError("Invalid device session in service response.")
        device = next(device for device in devices if device["id"] == selected)
        driver = _driver(device)
        try:
            if state["settings"]:
                driver().validate_settings(state["settings"])
            effect = state.get("effect")
            if effect is not None:
                if not isinstance(effect, dict) or not isinstance(effect.get("options"), dict):
                    raise ProtocolError("Invalid effect in service response.")
                create_effect(effect.get("name"), effect["options"])
            known = set(state["settings"])
            if effect is not None:
                known.add("colors")
            if set(state["unknown_fields"]) != PROFILE_FIELDS - known:
                raise ProtocolError("Device knowledge does not match its settings.")
        except (MuvvError, TypeError) as error:
            raise ProtocolError("Invalid device settings in service response.") from error
    error = result.get("device_error")
    if error is not None and (
        not isinstance(error, dict)
        or not isinstance(error.get("message"), str)
        or not isinstance(error.get("code"), str)
    ):
        raise ProtocolError("Invalid device error in service response.")


def fetch_snapshot(client, selected=None):
    result = deepcopy(require_ok(client("snapshot", {"device": selected} if selected is not None else {})))
    _snapshot(result)
    _profile_page(result)
    result.setdefault("profile_errors", [])
    result.setdefault("profile_limit_exceeded", False)
    result["profiles_complete"] = True
    result["profile_refresh_error"] = None
    seen = set()
    while result.get("next_offset") is not None:
        offset = result["next_offset"]
        if type(offset) is not int or not 0 <= offset < 128 or offset in seen:
            raise ProtocolError("Invalid profile pagination response.")
        seen.add(offset)
        try:
            page = require_ok(client("list-profiles", {"offset": offset, "limit": 32}))
        except ProtocolError:
            raise
        except Exception as error:
            result["profiles_complete"] = False
            result["profile_refresh_error"] = str(error)
            break
        _profile_page(page)
        if result.get("catalog_id") != page.get("catalog_id"):
            result["profiles_complete"] = False
            result["profile_refresh_error"] = "Profil klasörü yenileme sırasında değişti."
            break
        if page.get("next_offset") is not None and page["next_offset"] <= offset:
            raise ProtocolError("Profile pagination did not advance.")
        if (
            len(result["profiles"])
            + len(result["profile_errors"])
            + len(page["profiles"])
            + len(page.get("profile_errors", []))
            > MAX_PROFILES
        ):
            raise ProtocolError("Profile response exceeds the catalog limit.")
        result["profiles"].extend(page["profiles"])
        result["profile_errors"].extend(page.get("profile_errors", []))
        result["next_offset"] = page.get("next_offset")
        result["profile_limit_exceeded"] |= page.get("profile_limit_exceeded", False)
    result["profiles"].sort(key=lambda profile: profile["name"].casefold())
    if len({profile["name"] for profile in result["profiles"]}) != len(result["profiles"]):
        raise ProtocolError("Duplicate profile name in service response.")
    return result


def command_then_snapshot(client, command, payload, selected=None):
    response = require_ok(client(command, payload))
    try:
        snapshot = fetch_snapshot(client, selected)
    except Exception as error:
        return {"response": response, "snapshot": None, "refresh_error": str(error)}
    return {"response": response, "snapshot": snapshot, "refresh_error": None}
