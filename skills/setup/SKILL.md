---
name: setup
description: Create a private Job Hunt Studio workspace for one job seeker. Interviews them, drafts their Evidence Ledger from their resume and confirms every fact, writes jhs.yaml settings, offers the options (humanizer, JobSpy, resume template), copies the workspace files and checks the tools. Use when someone wants to set up or start Job Hunt Studio, or a skill reports that jhs.yaml or the Ledger is missing or not set up. Resumes an unfinished setup; with a section name, redoes only that part; `example` makes a demo workspace for the fictional example candidate.
argument-hint: "[profile | search | ledger | hard-lines | skills | options | files | tools | example]"
---

Set up a Job Hunt Studio workspace in the current folder. Section to redo, if any: "$ARGUMENTS".

The workspace is the job seeker's own private folder; the plugin supplies logic and templates only. Plugin files: `${CLAUDE_PLUGIN_ROOT}`. Read `${CLAUDE_PLUGIN_ROOT}/docs/LEDGER_FORMAT.md` before step 4. A filled example: `${CLAUDE_PLUGIN_ROOT}/examples/persona/`. The user guide this skill follows: `${CLAUDE_PLUGIN_ROOT}/docs/GETTING_STARTED.md`.

Talk to the user as "you". Ask one topic at a time, give examples, and never write a fact about them they have not confirmed. Run commands yourself when you can; ask before installing anything.

## Steps and progress

| Step | Section name | What |
|---|---|---|
| 1 | | Check the folder |
| 2 | | Gather documents |
| 3 | `profile`, `search` | Settings in `jhs.yaml` (`search` redoes only the targets and location tiers) |
| 4 | `ledger` | Draft and confirm the Ledger |
| 5 | `hard-lines` | Hard lines and never-print items |
| 6 | `skills` | Claimed skills and gaps |
| 7 | `options` | Humanizer, JobSpy, resume template |
| 8 | `files` | Workspace files |
| 9 | `tools` | Venv, packages, tool check |
| 10 | | Commit and finish |

After each step, add its number to `setup.done` in `jhs.yaml` (once the file exists) and update the `Setup status:` line in the Ledger. At the start:
- **Section name given:** do that step only (it may run again on a finished setup).
- **`jhs.yaml` exists and `setup.done` lacks a step:** say which steps are done and offer to resume at the first missing one.
- **Setup complete and no section given:** say so, and list the section names.
- **`example`:** make a demo workspace instead (next section).

## Demo workspace (`example`)

For trying the plugin before entering anything personal. Run step 1 (the folder must be empty or hold only a previous demo), then:
1. Copy `${CLAUDE_PLUGIN_ROOT}/examples/persona/jhs.yaml` to `jhs.yaml` and `${CLAUDE_PLUGIN_ROOT}/examples/persona/docs/Evidence_Ledger.md` to `docs/Evidence_Ledger.md`. Change nothing in them: every fact is the fictional Alex Rivera's.
2. Run steps 8, 9 and 10 with the example's answers (layout `jakes`, no humanizer, no JobSpy), without asking the interview questions; commit as `Job Hunt Studio demo workspace (fictional example)`.
3. Say plainly: this is a demo for a fictional person; never put real data in it; for a real search, make a new empty folder and run `/job-hunt-studio:setup` there. Then suggest the demo steps from the README: `/job-hunt-studio:tailor-resume base`, `/job-hunt-studio:review-resume`, a fictional posting pasted into `/job-hunt-studio:apply-job`, and `/job-hunt-studio:mock-interview learning to rank`.

## 1. Check the folder

- Inside the plugin (`${CLAUDE_PLUGIN_ROOT}` or below): stop; the workspace must be a separate folder.
- Run `git rev-parse --show-toplevel`. If it prints a folder other than this one, this folder sits inside another git repository (a home folder, a synced or shared repo), and personal data could end up there. Stop and suggest a folder outside it; continue only if the user insists, and then create a separate repository here in step 10.
- If this folder is a git repository, run `git remote -v`. Any remote means the data could be pushed somewhere; warn that the workspace must stay private and ask before continuing.
- If the folder holds unrelated files, ask before adding the workspace beside them.

Explain in three lines: a short interview (about 30 to 45 minutes), a draft Ledger they confirm block by block, then settings and tools. They can stop any time and continue later by running setup again.

## 2. Gather documents

Show the checklist from section 1 of `GETTING_STARTED.md` in short form:
- **Strongly recommended:** their current resume (PDF or `.tex`; for Word, save as PDF or paste the text).
- **Recommended:** their LinkedIn profile as a PDF (on their profile: **More** or **Resources**, then **Save to PDF**); links to papers, a portfolio or GitHub; exact numbers they are proud of, with what each was compared against.
- **Optional:** their LinkedIn connections export, for outreach (steps in the guide); a LaTeX resume they want to keep.
- **Do not provide:** passwords, or confidential employer documents.

