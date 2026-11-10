# Changelog

## 0.1.0 (first release)

Getting started
- `/job-hunt-studio:setup`: checks the folder, gathers your documents, drafts and confirms the Evidence Ledger, writes `jhs.yaml`, offers humanizer, JobSpy and a resume layout (or keeping your own), copies the workspace files, checks the tools; resumes if stopped part-way. `setup example` makes a demo workspace for the fictional example candidate.
- [Getting started](docs/GETTING_STARTED.md): what to gather, what setup asks, what each feature needs, how to keep it up to date, what Claude cannot do in your workspace.
- Evidence Ledger format with named anchors, placeholders that mark unfinished blocks, and a hard-lines table ([docs/LEDGER_FORMAT.md](docs/LEDGER_FORMAT.md)).
- Workspace templates: `jhs.yaml`, Ledger, `CLAUDE.md`, `HANDOFF.md`, tracker, permissions.
- A fictional example candidate ([examples/persona/](examples/persona/)).

Resumes and applications
- `update-ledger`, `audit-claims`, `score-job`, `tailor-resume` (with `base` to build or change the base resume), `apply-job`, `compile-resume`, `review-resume` and the `cv-reviewer` agent. Each skill checks what it needs first and names the fix when something is missing.
- Posting guard: every posting is saved as clean text; hidden text (white or tiny text in any CSS notation, hidden boxes, screen-reader-only text), invisible characters and instruction-like lines are removed or quoted as data. LinkedIn links, short links and redirects to LinkedIn are never followed; you paste the text.
- Fact and voice check: numbers (durations with their unit), dates, job titles, hard lines, gap skills, never-print items, dashes and stock phrases compared with the Ledger. Warnings never fail a build; a resume is READY only when each is fixed or, for a true number, date or hard-line sentence, acknowledged with a reason that cites the Ledger. In a message, cover letter or form answer, a number or date about the person or company written to can be acknowledged with `[recipient]` (in a cover letter or form answer, only one the posting contains; never a duration).
- Two resume layouts, `classic` (from RenderCV) and `jakes` (from Jake's Resume), or your own layout once it passes the checks.
- Approval of a resume version as a git tag with an archived PDF; approved versions are never changed.

Job search, outreach, interviews, LinkedIn
- `find-jobs`: scans the public Greenhouse, Lever and Ashby job boards of the companies you watch (`find-jobs add <company>` finds a company's board), plus LinkedIn and Indeed only if you chose JobSpy at setup; filters by your titles, level, years asked and location tiers; ranks by overlap with your Ledger; flags language, work authorization and PhD requirements; Claude triages the top leads into Strong, Possible and Skip ([docs/JOB_SEARCH.md](docs/JOB_SEARCH.md)). Every description passes the posting guard.
- `outreach`: finds people at target companies from free public sources (your own connections export, OpenAlex paper authors, GitHub, web search limited to public LinkedIn results), drafts connection notes, messages, emails and introduction requests from your Ledger, checks them with the humanizer and the fact and voice check, and tracks replies and follow-ups in `applications/outreach/CONTACTS.md` ([docs/OUTREACH.md](docs/OUTREACH.md)).
- `mock-interview`: topic, plan, resume, behavioral, company-stage and weak-spot rounds that teach after each answer; a practice log with coverage and weak spots; revision notes; a debrief right after a real interview (timeline, tracker, weak spots, an optional thank-you note checked against the Ledger) ([docs/INTERVIEWS.md](docs/INTERVIEWS.md)).
- `interview-drill`: the claim gate. Five questions on your own project decide whether a skill moves from gaps to claimed, recorded in `interview/CLAIM_GATE.md`.
- `linkedin-refresh`: paste-ready LinkedIn text from the Ledger, compared with the current profile, checked with the humanizer and the fact and voice check ([docs/LINKEDIN_GUIDE.md](docs/LINKEDIN_GUIDE.md)).
- The `ml-research` pack: keywords and 16 interview areas with readings ([packs/](packs/README.md)).

Safety and quality
- Guards (plugin hooks): in a workspace, Claude cannot change `resumes/approved/` or `resumes/current/` (it can read and copy from them), delete, move or hand-make an approved-version tag, run `git reset --hard`, or push. They do nothing in other folders ([what they block](docs/GETTING_STARTED.md#7-what-claude-cannot-do-in-your-workspace)).
- Unit tests with fictional data only (`tests/`), and plugin evals for `claude plugin eval` ([evals/](evals/README.md)).
