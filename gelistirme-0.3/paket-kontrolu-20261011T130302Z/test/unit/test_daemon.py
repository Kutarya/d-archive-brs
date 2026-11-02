import unittest
from unittest.mock import Mock, patch

import daemon
from managers.errors import TransportError


class DaemonTests(unittest.TestCase):
    def run_daemon(self, manager, uid=1000):
        with (
            patch("daemon.require_linux"),
            patch("daemon.os.geteuid", return_value=uid, create=True),
            patch("daemon.signal.signal"),
            patch("daemon.DeviceManager", return_value=manager) as factory,
            patch("daemon.threading.Event") as event,
        ):
            event.return_value.wait.return_value = True
            return daemon.main([]), factory

    def test_root_service_is_rejected_before_device_scan(self):
        manager = Mock()
        status, factory = self.run_daemon(manager, uid=0)
        self.assertEqual(status, 1)
        factory.assert_not_called()
        manager.start.assert_not_called()

    def test_normal_user_start_and_shutdown_are_balanced(self):
        manager = Mock()
        status, _ = self.run_daemon(manager)
        self.assertEqual(status, 0)
        manager.start.assert_called_once()
        manager.stop.assert_called_once()

    def test_startup_failure_still_cleans_up(self):
        manager = Mock()
        manager.start.side_effect = TransportError("socket already in use")
        status, _ = self.run_daemon(manager)
        self.assertEqual(status, 1)
        manager.stop.assert_called_once()
