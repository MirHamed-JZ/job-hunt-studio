"""The install guards (hooks/guard.py): inside a workspace, Claude cannot change approved resumes, approved tags,
or push; outside one, nothing is blocked.

Run from the plugin folder: python -m unittest discover tests
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))

import guard  # noqa: E402

BASH = shutil.which("sh")


class GuardCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.ws = self.tmp / "ws"
        for sub in ("resumes/approved/v1_2026-01-12", "resumes/current", "resumes/base", "resumes/draft",
                    "applications/Acme_MLE_2026-03-20"):
            (self.ws / sub).mkdir(parents=True)
        shutil.copyfile(ROOT / "examples" / "persona" / "jhs.yaml", self.ws / "jhs.yaml")
        self.outside = self.tmp / "other-project"
        self.outside.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def bash(self, command: str, cwd: Path | None = None):
        return guard.decide({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd or self.ws)})

    def edit(self, rel: str, tool: str = "Edit"):
        field = "notebook_path" if tool == "NotebookEdit" else "file_path"
        return guard.decide({"tool_name": tool, "tool_input": {field: str(self.ws / rel)}, "cwd": str(self.ws)})


class Edits(GuardCase):
    def test_protected_folders_are_blocked_for_every_edit_tool(self):
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            for rel in ("resumes/current/Alex_Rivera_Resume.pdf", "resumes/approved/v1_2026-01-12/NOTES.md",
                        "resumes/approved/v2_2026-02-01/Resume.tex"):
                with self.subTest(tool=tool, path=rel):
                    self.assertIn("Job Hunt Studio guard", self.edit(rel, tool) or "")

    def test_other_workspace_files_are_allowed(self):
        for rel in ("resumes/base/Resume.tex", "resumes/draft/README.md", "applications/Acme_MLE_2026-03-20/x.tex",
                    "docs/Evidence_Ledger.md", "resumes/current_notes.md", "resumes/approved.md"):
            with self.subTest(path=rel):
                self.assertIsNone(self.edit(rel))

    def test_relative_and_dotted_paths(self):
        reason = guard.decide({"tool_name": "Write", "cwd": str(self.ws / "resumes" / "base"),
                               "tool_input": {"file_path": "../current/x.pdf"}})
        self.assertIsNotNone(reason)

    def test_outside_a_workspace_nothing_is_blocked(self):
        (self.outside / "resumes" / "current").mkdir(parents=True)
        reason = guard.decide({"tool_name": "Edit", "cwd": str(self.outside),
                               "tool_input": {"file_path": str(self.outside / "resumes" / "current" / "a.pdf")}})
        self.assertIsNone(reason)


class Commands(GuardCase):
    BLOCKED = [
        "git push", "git push origin main", "git -C . push", "git --no-pager push --tags", "git send-pack x",
        "bash -c 'git push'", "sh -c \"git add . && git push\"", "eval git push", "git commit -m x && git push",
        "git add .\ngit push", "true; git push", "(git push)", "echo $(git push)",
        "gh repo create my-search --private --source . --push",
        "git tag -d resume-approved-v1", "git tag --delete resume-approved-v1", "git tag -f resume-approved-v1 HEAD",
        "git tag -l 'resume-approved-v*' | xargs git tag -d", "git tag resume-approved-v2",
        "git tag -a resume-approved-v2 -m 'v2'", "git update-ref -d refs/tags/resume-approved-v1",
        "rm resumes/current/Alex_Rivera_Resume.pdf", "rm -rf resumes", "rm -rf resumes/*", "rm -rf .",
        "mv resumes/approved/v1_2026-01-12 old", "cp build/x.pdf resumes/current/", "cp -t resumes/current x.pdf",
        "echo x > resumes/current/notes.txt", "echo x >> resumes/approved/v1_2026-01-12/NOTES.md",
        "sed -i 's/a/b/' resumes/approved/v1_2026-01-12/NOTES.md", "touch resumes/current/x",
        "git rm -r resumes/approved", "git checkout HEAD~1 -- resumes/current/Alex_Rivera_Resume.pdf",
        "git restore resumes/current", "cd resumes && rm -rf current", "sudo rm -rf resumes/current",
        "Remove-Item -Recurse resumes/current", "Set-Content -Path resumes/current/x.txt -Value hi",
        # found by the end-to-end reviewer (phase 4): wrappers, PowerShell forms, other writers
        "timeout 60 git push", "winpty git push", "nice -n 5 git push", "stdbuf -oL git push",
        "powershell -Command git push", "pwsh -NoProfile -Command \"git push\"", "iex 'git push'",
        "Invoke-Expression 'git push'", "Start-Process git -ArgumentList push", "start git push",
        "git subtree push --prefix docs origin main", "gh repo create x --source . --push=true",
        "perl -pi -e 's/a/b/' resumes/approved/v1_2026-01-12/NOTES.md", "sed -Ei 's/a/b/' resumes/current/x",
        "sed --in-place=.bak 's/a/b/' resumes/current/x", "find resumes -name '*.pdf' -delete",
        "find resumes -name '*.pdf' | xargs rm", "latexmk -pdf -outdir=resumes/current resumes/base/Resume.tex",
        "dd if=build/x.pdf of=resumes/current/x.pdf", "Copy-Item -Destination resumes/current -Path build/x.pdf",
        "git reset --hard HEAD~1", "git tag -l 'resume-*' | xargs git tag -d", "git tag -d $(git tag -l)",
        "rm .git/refs/tags/resume-approved-v1", "rm -rf ..", "cd applications && rm -rf ../resumes",
        "python tools/build_resume.py resumes/approved/v1_2026-01-12/Resume.tex",
        # found by the final check: paths that are not literal, pipelines, more wrappers
        "echo x > \"$PWD/resumes/current/x.txt\"", "rm -rf resumes/{approved,current}",
        "rm $(ls resumes/current/*.pdf)", "D=resumes/current; rm -f $D/a.pdf", "touch resumes/current/.gitkeep",
        "mkdir resumes/approved/v9", "cd resumes/current && latexmk -pdf x.tex", "git checkout HEAD~1 -- resumes",
        "git restore --source=HEAD~1 .", "powershell -enc ZwBpAHQAIABwAHUAcwBoAA==", "powershell \"git push\"",
        "cmd //c \"git push\"", "bash -ec 'git push'", "flock /tmp/l git push", "watch git push",
        "script -qc 'git push' /dev/null", "bash <<< 'git push'", "echo 'git push' | bash",
        "git -c alias.pub=push pub origin main", "git rev-parse HEAD > .git/refs/tags/resume-approved-v1",
        "sed -i 's/a/b/' .git/packed-refs", "rm -rf .git", "sort -o resumes/current/README.md notes.txt",
        "cp -tresumes/current build/x.pdf", "rsync --remove-source-files resumes/current/a.pdf /tmp/",
        "python -c \"import os; os.remove('resumes/current/a.pdf')\"", "perl -e 'unlink \"resumes/current/a.pdf\"'",
        "git fetch . +refs/heads/main:refs/tags/resume-approved-v1",
    ]
    ALLOWED = [
        "git status", "git commit -m 'push the fix later'", "git log --oneline", "git add -A && git commit -m x",
        "git tag -l 'resume-approved-v*' --sort=-v:refname", "git tag", "git show resume-approved-v1:resumes/base/Resume.tex",
        "git diff resume-approved-v1 -- resumes/base/Resume.tex", "git tag -d my-own-tag", "git checkout main",
        "rm -rf build", "rm resumes/draft/x.pdf", "cp resumes/current/Alex_Rivera_Resume.pdf ~/Desktop/",
        "ls resumes/current", "cat resumes/approved/v1_2026-01-12/NOTES.md", "echo hi 2>&1 | tee log.txt",
        "python tools/approve_resume.py 'first version' '85/100 READY'", "latexmk -pdf resumes/base/Resume.tex",
        "git commit -F - <<'EOF'\nNotes\ngit push later\nEOF",
        "timeout 60 git status", "grep -n Rivera resumes/current/notes.txt", "pdfinfo resumes/current/Alex_Rivera_Resume.pdf",
        "pdftotext -layout resumes/current/Alex_Rivera_Resume.pdf -", "pdftoppm -png -r 70 resumes/current/a.pdf build/page",
        "python tools/ats_check.py resumes/current/Alex_Rivera_Resume.pdf", "sed -n 1,5p resumes/current/notes.txt",
        "find resumes -name '*.pdf'", "find build -name '*.aux' | xargs rm", "git reset --soft HEAD~1",
        "start resumes/current/Alex_Rivera_Resume.pdf", "Get-Content resumes/current/notes.txt",
        # found by the final check: setup and the plugin's own tools must pass
        "mkdir -p applications/leads resumes/base resumes/approved resumes/current resumes/draft",
        "python tools/visual_check.py build/visual resumes/current/Alex_Rivera_Resume.pdf",
        "python tools/approve_resume.py 'v2: replaces resumes/current/Alex_Rivera_Resume.pdf' '90/100 READY'",
        "git tag -n1 resume-approved-v1", "latexdiff resumes/approved/v1_2026-01-12/Resume.tex resumes/base/Resume.tex",
        "grep -c 'git push' docs/notes.md", "git restore --staged resumes/base/Resume.tex",
        "python -c \"from pypdf import PdfReader; print(len(PdfReader('resumes/current/a.pdf').pages))\"",
        "Copy-Item -Path resumes/current/a.pdf -Destination build/", "rm -rf ../other-project",
    ]

    def test_blocked_in_a_workspace(self):
        for command in self.BLOCKED:
            with self.subTest(command=command):
                self.assertIsNotNone(self.bash(command), command)

    def test_allowed_in_a_workspace(self):
        for command in self.ALLOWED:
            with self.subTest(command=command):
                self.assertIsNone(self.bash(command), command)

    def test_other_projects_are_not_touched(self):
        for command in ("git push", "git tag -d resume-approved-v1", "rm -rf resumes", "cd .. && git push"):
            with self.subTest(command=command):
                self.assertIsNone(self.bash(command, cwd=self.outside))

    def test_entering_a_workspace_counts(self):
        self.assertIsNotNone(self.bash(f"cd '{self.ws.as_posix()}' && git push", cwd=self.outside))
        self.assertIsNotNone(self.bash(f"git -C '{self.ws.as_posix()}' push", cwd=self.outside))
        self.assertIsNotNone(self.bash(f"rm -rf '{(self.ws / 'resumes' / 'current').as_posix()}'", cwd=self.outside))

    def test_custom_tag_prefix(self):
        text = (self.ws / "jhs.yaml").read_text(encoding="utf-8").replace("tag_prefix: resume-approved-v",
                                                                         "tag_prefix: cv-v")
        (self.ws / "jhs.yaml").write_text(text, encoding="utf-8")
        self.assertIsNotNone(self.bash("git tag -d cv-v3"))
        self.assertIsNone(self.bash("git tag -d resume-approved-v1"))

    def test_windows_paths(self):
        self.assertIsNotNone(self.bash(r"del resumes\current\x.pdf"))
        self.assertIsNotNone(self.bash(f'rm "{self.ws}\\resumes\\current\\x.pdf"'))

    @unittest.skipUnless(sys.platform == "win32", "Git Bash drive paths exist only on Windows")
    def test_git_bash_drive_paths(self):
        drive, rest = self.ws.as_posix().split(":", 1)
        msys = f"/{drive.lower()}{rest}"
        for command in (f"rm -rf {msys}/resumes/current", f"echo hello > {msys}/resumes/current/msys.txt",
                        f"cp x.pdf {msys}/resumes/current/", f"cd {msys} && git push",
                        f"rm '//?/{self.ws.as_posix()}/resumes/current/x.pdf'"):
            with self.subTest(command=command):
                self.assertIsNotNone(self.bash(command, cwd=self.outside), command)


class HookFile(unittest.TestCase):
    def test_hooks_json_runs_the_launcher_on_edits_and_commands(self):
        spec = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        entry = spec["hooks"]["PreToolUse"][0]
        self.assertEqual(set(entry["matcher"].split("|")), {"Edit", "Write", "MultiEdit", "NotebookEdit", "Bash",
                                                             "PowerShell"})
        command = entry["hooks"][0]["command"]
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}/hooks/run_guard.sh"', command)
        self.assertTrue((ROOT / "hooks" / "run_guard.sh").is_file())

    def test_launcher_has_unix_line_endings(self):
        self.assertNotIn(b"\r\n", (ROOT / "hooks" / "run_guard.sh").read_bytes())

    @unittest.skipUnless(BASH, "needs sh (Git Bash on Windows)")
    def test_launcher_blocks_with_exit_code_2_and_a_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp).resolve()
            shutil.copyfile(ROOT / "examples" / "persona" / "jhs.yaml", ws / "jhs.yaml")

            def run(command: str) -> subprocess.CompletedProcess:
                event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(ws)}
                return subprocess.run([BASH, str(ROOT / "hooks" / "run_guard.sh")], input=json.dumps(event),
                                      capture_output=True, text=True, encoding="utf-8",
                                      env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(ws)})
            blocked, allowed = run("git push"), run("git status")
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        self.assertIn("pushing is blocked", blocked.stderr)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)

    def test_bad_input_never_blocks(self):
        r = subprocess.run([sys.executable, str(ROOT / "hooks" / "guard.py")], input="not json", capture_output=True,
                           text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
