---
name: audit-claims
description: Check a resume, cover letter, form answer, LinkedIn text or message against the user's Evidence Ledger before it goes out (numbers, dates, titles, hard lines, gap skills, never-print items, dashes, stock phrases) and report what to fix. Use before sending any written material, after a humanizer rewrite, or when the user asks to check, verify or fact-check a draft.
argument-hint: "[file to check] [resume | cover-letter | form | linkedin | message | interview]"
---

Check: "$ARGUMENTS". If no file is named, use the most recently changed text the user will send: a tailored copy (`applications/<folder>/<folder>.tex`), `form_answers.md`, `cover_letter.md`, or a file in `applications/drafts/`; never `TRACKER.md`, `timeline.md`, `analysis.md`, `posting.md`, `changes.md`, a `diff_vs_*` file or anything in `build/`. Say which file you chose. If the user pasted text, save it as `applications/drafts/<YYYY-MM-DD>_<kind>.md` and check that file.

The workspace Python is `.venv/Scripts/python` on Windows and `.venv/bin/python` on macOS and Linux; run every command from the workspace folder. This skill never edits the file it checks.

## 0. Check the inputs

Run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py audit-claims`. If `.venv` does not exist, say the workspace tools are not set up and point to `/job-hunt-studio:setup tools`. On `RESULT: STOP`, show the MISSING lines as printed and stop; mention WARN lines in one sentence.

## 1. Kind of text

The kind decides which hard lines apply (their `scope` column): `resume` (a `.tex`), `cover-letter`, `form` (application form answers), `linkedin`, `message` (outreach, emails), `interview` (prepared answers). Take it from the arguments, else from the file name; ask if unclear.

## 2. Code check

Run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/fact_check.py <file> --kind <kind>` (for a `.tex`, add `--pdf <its build PDF>` when one exists). Keep the full output; every WARN line must appear in your report.

## 3. Read it line by line

Read Ledger section 0 (`docs/Evidence_Ledger.md`), and the dated entries it cites when a line needs checking. Then check what code cannot:
- **Claims broader than their source:** a result for one subset stated as general, "led" for a team project, a status rounded up (prototype to "deployed"), a venue or paper status not exactly as `[publications]` allows.
- **Right number, wrong attachment:** a Ledger number tied to a different metric, baseline, dataset or period, or to a different version of a paper than the one the text names or links.
- **Skills** not backed in `[skills-claimed]` or `[skill-paraphrases]`, and anything from `[skills-gaps]`, in any wording.
- **`[never-print]` items** in any wording, and `[hard-lines]` rules whose `banned` pattern is empty (judge them by their rule).
- **Resumes:** the bullet rules in `${CLAUDE_PLUGIN_ROOT}/docs/RESUME_GUIDE.md` (verb first, result with a baseline, no pronouns, consistent final periods).
- **LinkedIn text:** the rules in `${CLAUDE_PLUGIN_ROOT}/docs/LINKEDIN_GUIDE.md` instead of the resume bullet rules.
- **LinkedIn and messages:** only facts that may be public; `[platform-facts]` for platform-only facts.
- **Voice:** text that reads as machine-written (stock phrases, forced triads, one-line closers). When `writing.humanizer` is true in `jhs.yaml`, suggest a humanizer pass and then a re-check, because rewrites can drop or bend numbers.

## 4. Report

A table: line or quote, issue, Ledger block (for example `[project:ranker-v2]`), suggested fix (exact new text, true to the Ledger). Include every open warning from step 2 with your verdict: fix it (give the fix), or acknowledge it (a true derived fact; give the `fact-ok` line to add, citing the Ledger block, as described in `RESUME_GUIDE.md`).

End with **PASS** (no issues and no open warnings) or **FIX FIRST** with the number of issues.
