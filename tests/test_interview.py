"""Interview practice, the claim gate and LinkedIn text: the pack's topics, the practice log, the input checks, and the
fact and voice check on a LinkedIn draft and a thank-you note.

Run from the plugin folder: python -m unittest discover tests
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from fact_check import check, infer_kind, md_to_text  # noqa: E402
from practice import Area, parse_topics, standings, table_rows  # noqa: E402

HAVE_YAML = importlib.util.find_spec("yaml") is not None
LEDGER = (ROOT / "examples" / "persona" / "docs" / "Evidence_Ledger.md").read_text(encoding="utf-8")
TOPICS = (ROOT / "packs" / "ml-research" / "TOPICS.md").read_text(encoding="utf-8")
LOG_TEMPLATE = (ROOT / "templates" / "workspace" / "interview" / "PRACTICE_LOG.md").read_text(encoding="utf-8")
GATE_TEMPLATE = (ROOT / "templates" / "workspace" / "interview" / "CLAIM_GATE.md").read_text(encoding="utf-8")


def tool(name: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOLS / name), *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def make_workspace(tmp: Path, persona: bool = True) -> Path:
    ws = tmp / "ws"
    (ws / "docs").mkdir(parents=True)
    source = ROOT / "examples" / "persona" if persona else ROOT / "templates" / "workspace"
    shutil.copyfile(source / "jhs.yaml", ws / "jhs.yaml")
    shutil.copyfile(source / "docs" / "Evidence_Ledger.md", ws / "docs" / "Evidence_Ledger.md")
    return ws


class Topics(unittest.TestCase):
    def test_ml_research_pack_parses(self):
        areas, problems = parse_topics(TOPICS)
        self.assertEqual(problems, [])
        self.assertEqual(len(areas), 16)
        self.assertEqual(len({a.slug for a in areas}), 16)
        groups = {a.group for a in areas}
        self.assertEqual(groups, {"Core areas", "Field areas"})
        self.assertIn("recsys-ranking", [a.slug for a in areas])

    def test_problems_are_named(self):
        text = ("## Areas\n\n1. **Good Area**: bad name\n   Reading: x\n2. **dup**: one\n   Reading: x\n"
                "3. **dup**: two\n4. **no-reading**: none\n")
        problems = " ".join(parse_topics(text)[1])
        self.assertIn("`Good Area` must be lowercase", problems)
        self.assertIn("`dup` appears twice", problems)
        self.assertIn("`no-reading` has no indented", problems)
        self.assertIn("no areas found", " ".join(parse_topics("# nothing\n")[1]))


class PracticeLog(unittest.TestCase):
    LOG = LOG_TEMPLATE.replace(
        "| Area | Subtopic | Last practiced | Best grade | Status |\n|---|---|---|---|---|\n",
        "| Area | Subtopic | Last practiced | Best grade | Status |\n|---|---|---|---|---|\n"
        "| recsys-ranking | LambdaMART | 2026-11-01 | 3 | solid |\n"
        "| recsys-ranking | position bias | 2026-11-02 | 4 | solid |\n"
        "| evaluation | A/B test power | 2026-11-03 | 2 | shaky |\n"
        "| behavioral | conflict story | 2026-11-04 | 3 | passed once |\n").replace(
        "| Area | Question | What was missing | Added |\n|---|---|---|---|\n",
        "| Area | Question | What was missing | Added |\n|---|---|---|---|\n"
        "| evaluation | Sample size for a 1% lift | no power formula | 2026-11-03 |\n")

    def test_template_has_empty_tables(self):
        for heading in ("Coverage", "Open weak spots", "Rounds", "Story bank"):
            self.assertIn(f"## {heading}", LOG_TEMPLATE)
        self.assertEqual(table_rows(LOG_TEMPLATE, "Coverage"), [])
        self.assertEqual(table_rows(LOG_TEMPLATE, "Open weak spots"), [])
        self.assertIn("| Date | Skill | Project (Ledger block or link) | Result |", GATE_TEMPLATE)

    def test_order_never_then_shaky_then_solid(self):
        areas = [Area("evaluation", "Core areas", ""), Area("recsys-ranking", "Field areas", ""),
                 Area("ml-coding", "Core areas", "")]
        result = {s.area: s for s in standings(areas, self.LOG)}
        order = [s.area for s in standings(areas, self.LOG)]
        self.assertEqual(order[0], "ml-coding")
        self.assertEqual(result["ml-coding"].status, "never")
        self.assertEqual(result["evaluation"].status, "shaky")
        self.assertEqual(len(result["evaluation"].weak_spots), 1)
        self.assertEqual(result["recsys-ranking"].status, "solid")
        self.assertEqual(result["recsys-ranking"].last, "2026-11-02")
        self.assertEqual(order[-1], "recsys-ranking")
        self.assertEqual(result["behavioral"].group, "your own")  # in the log, not in the pack
        self.assertEqual(result["behavioral"].status, "once")


@unittest.skipUnless(HAVE_YAML, "needs PyYAML (requirements.txt)")
class Workspace(unittest.TestCase):
    def test_plan_without_a_log_and_with_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_workspace(Path(tmp))
            first = tool("practice.py", "plan", cwd=ws)
            (ws / "interview").mkdir()
            (ws / "interview" / "PRACTICE_LOG.md").write_text(PracticeLog.LOG, encoding="utf-8")
            second = tool("practice.py", "plan", cwd=ws)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("not created yet", first.stdout)
        self.assertIn("pack ml-research, 16 areas", first.stdout)
        self.assertIn("Open weak spots (1):", second.stdout)
        self.assertLess(second.stdout.index("ml-coding"), second.stdout.index("recsys-ranking"))

    def test_no_pack_still_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_workspace(Path(tmp))
            text = (ws / "jhs.yaml").read_text(encoding="utf-8").replace("pack: ml-research", "pack: none")
            (ws / "jhs.yaml").write_text(text, encoding="utf-8")
            plan = tool("practice.py", "plan", cwd=ws)
            pre = tool("preflight.py", "mock-interview", cwd=ws)
        self.assertEqual(plan.returncode, 0)
        self.assertIn("no topic list", plan.stdout)
        self.assertEqual(pre.returncode, 0, pre.stdout)
        self.assertIn("WARN", pre.stdout)
        self.assertIn("name any topic", pre.stdout)

    def test_preflight_blank_workspace_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_workspace(Path(tmp), persona=False)
            results = {s: tool("preflight.py", s, cwd=ws) for s in
                       ("mock-interview", "mock-interview-cv", "interview-drill", "linkedin-refresh")}
        for skill, r in results.items():
            with self.subTest(skill):
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("RESULT: STOP", r.stdout)
                self.assertIn("/job-hunt-studio:setup", r.stdout)
        self.assertIn("[positioning] still holds setup placeholders", results["mock-interview"].stdout)
        self.assertIn("[skills-gaps] still holds setup placeholders", results["interview-drill"].stdout)

    def test_preflight_persona(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_workspace(Path(tmp))
            subprocess.run(["git", "init", "-q"], cwd=ws)
            cv = tool("preflight.py", "mock-interview-cv", cwd=ws)
            drill = tool("preflight.py", "interview-drill", cwd=ws)
            linkedin = tool("preflight.py", "linkedin-refresh", cwd=ws)
            (ws / "linkedin").mkdir()
            (ws / "linkedin" / "PROFILE.md").write_text("Live since: 2026-11-01\n", encoding="utf-8")
            linkedin_after = tool("preflight.py", "linkedin-refresh", cwd=ws)
        self.assertEqual(cv.returncode, 0, cv.stdout)
        self.assertIn("resume questions come from the base draft", cv.stdout)
        self.assertIn("pack ml-research: 16 interview areas", cv.stdout)
        self.assertEqual(drill.returncode, 0, drill.stdout)
        self.assertEqual(linkedin.returncode, 0, linkedin.stdout)
        self.assertIn("No current LinkedIn profile", linkedin.stdout)
        self.assertIn("current profile: linkedin/PROFILE.md", linkedin_after.stdout)


class LinkedInDraft(unittest.TestCase):
    CLEAN = ("# LinkedIn draft\n\n## Headline (61 characters)\n\nMachine Learning Engineer | Search ranking and evaluation\n\n"
             "## About (240 characters)\n\nI build and evaluate ranking models for e-commerce search. My learning-to-rank "
             "model improved NDCG@10 by 3.1% in a 30-day offline replay.\n\n"
             "## Skills\n\nPython, learning to rank, offline evaluation, PySpark, SQL, PyTorch\n")

    def open_findings(self, text: str, kind: str = "linkedin"):
        return check(md_to_text(text), LEDGER, kind=kind)

    def test_clean_draft_and_counts_in_headings(self):
        self.assertEqual(self.open_findings(self.CLEAN).open, [])

    def test_planted_overclaims_are_caught(self):
        cases = {
            "The v2 ranker was deployed to production.": "HL-ranker-status",
            "I led the search revamp.": "HL-team-role",
        }
        for sentence, rule in cases.items():
            with self.subTest(rule):
                report = self.open_findings(self.CLEAN + "\n" + sentence + "\n")
                self.assertIn(rule, [f.rule for f in report.open])
        kinds = [f.kind for f in self.open_findings(self.CLEAN.replace("PyTorch", "PyTorch, Kubernetes")).open]
        self.assertIn("gap-skill", kinds)

    def test_work_authorization_never_on_linkedin(self):
        class Cfg:
            def get(self, key, default=None):
                return {"candidate.work_authorization": "EU citizen"}.get(key, default)

        report = check(md_to_text(self.CLEAN + "\nEU citizen, open to relocation.\n"), LEDGER, kind="linkedin",
                       cfg=Cfg())
        self.assertIn("never-print", [f.kind for f in report.open])

    def test_file_kinds(self):
        self.assertEqual(infer_kind(Path("linkedin/LINKEDIN_2026-11-08.md")), "linkedin")
        self.assertEqual(infer_kind(Path("applications/X/thank_you_2026-11-13.md")), "message")


if __name__ == "__main__":
    unittest.main()
