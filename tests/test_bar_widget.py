#!/usr/bin/env python3
from pathlib import Path
import unittest


QML = Path(__file__).resolve().parents[1] / "BarWidget.qml"


class BarWidgetLaunchPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = QML.read_text(encoding="utf-8")

    def test_status_probe_does_not_invoke_a_shell(self):
        self.assertIn('command: [root.binPath, "status"]', self.source)
        self.assertNotIn('"-c"', self.source)

    def test_external_launchers_have_absolute_paths(self):
        for expected in (
            '"/usr/bin/systemctl"',
            '"/usr/bin/uwsm-app"',
            '"/usr/bin/xdg-terminal-exec"',
            '"/usr/bin/bash"',
        ):
            self.assertIn(expected, self.source)

    def test_ipc_page_argument_is_allowlisted(self):
        self.assertIn('if (allowed.indexOf(name) !== -1)', self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
