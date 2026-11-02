class MuvvError(Exception):
    code = "internal_error"


class ValidationError(MuvvError, ValueError):
    code = "invalid_argument"


class DeviceNotFound(MuvvError):
    code = "device_not_found"


class AmbiguousDevice(MuvvError):
    code = "ambiguous_device"


class TransportError(MuvvError):
    code = "transport_error"


class DeviceBusy(TransportError):
    code = "device_busy"


class OperationTimeout(TransportError):
    code = "operation_uncertain"


class UnknownDeviceState(MuvvError):
    code = "unknown_device_state"


class ProtocolError(MuvvError):
    code = "invalid_request"
