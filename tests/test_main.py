import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class TaskStorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "tasks.jsonl"
        self.log = Path(self.directory.name) / "log.txt"
        self.tasks_patch = patch.object(main, "TASKS_FILE", str(self.path))
        self.log_patch = patch.object(main, "LOG_FILE", str(self.log))
        self.tasks_patch.start()
        self.log_patch.start()
        self.addCleanup(self.tasks_patch.stop)
        self.addCleanup(self.log_patch.stop)
        self.task = {
            "id": 1, "title": "Keep me", "completed": False,
            "created_at": "2026-07-06, 09:23 AM",
        }

    def test_corrupt_line_blocks_loading_and_preserves_original(self):
        original = json.dumps(self.task) + "\n{broken json\n"
        self.path.write_text(original)
        with self.assertRaisesRegex(main.TaskDataError, "line 2"):
            main.load_tasks()
        with patch("builtins.input", side_effect=AssertionError("App must not accept edits")):
            main.main()
        self.assertEqual(self.path.read_text(), original)

    def test_missing_file_starts_empty_and_valid_tasks_round_trip(self):
        self.assertEqual(main.load_tasks(), [])
        main.save_tasks([self.task])
        self.assertEqual(main.load_tasks(), [self.task])
        self.assertEqual(list(main.read_tasks_generator(self.path)), [self.task])

    def test_duplicate_ids_are_rejected(self):
        self.path.write_text(json.dumps(self.task) + "\n" + json.dumps(self.task) + "\n")
        with self.assertRaisesRegex(main.TaskDataError, "Duplicate"):
            main.load_tasks()

    def test_generator_reports_corrupt_data(self):
        self.path.write_text(json.dumps(self.task) + "\n{broken json\n")
        iterator = main.read_tasks_generator(self.path)
        self.assertEqual(next(iterator), self.task)
        with self.assertRaisesRegex(main.TaskDataError, "line 2"):
            next(iterator)

    def test_failed_save_keeps_existing_file(self):
        original = json.dumps(self.task) + "\n"
        self.path.write_text(original)
        with self.assertRaises(main.TaskDataError):
            main.save_tasks([self.task, {**self.task, "id": 2, "title": ""}])
        self.assertEqual(self.path.read_text(), original)
        self.assertEqual(list(self.path.parent.glob(".tasks.jsonl.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
