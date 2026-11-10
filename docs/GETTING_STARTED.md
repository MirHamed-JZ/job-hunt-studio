# Getting started

Job Hunt Studio only knows what you tell it. Everything it writes about you comes from one file, your **Evidence Ledger**: a list of facts about your work that you have confirmed, each with where it comes from. The better your Ledger, the better every resume, answer and message. This page says what to gather before setup, what setup will ask, how to get your first approved resume, what each feature needs, and how to keep things up to date.

## 1. Before you start: gather these

You can start with nothing but your memory, but setup is faster and more accurate with documents. Put them in one folder you can point to.

| What | Why | How to get it | Needed? |
|---|---|---|---|
| **Your current resume** (PDF or LaTeX `.tex`; save a Word file as PDF first) | The starting draft for your Ledger | Your latest version, even if outdated | Strongly recommended |
| **Your LinkedIn profile as a PDF** | Fills gaps the resume misses (older roles, dates, volunteering) | On your LinkedIn profile, click **More** (or **Resources**) then **Save to PDF** | Recommended |
| **Links to your work** | Papers, a portfolio, GitHub, talks, a thesis; they become the sources for your facts | Copy the URLs | Recommended if you have them |
| **Exact numbers you are proud of** | Results with their baseline ("40% faster than the old pipeline, on the March dataset") | From reports, dashboards or your notes | Recommended |
| **Your LinkedIn connections export** | Lets outreach list people you already know at a company | Steps in [Outreach](OUTREACH.md#your-connections-export-optional) | Optional; for outreach |
| **Your resume's own layout** | If it already looks good, you can keep it instead of the included layouts; it is checked first ([what is checked](../templates/resume/README.md#keeping-your-own-layout)) | Your `.tex`, or the PDF of a Word or Google Docs resume | Optional |

**Do not provide:** passwords, confidential employer documents (internal reports, unreleased results, client data), or anything you are not allowed to share. If a result is confidential, describe it at the level you could say in an interview.

## 2. What setup asks

To look around first, `/job-hunt-studio:setup example` makes a demo workspace for the fictional example candidate in a few minutes, with nothing personal in it.

Run `/job-hunt-studio:setup` in an empty folder (all skills are typed with the `job-hunt-studio:` prefix). It takes 30 to 45 minutes, and you can stop at any point and continue later.

1. **Your documents.** It reads what you gathered.
2. **Your profile.** Contact details, the roles you want, where you want to work, how senior, and a field pack (`ml-research`, or `none` for other fields; it sets the interview topics and search keywords).
3. **Your facts, one block at a time.** It drafts each block of your Ledger (roles, each project, publications) and asks you to confirm or correct it. Expect questions an interviewer would ask: the exact number and what it was compared against; whether a project was a prototype or used by real users; what *you* did versus your team.
4. **Your hard lines.** Claims you must never make, in your own words ("never say the model was deployed", "never say I led that project"). Setup turns each into a check and shows you two sentences it would catch. You never write code.
5. **Your skills.** For each skill, the example you would give in an interview. Skills without one are listed as gaps and stay off your resume until you have built something with them.
6. **Options.** Humanizer (rewrites text that sounds AI-written; recommended), LinkedIn and Indeed search through JobSpy for `find-jobs` (off unless you choose it; LinkedIn's terms forbid scraping), and a resume layout: `classic`, `jakes`, or your current one if it passes the checks.
7. **Tools.** It installs what it can and tells you what is missing (usually a TeX distribution for building PDFs).

What you end up with, in your folder:
- `docs/Evidence_Ledger.md`: your facts.
- `jhs.yaml`: your settings.
- `CLAUDE.md`: the rules Claude follows in this folder.
- `HANDOFF.md`: where you left off.
- `applications/TRACKER.md`: your applications.
- `docs/Resume_Notes.md`: your layout choices (what to cut first, the header, lines kept in reserve).
- `interview/`: your practice log and claim gate (empty until you practice); `linkedin/`: your LinkedIn text.
- `resumes/`: `base/` (your resume source) and `draft/` (never send); `current/` (the PDF to send) and `approved/` (fixed copies of each approved version) appear with your first approved version.

Anything you were unsure about is listed under "Open items" in the Ledger, to answer later.

## 3. After setup: your base resume

1. Run `/job-hunt-studio:tailor-resume base`. It fills your chosen layout from the Ledger and shows you each bullet to confirm.
2. It then runs `/job-hunt-studio:review-resume`: automatic checks plus a separate Claude reviewer. **READY** means every check passed and the score reached `review.ready_threshold` in `jhs.yaml` (85 by default). If it is not ready, you see exactly what to fix.
3. Claude asks "Approve as v1?" Reply OK only after you have opened the PDF. Approval saves a fixed copy that never changes (a git tag, `resume-approved-v1`) and puts the file to send in `resumes/current/`. Never send anything from `resumes/draft/`.
4. Then paste a job posting link or its text (for LinkedIn, always the text), or run `/job-hunt-studio:apply-job <link>`, to score it and, if you want, tailor a copy for it ([the steps and files](APPLICATIONS.md)).
5. To find postings, watch a few companies (`/job-hunt-studio:find-jobs add <company>`) and run `/job-hunt-studio:find-jobs`; to reach people there, `/job-hunt-studio:outreach <company>`.
6. Before an interview, `/job-hunt-studio:mock-interview <company>`; right after it, `/job-hunt-studio:mock-interview debrief <company>`.
7. For LinkedIn, save your profile as a PDF into `linkedin/` and run `/job-hunt-studio:linkedin-refresh`. You paste the text yourself, then tell Claude what you pasted.

## 4. What each feature needs

| Feature | Needs from you |
|---|---|
| setup | the documents above, about 30 to 45 minutes |
| update-ledger | the new fact in plain words, and its source |
| tailor-resume base | a confirmed Ledger (roles, skills, hard lines), a layout choice, a TeX distribution |
| review-resume, compile-resume | a TeX distribution and a base resume; Poppler (MiKTeX includes it; `brew install poppler` on macOS, `sudo apt install poppler-utils` on Linux) adds the page images for the visual check |
| score-job | a job posting (link or pasted text) and a confirmed Ledger; an approved resume for the second score |
| apply-job, tailor-resume | a job posting and an approved base resume |
| audit-claims | the text to check (a file, or pasted) and a confirmed Ledger |
| find-jobs | target titles and location tiers (asked at setup); companies to watch, added with `find-jobs add <company>` ([how it works](JOB_SEARCH.md)) |
| outreach | companies to reach; optionally your connections export ([how it works](OUTREACH.md)) |
| mock-interview | nothing extra (a pack in `jhs.yaml` adds a topic list); for a company's round, its application folder or the posting ([how it works](INTERVIEWS.md)) |
| interview-drill | a project you built with the skill you want to claim; it runs only when you type it |
| linkedin-refresh | a confirmed Ledger and, ideally, an approved resume (titles and dates must match it); optionally your current profile as a PDF in `linkedin/` ([how it works](LINKEDIN_GUIDE.md)) |

If something a feature needs is missing, it says what is missing and how to add it, instead of guessing.

## 5. Keeping it up to date

Your Ledger is meant to change. Never edit facts by hand in a hurry; tell Claude and let it record the change with its source and date, so old versions stay as history.

- **Something new happened:** `/job-hunt-studio:update-ledger my paper was accepted at <venue>, email of 12 March`, or "I finished the pricing project, it cut costs 12% against last year's budget".
- **A fact was wrong:** `/job-hunt-studio:update-ledger correction: the dataset had 1.8M sessions, not 2.4M`. The old line is marked as replaced, never deleted.
- **You learned a new skill:** build something with it and record the project with `update-ledger`. It stays a gap until `/job-hunt-studio:interview-drill <skill>` checks that you can discuss it ([the claim gate](INTERVIEWS.md#the-claim-gate-interview-drill)).
- **Your search changed** (new city, new titles): ask Claude to update `jhs.yaml`, or re-run part of setup with `/job-hunt-studio:setup search`. The other sections are `profile`, `ledger`, `hard-lines`, `skills`, `options`, `files` and `tools`.
- **Your base resume should change:** run `/job-hunt-studio:tailor-resume base` and say what to change. It becomes the next version (v2, v3), approved only after you see the reviewed PDF; earlier versions are kept.

## 6. Privacy

Your workspace is a private folder on your computer, tracked with git but never pushed anywhere: Claude cannot run `git push` there ([the guards](#7-what-claude-cannot-do-in-your-workspace)). Claude reads it during your Claude Code sessions, as with any project. Back it up privately (a private repository or a private cloud folder), never in a public one; if you push to a private repository, do it from your own terminal.

## 7. What Claude cannot do in your workspace

The plugin installs guards that check each file edit and shell command Claude makes in a folder with a `jhs.yaml` (your workspace). Claude cannot:

- change, delete or move anything in `resumes/approved/` or `resumes/current/`; only the approve step writes there, after your explicit OK. Claude can still read those files and copy them elsewhere;
- delete, move or make by hand an approved-version tag (`resume-approved-v1` and so on, or the prefix in `resume.tag_prefix`), or run `git reset --hard`;
- push: `git push`, or creating a GitHub repository with `--push`.

When a guard stops a command, Claude sees why and says so. In any other folder the guards do nothing. They catch mistakes, not every possible command: a script that writes files itself is not inspected, which is one more reason to read what Claude proposes. They cover only what Claude does: commands you type in your own terminal are up to you. They run with Python 3 (setup checks for it) and, on Windows, Git Bash (part of Git for Windows). Setup also writes `.claude/settings.json` in your workspace: Claude asks before it edits files in `docs/` (your Ledger), `CLAUDE.md` or `jhs.yaml`, or runs `git rm`, and may not run `rm` or add a git remote.
