"""The guard against a matrix of real commands (tests/guard_cases.json), collected by the end-to-end reviewer:
commands the plugin's own skills, agent and docs run (all must pass), and ways to push or to change approved
resumes and tags (all must be blocked). Cases marked "gap" are known limits: history rewrites such as git revert.

Placeholders in the commands: {WS} the workspace (C:/... or /tmp/...), {WSB} its Git Bash form (/c/...), {WSC} its
/cygdrive form, {WSW} its backslash form, {PLUGIN}, {PLUGINB}, {PLUGINW} the plugin folder in the same forms, and
<<ENC:text>> a PowerShell -EncodedCommand payload.

Run from the plugin folder: python -m unittest discover tests
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))

import guard  # noqa: E402

CASES = json.loads((ROOT / "tests" / "guard_cases.json").read_text(encoding="utf-8"))
WINDOWS = sys.platform == "win32"
BACKSLASH = chr(92)


def forms(path: Path) -> dict:
    plain = path.as_posix()
    drive = re.match(r"^([A-Za-z]):(/.*)$", plain)
    return {"plain": plain,
            "bash": f"/{drive.group(1).lower()}{drive.group(2)}" if drive else plain,
            "cygdrive": f"/cygdrive/{drive.group(1).lower()}{drive.group(2)}" if drive else plain,
            "windows": plain.replace("/", BACKSLASH)}


class Matrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        ws = Path(cls._tmp.name).resolve() / "ws"
        for folder in ("resumes/approved/v1_2026-11-10", "resumes/current", "resumes/base/build", "resumes/draft",
                       "applications/Fernwick_MLEngineerRanking_2026-11-10/build", "applications/leads", "docs",
                       "interview/notes", "linkedin", ".git/refs/tags", ".git/refs/heads", "build"):
            (ws / folder).mkdir(parents=True)
        for name in ("jhs.yaml", "docs/Evidence_Ledger.md"):
            (ws / name).write_bytes((ROOT / "examples" / "persona" / name).read_bytes())
        for name in ("resumes/approved/v1_2026-11-10/Resume_v1.tex", "resumes/approved/v1_2026-11-10/NOTES.md",
                     "resumes/approved/v1_2026-11-10/Alex_Rivera_Resume_v1.pdf", "resumes/current/README.md",
                     "resumes/current/Alex_Rivera_Resume.pdf", "resumes/base/Resume.tex",
                     "resumes/base/build/Resume.pdf", "resumes/base/build/Alex_Rivera_Resume.pdf",
                     ".git/refs/tags/resume-approved-v1", ".git/packed-refs", ".git/HEAD",
                     "applications/Fernwick_MLEngineerRanking_2026-11-10/Fernwick_MLEngineerRanking_2026-11-10.tex"):
            (ws / name).write_text("x", encoding="utf-8")
        cls.ws = ws
        w, p = forms(ws), forms(ROOT)
        cls.subs = {"{WS}": w["plain"], "{WSB}": w["bash"], "{WSC}": w["cygdrive"], "{WSW}": w["windows"],
                    "{PLUGIN}": p["plain"], "{PLUGINB}": p["bash"], "{PLUGINW}": p["windows"]}
        cls._env = os.environ.get("CLAUDE_PROJECT_DIR")
        os.environ["CLAUDE_PROJECT_DIR"] = str(ws)

    @classmethod
    def tearDownClass(cls):
        if cls._env is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = cls._env
        cls._tmp.cleanup()

    def ask(self, tool: str, command: str):
        for mark, value in self.subs.items():
            command = command.replace(mark, value)
        command = re.sub(r"<<ENC:(.*?)>>", lambda m: base64.b64encode(m.group(1).encode("utf-16-le")).decode(),
                         command, flags=re.S)
        if tool in ("Write", "Edit", "MultiEdit"):
            tool_input = {"file_path": command}
        elif tool == "NotebookEdit":
            tool_input = {"notebook_path": command}
        else:
            tool_input = {"command": command}
        return guard.decide({"tool_name": tool, "tool_input": tool_input, "cwd": str(self.ws)})

    def run_cases(self, expect: str):
        wrong = []
        for want, tool, command in CASES:
            if want != expect:
                continue
            if not WINDOWS and ("{WSW}" in command or "{WSB}" in command or "{WSC}" in command
                                or "{PLUGINW}" in command or tool == "PowerShell" or BACKSLASH in command):
                continue  # drive letters and backslash paths exist only on Windows
            reason = self.ask(tool, command)
            if (reason is None) != (expect == "allow"):
                wrong.append(f"[{tool}] {command}" + (f"  -> {reason[:90]}" if reason else ""))
        return wrong

    def test_the_plugins_own_commands_pass(self):
        wrong = self.run_cases("allow")
        self.assertEqual(wrong, [], f"{len(wrong)} blocked but should pass:\n" + "\n".join(wrong[:40]))

    def test_pushes_and_changes_to_approved_files_and_tags_are_blocked(self):
        wrong = self.run_cases("block")
        self.assertEqual(wrong, [], f"{len(wrong)} not blocked:\n" + "\n".join(wrong[:40]))

    def test_the_matrix_is_not_empty(self):
        counts = {k: sum(1 for c in CASES if c[0] == k) for k in ("allow", "block", "gap")}
        self.assertGreater(counts["allow"], 200)
        self.assertGreater(counts["block"], 200)


if __name__ == "__main__":
    unittest.main()
