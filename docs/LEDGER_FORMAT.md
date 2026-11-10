# Evidence Ledger format

Every Job Hunt Studio skill takes facts about you from one file in your workspace, `docs/Evidence_Ledger.md`. This page describes that file. You rarely edit it by hand: `/job-hunt-studio:setup` creates it from the template, and `/job-hunt-studio:update-ledger` records changes. A filled example: [`examples/persona/docs/Evidence_Ledger.md`](../examples/persona/docs/Evidence_Ledger.md).

## Rules

1. **Section 0 is the current truth.** Skills read section 0 first and copy numbers from it; they never reconstruct or recompute them.
2. **History is never deleted.** Below section 0, each change gets a dated entry (`## YYYY-MM-DD: what changed`). When a fact changes, the old line stays and is marked `SUPERSEDED YYYY-MM-DD (see the YYYY-MM-DD entry)`, and section 0 shows the new value. Newer entries win.
3. **Every fact has a source:** a paper, a document, a link, or "confirmed by you on YYYY-MM-DD". A fact without one waits in Open items.
4. **You confirm every fact before it is written.** Claude drafts; you say yes or correct it.
5. **Skills refer to blocks by anchor, never by section number.** An anchor is the tag in square brackets at the end of a heading, for example `### Hard lines [hard-lines]`. Numbers change as the Ledger grows; anchors do not.
6. **Placeholders mean "not set up yet".** Text like `<title>` or `TODO(setup)` marks a block that setup has not filled. Skills treat such a block as missing, never print it, and point you to `/job-hunt-studio:setup <section>`. The `Setup status:` line under the title lists what is still pending.

## The blocks in section 0

| Anchor | Holds | Used for |
|---|---|---|
| `[positioning]` | The roles you target, a one-line positioning, seniority | scoring, tailoring, outreach, LinkedIn |
| `[identity]` | Name and title as printed, city, languages (contact details live in `jhs.yaml`) | resume header, scoring, LinkedIn |
| `[roles]` | Every job and degree: title, organization, location, exact dates | resume, interview questions about your CV |
| `[project:<name>]` | One block per project: what it is, your part versus the team's, results with exact numbers (per paper version when versions differ), status, sources | every writing skill, interview questions |
| `[publications]` | Each paper: authors in order, title, venue exactly as it may be printed, year, status, link | resume, LinkedIn, outreach |
| `[summary]` | Your approved resume summary, word for word (optional) | tailoring, LinkedIn |
| `[skills-claimed]` | Skills you can discuss for 2 to 3 minutes with a specific example, with the evidence | scoring, tailoring, review |
| `[skills-gaps]` | Skills you do not have yet, each as the bare term with any qualifier in parentheses ("A/B testing (online)"), so the check catches every mention; they stay off every document until `/job-hunt-studio:interview-drill` passes | scoring, tailoring, interview practice |
| `[skill-paraphrases]` | Other names you approved for a claimed skill ("LTR" for "learning to rank"), never wider | scoring, tailoring, review |
| `[hard-lines]` | The table below | every check |
| `[never-print]` | Facts that never appear on a resume or public text (work authorization, salary history) | every writing skill |
| `[platform-facts]` | Facts allowed on one platform only (optional) | LinkedIn, outreach |
| `[open-items]` | Unconfirmed facts and questions waiting for you | setup, update-ledger |

## Hard lines

Hard lines are claims you must never make, or may make only in exact words. They keep strong framing from becoming fabrication. You describe them in plain words; setup writes the table row, including the search pattern, and shows you sentences it would catch.

| Column | Meaning |
|---|---|
| `id` | A short name, by convention starting with `HL-`; reports cite it |
| `rule` | The rule in one sentence |
| `allowed` | True wording you may use |
| `banned` | A search pattern (a case-insensitive Python regular expression, in backticks) for wording that breaks the rule. Every match becomes a warning you resolve before a resume is READY. Empty when no pattern fits; the reviewer still applies the rule. Inside the table, `\|` stands for "or" |
| `scope` | Where it applies, one or more of: `resume` (the resume and everything sent with an application: cover letters, form answers), `linkedin`, `public` (text other people read outside an application: LinkedIn, posts, messages), `interview` (prepared answers), `all`; separate several with commas |

The fictional persona's rows:

| id | rule | allowed | banned | scope |
|---|---|---|---|---|
| HL-ranker-status | The v2 ranker was evaluated offline only | "evaluated offline on a 30-day replay" | `ranker.{0,60}\b(deploy\w*\|in production\|launch\w*\|ship(ped\|s)?\|live)\b\|\b(deploy\w*\|launch\w*\|ship(ped\|s)?)\b.{0,60}ranker` | all |
| HL-codename | The ranker's internal codename is confidential | "the v2 product ranker" | `\bkestrel\b` | all |
| HL-team-role | The search revamp was a team project led by someone else | "built the evaluation for the search revamp" | `\b(led\|owned\|spearheaded)\b.{0,40}\b(search\|revamp)` | resume, linkedin |

The first one flags "Deployed the v2 ranker to production" but not "Prototyped the ranker during my internship".

## Dated entries

```
## 2025-03-14: paper accepted

- [publications]: "Contrastive Pretraining for Sparse Product Catalogs" moved from under review
  to accepted at the Workshop on Retrieval for Commerce (source: acceptance email of 2025-03-13).
```

And in the older entry, the replaced line is kept and marked:

```
- [publications] status: under review. SUPERSEDED 2025-03-14 (see the 2025-03-14 entry).
```

## For skill and script authors

`tools/ledger.py` reads a Ledger: `anchors(text)` maps each anchor in section 0 to its text, `hard_lines(text)` returns the parsed table (it raises an error if the table is missing or a pattern is invalid), `roles(text)` and `table_column(text, anchor)` read tables, and `is_pending(text)` tells whether a block still holds placeholders. `python tools/ledger.py check docs/Evidence_Ledger.md` reports missing blocks, pending blocks and invalid patterns.

`tools/fact_check.py` compares a document with section 0 (numbers, dates, `[roles]` entries, hard lines in the document's scope, gap skills, never-print items, dashes, stock phrases); `tools/preflight.py <skill>` checks that the blocks a skill needs are set up.
