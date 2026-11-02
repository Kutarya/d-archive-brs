"""Client workflows independent from Tk, including partial refresh failures."""

from managers.errors import ProtocolError


class ServiceError(ValueError):
    def __init__(self, response):
        self.code = response.get("code", "service_error")
        self.response = response
        super().__init__(response.get("message", "İşlem tamamlanamadı."))


def require_ok(response):
    if not isinstance(response, dict):
        raise ProtocolError("Service returned an invalid response.")
    if response.get("status") != "ok":
        raise ServiceError(response)
    return response


def fetch_snapshot(client, selected=None):
    result = require_ok(client("snapshot", {"device": selected} if selected is not None else {}))
    seen = set()
    while result.get("next_offset") is not None:
        offset = result["next_offset"]
        if type(offset) is not int or not 0 <= offset < 128 or offset in seen:
            raise ProtocolError("Invalid profile pagination response.")
        seen.add(offset)
        page = require_ok(client("list-profiles", {"offset": offset, "limit": 32}))
        result["profiles"].extend(page["profiles"])
        result["profile_errors"].extend(page.get("profile_errors", []))
        result["next_offset"] = page.get("next_offset")
        result["profile_limit_exceeded"] |= page.get("profile_limit_exceeded", False)
    result["profiles"].sort(key=lambda profile: profile["name"].casefold())
    return result


def command_then_snapshot(client, command, payload, selected=None):
    response = require_ok(client(command, payload))
    try:
        snapshot = fetch_snapshot(client, selected)
    except Exception as error:
        return {"response": response, "snapshot": None, "refresh_error": str(error)}
    return {"response": response, "snapshot": snapshot, "refresh_error": None}
