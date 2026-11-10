---
name: tailor-resume
description: Build the user's base resume from their Evidence Ledger in the layout they chose (mode "base", including keeping their own layout), or tailor the approved resume to one job posting, using only Ledger facts and never editing before the user's OK on the proposed changes. Use when the user asks to build, create, rebuild or change their base resume (add, remove or reword a line), or to tailor, adapt or customize the resume for a role.
argument-hint: "base | [application folder or posting link]"
---

Run for: "$ARGUMENTS". `base` builds or revises the base resume; anything else is one application (normally this runs as `/job-hunt-studio:apply-job` stage 3).

The workspace Python is `.venv/Scripts/python` on Windows and `.venv/bin/python` on macOS and Linux; run every command from the workspace folder. House rules: `${CLAUDE_PLUGIN_ROOT}/docs/RESUME_GUIDE.md`. Facts: `docs/Evidence_Ledger.md` section 0. The user's own layout decisions: `docs/Resume_Notes.md`. **STOP** means end the turn and wait for the user.

# Mode `base`

## 0. Check the inputs

Run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py tailor-base`. If `.venv` does not exist, point to `/job-hunt-studio:setup tools`. On `RESULT: STOP`, show the MISSING lines as printed and stop.

If the base file (`resume.base_tex` in `jhs.yaml`) exists and an approved tag exists, this is a revision: ask what should change, edit the base, and continue at step 4. Decline a change that would add a `[skills-gaps]` skill (in any wording, "familiar with" or "exposure to" included), a `[never-print]` item, wording a `[hard-lines]` rule forbids, or a fact not in the Ledger: name the Ledger block it conflicts with and the way forward (a new fact goes through `/job-hunt-studio:update-ledger` with its source; a gap needs a project, then `/job-hunt-studio:interview-drill`). Do not offer to add it anyway; the review gate would not pass it. Every change to the base becomes the next version, approved only on the user's explicit OK.

## 1. Choose the layout

Read `resume.template` in `jhs.yaml`. If it is empty, show the choices from `${CLAUDE_PLUGIN_ROOT}/templates/resume/README.md` in a few lines: `classic`, `jakes`, or keeping the user's current layout (`own`), and record the answer in `jhs.yaml`.

- **`classic` or `jakes`:** copy `${CLAUDE_PLUGIN_ROOT}/templates/resume/<layout>/Resume.tex` to the `resume.base_tex` path (ask before overwriting a file).
- **`own`:** check the user's current resume against the seven criteria in that README first. With a PDF of it, run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/ats_check.py <their.pdf>` and `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/visual_check.py <scratch folder> <their.pdf> ${CLAUDE_PLUGIN_ROOT}/tools/assets/reference_jakes_resume.pdf`, look at the page image, and report each criterion as met or not, in plain words. If one is missed, explain why it matters and let the user choose: fix it in the LaTeX copy, or switch to `classic` or `jakes`.
  - **A LaTeX resume:** copy it to `resume.base_tex`. Add a comment line `% jhs-entry: \<command>{title}{organization}{dates}` naming the command the file uses for each job and what each argument holds (format in the README), so the fact check can compare entries with `[roles]`; ask the user if the file has no such command.
  - **A Word, Google Docs or PDF resume:** recreate its layout in LaTeX, starting from the closer of the two included layouts and matching the font, sizes, spacing, headings and order. Build it (step 4) and show the two side by side: render both with `pdftoppm -r 70 -png -singlefile <pdf> <name>` and look at both images. Adjust until the user confirms it looks right.

## 2. Fill it from the Ledger

Replace every fact in the file with the user's facts:
- **Header** from `jhs.yaml` `candidate`: name, city, email, phone only if set, LinkedIn, GitHub and website only if set. Header wording from `docs/Resume_Notes.md` if it has some. Set the PDF title and author (`pdftitle`, `pdfauthor`) to the user's name.
- **Summary:** `[summary]` word for word if it exists; otherwise draft one from `[positioning]` and the strongest results and show it for OK (or leave the section out if the user prefers).
- **Entries:** `[roles]` titles, organizations and dates exactly as printed there.
- **Bullets:** from the `[project:...]` blocks and roles, following `RESUME_GUIDE.md`; numbers copied, never recomputed; status exactly as the Ledger says.
- **Publications:** authors, title, venue and status exactly as `[publications]` allows.
- **Skills:** from `[skills-claimed]`, plus approved names from `[skill-paraphrases]`.
- Nothing from `[skills-gaps]` or `[never-print]`, and no wording a `[hard-lines]` rule forbids.

