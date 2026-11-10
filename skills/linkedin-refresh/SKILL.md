---
name: linkedin-refresh
description: Write paste-ready LinkedIn profile text (headline, About, experience, education, publications, skills) from the user's Evidence Ledger, compared with their current profile, checked against the Ledger and their hard lines; the user pastes it in by hand. Use when the user wants to write, update or review their LinkedIn profile.
argument-hint: "[headline | about | experience | skills | all] | updated"
---

LinkedIn text for: "$ARGUMENTS" (default `all`; `updated` when the user says they pasted it in, step 6).

Rules for the text: `${CLAUDE_PLUGIN_ROOT}/docs/LINKEDIN_GUIDE.md` (read it first). Facts: Ledger section 0 only. Files in the workspace: `linkedin/LINKEDIN_<YYYY-MM-DD>.md` (the draft), `linkedin/PROFILE.md` (the text that is live), and the profile PDF the user saved, if any.

The workspace Python is `.venv/Scripts/python` on Windows and `.venv/bin/python` on macOS and Linux; run every command from the workspace folder. **STOP** means end the turn and wait for the user.

## 0. Check the inputs

Run `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py linkedin-refresh`. If `.venv` does not exist, point to `/job-hunt-studio:setup tools`. On `RESULT: STOP`, show the MISSING lines as printed and stop; mention WARN lines in one sentence.

## 1. Read

- Ledger section 0: `[positioning]`, `[identity]`, `[roles]`, the `[project:...]` blocks, `[publications]`, `[summary]`, `[skills-claimed]`, `[skill-paraphrases]`, `[hard-lines]` (scope `linkedin`, `public` or `all`), `[never-print]`, `[platform-facts]`.
- The latest approved resume, for wording: `git show <tag>:<resume.base_tex>` (the newest tag starting with `resume.tag_prefix`). LinkedIn must match it: titles, dates, venues, statuses.
- The current profile: `linkedin/PROFILE.md`, else the newest PDF in `linkedin/` (read it with `pdftotext -layout <file> -` when Poppler is installed, else `<workspace Python> -c "import pypdf,sys; print('\n'.join(p.extract_text() or '' for p in pypdf.PdfReader(sys.argv[1]).pages))" <file>`). With neither, ask once for the PDF (on their profile: **More** or **Resources**, then **Save to PDF**, then put it in `linkedin/`) or a paste; save a paste as `linkedin/PROFILE.md` under the line `Live since: before <YYYY-MM-DD> (pasted, not yet checked against the Ledger)`. If they prefer neither, write from the Ledger alone.
- Search terms: the pack's `keywords.yaml` (`${CLAUDE_PLUGIN_ROOT}/packs/<pack>/`) and the `posting.md` files of recent applications. A term goes into the text only when the Ledger supports it.

## 2. Compare, and ask before changing a fact

List what the current profile says that the Ledger does not, or says differently: a title, a date, a number, a role, a status, a skill. For each, ask whether it is true and what its source is:
- true, and fine everywhere: record it with `/job-hunt-studio:update-ledger` before using it;
- true, but for LinkedIn only (an older role, a volunteer position, a course): `update-ledger` into `[platform-facts]`;
- not true, or no longer wanted: the draft leaves it out, and the hand-over says so.

Also ask, once, which work to lead with when the Ledger leaves it open (the project that best matches `target.titles`). If there is nothing to ask, go on; otherwise **STOP** and wait for the answers. Never change or add a fact without the user's answer.

## 3. Draft

Write `linkedin/LINKEDIN_<YYYY-MM-DD>.md` with one `## <Field>` heading per field, in profile order: Headline, About, Experience (one `### <Title>, <Organization>` per role), Education, Publications, Skills (with the five Top skills), Languages (from `[identity]`), Volunteering, Featured; leave out a field the Ledger has nothing for; only the fields asked for when "$ARGUMENTS" names some. Under each heading, the paste-ready text and nothing else (notes go in the hand-over, not the file); headings are not fact-checked, the text is.

Follow the guide. Facts only from Ledger section 0, within the hard lines; nothing from `[skills-gaps]` or `[never-print]`; `[platform-facts]` only as they allow; the same titles, dates, venues and statuses as the resume. Skills: `[skills-claimed]` and approved paraphrases, plus true extras the user confirms they could discuss with an example. No em dashes, en dashes or double hyphens.

## 4. Writing pass

1. If `writing.humanizer` in `jhs.yaml` is true and the humanizer skill is available, run it on every prose block (About, the Experience and Publications descriptions, Volunteering); if it is true but missing, say once that it is enabled but not installed (`/job-hunt-studio:setup options`).
2. Run `/job-hunt-studio:audit-claims linkedin/LINKEDIN_<YYYY-MM-DD>.md linkedin` (a rewrite can drop or bend a number) and fix everything it flags.
3. Count characters with a short Python snippet: Headline 220, About 2,600 (aim for 900 to 1,600), each Experience description 2,000; trim anything over, and put the counts in the headings (`## Headline (148 characters)`).

Show nothing before all three are done.

## 5. Hand over (STOP)

In chat, short: the headline, the first two lines of About (what shows before "see more"), the path of the file, and what changes against the current profile (one line per field, including anything removed in step 2). Then the steps before pasting: turn off **Share profile updates**, keep Open to Work visible to recruiters only, and paste by hand in one sitting. Commit locally: `git add linkedin` then `git commit -m "LinkedIn: draft <YYYY-MM-DD>"`. **STOP:** "Paste what you want, then tell me (with any edits you made) and I'll record it as your live profile."

## 6. After the user updates (`updated`)

Ask for the edits they made, or a freshly saved profile PDF. If an edit adds or changes a fact, record it with `/job-hunt-studio:update-ledger` first. Then replace `linkedin/PROFILE.md` with the text as it is live, with `Live since: <YYYY-MM-DD>` at the top, update `HANDOFF.md` section 0, and commit locally: `LinkedIn: profile updated`.

## Never

- Never sign in to, fetch or automate anything on LinkedIn; the user pastes every change themselves (LinkedIn User Agreement, section 8.2).
- Never post or publish anything for the user.
- Never put a claim on LinkedIn that the Ledger and the resume do not support.
