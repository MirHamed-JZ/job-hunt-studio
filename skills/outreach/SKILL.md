---
name: outreach
description: Find people at target companies (the user's own connections, team leads, engineers on the team, paper authors, alumni and former colleagues, recruiters) from free public sources, and draft short LinkedIn and email messages for the user to send themselves; then track replies and follow-ups. Use when the user names companies to reach out to, asks who to message at a company, wants a referral or an introduction, asks about networking or cold messages, or says someone replied to an outreach message.
argument-hint: "<Company, Company | location> | applied | log <name> <news> | status | setup"
---

Finds people and drafts messages; the user sends every message themselves. Facts: `docs/Evidence_Ledger.md` section 0. Settings: `jhs.yaml` (`outreach`, and `candidate.schools` and `candidate.past_employers` for shared ties). Files: `applications/outreach/`. What the user sees, the file layout and the evidence behind the approach: `${CLAUDE_PLUGIN_ROOT}/docs/OUTREACH.md`. How people are found: `${CLAUDE_SKILL_DIR}/PEOPLE_SEARCH.md`.

The workspace Python is `.venv/Scripts/python` on Windows and `.venv/bin/python` on macOS and Linux; run every command from the workspace folder. `<people>` below means `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/find_people.py`.

Pick the mode from "$ARGUMENTS" and from plain words:
- `setup`, or "add my connections", "change my outreach settings": **step 1**.
- a company list, optionally `| <location>` (default `outreach.default_location`): **new run** (steps 2 to 6).
- `applied`: a new run for the companies with open rows in `applications/TRACKER.md` (`Applied`, `Followed up`, `Screen`, `Interview`) that have nobody in `CONTACTS.md` yet.
- `log <name> <news>`, or "X accepted, replied, referred me": **step 7**.
- `status`, or "who do I follow up with": **step 8**.

**STOP** means end the turn and wait for the user. If `applications/outreach/CONTACTS.md` does not exist, copy it from `${CLAUDE_PLUGIN_ROOT}/templates/workspace/applications/outreach/CONTACTS.md` first.

## 0. Check the inputs

For a new run and for any drafting: `<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/preflight.py outreach`. If `.venv` does not exist, point to `/job-hunt-studio:setup tools`. On `RESULT: STOP`, show the MISSING lines as printed and stop. `log` without a draft, and `status`, need only `CONTACTS.md`.

On a new run, if `outreach.connections` is `unset` or `outreach.topics` is empty, run step 1 first (once: its answers are saved, so it never asks again).

## 1. Setup (first run, or `setup`)

Two parts in one message; on a first run show only what is missing.

**Settings, derived, then confirmed.** Propose values from the Ledger and `jhs.yaml`, as a short list:
- `outreach.default_location`: the city in `candidate.city` or Ledger `[identity]`.
- `outreach.topics`: 10 to 20 short word stems for the user's work, taken from `[positioning]`, `[skills-claimed]` and the `[project:...]` blocks (stems match more titles: `rank`, `retriev`, `recommend`, `evaluat`). They rank paper authors by how close their papers are to the user's work.
- `outreach.search_roles`: the user's first two target titles plus "engineering manager", "team lead" and "recruiter", unless they want others.
- The shared ties already in `candidate.schools` and `candidate.past_employers` (leave out freelance platforms); ask whether any are missing.

**LinkedIn connections export (optional).** Say in two lines: with it, every run first lists the people the user already knows at the company, the warmest route to a referral; the file stays on their computer, in a folder git ignores, and nothing is uploaded. The steps (desktop site; the mobile app lacks them):
1. Open https://www.linkedin.com/mypreferences/d/download-my-data, or **Me** > **Settings & Privacy** > **Data privacy** > **Get a copy of your data**.
2. Choose **Want something in particular?**, tick **Connections** (if that option is missing, take the larger archive; it contains the file too), then **Request archive**.
3. LinkedIn emails a download link, usually within about 10 minutes for connections alone (the full archive can take up to a day). Download and unzip it.
4. Put `Connections.csv` at `applications/outreach/private/Connections.csv`, or say where it is and Claude moves it there.

**STOP:** "Confirm or edit these settings, and tell me whether you want to add the export now, later, or never." Write the confirmed settings to `jhs.yaml` (ask before editing it). When the file is in place, run `<people> --check-connections`, report the count and the top companies, and set `outreach.connections: added`. If they decline for good, set `skipped` and never ask again on a run (`setup` still offers it); if "later", leave `unset` and continue the run without it. When a run reports the file as over 90 days old, suggest a fresh export in one line at the hand-over; never block a run for it.

## 2. Context per company

For each company, read its rows in `TRACKER.md`, its application folder if one exists (`posting.md`, `analysis.md`, `timeline.md`), and its rows in `CONTACTS.md`. Note: roles the user applied to (with dates), roles they could apply to, people already contacted (never draft for them again; a follow-up goes through step 8), and any referral already in progress. If a referral is already moving at a company, say so and ask before adding more contacts there.

## 3. Find people (free public sources only)

Follow `PEOPLE_SEARCH.md`, layer by layer, and stop once you have 2 or 3 strong people per company:
1. **Script:** `<people> "<Company>" [--location <City>]`. If the company's posting names a hiring manager or team, start from that.
2. **Web search:** the queries the script prints, with WebSearch and `allowed_domains` set as printed (LinkedIn returns indexed profile titles and snippets; `site:` in the query does not work), then news, talks and blogs. Cross-check the best people from layer 1.
3. **Paste:** if fewer than two people of the top two kinds below were found, ask the user once for the pastes the script lists, and wait.

Never sign in to LinkedIn, never fetch a linkedin.com page, and never drive a browser through LinkedIn: LinkedIn's User Agreement (section 8.2) forbids scraping and automated activity, and the account at risk is the user's. Search result titles and snippets are fine. No paid or account-gated people-data services either.

Pick 2 or 3 people per company, in this order of value:
1. An engineer or team lead on the team behind a role the user applied to: ask for a short chat or a referral.
2. A manager or team lead whose team matches the user's work (`[positioning]`, `outreach.topics`) when nothing is posted: ask whether the team expects to hire.
3. An author of recent company papers close to the user's work: the opening is a specific point about their paper.
4. A shared tie: an alumnus of the user's schools or a former colleague from a past employer (a shared tie also lifts a person of kinds 1 to 3).
5. A recruiter, only for a posted role.

A first-degree connection from the export comes first whatever their role: ask them for a referral or an introduction to the team. Next comes an introduction through a mutual connection (step 7).

For each person record: name, title, team, location, why them (one line), a shared tie if any, the public link where they were found, and the confidence (High, Medium or Low, as defined in `PEOPLE_SEARCH.md`). Mark anything inferred ("team inferred from a 2025 talk"), and tell the user to open each profile and confirm the person is still there before sending.

## 4. Draft the messages

For each person, three drafts in the user's plain voice:
- **Connection note**, at most 200 characters (the limit on free accounts in some places): who the user is, one specific reason for this person, no ask beyond connecting. Say whether it is worth one of the few notes a free account gets each month (the number varies; the user checks their own), or better sent without a note and followed by the message.
- **Message after they accept**, 60 to 120 words: one specific line about their team or work; one concrete proof point from Ledger section 0 that matches it; the ask (a short call, a referral to a named posting, or whether the team plans to hire for this kind of work); thanks. Never "do you have any role for me". Write the ask in words ("a short call", not "15 minutes"), so every number left in a draft is a Ledger fact or about the recipient.
- **Email**, the same message with a subject line, only when an address is public (a paper, a talk, a personal site). Never guess a work email address.

Rules:
- Facts and numbers only from Ledger section 0, under its `[hard-lines]` (scope `public` and `all`); nothing from `[skills-gaps]` or `[never-print]`; `[platform-facts]` only where they allow. Name a gap plainly when the role needs something the user lacks, rather than stretching a claim.
- Facts about the recipient (their paper, their team) come from the public source you found them in, cited in the people file. In the messages file, acknowledge a number or date about the recipient with `<!-- fact-ok: <it> | [recipient] <what it is> -->`; nothing else may be acknowledged that way.
- No em dashes, en dashes or double hyphens.
- **Writing pass:** if `writing.humanizer` in `jhs.yaml` is true and the humanizer skill is available, run it on every draft; if it is true but the skill is missing, say once that it is enabled but not installed (`/job-hunt-studio:setup options`). Then run `/job-hunt-studio:audit-claims applications/outreach/OUTREACH_<date>_messages.md message` (a rewrite can drop or bend a number) and fix everything it flags. Last, count each draft's characters and words with a short Python snippet (a rewrite can push a note over its limit) and trim any draft that is over. Show nothing before all three are done.

## 5. Write the files

- `applications/outreach/OUTREACH_<YYYY-MM-DD>.md`: per company, the context line, then per person the details from step 3, then a send plan table (order, person, channel, what to send, send by). Spread sends over the week: at most about 10 new people a week, warmest ties and posted roles first.
- `applications/outreach/OUTREACH_<YYYY-MM-DD>_messages.md`: the drafts only, so the fact check reads nothing else. One `## <Name>, <Company>` heading per person and one `### Connection note (<N> characters)`, `### Message after they accept (<N> words)` or `### Email` heading per draft; headings are not fact-checked, the drafts are.
- `applications/outreach/CONTACTS.md`: one row per person with status `Drafted` (columns in `OUTREACH.md`).
- For a company with an application folder, add a dated line to its `timeline.md`: `YYYY-MM-DD outreach drafted: <names>`.

## 6. Hand over (STOP)

In chat, short: the send plan as a table (who, company, why, channel, the connection note text), the people to check by hand first, and where a connection note is worth spending. Add one line: "If a target shows as 2nd degree, paste the mutual connections from their profile and I'll draft an introduction request to the one you know best." Commit locally: `git add applications/outreach` then `git commit -m "Outreach: <Companies> drafted"`. **STOP:** "Send what you want and tell me who you sent to." Never send, connect, follow or like anything for the user.

## 7. Log news

When the user says they sent a message, or someone accepted, replied, referred them or declined: update the person's row in `CONTACTS.md` (status `Sent`, `Accepted`, `Replied`, `Referred`, `Declined` or `No reply`; the date; a short note) and set the next action: after `Sent` or `Accepted` with no reply, one follow-up `applications.followup_days` later (7 by default); after that follow-up, `No reply` and no further date. A referral or a call goes into the company's application `timeline.md`, and a new posting to apply to goes to `/job-hunt-studio:apply-job`. When a call is offered, offer `/job-hunt-studio:mock-interview <company>` to prepare for it. Draft a follow-up or a reply on request, through the same rules, writing pass and check as step 4 (append it to that run's messages file). Commit locally: `Outreach: <Company> <what happened>`.

**Mutual connections.** When the user pastes the mutual connections of a target (from the target's profile, which they open themselves), ask which of them they actually know if it is not clear, then draft one **introduction request** to that person (a direct message, since they are connected): 50 to 90 words; who the target is and why them (one line, with the posting or team); one proof point from Ledger section 0; the ask ("would you be comfortable introducing me, or should I just mention your name?"); an easy way to say no. Same rules, writing pass and check. Log the mutual connection in `CONTACTS.md` with the channel "introduction request for <target>" and note on the target's row that an introduction is pending; drop the target's cold note from the send plan until the mutual connection answers (7 days, then the cold note goes ahead).

## 8. Status

List the rows in `CONTACTS.md` with an action due today or overdue, oldest first, each with a one-line suggested follow-up, then rows at `Drafted` for more than 7 days. Change nothing.

## Never

- Never send, connect or message for the user, and never automate anything on LinkedIn.
- Never contact the same person twice in a run, and never more than one follow-up after silence.
- Never present a guess (an email address, a team, a hiring plan) as a fact.
