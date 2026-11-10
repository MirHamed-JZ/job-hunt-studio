# Job Hunt Studio

An evidence-first job search for [Claude Code](https://code.claude.com). You keep one file of confirmed facts about your work, your **Evidence Ledger**. Every resume, form answer, cover letter and message is drawn from it, checked against it, and sent by you.

> **Version 0.1.0**, the first release. See [CHANGELOG.md](CHANGELOG.md). Questions and bug reports are welcome as GitHub issues; answers are best effort.

## Why

AI tools make it easy to send a hundred applications with claims you cannot defend in an interview. Job Hunt Studio does the opposite: fewer applications, each one true.

- **One source of truth.** Your Ledger holds every fact with where it comes from.
- **Hard lines.** You say, in plain words, the claims you must never make ("never say the model was deployed"). Setup turns each into a check and shows you what it catches; you never write code.
- **A skill is claimed only if you can talk about it** for two or three minutes with a real example. Gaps stay off your resume until you have built something with them and passed a five-question check (`interview-drill`).
- **A review gate.** A resume is ready only when automatic checks and a separate Claude reviewer pass it. Every number, title and date is compared with your Ledger.
- **Job postings are treated as data.** Hidden text in a posting (white text, invisible characters, "ignore your instructions") is removed or flagged before Claude reads it.
- **You stay in charge.** Nothing is submitted, sent or posted for you, and nothing scrapes LinkedIn unless you choose JobSpy. Approved resume versions are fixed: Claude cannot change them, or push your workspace anywhere ([the guards](docs/GETTING_STARTED.md#7-what-claude-cannot-do-in-your-workspace)).
- **Interview practice that teaches.** Questions as an interviewer asks them, then what your answer missed, with your weak spots tracked across rounds.

## What it does

All skills are typed with the plugin's prefix, for example `/job-hunt-studio:setup`. Most also start from plain words ("score this posting").

| Step | Skill | What you get |
|---|---|---|
| Start | `setup` | A private workspace, your Ledger drafted from your resume and confirmed by you, settings, a tool check |
| Find roles | `find-jobs` | New postings from the job boards of companies you watch, filtered by location and level, ranked against your Ledger and sorted into Strong, Possible and Skip ([how](docs/JOB_SEARCH.md)) |
| Build | `tailor-resume base` | Your base resume, built from your Ledger in the layout you chose (an included one, or your own) |
| Decide | `score-job` | Two scores: what your evidence supports, and what a recruiter sees on your resume |
| Apply | `apply-job`, `tailor-resume` | Proposed resume edits for your OK, a tailored PDF reviewed to READY, form answers, tracking and follow-ups ([how](docs/APPLICATIONS.md)) |
| Check | `review-resume`, `compile-resume`, `audit-claims` | A PDF build; checks that applicant tracking systems (ATS) can read it, that the layout holds and every fact matches the Ledger; a separate Claude reviewer ([rules](docs/RESUME_GUIDE.md), [rubric](docs/REVIEW_RUBRIC.md)) |
| Reach people | `outreach` | People at target companies found on public pages; short message drafts you send yourself; follow-ups tracked ([how](docs/OUTREACH.md)) |
| Prepare | `mock-interview` | Interview practice that teaches after each answer, tracks weak spots, and debriefs real interviews ([how](docs/INTERVIEWS.md)) |
| Keep it true | `update-ledger` | New facts recorded with their sources; old versions kept as history |
| Claim a new skill | `interview-drill` | Five questions on your own project decide whether a skill you learned may go on your resume ([how](docs/INTERVIEWS.md#the-claim-gate-interview-drill)) |
| Show up | `linkedin-refresh` | Paste-ready LinkedIn text from your Ledger, compared with your current profile ([rules](docs/LINKEDIN_GUIDE.md)) |

## Install

You need a Claude plan that includes Claude Code. Everything else is free, with no extra accounts or API keys:
- **Git** (on Windows, Git for Windows, which includes the Git Bash that the guards run in);
- **Python 3** (3.8 or later);
- **a TeX distribution** for building resume PDFs: TeX Live, MiKTeX or MacTeX; on Windows, MiKTeX also needs Strawberry Perl. Setup tells you if either is missing.

In a terminal:

```
claude plugin marketplace add MirHamed-JZ/job-hunt-studio
claude plugin install job-hunt-studio@job-hunt-studio
```

Or inside Claude Code: `/plugin marketplace add MirHamed-JZ/job-hunt-studio`, then `/plugin install job-hunt-studio@job-hunt-studio`, then `/reload-plugins`.

To update later: `claude plugin marketplace update job-hunt-studio`, then `claude plugin update job-hunt-studio@job-hunt-studio`, and restart Claude Code.

## Try it on the example candidate

Before you enter anything about yourself, you can watch it work for Alex Rivera, a fictional machine learning engineer ([the example files](examples/persona/)). Make an empty folder, open a terminal in it, type `claude`, then:

1. `/job-hunt-studio:setup example` makes a demo workspace from the example (a few minutes; it creates a Python environment).
2. `/job-hunt-studio:tailor-resume base` builds Alex's one-page resume from the Ledger, shows each bullet for your OK, then runs `review-resume`: the automatic checks and the separate reviewer, then READY or NOT READY with fixes.
3. At READY, Claude asks "Approve as v1?" Open the PDF, then reply OK. This tags the version that `apply-job` tailors from.
4. Paste a posting into `/job-hunt-studio:apply-job` (a real one, or one you make up): two scores, then proposed edits for your OK.
5. `/job-hunt-studio:mock-interview learning to rank` asks five or six questions on one of Alex's skills and teaches after each answer.

Then try to make it overclaim. Here is a cover letter for Alex with four problems:

```
I am a passionate ML engineer with 6 years of experience. At Brightfield I deployed the v2 ranker
to production and improved NDCG@10 by 3.1% over the production scorer. I also run our Kubernetes cluster.
```

Type `/job-hunt-studio:audit-claims cover-letter` and paste it. The code check prints this before Claude reads the letter line by line (real output, shortened):

```
WARN gap-skill: "Kubernetes" (listed in [skills-gaps]; stays off until /job-hunt-studio:interview-drill passes)
WARN hard-line HL-ranker-status: "deployed the v2 ranker" (The v2 ranker was evaluated offline only)
WARN number: "6" (not in Ledger section 0 with the unit year)
WARN phrase: "passionate" (stock phrase)
FACTS: 4 TO RESOLVE
```

The 3.1% passes: it is in Alex's Ledger. The rest must be fixed before anything is sent.

## Start for real

1. Read [Getting started](docs/GETTING_STARTED.md): what to gather first (your resume, your LinkedIn profile as a PDF, links to your work) and what setup will ask.
2. Make a new empty folder for your job search (not the demo one), open a terminal in it, and type `claude`.
3. Run `/job-hunt-studio:setup`. It takes 30 to 45 minutes and you can stop and continue later.
4. After setup, build and approve your base resume: [Getting started, section 3](docs/GETTING_STARTED.md#3-after-setup-your-base-resume).

**Keep that folder private.** It holds your personal details and applications ([more on privacy](docs/GETTING_STARTED.md#6-privacy)).

## Choices setup asks about

- **Humanizer** ([blader/humanizer](https://github.com/blader/humanizer), MIT): rewrites text that reads as AI-written. Recommended; setup installs it if you agree.
- **JobSpy** ([speedyapply/JobSpy](https://github.com/speedyapply/JobSpy), MIT): adds LinkedIn and Indeed search. Off unless you choose it, because LinkedIn's User Agreement forbids scraping. Without it, `find-jobs` reads the public job boards of the companies you watch, and you can paste any posting into `apply-job`.
- **Field pack:** `ml-research` (interview topics with readings, keywords for machine learning roles) or `none` for other fields ([packs](packs/README.md)).
- **Resume layout:** `classic` or `jakes` ([see both](templates/resume/README.md)), or your current resume's layout if it passes the checks there (a Word or PDF resume is recreated in LaTeX for you to compare).

## For contributors

- Unit tests: `python -m unittest discover tests` with the packages in `requirements.txt` (the build tests also need latexmk).
- Plugin evals: [`evals/`](evals/README.md), run with `claude plugin eval`.
- The Ledger format: [docs/LEDGER_FORMAT.md](docs/LEDGER_FORMAT.md). Field packs: [packs/README.md](packs/README.md).

## Credits

- Resume layouts based on [Jake's Resume](https://github.com/jakegut/resume) (MIT) and [RenderCV](https://github.com/rendercv/rendercv) (MIT).
- Humanizer by [blader](https://github.com/blader/humanizer); JobSpy by [speedyapply](https://github.com/speedyapply/JobSpy).

Job Hunt Studio is an independent project, not affiliated with or endorsed by Anthropic. No warranty: read every document before you send it.

## License

[MIT](LICENSE)
