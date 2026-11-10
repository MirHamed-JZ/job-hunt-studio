---
name: compile-resume
description: Quick build of a resume .tex file. Compiles it, runs the ATS parse check, the lint and the fact and voice check, and reports the page count. Use to preview a change; use review-resume for the readiness gate.
argument-hint: "[path to the .tex file]"
allowed-tools: Bash(latexmk *) Bash(.venv/Scripts/python *) Bash(.venv/bin/python *) Bash(git tag *) Bash(git diff *) Bash(git status *)
---

Build "$ARGUMENTS". If empty: the tailored copy of the most recently changed application folder (`applications/<folder>/<folder>.tex`; never a `diff_vs_*` file or anything in `build/`), else `resume.base_tex` from `jhs.yaml`; say which.

The workspace Python is `.venv/Scripts/python` on Windows and `.venv/bin/python` on macOS and Linux; run every command from the workspace folder. This skill never edits the source.

1. **Check the inputs:** `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py compile-resume --tex <file>`. If `.venv` does not exist, point to `/job-hunt-studio:setup tools`. On `RESULT: STOP`, show the MISSING lines as printed and stop.
2. **Build:** `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/build_resume.py <file>`. It builds into the `build/` folder next to the file (or `build/preview/` when a viewer locks the PDF; then ask the user to close it), copies the PDF to `build/<resume.output_name>`, and for an unapproved base also to `resumes/draft/` (a draft is never sent).
3. **Checks** on the built PDF (`build/<name>.pdf`, the path the build printed):
   - `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/ats_check.py <pdf>`
   - `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/resume_lint.py <file> <pdf>`
4. **Report:** built or the first LaTeX error with its line; pages; ATS PASS or the issues; lint FAIL items; the number of open fact and voice warnings. If the resume runs over `resume.pages`, say by about how much and suggest cuts from the cut order in `docs/Resume_Notes.md` (else the weakest bullet of the oldest job). For the readiness gate, point to `/job-hunt-studio:review-resume`.
