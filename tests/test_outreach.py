"""Tests for the Vektor Outreach Agent (stdlib unittest only).

Run: python -m unittest discover -s tests -v
"""

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outreach import brain, drafts, targets  # noqa: E402
from outreach import cli  # noqa: E402


class TestBrainConfig(unittest.TestCase):
    def test_missing_key_makes_no_call(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("urllib.request.urlopen") as fake_open:
                with self.assertRaises(brain.MissingKeyError):
                    brain.chat([{"role": "user", "content": "hello"}])
                fake_open.assert_not_called()

    def test_empty_key_makes_no_call(self):
        with mock.patch.dict(os.environ, {"META_MODEL_API_KEY": "   "}):
            with mock.patch("urllib.request.urlopen") as fake_open:
                with self.assertRaises(brain.MissingKeyError):
                    brain.chat([{"role": "user", "content": "hello"}])
                fake_open.assert_not_called()

    def test_default_model(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(brain.get_model(), "muse-spark")

    def test_model_from_env(self):
        with mock.patch.dict(os.environ, {"META_MODEL": "muse-spark-1.3"}):
            self.assertEqual(brain.get_model(), "muse-spark-1.3")


class TestTargets(unittest.TestCase):
    def test_targets_load(self):
        loaded = targets.load_targets()
        self.assertEqual(len(loaded), 11)
        names = [t["name"] for t in loaded]
        self.assertIn("EPIC Ventures", names)
        self.assertIn("Draper Associates", names)

    def test_undocumented_route_is_null(self):
        loaded = targets.load_targets()
        planetary = targets.find_target(loaded, "Planetary VC")
        self.assertIsNone(planetary["contact_route"])
        mana = targets.find_target(loaded, "Mana Ventures")
        self.assertIsNone(mana["contact_route"])

    def test_find_target_case_insensitive(self):
        loaded = targets.load_targets()
        found = targets.find_target(loaded, "epic ventures")
        self.assertEqual(found["name"], "EPIC Ventures")

    def test_find_target_unknown_raises(self):
        loaded = targets.load_targets()
        with self.assertRaises(targets.TargetError):
            targets.find_target(loaded, "Nonexistent Fund")


class TestDraftsAndApprovalGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.drafts_dir = Path(self.tmp.name) / "drafts"
        self.target = {"name": "EPIC Ventures", "stage": "Pre-seed through Series B"}

    def tearDown(self):
        self.tmp.cleanup()

    def test_draft_written_with_correct_header(self):
        path = drafts.write_draft(
            self.target, "Subject: hello\n\nBody text.",
            drafts_dir=self.drafts_dir, today=date(2026, 11, 25),
        )
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "epic-ventures-2026-11-25.md")
        fields = drafts.read_header(path)
        self.assertEqual(fields["target"], "EPIC Ventures")
        self.assertEqual(fields["date"], "2026-11-25")
        self.assertEqual(fields["status"], drafts.STATUS_DRAFT)
        self.assertIn("Body text.", path.read_text(encoding="utf-8"))

    def test_draft_command_with_mocked_brain(self):
        with mock.patch(
            "outreach.cli.brain.chat", return_value="Subject: hi\n\nDraft body."
        ) as fake_chat:
            rc = cli.main([
                "draft", "--target", "EPIC Ventures",
                "--drafts-dir", str(self.drafts_dir),
            ])
        self.assertEqual(rc, 0)
        fake_chat.assert_called_once()
        rows = drafts.list_drafts(drafts_dir=self.drafts_dir)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], drafts.STATUS_DRAFT)

    def test_status_only_changes_via_approve(self):
        path = drafts.write_draft(
            self.target, "Subject: hi\n\nBody.",
            drafts_dir=self.drafts_dir, today=date(2026, 11, 25),
        )
        # Writing and listing never change the status.
        self.assertEqual(drafts.read_header(path)["status"], drafts.STATUS_DRAFT)
        drafts.list_drafts(drafts_dir=self.drafts_dir)
        self.assertEqual(drafts.read_header(path)["status"], drafts.STATUS_DRAFT)
        # The approve command flips it.
        rc = cli.main(["approve", str(path)])
        self.assertEqual(rc, 0)
        self.assertEqual(drafts.read_header(path)["status"], drafts.STATUS_APPROVED)
        # Approving again is a no-op, status stays APPROVED.
        rc = cli.main(["approve", str(path)])
        self.assertEqual(rc, 0)
        self.assertEqual(drafts.read_header(path)["status"], drafts.STATUS_APPROVED)

    def test_approve_missing_file_errors(self):
        with self.assertRaises(drafts.DraftError):
            drafts.approve_draft(self.drafts_dir / "nope.md")

    def test_no_send_command_exists(self):
        parser = cli.build_parser()
        # argparse stores subparsers; inspect the choices.
        subparsers = [
            action for action in parser._actions
            if isinstance(action, __import__("argparse")._SubParsersAction)
        ]
        self.assertEqual(len(subparsers), 1)
        self.assertEqual(
            set(subparsers[0].choices), {"draft", "approve", "list"}
        )


if __name__ == "__main__":
    unittest.main()
