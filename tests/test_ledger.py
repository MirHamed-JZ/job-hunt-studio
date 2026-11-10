"""The Ledger reader works on the blank template a new user starts from.

Run from the plugin folder: python -m unittest discover tests
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from ledger import anchors, hard_lines, is_pending  # noqa: E402

TEMPLATE = (ROOT / "templates" / "workspace" / "docs" / "Evidence_Ledger.md").read_text(encoding="utf-8")

REQUIRED = {"positioning", "identity", "roles", "publications", "summary", "skills-claimed", "skills-gaps",
            "skill-paraphrases", "hard-lines", "never-print", "platform-facts", "open-items"}


class TemplateLedger(unittest.TestCase):
    def test_anchors_present(self):
        self.assertTrue(REQUIRED <= set(anchors(TEMPLATE)))

    def test_blank_template_is_pending_not_empty_rules(self):
        self.assertEqual(hard_lines(TEMPLATE), [])  # no rows yet
        self.assertTrue(is_pending(anchors(TEMPLATE)["hard-lines"]))  # but marked as not set up

    def test_missing_table_raises(self):
        with self.assertRaises(ValueError):
            hard_lines("# Evidence Ledger\n\n## 0. Current facts\n\n### Identity [identity]\n")


if __name__ == "__main__":
    unittest.main()