Ask them to drop the files in this folder (or give paths) and say when ready; offer to start from memory if they have nothing. Read each file they give.

## 3. Profile and settings (`jhs.yaml`)

Copy `${CLAUDE_PLUGIN_ROOT}/templates/workspace/jhs.yaml` to `./jhs.yaml` and fill it with the user, a few keys at a time:
- `candidate`: name as printed, email, phone (empty keeps it off public pages), city, LinkedIn, GitHub, website, schools, past employers. Work authorization only if they want form answers to use it; it is never printed. Contact details live here only, not in the Ledger.
- `target`: the titles to search for and to exclude, seniority levels, and the most years of experience a posting may ask for.
- `search.tiers`: where they want to work, best first (home city, remote with the regions a remote job must accept, other cities). Write the place patterns yourself and show them in plain words ("Lyon or Villeurbanne"). A tier with `remote_ok: true` takes remote postings whose location names one of its `remote_regions`; leave its `location_regex` empty (how tiers match: `${CLAUDE_PLUGIN_ROOT}/docs/JOB_SEARCH.md`).
- `pack`: offer the packs in `${CLAUDE_PLUGIN_ROOT}/packs/` (folders with a `README.md`), saying what each includes: keywords for job search and scoring, interview topics for practice; otherwise set `none` (general questions, no keyword list).
- `resume.output_name`: suggest `First_Last_Resume.pdf`.

Leave the watchlist empty; `/job-hunt-studio:find-jobs add <company>` fills it after setup (ask which companies they want to watch, and note them for step 10).

## 4. Draft and confirm the Ledger

Copy `${CLAUDE_PLUGIN_ROOT}/templates/workspace/docs/Evidence_Ledger.md` to `docs/Evidence_Ledger.md`, replace `{{candidate.name}}` and `{{date}}` (today, YYYY-MM-DD), then fill section 0 from the documents, one block at a time: `[positioning]`, `[identity]`, `[roles]`, one `[project:<name>]` block per project, `[publications]`, `[summary]` if they have an approved one.

For every block, show the draft, mark anything you inferred rather than read, and ask them to confirm or correct it. Press on what an interviewer would press on:
- **Numbers:** the exact value, its baseline, the test set or period ("cut report time from 3 hours to 20 minutes for the monthly close", not "made reporting faster").
- **Status:** prototype, offline evaluation, handed off, or in production; never round up.
- **Their part versus the team's:** "built the evaluation" is not "led the project".
- **Venue and authorship:** the venue exactly as it may be printed, authors in order.

Write only confirmed facts, each with its source ("resume of 2025-06", "paper on arXiv", "confirmed by you on <date>"). Anything unsure goes to Open items. Replace each placeholder you fill; leave untouched blocks with their placeholders so skills know they are pending.

## 5. Hard lines

Explain: hard lines are claims they must never make, or only in exact words; every skill checks them. Ask, with examples from their own Ledger:
- Anything never deployed, shipped or used by real users?
- Team work where "led" would overstate their role?
- A paper whose venue or status must be named exactly (workshop versus main conference, under review versus accepted)?
- Confidential names or details (internal codenames, unreleased results)?
- Claims they used before and have retired?

Write each as a row of the `[hard-lines]` table (format in `LEDGER_FORMAT.md`). Write the search pattern yourself with word boundaries (`\b`), test it with Python on two sentences that should be caught and two true sentences that should not, show the user the results in plain words, and adjust until both pass. Then ask for `[never-print]` items. If they have none, write "None." in the block, so it no longer counts as pending.

## 6. Skills

For each skill they want on a resume, ask for the project or role behind it and the example they would give in a 2 to 3 minute interview answer. With an example: `[skills-claimed]` with its evidence. Without: `[skills-gaps]` with status `gap` (or `learning: <project>`), written as the bare term with any qualifier in parentheses ("A/B testing (online)", not "online A/B testing") so the fact check catches every mention; it stays off every document until a project exists and `/job-hunt-studio:interview-drill` passes. Be kind and firm: this rule is what makes everything else trustworthy. Record approved other names in `[skill-paraphrases]`.

## 7. Options