Delete the `JHS-EXAMPLE-CONTENT` line only when no example content is left: search the file for the example's name, employer and links (`Alex Rivera`, `Brightfield`, `example.com`, `example.org`) and make sure none remain that are not the user's own (compare with `jhs.yaml` `candidate` and `[roles]`).

## 3. Show the draft

Show the summary and the bullets you wrote, each with the Ledger block behind it, and ask for corrections (**STOP**). Apply them.

## 4. Build, fit, review

1. `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/build_resume.py <base .tex>`. If it runs over `resume.pages`, cut by the order in `docs/Resume_Notes.md`, else the weakest bullet of the oldest job, and say what was cut.
2. Record any layout decision the user made (header wording, cut order) in `docs/Resume_Notes.md`.
3. Commit the base source (`git add <base .tex> docs/Resume_Notes.md jhs.yaml`, then `git commit -m "Base resume draft"`), then run `/job-hunt-studio:review-resume <base .tex>` and follow it to READY. Approval happens there, only on the user's explicit OK after seeing the PDF.

# Mode: one application

## 0. Check the inputs

Run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py tailor-resume`. On `RESULT: STOP`, show the MISSING lines and stop (a tailored copy needs an approved resume; with none, the fix it names is `tailor-resume base`).

## 1. The folder and its score

Find the folder under `applications/` (a name or any unambiguous part of company or role), or create it from a posting link. If it has no `analysis.md`, run the `/job-hunt-studio:score-job` steps first (the posting guard included). If the verdict is Do Not Apply, say why in one line and stop; the user may overrule.

## 2. Proposal (STOP for OK)

If `timeline.md` does not record a "tailoring OK", write `## Proposed tailoring` at the end of `analysis.md` and show it as a numbered list. Each item: exact before and after text, the Ledger block behind it, **content** or **emphasis**, and the posting requirement it makes visible. Also list:
- what gets cut to stay within `resume.pages` (cut order from `docs/Resume_Notes.md`);
- posting keywords left off because they are gaps;
- "send the approved version unchanged" as an option when it already fits well;
- the expected resume fit after the changes.

Before showing it, test-build the items on a scratch copy of the approved source (step 3) and show only a set that fits; say which cut makes room. **STOP:** "Reply OK, or tell me what to change." A question or a partial answer is not an OK. When the user says OK, add `YYYY-MM-DD tailoring OK` to `timeline.md`.

## 3. The tailored copy

`TAG` = the first line of `git tag -l "<resume.tag_prefix>*" --sort=-v:refname`. Write `git show <TAG>:<resume.base_tex>` to `<folder>/<Company>_<Role>_<YYYY-MM-DD>.tex` (the folder's name). Never start from the working base file, which may hold an unapproved draft. Edit only this copy and apply exactly the approved items; an edit made for one posting never goes into the base, an approved version or a tag.

## 4. Build and review until READY

1. Write `<folder>/changes.md`: the tag it starts from, each change and why, posting keywords left off as gaps, open questions.
2. Run `/job-hunt-studio:review-resume <copy .tex>` with the folder's `analysis.md`. Apply the agreed FIX items that stay inside the approved scope. A FIX beyond it (a new claim, a different summary, a cut the user did not see) needs the user's OK first: **STOP** and ask. After three rounds without READY, stop and show the blocking items.
3. Change-tracked diff (optional): `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/resume_diff.py <copy .tex> --copy-to <folder>/diff_vs_v<N>.tex`. If it prints SKIPPED, say so; `changes.md` already records the changes.
4. In `applications/TRACKER.md` set the row to `Ready to submit` with the resume (`<TAG>`, tailored) and the review score, and add a line to `timeline.md`.

Report in chat: what changed (at most 5 lines), the review verdict and score, the PDF path (`<folder>/build/<resume.output_name>`), open questions.
