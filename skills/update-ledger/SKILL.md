---
name: update-ledger
description: Record new or corrected facts in the user's Evidence Ledger, with their source and date, keeping the old version as history (marked SUPERSEDED, never deleted). Use when the user shares new work, a result, a status change (a paper accepted, a project in production), a new skill or hard line, or a correction to a fact.
argument-hint: "[the new fact in plain words, with its source]"
---

Record in the Ledger: "$ARGUMENTS" (if empty, ask what changed).

The Ledger is `docs/Evidence_Ledger.md` in the workspace; its format and rules are in `${CLAUDE_PLUGIN_ROOT}/docs/LEDGER_FORMAT.md` (read it once if you have not). Section 0 holds the current facts in blocks named by anchors such as `[roles]` or `[project:ranker-v2]`; dated entries below it hold the history. The workspace Python is `.venv/Scripts/python` on Windows and `.venv/bin/python` on macOS and Linux; run every command from the workspace folder.

## 0. Check the inputs

Run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py update-ledger`. If `.venv` does not exist, say the workspace tools are not set up and point to `/job-hunt-studio:setup tools`. On `RESULT: STOP`, show the MISSING lines as printed (each names its fix) and stop.

## 1. Understand the fact

Ask at most three questions, only where the fact is ambiguous or could overclaim. Press on what an interviewer would press on:
- **Numbers:** the exact value, its baseline, the test set or period.
- **Status:** prototype, offline evaluation, handed off, or in production; never round up.
- **Their part versus the team's:** "built the evaluation" is not "led the project".
- **Venue and authorship:** the venue exactly as it may be printed; the author order.
- **Source:** an email, a paper link, a document, or "said by the user on <today>".

Anything still unsure goes to `[open-items]`, not into a block. Never write government ID, bank or card numbers, passwords, or anything the user did not say.

## 2. Show the change, then write it

Show the exact lines you will write (block, old text, new text, source). Write them once the user confirms; the edit permission prompt for `docs/` counts as their confirmation only if they saw these lines first.

1. **Dated entry.** Add `## YYYY-MM-DD: <what changed>` (today) directly below the `---` that closes section 0, so the newest entry comes first. If an entry for today exists, add to it. One line per fact: `- [block]: <fact> (source: <source>)`.
2. **Section 0.** Put the current value in its block, and update the date in `## 0. Current facts (as of YYYY-MM-DD)` and any `Last updated:` line.
3. **History.** When a fact replaces an older one, find the dated entry that recorded the old value and append ` SUPERSEDED YYYY-MM-DD (see the YYYY-MM-DD entry)` to that line. If the old value appears only in section 0, first record it in the new entry as `- [block] was: <old text>. SUPERSEDED YYYY-MM-DD.` Never delete a line.

Special cases:
- **A new skill** goes to `[skills-gaps]` (status `gap`, or `learning: <project>`). It moves to `[skills-claimed]` only when `interview/CLAIM_GATE.md` has a `pass` row for it from `/job-hunt-studio:interview-drill`; the row's example goes in the "Example you would give" column, and a project the drill relied on gets its own `[project:...]` block if it has none. Without a pass row, keep it a gap and suggest the drill (the user types `/job-hunt-studio:interview-drill <skill>`).
- **A new hard line:** write the `[hard-lines]` row (format in `LEDGER_FORMAT.md`). Write the `banned` pattern yourself with word boundaries (`\b`), test it with Python on two sentences that should be caught and two true sentences that should not, show the results in plain words, and adjust until both pass.
- **A new never-print item:** add it to `[never-print]` in the user's words.
- **Contact details, target roles or locations** are settings, not facts: they go in `jhs.yaml` (ask before editing it).

## 3. Check and follow through

1. Run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/ledger.py check docs/Evidence_Ledger.md`. On a PROBLEM line, fix the Ledger and run it again until `RESULT: OK`.
2. If the change affects text already in use (the approved resume, a tailored copy waiting to be sent, `HANDOFF.md`), say which, and what would update it: a base change becomes a new resume version (`/job-hunt-studio:review-resume`, then approval), never an edit to an approved one.
3. Update `HANDOFF.md` section 0 if the change affects it.

## 4. Report

In a few lines: what was written where, what was marked SUPERSEDED, what waits in `[open-items]`, and anything that needs the user's confirmation.