Ask each, with its trade-off, and record the answer in `jhs.yaml`:
1. **Humanizer** (recommended): a third-party MIT skill, `blader/humanizer`, that rewrites text that reads as AI-written. If yes, run `claude plugin marketplace add blader/humanizer` and `claude plugin install humanizer@humanizer` (with their OK), confirm with `claude plugin list`, set `writing.humanizer: true`, and tell them it loads after `/reload-plugins` or a restart. If no, or if the install fails, leave it false; skills still check dashes and stock phrases.
2. **JobSpy for LinkedIn and Indeed search** (default no): say plainly, "LinkedIn's User Agreement (section 8.2) forbids scraping and automated access, so this is off unless you choose it. Without it, job search uses the public Greenhouse, Lever and Ashby job boards of the companies you watch, and you can paste the text of any LinkedIn posting into `/job-hunt-studio:apply-job`." Only on an explicit yes: set `search.jobspy.enabled: true` with the sites chosen, write one `search.jobspy.searches` item per tier they want searched (`{location: "Lyon, France", country: "France", remote: false, tier: 1}`; `country` is the country name Indeed uses; `remote: true` for a remote tier), and install `python-jobspy` in step 9.
3. **Resume layout:** offer the layouts in `${CLAUDE_PLUGIN_ROOT}/templates/resume/` (folders with a `Resume.tex`; their looks are in that folder's `README.md`), and keeping the layout of the resume they gave in step 2 (`own`). If they lean towards their own, say it is checked against seven criteria (text PDF, one column, standard headings, dates next to each job, contact details in the page, length, readability) when the base resume is built, and that a Word or PDF resume is recreated in LaTeX for them to compare. Record `resume.template` (`classic`, `jakes` or `own`). The base resume itself is built after setup, with `/job-hunt-studio:tailor-resume base`.

## 8. Workspace files

Copy from `${CLAUDE_PLUGIN_ROOT}/templates/workspace/`, replacing every `{{...}}` placeholder with its value from `jhs.yaml` (`{{date}}` is today):
- `CLAUDE.md`, `HANDOFF.md`, `.gitignore`, `.claude/settings.json`, `applications/TRACKER.md`, `applications/outreach/CONTACTS.md`, `docs/Resume_Notes.md`, `interview/PRACTICE_LOG.md`, `interview/CLAIM_GATE.md`.
- Create `applications/leads/`, `interview/notes/`, `linkedin/`, `resumes/base/` and `resumes/draft/`, each with an empty `.gitkeep` so git keeps it. Do not create `resumes/approved/` or `resumes/current/`: the approve step makes them with the first approved version, and the guards block anything else from writing there. Also create `applications/outreach/private/` without one: git ignores it on purpose. If they gave their LinkedIn connections export in step 2, move `Connections.csv` there and set `outreach.connections: added` in `jhs.yaml`. If they gave their LinkedIn profile PDF, keep it in `linkedin/` (`linkedin-refresh` compares with it).
- If they chose `own` and gave a resume file, keep it in the workspace (for example `docs/my_resume.pdf` or `.tex`); `tailor-resume base` checks it and turns it into the base.

Never overwrite an existing file without asking. Afterwards, check that no `{{` remains in the copied files.

## 9. Tools

1. **Python:** find a working interpreter: on Windows try `py -3`, then `python` (`python3` is often a Microsoft Store stub there); on macOS and Linux use `python3`. If there is none, give the install link (python.org) and continue without the venv.
2. **Venv:** `<python> -m venv .venv`. On Debian or Ubuntu, if that fails, the fix is `sudo apt install python3-venv`. The venv interpreter is `.venv\Scripts\python.exe` on Windows and `.venv/bin/python` elsewhere; use its absolute path from here on.
3. **Packages:** `<venv python> -m pip install -r ${CLAUDE_PLUGIN_ROOT}/requirements.txt`, plus `python-jobspy` only if chosen in step 7.
4. **Check:** `<venv python> ${CLAUDE_SKILL_DIR}/scripts/check_env.py` and show the result.
5. **TeX, if missing:** setup can finish without it; only building resume PDFs needs it. Suggest the lightest route: Windows, MiKTeX plus Strawberry Perl (MiKTeX's `latexmk` needs Perl); macOS, BasicTeX then `sudo tlmgr install latexmk`; Linux, `sudo apt install texlive-latex-extra latexmk`. A new install is found only after Claude Code is restarted.

## 10. Commit and finish

1. If this folder is not its own git repository (step 1), run `git init`. If `git config user.name` or `user.email` is empty, ask for a name and email to use for this repository only (`git config user.name ...` without `--global`; any address works, it stays private).
2. Commit everything: `Job Hunt Studio workspace created`. Never add a remote and never push.
3. Remind them: the folder is private. To back it up, they can make a private repository or use a private cloud folder themselves; never a public one.
4. Summarize: what the Ledger holds, the open items and pending blocks left, the options chosen, missing tools.
5. Next steps: check which skills exist in `${CLAUDE_PLUGIN_ROOT}/skills/` and offer only those, in this order: build the base resume (`/job-hunt-studio:tailor-resume base`, then review and approve it), score a first posting (`/job-hunt-studio:apply-job <link>`), watch the companies they named (`/job-hunt-studio:find-jobs add <company>`) and run a first search, then the others listed in `HANDOFF.md`.
