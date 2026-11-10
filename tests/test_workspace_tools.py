"""The workspace tools on a throwaway workspace: preflight, build, ATS check, lint and approval.

Needs the packages in requirements.txt; the build tests also need latexmk (they are skipped without it).
Run from the plugin folder with a Python that has them, for example a workspace venv:
    <workspace>/.venv/Scripts/python -m unittest discover tests
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
HAVE_PACKAGES = all(importlib.util.find_spec(m) for m in ("yaml", "pypdf", "pdfminer"))
HAVE_TEX = shutil.which("latexmk") is not None


def tool(name: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOLS / name), *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def make_workspace(tmp: Path, persona: bool = True) -> Path:
    ws = tmp / "ws"
    (ws / "docs").mkdir(parents=True)
    if persona:
        shutil.copyfile(ROOT / "examples" / "persona" / "jhs.yaml", ws / "jhs.yaml")
        shutil.copyfile(ROOT / "examples" / "persona" / "docs" / "Evidence_Ledger.md", ws / "docs" / "Evidence_Ledger.md")
    else:
        shutil.copyfile(ROOT / "templates" / "workspace" / "jhs.yaml", ws / "jhs.yaml")
        shutil.copyfile(ROOT / "templates" / "workspace" / "docs" / "Evidence_Ledger.md",
                        ws / "docs" / "Evidence_Ledger.md")
    return ws


@unittest.skipUnless(HAVE_PACKAGES, "needs the packages in requirements.txt")
class Preflight(unittest.TestCase):
    def test_blank_workspace_names_what_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_workspace(Path(tmp), persona=False)
            r = tool("preflight.py", "score-job", cwd=ws)
        self.assertEqual(r.returncode, 1)
        self.assertIn("RESULT: STOP", r.stdout)
        self.assertIn("jhs.yaml `candidate.name` is empty", r.stdout)
        self.assertIn("[skills-gaps] still holds setup placeholders", r.stdout)
        self.assertIn("/job-hunt-studio:setup", r.stdout)

    def test_no_jhs_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = tool("preflight.py", "audit-claims", cwd=Path(tmp))
        self.assertEqual(r.returncode, 1)
        self.assertIn("No jhs.yaml", r.stdout)

    def test_persona_can_score_but_not_tailor_without_an_approved_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_workspace(Path(tmp))
            git(ws, "init", "-q")
            score = tool("preflight.py", "score-job", cwd=ws)
            tailor = tool("preflight.py", "tailor-resume", cwd=ws)
        self.assertEqual(score.returncode, 0, score.stdout)
        self.assertIn("No approved resume yet", score.stdout)
        self.assertEqual(tailor.returncode, 1)
        self.assertIn("tailor-resume base", tailor.stdout)


@unittest.skipUnless(HAVE_PACKAGES and HAVE_TEX, "needs requirements.txt packages and latexmk")
class BuildAndApprove(unittest.TestCase):
    def test_templates_build_and_pass_the_checks(self):
        for layout in ("classic", "jakes"):
            with self.subTest(layout), tempfile.TemporaryDirectory() as tmp:
                ws = make_workspace(Path(tmp))
                tex = ws / "resumes" / "base" / "Resume.tex"
                tex.parent.mkdir(parents=True)
                shutil.copyfile(ROOT / "templates" / "resume" / layout / "Resume.tex", tex)
                built = tool("build_resume.py", str(tex), cwd=ws)
                self.assertEqual(built.returncode, 0, built.stdout)
                self.assertIn("Pages: 1", built.stdout)
                pdf = tex.parent / "build" / "Resume.pdf"
                self.assertTrue((tex.parent / "build" / "Alex_Rivera_Resume.pdf").is_file())
                ats = tool("ats_check.py", str(pdf), cwd=ws)
                self.assertEqual(ats.returncode, 0, ats.stdout)
                lint = tool("resume_lint.py", str(tex), str(pdf), cwd=ws)
                self.assertIn("1 FAIL", lint.stdout)  # the example marker, and only that
                self.assertIn("no example content", lint.stdout)
                tex.write_text("\n".join(l for l in tex.read_text(encoding="utf-8").splitlines()
                                         if "JHS-EXAMPLE-CONTENT" not in l), encoding="utf-8")
                tool("build_resume.py", str(tex), cwd=ws)
                lint = tool("resume_lint.py", str(tex), str(pdf), cwd=ws)
                self.assertEqual(lint.returncode, 0, lint.stdout)
                self.assertIn("RESULT: PASS (0 WARN)", lint.stdout)
                self.assertIn("FACTS: CLEAN", lint.stdout)

    def test_approve_refuses_example_content_then_tags_and_archives(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_workspace(Path(tmp))
            tex = ws / "resumes" / "base" / "Resume.tex"
            tex.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / "templates" / "resume" / "jakes" / "Resume.tex", tex)
            git(ws, "init", "-q")
            git(ws, "config", "user.name", "Test")
            git(ws, "config", "user.email", "test@example.com")
            (ws / ".gitignore").write_text("build/\n", encoding="utf-8")
            git(ws, "add", "-A")
            git(ws, "commit", "-q", "-m", "base")

            refused = tool("approve_resume.py", "first version", "90/100", cwd=ws)
            self.assertEqual(refused.returncode, 1)
            self.assertIn("example content", refused.stdout)

            tex.write_text("\n".join(l for l in tex.read_text(encoding="utf-8").splitlines()
                                     if "JHS-EXAMPLE-CONTENT" not in l), encoding="utf-8")
            dirty = tool("approve_resume.py", "first version", "90/100", cwd=ws)
            self.assertIn("uncommitted", dirty.stdout)
            git(ws, "commit", "-q", "-am", "marker removed")

            ok = tool("approve_resume.py", "first version", "90/100", cwd=ws)
            self.assertEqual(ok.returncode, 0, ok.stdout)
            self.assertIn("resume-approved-v1", git(ws, "tag", "-l").stdout)
            self.assertTrue((ws / "resumes" / "current" / "Alex_Rivera_Resume.pdf").is_file())
            archived = list((ws / "resumes" / "approved").glob("v1_*/Alex_Rivera_Resume_v1.pdf"))
            self.assertEqual(len(archived), 1)
            self.assertEqual(git(ws, "status", "--porcelain").stdout.strip(), "")

            again = tool("approve_resume.py", "nothing new", "90/100", cwd=ws)
            self.assertEqual(again.returncode, 1)
            self.assertIn("unchanged since resume-approved-v1", again.stdout)



class NoAutomatedLinkedIn(unittest.TestCase):
    def test_link_check_never_requests_linkedin(self):
        sys.path.insert(0, str(TOOLS))
        import urllib.request
        from unittest import mock

        import resume_lint

        with mock.patch.object(urllib.request, "urlopen", side_effect=AssertionError("network call")) as call:
            resume_lint.check_links(["https://www.linkedin.com/in/example-alex-rivera", "https://linkedin.com/in/x",
                                     "https://example.org/paper"])
        call.assert_not_called()


@unittest.skipUnless(HAVE_PACKAGES, "needs the packages in requirements.txt")
class FactCheckPaths(unittest.TestCase):
    def test_a_file_outside_the_workspace_uses_the_current_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = make_workspace(Path(tmp))
            outside = Path(tmp) / "elsewhere" / "note.md"
            outside.parent.mkdir()
            outside.write_text("I improved NDCG@10 by 3.1%.", encoding="utf-8")
            inside = tool("fact_check.py", str(outside), "--kind", "message", cwd=ws)
            nowhere = tool("fact_check.py", str(outside), "--kind", "message", cwd=outside.parent)
        self.assertEqual(inside.returncode, 0, inside.stderr)
        self.assertIn("FACTS: CLEAN", inside.stdout)
        self.assertEqual(nowhere.returncode, 1)
        self.assertIn("No jhs.yaml", nowhere.stdout)
        self.assertNotIn("Traceback", nowhere.stderr)


if __name__ == "__main__":
    unittest.main()
