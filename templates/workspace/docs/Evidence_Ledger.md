# Evidence Ledger

Setup status: incomplete (pending: positioning, identity, roles, projects, publications, skills, hard-lines, never-print)

The single source of truth for every fact about {{candidate.name}} used in resumes, LinkedIn text, form answers, cover letters and messages. Copy numbers from this file; never reconstruct them. Format and rules: the plugin's `docs/LEDGER_FORMAT.md`.

Section 0 is the current summary and is read first. Below it, dated entries record every change; old lines that became wrong are marked SUPERSEDED, never deleted. Every fact has a source; anything unconfirmed waits in Open items.

Placeholders look like `<like this>` or `TODO(setup)`. A block that still has one is not set up yet: skills treat it as missing, never print it, and point to `/job-hunt-studio:setup`.

---

## 0. Current facts (as of {{date}})

### Positioning [positioning]

- Target: <role titles, for example "Data Scientist, Analytics Engineer">
- One-line positioning: <what you do and for whom, in one sentence>
- Seniority: <for example "mid level, 3 years of industry experience">

### Identity [identity]

- Name as printed: <name>
- Title on the resume: <title>
- City: <city, region>
- Languages: <for example "English (fluent), French (working proficiency)">
- Contact details (email, phone, links): in `jhs.yaml`.

### Roles and education [roles]

| Title | Organization | Location | Dates (exact, as printed) | Source |
|---|---|---|---|---|
| <title> | <organization> | <city> | <Mon YYYY to Mon YYYY> | <offer letter, an old resume, or "confirmed by you on YYYY-MM-DD"> |

### Project: <name> [project:<slug>]

- What it is: <one or two sentences>
- My part (versus the team's): <what you personally did>
- Results: <exact numbers with their baseline and test set, for example "cut report time from 3 hours to 20 minutes for the finance team's monthly close">
- Status: <prototype, offline evaluation, handed off, or in production; say exactly which>
- Sources: <paper, report, link, or "confirmed by you on YYYY-MM-DD">

(Setup adds one block like this per project.)

### Publications [publications]

TODO(setup): one row per paper, or "None."

| Authors (in order, your name in bold) | Title | Venue, exactly as it may be printed | Year | Status | Link |
|---|---|---|---|---|---|

### Approved summary [summary]

TODO(setup): your approved resume summary, word for word, or "None yet."

### Skills claimed [skills-claimed]

Only skills you can discuss for 2 to 3 minutes with a specific example.

TODO(setup): one row per skill.

| Skill | Evidence (project, paper or role) | Example you would give |
|---|---|---|

### Skill gaps [skills-gaps]

Stay off every document until a project exists and `/job-hunt-studio:interview-drill` passes. Write the bare term, with any qualifier in parentheses ("A/B testing (online)"), so the check catches every mention.

TODO(setup): one row per gap, or "None."

| Skill | Status (gap, or learning: project name) | Since |
|---|---|---|

### Skill paraphrases [skill-paraphrases]

Other names you approved for a claimed skill (for example "LTR" for "learning to rank"); never wider than the original.

| Claimed skill | May also be written as | Approved on |
|---|---|---|

### Hard lines [hard-lines]

Claims never to make, or to make only in the allowed words. Setup writes the `banned` search pattern for you and shows what it catches; to add a rule later, ask Claude.

TODO(setup): one row per hard line, or "None." (an empty table is not the same as "no restrictions").

| id | rule | allowed | banned | scope |
|---|---|---|---|---|

### Never print [never-print]

TODO(setup): for example work authorization or visa status, salary history; or "None."

### Platform-only facts [platform-facts]

None.

### Open items [open-items]

None yet.

---

## {{date}}: Ledger created by /job-hunt-studio:setup

- Sources read: <files and links>
- Confirmed in the setup interview: <blocks>
- Left open: see Open items.
