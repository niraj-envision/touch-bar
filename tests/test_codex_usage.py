#!/usr/bin/env python3
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import time
import unittest
from unittest import mock

TOOL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "omarchy-touchbar")
loader = importlib.machinery.SourceFileLoader("touchbar_codex_usage", TOOL)
spec = importlib.util.spec_from_loader("touchbar_codex_usage", loader)
tb = importlib.util.module_from_spec(spec)
loader.exec_module(tb)


def write_rollout(path, metadata, primary, secondary):
    events = [
        {"payload": metadata},
        {"payload": {"type": "thread_settings_applied", "thread_settings": {
            "model": "gpt-test", "reasoning_effort": "high"}}},
        {"payload": {"type": "task_started", "started_at": "2026-09-04T00:00:00Z"}},
        {"payload": {"type": "task_complete"}},
        {"payload": {"type": "token_count", "info": {
            "last_token_usage": {"total_tokens": 1234},
            "total_token_usage": {"output_tokens": 567},
            "model_context_window": 200000,
        }, "rate_limits": {
            "primary": {"used_percent": primary},
            "secondary": {"used_percent": secondary},
        }}},
    ]
    with open(path, "w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event) + "\n")


class CodexUsageDiscovery(unittest.TestCase):
    def setUp(self):
        tb.CODEX_SESSION_CACHE.clear()

    def test_user_thread_source_is_a_root_task(self):
        with tempfile.TemporaryDirectory() as home:
            directory = os.path.join(home, ".codex", "sessions", "2026", "09", "04")
            os.makedirs(directory)
            root = os.path.join(directory, "rollout-root.jsonl")
            child = os.path.join(directory, "rollout-child.jsonl")
            write_rollout(root, {
                "type": "session_meta", "session_id": "root",
                "source": "vscode", "thread_source": "user",
            }, 18, 50)
            write_rollout(child, {
                "type": "session_meta", "session_id": "child",
                "source": {"subagent": "reviewer"},
                "thread_source": "guardian_review", "parent_thread_id": "root",
            }, 99, 99)
            now = time.time()
            os.utime(root, (now - 1, now - 1))
            os.utime(child, (now, now))

            with mock.patch.object(tb, "HOME", home):
                result = tb.latest_codex_state()

            self.assertEqual(result["usage"], 18)
            self.assertEqual(result["secondary_usage"], 50)
            self.assertEqual(result["model"], "gpt-test")
            self.assertEqual(result["context"], 1234)

    def test_special_file_is_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as home:
            directory = os.path.join(home, ".codex", "sessions")
            os.makedirs(directory)
            fifo = os.path.join(directory, "planted.jsonl")
            os.mkfifo(fifo)
            with mock.patch.object(tb, "HOME", home):
                with self.assertRaises(OSError):
                    tb.open_codex_session(fifo)

    def test_malformed_usage_is_bounded_and_does_not_crash(self):
        self.assertIsNone(tb.codex_percent("not-a-number"))
        self.assertIsNone(tb.codex_percent(float("inf")))
        self.assertEqual(tb.codex_percent(-4), 0)
        self.assertEqual(tb.codex_percent(140), 100)
        self.assertEqual(tb.codex_count("bad"), 0)
        self.assertEqual(tb.codex_count(10**20), 10**12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
