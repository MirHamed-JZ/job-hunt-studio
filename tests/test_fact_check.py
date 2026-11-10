"""The fact and voice check flags planted overclaims in the example persona's resume, and nothing in the clean one.

Run from the plugin folder: python -m unittest discover tests
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from fact_check import EXAMPLE_MARKER, check, tex_to_text  # noqa: E402

LEDGER = (ROOT / "examples" / "persona" / "docs" / "Evidence_Ledger.md").read_text(encoding="utf-8")
TEMPLATES = {name: (ROOT / "templates" / "resume" / name / "Resume.tex").read_text(encoding="utf-8")
             for name in ("classic", "jakes")}


class Cfg:
    """Stands in for jhs.yaml."""

    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


CFG = Cfg(**{"candidate.work_authorization": "EU citizen"})


def run(tex: str, kind: str = "resume"):
    return check(tex_to_text(tex), LEDGER, kind=kind, cfg=CFG, tex_source=tex, source=tex)


def without_marker(tex: str) -> str:
    return "\n".join(line for line in tex.splitlines() if EXAMPLE_MARKER not in line)


class CleanTemplates(unittest.TestCase):
    def test_only_the_example_marker_is_reported(self):
        for name, tex in TEMPLATES.items():
            with self.subTest(name):
                kinds = [f.kind for f in run(tex).open]
                self.assertEqual(kinds, ["example"])

    def test_clean_once_the_marker_is_gone(self):
        for name, tex in TEMPLATES.items():
            with self.subTest(name):
                self.assertEqual([(f.kind, f.match) for f in run(without_marker(tex)).open], [])


class PlantedOverclaims(unittest.TestCase):
    def setUp(self):
        self.base = without_marker(TEMPLATES["jakes"])

    def plant(self, old: str, new: str) -> list[tuple[str, str]]:
        self.assertIn(old, self.base)
        return [(f.kind, f.match) for f in run(self.base.replace(old, new, 1)).open]

    def test_number_not_in_ledger(self):
        self.assertIn(("number", "4.2%"), self.plant(r"(NDCG@10) by 3.1\%", r"(NDCG@10) by 4.2\%"))

    def test_a_duration_must_match_with_its_unit(self):
        # "6 hours" is in the Ledger; "6 years" is not
        self.assertIn(("number", "6"), self.plant("ML engineer with 4 years", "ML engineer with 6 years"))
        self.assertIn(("number", "5+"), self.plant("ML engineer with 4 years", "ML engineer with 5+ years"))
        self.assertIn(("number", "6"), self.plant("from 6 hours", "from 6 days"))
        self.assertEqual(self.plant("ML engineer with 4 years", "ML engineer with 4+ years"), [])

    def test_hard_line_deployed(self):
        found = self.plant("validation tests;", "validation tests; deployed the v2 ranker;")
        self.assertIn("hard-line", [k for k, _ in found])

    def test_codename(self):
        self.assertIn(("hard-line", "Kestrel"), self.plant("learning-to-rank model (LightGBM", "Kestrel model (LightGBM"))

    def test_gap_skill(self):
        self.assertIn(("gap-skill", "Kubernetes"), self.plant("PyTorch, PySpark}", "PyTorch, PySpark, Kubernetes}"))

    def test_wrong_dates_on_an_entry(self):
        found = self.plant("{Machine Learning Engineer}{Sep 2022 -- Present}", "{Machine Learning Engineer}{Sep 2021 -- Present}")
        self.assertIn("title", [k for k, _ in found])
        self.assertIn(("date", "Sep 2021"), found)

    def test_title_not_in_roles(self):
        found = self.plant("{Machine Learning Engineer}{Sep 2022", "{Senior Machine Learning Engineer}{Sep 2022")
        self.assertIn(("title", "Senior Machine Learning Engineer"), found)

    def test_voice(self):
        found = self.plant("ML engineer with 4 years", "Passionate ML engineer --- with 4 years, 3--5 teams")
        kinds = [k for k, _ in found]
        self.assertIn(("phrase", "Passionate"), found)
        self.assertEqual(kinds.count("dash"), 2)  # the em dash and the en dash in "3-5"; date ranges are exempt

    def test_never_print(self):
        self.assertIn("never-print", [k for k, _ in self.plant("ML engineer with 4 years", "EU citizen; ML engineer with 4 years")])


class Acknowledgements(unittest.TestCase):
    def test_ack_citing_a_block_resolves_the_warning(self):
        tex = without_marker(TEMPLATES["jakes"]).replace("with 4 years", "with 5+ years", 1)
        self.assertEqual([f.match for f in run(tex).open], ["5+"])
        acked = tex + "\n% fact-ok: 5+ | counted from the [roles] dates\n"
        report = run(acked)
        self.assertEqual(report.open, [])
        self.assertEqual([f.ack for f in report.findings], ["counted from the [roles] dates"])

    def test_ack_without_a_ledger_reference_is_ignored(self):
        tex = without_marker(TEMPLATES["jakes"]).replace("with 4 years", "with 5+ years", 1)
        report = run(tex + "\n% fact-ok: 5+ | trust me\n")
        self.assertEqual(len(report.open), 1)
        self.assertIn("ignored", report.open[0].ack_problem)

    def test_gap_never_print_and_title_cannot_be_acknowledged(self):
        base = without_marker(TEMPLATES["jakes"])
        planted = (base.replace("PyTorch, PySpark}", "PyTorch, PySpark, Kubernetes}", 1)
                   .replace("ML engineer with 4 years", "EU citizen; ML engineer with 4 years", 1)
                   .replace("{Machine Learning Engineer}{Sep 2022", "{Senior Machine Learning Engineer}{Sep 2022", 1))
        acks = ("\n% fact-ok: Kubernetes | [skills-claimed] used it at work"
                "\n% fact-ok: EU citizen | [identity]"
                "\n% fact-ok: Senior Machine Learning Engineer | [roles]\n")
        kinds = sorted(f.kind for f in run(planted + acks).open)
        self.assertEqual(kinds, ["gap-skill", "never-print", "title"])

    def test_hard_line_acknowledgement_must_name_the_rule(self):
        tex = without_marker(TEMPLATES["jakes"]).replace("validation tests;", "validation tests; the ranker was not deployed;", 1)
        self.assertEqual([f.kind for f in run(tex).open], ["hard-line"])
        wrong = run(tex + "\n% fact-ok: not deployed | [project:ranker-v2]\n")
        self.assertEqual(len(wrong.open), 1)
        right = run(tex + "\n% fact-ok: not deployed | HL-ranker-status: says it was not deployed, see [project:ranker-v2]\n")
        self.assertEqual(right.open, [])
        # the documented form: the rule id is the Ledger reference
        documented = run(tex + "\n% fact-ok: deployed | HL-ranker-status: says it was not deployed\n")
        self.assertEqual(documented.open, [])

    def test_dashes_and_stock_phrases_are_reworded_not_acknowledged(self):
        tex = without_marker(TEMPLATES["jakes"]).replace("ML engineer with 4 years", "Passionate ML engineer --- with 4 years", 1)
        acks = "\n% fact-ok: — | [identity] style choice\n% fact-ok: Passionate | [summary] my word\n"
        report = run(tex + acks)
        self.assertEqual(sorted(f.kind for f in report.open), ["dash", "phrase"])
        self.assertTrue(all("never acknowledged" in f.ack_problem for f in report.open))

    def test_a_gap_is_caught_in_other_forms(self):
        from fact_check import gap_pattern
        ab, llm = gap_pattern("A/B testing"), gap_pattern("LLM fine-tuning")
        for text in ("Ran online A/B tests", "A/B tested two rankers", "A/B testing at scale"):
            self.assertTrue(ab.search(text), text)
        for text in ("Fine-tuned LLMs", "fine-tuning of two LLMs", "LLM fine tuning", "LLMs fine-tuned"):
            self.assertTrue(llm.search(text), text)
        for text in ("fine-tuning embedding models with LoRA", "tests for the ranker", "A/B"):
            self.assertFalse(ab.search(text) or llm.search(text), text)
        self.assertTrue(gap_pattern("Kubernetes").search("Kubernetes clusters"))

    def test_a_gap_is_caught_without_its_qualifier(self):
        self.assertIn(("gap-skill", "A/B testing"),
                      [(f.kind, f.match) for f in run(without_marker(TEMPLATES["jakes"]).replace(
                          "PyTorch, PySpark}", "PyTorch, PySpark, A/B testing}", 1)).open])

    def test_example_marker_cannot_be_acknowledged(self):
        tex = TEMPLATES["classic"] + "\n% fact-ok: JHS-EXAMPLE-CONTENT | see [roles]\n"
        self.assertEqual([f.kind for f in run(tex).open], ["example"])


class Scopes(unittest.TestCase):
    def test_resume_only_rule_does_not_apply_to_messages(self):
        text = "I led the search revamp evaluation."
        self.assertIn("HL-team-role", [f.rule for f in check(text, LEDGER, kind="cover-letter").open])
        self.assertNotIn("HL-team-role", [f.rule for f in check(text, LEDGER, kind="message").open])

    def test_questions_in_headings_and_word_counts_are_not_claims(self):
        from fact_check import md_to_text
        md = "## Why this role? (100 words max)\n\nI improved NDCG@10 by 3.1%.\n\n(84 words)\n"
        self.assertEqual(check(md_to_text(md), LEDGER, kind="form").open, [])
        self.assertEqual(len(check(md_to_text(md.replace("3.1%", "9%")), LEDGER, kind="form").open), 1)

    def test_form_answers_may_state_work_authorization(self):
        text = "Work authorization: EU citizen."
        self.assertEqual([f.kind for f in check(text, LEDGER, kind="form", cfg=CFG).open], [])
        self.assertIn("never-print", [f.kind for f in check(text, LEDGER, kind="cover-letter", cfg=CFG).open])


if __name__ == "__main__":
    unittest.main()
