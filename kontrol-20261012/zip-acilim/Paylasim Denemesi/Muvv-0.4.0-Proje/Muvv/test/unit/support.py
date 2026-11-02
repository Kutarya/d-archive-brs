import threading

from drivers.steelseries.rival3_gen2 import Rival3Gen2Mouse


class FakeHID:
    def __init__(self, result=None, fail_on=None, block=False):
        self.packets = []
        self.result = result
        self.fail_on = fail_on
        self.entered = threading.Event()
        self.release = threading.Event()
        self.block = block
        self.closed = False

    def write(self, packet):
        self.entered.set()
        if self.block:
            self.release.wait(5)
        if self.fail_on is not None and len(self.packets) == self.fail_on:
            raise OSError("device unplugged")
        self.packets.append(packet)
        return len(packet) if self.result is None else self.result

    def close(self):
        self.closed = True


def connected_mouse(handle=None):
    mouse = Rival3Gen2Mouse(device_path=b"fake-hid")
    mouse.device = handle or FakeHID()
    mouse.is_connected = True
    mouse._start_worker()
    return mouse


class FakeRival(Rival3Gen2Mouse):
    handle_factory = FakeHID

    def connect(self):
        self.device = self.handle_factory()
        self.is_connected = True
        self._reset_session()
        self._start_worker()
