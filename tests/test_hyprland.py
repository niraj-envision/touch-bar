#!/usr/bin/env python3
import importlib.machinery
import importlib.util
import json
import os
import socket
import tempfile
import threading
import unittest
from unittest import mock

TOOL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "omarchy-touchbar")
loader = importlib.machinery.SourceFileLoader("touchbar_hyprland", TOOL)
spec = importlib.util.spec_from_loader("touchbar_hyprland", loader)
tb = importlib.util.module_from_spec(spec)
loader.exec_module(tb)


class BrowserTabNumbering(unittest.TestCase):
    def test_zen_placeholders_do_not_shift_tab_numbers(self):
        def tab(title, **flags):
            return dict({"entries": [{"title": title, "url": "https://x/" + title}],
                         "index": 1, "zenWorkspace": "ws1"}, **flags)

        window = {"selected": 4, "activeZenSpace": "ws1", "tabs": [
            tab("empty", zenIsEmpty=True),
            tab("one"), tab("two"),
            tab("elsewhere", zenWorkspace="ws2"),
            tab("three"), tab("ghost", hidden=True), tab("four"),
        ]}
        tabs, selected = tb.BrowserTabs.visible_tabs(window)
        self.assertEqual([t["title"] for t in tabs], ["one", "two", "three", "four"])
        # `selected` is 1-based over the raw list: 4 -> "elsewhere" is not
        # visible, so the nearest kept index before it stays selected.
        window["selected"] = 5
        tabs, selected = tb.BrowserTabs.visible_tabs(window)
        self.assertEqual(tabs[selected]["title"], "three")


class HyprlandDiscovery(unittest.TestCase):
    def setUp(self):
        self.old_root = tb.HYPR_ROOT
        self.old_cache = tb._HYPR_DIR_CACHE
        self.old_error = tb._HYPR_ERROR

    def tearDown(self):
        tb.HYPR_ROOT = self.old_root
        tb._HYPR_DIR_CACHE = self.old_cache
        tb._HYPR_ERROR = self.old_error

    def test_command_socket_is_discovered_without_exported_signature(self):
        with tempfile.TemporaryDirectory() as root:
            instance = os.path.join(root, "live-instance")
            os.mkdir(instance)
            path = os.path.join(instance, ".socket.sock")
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(path)
            server.settimeout(2)
            server.listen(1)
            received = []

            def reply():
                conn, _ = server.accept()
                with conn:
                    received.append(conn.recv(256))
                    conn.sendall(json.dumps({"class": "chatgpt"}).encode())

            worker = threading.Thread(target=reply, daemon=True)
            worker.start()
            tb.HYPR_ROOT = root
            tb._HYPR_DIR_CACHE = os.path.join(root, "stale-instance")
            with mock.patch.dict(os.environ, {"HYPRLAND_INSTANCE_SIGNATURE": ""}):
                result = tb.hypr("activewindow")
            worker.join(2)
            server.close()

            self.assertEqual(result, {"class": "chatgpt"})
            self.assertEqual(received, [b"j/activewindow"])
            self.assertEqual(tb._HYPR_DIR_CACHE, instance)


if __name__ == "__main__":
    unittest.main(verbosity=2)
