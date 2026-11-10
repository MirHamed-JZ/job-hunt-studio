---
name: review-resume
description: Readiness gate for a resume before it is approved or sent. Builds it, runs the ATS parse check, the lint, the link check, the fact and voice check against the Evidence Ledger and the visual check, then has the independent cv-reviewer agent score it against the review rubric. Use after every resume change, before saying a resume is done, or when the user asks whether a resume is ready.
argument-hint: "[path to the .tex, default: the base resume]"
---

Review "$ARGUMENTS" (if empty: `resume.base_tex` from `jhs.yaml`). For a tailored copy under `applications/`, also use that folder's `analysis.md`, so the reviewer judges fit to the posting.

The workspace Python is `.venv/Scripts/python` on Windows and `.venv/bin/python` on macOS and Linux; run every command from the workspace folder. Rubric: `${CLAUDE_PLUGIN_ROOT}/docs/REVIEW_RUBRIC.md`. House rules: `${CLAUDE_PLUGIN_ROOT}/docs/RESUME_GUIDE.md`.

## 0. Check the inputs

Run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py review-resume --tex <file>`. If `.venv` does not exist, point to `/job-hunt-studio:setup tools`. On `RESULT: STOP`, show the MISSING lines as printed and stop. A WARN about `pdftoppm` means the visual check is skipped: say so, and tell the reviewer it has no images.

## 1. Build

`<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/build_resume.py <file>`. It prints the built PDF, the file to send (`build/<resume.output_name>`) and, for an unapproved base, the draft copy. If it built into `build/preview/` because a viewer locks the PDF, use that PDF and ask the user to close the viewer.

## 2. Automated checks (keep the full output)

- `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/ats_check.py <pdf>`
- `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/resume_lint.py <file> <pdf> --links` (the second part of its output is the fact and voice check)
- `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/visual_check.py <tex folder>/build/visual <pdf> ${CLAUDE_PLUGIN_ROOT}/tools/assets/reference_jakes_resume.pdf` (page image, blurred squint image, density numbers, a comparison sheet)

## 3. Independent review

Start the reviewer agent (Agent tool, `subagent_type: "job-hunt-studio:cv-reviewer"`). If that agent type is not available, use `general-purpose` and give it the body of `${CLAUDE_PLUGIN_ROOT}/agents/cv-reviewer.md` as its instructions. Give it: the workspace folder; the `.tex` and PDF paths; the page, squint and comparison images from `<tex folder>/build/visual/`; the full output of step 2; the absolute paths of `REVIEW_RUBRIC.md` and `RESUME_GUIDE.md` (above); the pack's `keywords.yaml` when `pack` is set (`${CLAUDE_PLUGIN_ROOT}/packs/<pack>/keywords.yaml`); `review.ready_threshold`; and for a tailored copy, the folder's `analysis.md`. Do not give your own opinion of the resume; the point is a fresh read.

## 4. Verify before relaying

Check each FIX the reviewer proposes against the Ledger yourself; drop any that would overclaim (a gap skill, a number not in the Ledger, a status rounded up), and say that you dropped it.

## 5. Resolve the fact and voice warnings

Every open warning from the fact and voice check must be fixed or acknowledged before READY:
- **Wrong or unsupported text:** propose the fix (exact before and after).
- **True text the code cannot match** (a number derived from Ledger facts, such as years counted from `[roles]` dates or a count of `[publications]`): add a comment line next to it in the `.tex`, `% fact-ok: <the text> | <reason naming the Ledger block>`, and tell the user what you acknowledged.
- A `gap-skill`, `never-print`, `title`, `dash`, `phrase` or `example` warning is never acknowledged (the check ignores such lines): fix the text (reword a dash or stock phrase), or correct the Ledger with `/job-hunt-studio:update-ledger` if the Ledger is what is wrong. A `hard-line` warning is acknowledged only when the sentence is plainly true and keeps the rule's purpose (for example "evaluated offline, not deployed"); the reason must name the rule id (`% fact-ok: deployed | HL-ranker-status: says it was not deployed`), and you say so to the user explicitly.

Edits to the `.tex` that the user has not agreed to are proposals, not changes, except acknowledgement lines. After agreed edits or new acknowledgements, run this skill again; READY needs `FACTS: CLEAN` in the run that gives the verdict.

## 6. Verdict and report

**READY** only when the reviewer says READY, every gate passed (ATS PASS on both engines, lint with no FAIL, the page count right) and the fact check says `FACTS: CLEAN`. Report: the verdict and score, the gate results, the FIX items you agree with (exact before and after), the CONSIDER items, the warnings and how each was resolved. Save the report as `<tex folder>/build/review_<YYYY-MM-DD>.md` (not committed). For an unapproved base, write the verdict, the score and "waiting for approval" into `resumes/draft/README.md`.

## 7. When READY

- **The base:** give the user the PDF path and ask: "Approve as v<N>?" Approve only after their explicit OK; a request for edits is not approval. Then commit the base source (`git add <base .tex>` and `git commit -m "Resume v<N> source"`, if anything is uncommitted) and run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/approve_resume.py "<what changed>" "<score>/100 READY"`. It tags the version, archives it, puts the PDF in `resumes/current/` and commits locally. Then update the resume line in `HANDOFF.md` section 0.
- **A tailored copy:** set its `applications/TRACKER.md` row to `Ready to submit` with the base tag and the score. It is ready to send; the user submits.
