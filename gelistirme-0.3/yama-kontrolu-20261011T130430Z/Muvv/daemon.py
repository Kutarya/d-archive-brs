import argparse
import logging
import os
import signal
import threading

from ipc_protocol import require_linux
from managers.device_manager import DeviceManager
from managers.errors import MuvvError

LOG = logging.getLogger(__name__)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Muvv device service")
    parser.add_argument("--scan-interval", type=float, default=2.0)
    parser.add_argument("--verbose", action="store_true")
    namespace = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if namespace.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    manager = None
    try:
        require_linux()
        if os.geteuid() == 0:
            raise MuvvError(
                "Run muvvd as your desktop user. Configure hidraw access using the supplied udev rule."
            )
        manager = DeviceManager(scan_interval=namespace.scan_interval)
        stopped = threading.Event()
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(number, lambda *_: stopped.set())
        manager.start()
        LOG.info("Device service listening at %s", manager.ipc_server.socket_path)
        while not stopped.wait(0.5):
            pass
        return 0
    except (MuvvError, ValueError, OSError) as error:
        LOG.error("%s", error)
        return 1
    finally:
        if manager is not None:
            manager.stop()


if __name__ == "__main__":
    raise SystemExit(main())
