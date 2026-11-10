---
name: interview-drill
description: The check before a new skill goes on the user's resume or LinkedIn. Five hard questions about the user's own project with that skill decide whether they can discuss it the way an interviewer expects; the result is recorded in the claim gate. Not practice (that is mock-interview). Runs only when the user types it.
disable-model-invocation: true
argument-hint: "<skill name>"
---

Drill on the skill "$ARGUMENTS" (if empty, ask which skill).

The rule this enforces, from the workspace `CLAUDE.md`: a skill is claimed only if the user can discuss it for 2 to 3 minutes with a specific example from their own work. A pass is how a skill moves from Ledger `[skills-gaps]` to `[skills-claimed]`. This skill records the result in `interview/CLAIM_GATE.md` and never edits the Ledger, a resume or LinkedIn text. What the user sees: `${CLAUDE_PLUGIN_ROOT}/docs/INTERVIEWS.md`.

The workspace Python is `.venv/Scripts/python` on Windows and `.venv/bin/python` on macOS and Linux; run every command from the workspace folder. **STOP** means end the turn and wait for the user.

## 0. Check the inputs

Run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py interview-drill`. If `.venv` does not exist, point to `/job-hunt-studio:setup tools`. On `RESULT: STOP`, show the MISSING lines as printed and stop. If `interview/CLAIM_GATE.md` does not exist, copy it from `${CLAUDE_PLUGIN_ROOT}/templates/workspace/interview/CLAIM_GATE.md`.

## 1. Find the project

1. Find the skill in `[skills-gaps]`, by name or a close wording. If it is already in `[skills-claimed]`, say so; a drill then is only a refresher and changes nothing. If it is in neither, it is new: the drill can still run.
2. Find the project behind it: a `[project:...]` block that uses the skill, the project named in the gap's status (`learning: <project>`), or what the user points to (a repository, a folder of notes, a report). Read it: the README, the main code, the results, the notes. Work the user cannot share (an employer's internal project) is discussed at the level they could say in an interview.
3. **No project, no drill.** If nothing exists, say so and stop: the gate needs something the user built or did with the skill. Suggest one small project that would count, sized to a few evenings: what to build, what to measure, what to write down. Once it exists, `/job-hunt-studio:update-ledger` records it (the gap's status becomes `learning: <project>`), then the drill runs.
4. If the project has no `[project:...]` block, say that what the user tells you during the drill is not yet a Ledger fact; on a pass, `update-ledger` records the project with its source.
5. **Match the skill to the project.** If the project shows a narrower skill than the one named (fine-tuning a small embedding model is not "LLM fine-tuning"; a notebook is not "production MLOps"), say so now: the drill judges the narrower skill, and on a pass only that one moves; the wider one stays a gap.

Say in two lines what the drill covers and that grading comes at the end. **STOP** until the user is ready.

## 2. Five questions, one at a time

Ask as a skeptical senior interviewer would, with no hints and no teaching until the end. Each question gets one follow-up on a specific decision, failure or trade-off in the user's own project ("why X and not Y here", "what broke first", "how did you know it worked", "what changes at ten times the data"). Wait for each answer before going on. Cover:
1. What they built with the skill, and why the skill was the right tool.
2. A design decision and the alternative they rejected.
3. Something that failed or surprised them, and how they found it.
4. How they measured the result, and against what.
5. The depth expected of anyone who claims the skill: how it works underneath, and where it breaks.

## 3. Grade

Each answer passes when it gives a specific example from the user's own project and sound reasoning; it does not pass when it is generic, textbook only, wrong, or someone else's work. The drill passes with 4 or more of 5. Name each answer that did not pass and what was missing. An answer that breaks a `[hard-lines]` rule (scope `interview` or `all`) or contradicts the Ledger does not pass until restated truthfully; give the true wording.

## 4. Record

Append one row to `interview/CLAIM_GATE.md`: the date, the skill, the project (its Ledger block or link), the result (`pass 4/5`, or `not yet 2/5`), the answers that did not pass, and, on a pass, the example the user would give in an interview (one line, from their best answer). Commit locally: `git add interview` then `git commit -m "Claim gate: <skill> <result>"`.

## 5. Then

- **Pass:** propose (a) the `[skills-claimed]` row: the skill, the evidence (the project block or link), the example from step 4; (b) any other name for it the user wants approved for `[skill-paraphrases]`, never wider than the skill; (c) resume wording where it fits (the skills line, a bullet), true to the project. Then ask the user to run `/job-hunt-studio:update-ledger <skill> passed the drill on <date>, project <name>`, which moves it and records the project if needed. A resume change then becomes a new version through review and approval, like every change.
- **Not yet:** for each answer that did not pass, what to build, measure or study next, and `/job-hunt-studio:mock-interview <area>` for the theory. The skill stays in `[skills-gaps]`; drill again once that is done.

## Never

- Never edit the Ledger, a resume or LinkedIn text, and never move a skill yourself.
- Never pass on textbook knowledge alone: the gate is about the user's own work.
