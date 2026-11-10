"""find_people.py and the outreach parts of preflight and the fact check, on fictional data (no network).

Needs PyYAML (requirements.txt). Run from the plugin folder: python -m unittest discover tests
"""
from __future__ import annotations

import datetime as dt
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

import find_people as fp  # noqa: E402
from fact_check import check, md_to_text  # noqa: E402

HAVE_YAML = importlib.util.find_spec("yaml") is not None
PERSONA = ROOT / "examples" / "persona"
LEDGER = (PERSONA / "docs" / "Evidence_Ledger.md").read_text(encoding="utf-8")
CSV = """Notes:
"When exporting your connection data, you may notice that some of the email addresses are missing."

First Name,Last Name,URL,Email Address,Company,Position,Connected On
Jordan,Example,https://www.linkedin.com/in/jhs-fictional-jordan-0001,,Calloway Market,Senior Data Scientist,12 Mar 2025
Casey,Sample,https://www.linkedin.com/in/jhs-fictional-casey-0002,,Northwind Retail Labs Inc.,ML Engineer,03 Oct 2023
Riley,Placeholder,https://www.linkedin.com/in/jhs-fictional-riley-0003,,Calloway Marketplace Bank,Analyst,21 Jun 2024
"""


class Cfg:
    """Stands in for jhs.yaml."""

    def __init__(self, **values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


def tool(name: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOLS / name), *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


class Companies(unittest.TestCase):
    def test_same_company(self):
        self.assertTrue(fp.same_company("Acme Corporation Inc.", "Acme"))
        self.assertTrue(fp.same_company("Calloway Market (fictional)", "Calloway Market"))
        self.assertFalse(fp.same_company("Acme", "Acmeville Bank"))
        self.assertFalse(fp.same_company("", "Acme"))


class Connections(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "Connections.csv"
        self.path.write_text(CSV, encoding="utf-8")

    def test_reads_the_export_after_its_note_lines(self):
        rows = fp.read_connections(self.path)
        self.assertEqual(len(rows), 3)

    def test_matches_the_company_and_its_aliases_only(self):
        rows = fp.read_connections(self.path)
        found = fp.scan_connections("Calloway Market (fictional)", rows)
        self.assertEqual([p["name"] for p in found], ["Jordan Example"])
        self.assertTrue(found[0]["confidence"].startswith("High"))
        self.assertEqual([p["name"] for p in fp.scan_connections("Northwind", rows, ["Northwind Retail Labs"])],
                         ["Casey Sample"])

    def test_not_an_export(self):
        self.path.write_text("Name,Company\nA,B\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            fp.read_connections(self.path)

    def test_status_lines(self):
        missing = self.path.with_name("none.csv")
        self.assertIn("skipped", fp.connections_status(missing, "skipped"))
        self.assertIn("missing", fp.connections_status(missing, "added"))
        self.assertIn("not set up", fp.connections_status(missing, "unset"))
        self.assertIn("0 days old", fp.connections_status(self.path, "added"))


class Research(unittest.TestCase):
    def test_authors_ranked_by_topic_and_recency(self):
        recent = (dt.date.today() - dt.timedelta(days=30)).isoformat()
        old = (dt.date.today() - dt.timedelta(days=500)).isoformat()

        def author(aid, name, position, inst="I1"):
            return {"author": {"id": f"https://openalex.org/{aid}", "display_name": name}, "author_position": position,
                    "institutions": [{"id": f"https://openalex.org/{inst}"}], "raw_affiliation_strings": ["Acme"]}

        works = [
            {"id": "W1", "title": "Learning to rank for product search", "publication_date": recent,
             "authorships": [author("A1", "Sam Ranker", "first"), author("A2", "Pat Lead", "last"),
                             author("A9", "Elsewhere", "middle", inst="I2")]},
            {"id": "W2", "title": "Protein folding at scale", "publication_date": old,
             "authorships": [author("A3", "Lee Bio", "first")]},
        ]
        ids = {"I1"}
        people = fp.rank_authors(works, lambda a: bool(ids & {i["id"].rsplit("/", 1)[-1] for i in a["institutions"]}),
                                 ["rank", "search"])
        names = [p["name"] for p in people]
        self.assertEqual(names[:2], ["Pat Lead", "Sam Ranker"])  # on topic; the last author ranks first
        self.assertNotIn("Elsewhere", names)  # another affiliation
        self.assertTrue(people[-1]["confidence"].startswith("Low"))  # last paper over a year ago

    def test_one_person_split_across_records_is_merged(self):
        def author(aid, name):
            return {"author": {"id": f"https://openalex.org/{aid}", "display_name": name},
                    "author_position": "first", "institutions": [], "raw_affiliation_strings": []}

        works = [{"id": f"W{i}", "title": "Ranking", "publication_date": "2026-01-01",
                  "authorships": [author(f"A{i}", name)]}
                 for i, name in enumerate(["Chen Example", "Chen  Example", "chen example", "Other Person"])]
        people = fp.rank_authors(works, lambda a: True, ["rank"])
        self.assertEqual(sorted(p["name"] for p in people), ["Chen Example", "Other Person"])
        merged = next(p for p in people if p["name"] == "Chen Example")
        self.assertEqual((merged["papers"], merged["openalex_records"]), (3, 3))


class Github(unittest.TestCase):
    def test_confidence(self):
        self.assertTrue(fp.github_confidence("Acme", ["acme-ai"], "@acme", False).startswith("Medium (profile"))
        self.assertTrue(fp.github_confidence("Acme", ["acme-ai"], "Globex", True).startswith("Low (profile names"))
        self.assertTrue(fp.github_confidence("Acme", ["acme-ai"], "", True).startswith("Medium (public org"))
        self.assertTrue(fp.github_confidence("Acme", ["acme-ai"], "", False).startswith("Low (contributor"))


class Queries(unittest.TestCase):
    CFG = Cfg(**{"target.titles": ["Machine Learning Engineer", "Applied Scientist"],
                 "candidate.schools": ["Halden Institute of Technology"],
                 "candidate.past_employers": ["Brightfield Commerce", "Acme"]})

    def test_ties_and_domains(self):
        queries = fp.web_queries("Acme (fictional)", "Lyon", self.CFG)
        text = [q["query"] for q in queries]
        self.assertIn("Acme Halden Institute of Technology Lyon", text)
        self.assertIn("Acme Brightfield Commerce Lyon", text)
        self.assertNotIn("Acme Acme Lyon", text)  # a past employer that is the company itself
        self.assertFalse(any("site:" in q or "(fictional)" in q for q in text))
        for q in queries:
            if q["for"].startswith(("role", "tie", "hiring")):
                self.assertEqual(q["allowed_domains"], ["linkedin.com"])

    def test_field_and_pastes(self):
        self.assertEqual(fp.field_words(self.CFG), "Machine Learning")
        pastes = fp.paste_requests("Acme", "Lyon", self.CFG)
        self.assertIn("Halden Institute of Technology alumni", pastes[1])


@unittest.skipUnless(HAVE_YAML, "needs PyYAML")
class Workspace(unittest.TestCase):
    def make(self, persona=True) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        ws = Path(tmp.name)
        (ws / "docs").mkdir()
        src = PERSONA if persona else ROOT / "templates" / "workspace"
        shutil.copyfile(src / "jhs.yaml", ws / "jhs.yaml")
        shutil.copyfile(src / "docs" / "Evidence_Ledger.md", ws / "docs" / "Evidence_Ledger.md")
        return ws

    def test_check_connections(self):
        ws = self.make()
        private = ws / "applications" / "outreach" / "private"
        private.mkdir(parents=True)
        (private / "Connections.csv").write_text(CSV, encoding="utf-8")
        r = tool("find_people.py", "--check-connections", cwd=ws)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK: 3 connections", r.stdout)

    def test_preflight_outreach(self):
        r = tool("preflight.py", "outreach", cwd=self.make())
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("outreach.topics is empty", r.stdout)
        self.assertIn("connections export is not set up", r.stdout)
        r = tool("preflight.py", "outreach", cwd=self.make(persona=False))
        self.assertEqual(r.returncode, 1)
        self.assertIn("`candidate.name` is empty", r.stdout)

    def test_preflight_find_jobs(self):
        blank = tool("preflight.py", "find-jobs", cwd=self.make(persona=False))
        self.assertEqual(blank.returncode, 1)
        for text in ("`target.titles` is empty", "tier 1 (1 home city) has no place names",
                     "search.watchlist is empty"):
            self.assertIn(text, blank.stdout)
        ws = self.make()
        r = tool("preflight.py", "find-jobs", cwd=ws)
        self.assertIn("find-jobs add <company>", r.stdout)
        self.assertEqual(r.returncode, 1)
        yaml_text = (ws / "jhs.yaml").read_text(encoding="utf-8")
        (ws / "jhs.yaml").write_text(yaml_text.replace(
            "  watchlist: []", '  watchlist: [{company: "Acme", ats: lever, slug: "acme"}]'), encoding="utf-8")
        r = tool("preflight.py", "find-jobs", cwd=ws)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("watchlist: 1 company", r.stdout)
        self.assertEqual(tool("preflight.py", "find-jobs-add", cwd=self.make(persona=False)).returncode, 0)

    @unittest.skipIf(importlib.util.find_spec("jobspy") is not None, "JobSpy is installed here")
    def test_jobspy_chosen_but_missing_is_a_warning(self):
        ws = self.make()
        text = (ws / "jhs.yaml").read_text(encoding="utf-8").replace("    enabled: false", "    enabled: true")
        (ws / "jhs.yaml").write_text(text, encoding="utf-8")
        r = tool("preflight.py", "find-jobs", cwd=ws)
        self.assertEqual(r.returncode, 0, r.stdout)  # JobSpy alone is something to scan
        self.assertIn("JobSpy is enabled in jhs.yaml but not installed", r.stdout)


class RecipientAcknowledgement(unittest.TestCase):
    TEXT = ("Your paper on catalog ranking (September 2026) caught my eye. At Brightfield I improved NDCG@10 by 3.1% "
            "in a 30-day offline replay.\n<!-- fact-ok: September 2026 | [recipient] the date of their paper -->\n")

    POSTING = "Fernwick Goods (fictional). Our catalog ranks 400,000 products. Paper of September 2026. 6+ years."

    def run_check(self, text, kind, posting=None):
        return check(md_to_text(text), LEDGER, kind=kind, source=text, posting=posting)

    def test_resolves_a_date_about_the_recipient_in_a_message(self):
        report = self.run_check(self.TEXT, "message")
        self.assertEqual(report.open, [])

    def test_in_cover_letters_and_form_answers_only_what_the_posting_says(self):
        for kind in ("cover-letter", "form"):
            with self.subTest(kind):
                self.assertEqual(self.run_check(self.TEXT, kind, posting=self.POSTING).open, [])
                refused = self.run_check(self.TEXT, kind)  # no posting.md beside it
                self.assertEqual([f.kind for f in refused.open], ["date"])
                self.assertIn("posting.md", refused.open[0].ack_problem)
        letter = "Your team ranks 400,000 products.\n<!-- fact-ok: 400,000 | [recipient] from the posting -->\n"
        self.assertEqual(self.run_check(letter, "cover-letter", posting=self.POSTING).open, [])
        self.assertEqual(len(self.run_check(letter, "cover-letter", posting="Our catalog is large.").open), 1)

    def test_whole_numbers_from_the_posting_text_only(self):
        # found by the final check: "17" was accepted because the posting says "2017", "78" because of a link
        posting = "Founded in 2017. We serve 85 million shoppers. Apply: https://example.com/jobs/7781"
        for number, ok in (("17", False), ("78", False), ("2017", True), ("85 million", True)):
            letter = f"I read about your {number} figure." + chr(10) + f"<!-- fact-ok: {number} | [recipient] from the posting -->" + chr(10)
            with self.subTest(number):
                self.assertEqual(self.run_check(letter, "cover-letter", posting=posting).open == [], ok)

    def test_never_a_duration(self):
        # found by the end-to-end reviewer (phase 4): [recipient] silenced the candidate's own "6 years"
        letter = "I bring 6 years of experience.\n<!-- fact-ok: 6 | [recipient] from the posting -->\n"
        for kind in ("cover-letter", "message"):
            with self.subTest(kind):
                report = self.run_check(letter, kind, posting=self.POSTING)
                self.assertEqual([f.kind for f in report.open], ["number"])
                self.assertIn("never covers a duration", report.open[0].ack_problem)

    def test_not_in_text_about_the_user(self):
        for kind in ("resume", "linkedin"):
            with self.subTest(kind):
                self.assertEqual([f.kind for f in self.run_check(self.TEXT, kind).open], ["date"])

    def test_covers_numbers_and_dates_only(self):
        text = "We shipped the v2 ranker. A synergy!\n" \
               "<!-- fact-ok: shipped the v2 ranker | [recipient] about them -->\n" \
               "<!-- fact-ok: synergy | [recipient] their word -->\n"
        report = self.run_check(text, "message")
        kinds = sorted(f.kind for f in report.open)
        self.assertEqual(kinds, ["hard-line", "phrase"])
        problems = " ".join(f.ack_problem for f in report.open)
        self.assertIn("must name the rule", problems)
        self.assertIn("never acknowledged", problems)


if __name__ == "__main__":
    unittest.main()
