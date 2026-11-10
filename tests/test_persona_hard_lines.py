"""The example persona's Ledger parses: every anchor present, nothing pending, and each hard line catches bad sentences and passes good ones.

Run from the plugin folder: python -m unittest discover tests
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from ledger import anchors, hard_lines, is_pending  # noqa: E402

PERSONA = (ROOT / "examples" / "persona" / "docs" / "Evidence_Ledger.md").read_text(encoding="utf-8")

REQUIRED = {"positioning", "identity", "roles", "publications", "summary", "skills-claimed", "skills-gaps",
            "skill-paraphrases", "hard-lines", "never-print", "platform-facts", "open-items"}

# id -> (sentences that break the rule, sentences that keep it)
CASES = {
    "HL-ranker-status": (
        ["Deployed the v2 ranker to production", "The ranker is live on the search page", "Shipped the new ranker"],
        ["The ranker was evaluated offline on a 30-day replay", "Prototyped the ranker during my internship",
         "The ranker delivered NDCG@10 +3.1% over the production scorer"],
    ),
    "HL-codename": (["Built Kestrel, a learning-to-rank model"], ["Built the v2 product ranker"]),
    "HL-team-role": (["Led the search revamp", "Owned the search relevance revamp"],
                     ["Built the evaluation for the search revamp", "Led the weekly metrics report"]),
}


class PersonaLedger(unittest.TestCase):
    def test_anchors_present(self):
        found = set(anchors(PERSONA))
        self.assertTrue(REQUIRED <= found, REQUIRED - found)
        self.assertTrue(any(a.startswith("project:") for a in found))

    def test_hard_lines(self):
        rules = {r.id: r for r in hard_lines(PERSONA)}
        self.assertEqual(set(rules), set(CASES))
        for rule_id, (bad, good) in CASES.items():
            for sentence in bad:
                with self.subTest(rule_id, bad=sentence):
                    self.assertTrue(rules[rule_id].banned.search(sentence))
            for sentence in good:
                with self.subTest(rule_id, good=sentence):
                    self.assertFalse(rules[rule_id].banned.search(sentence))

    def test_mention_of_anchor_elsewhere_does_not_confuse_parser(self):
        text = PERSONA.replace("- Results:", "- See [hard-lines] for wording. Results:", 1)
        self.assertEqual(len(hard_lines(text)), len(CASES))

    def test_nothing_pending(self):
        pending = [a for a, body in anchors(PERSONA).items() if is_pending(body)]
        self.assertEqual(pending, [])


if __name__ == "__main__":
    unittest.main()
