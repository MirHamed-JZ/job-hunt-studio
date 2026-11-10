# Evidence Ledger

> **Fictional example.** Alex Rivera, every employer, school, project, paper, number and link in this file are invented to show how a Ledger looks and to test the plugin. Any resemblance to real people or organizations is coincidental.

The single source of truth for every fact about Alex Rivera used in resumes, LinkedIn text, form answers, cover letters and messages. Copy numbers from this file; never reconstruct them. Format and rules: the plugin's `docs/LEDGER_FORMAT.md`.

Section 0 is the current summary and is read first. Below it, dated entries record every change; old lines that became wrong are marked SUPERSEDED, never deleted.

Last updated: 2026-11-08 (internship project added).

---

## 0. Current facts (as of 2026-11-08)

### Positioning [positioning]

- Target: Applied ML Engineer, Machine Learning Engineer (ranking, recommendation, retrieval).
- One-line positioning: ML engineer who builds and evaluates ranking models for e-commerce search and recommendations.
- Seniority: mid level, 4 years of industry experience after an MSc.

### Identity [identity]

- Name as printed: Alex Rivera
- Title on the resume: Machine Learning Engineer
- City: Lyon, France
- Languages: Spanish (native), English (full professional), French (professional working)
- Contact details (email, phone, links): in `jhs.yaml`.

### Roles and education [roles]

| Title | Organization | Location | Dates (exact, as printed) | Source |
|---|---|---|---|---|
| Machine Learning Engineer | Brightfield Commerce | Lyon, France | Sep 2022 to present | offer letter; confirmed by Alex on 2025-01-10 |
| Data Science Intern | Brightfield Commerce | Lyon, France | Feb 2022 to Aug 2022 | internship agreement |
| MSc, Data Science | Halden Institute of Technology | Halden, Norway | Aug 2020 to Jun 2022 | diploma |
| BSc, Mathematics | Universidad de Valcastro | Valcastro, Spain | Oct 2016 to Jun 2020 | diploma |

### Project: v2 product ranker [project:ranker-v2]

- What it is: a learning-to-rank model (LightGBM LambdaMART) for product search, replacing hand-tuned scoring.
- My part (versus the team's): designed the features and the offline evaluation; trained and tuned the model. The data platform team owned the feature store.
- Results: NDCG@10 +3.1% over the production scorer on a 30-day offline replay of 2.4M search sessions.
- Status: evaluated offline only; not deployed (priorities changed in Q4 2024).
- Internal codename: Kestrel. Confidential; never printed (HL-codename).
- Sources: internal evaluation report of 2024-11-20 (not public; numbers confirmed by Alex on 2025-01-10).

### Project: feature pipeline rewrite [project:feature-pipeline]

- What it is: moved the nightly ranking-feature job from pandas scripts to PySpark on the company cluster.
- My part (versus the team's): wrote the new jobs and the validation tests; a senior engineer reviewed the design.
- Results: nightly runtime from 6 hours to 1.5 hours; in production since June 2023.
- Sources: team wiki page; confirmed by Alex on 2025-01-10.

### Project: search revamp evaluation [project:search-eval]

- What it is: an evaluation harness for the 2023 search revamp (a five-person team project).
- My part (versus the team's): built the offline evaluation and the weekly metrics report; the revamp itself was led by the search lead.
- Results: the harness ran 40 weekly comparisons during the revamp.
- Sources: confirmed by Alex on 2025-01-10.

### Project: query category classifier (internship) [project:query-classifier]

- What it is: a classifier that maps a search query to a product category, to replace the keyword rules then in use.
- My part (versus the team's): built a labeled set of 12,000 queries with the merchandising team; trained the classifier (logistic regression on TF-IDF features); wrote the evaluation and handoff report.
- Results: top-1 category accuracy 87% on a held-out set of 2,000 queries, versus 71% for the keyword rules.
- Status: handed off to the search team in Aug 2022; not known to be in production.
- Sources: internship report of Aug 2022; confirmed by Alex on 2026-11-08.

### Publications [publications]

| Authors (in order, your name in bold) | Title | Venue, exactly as it may be printed | Year | Status | Link |
|---|---|---|---|---|---|
| **Alex Rivera**, Ingrid Solvang | Contrastive Pretraining for Sparse Product Catalogs | Workshop on Retrieval for Commerce (fictional) | 2025 | accepted (workshop paper) | https://example.org/paper-rivera-2025 |

### Approved summary [summary]

ML engineer with 4 years building and evaluating ranking models for e-commerce search. Designed a learning-to-rank model that improved NDCG@10 by 3.1% in offline replay, and cut a nightly feature pipeline from 6 hours to 1.5 hours.

### Skills claimed [skills-claimed]

| Skill | Evidence (project, paper or role) | Example you would give |
|---|---|---|
| Python | all roles | feature pipeline and evaluation code |
| learning to rank | [project:ranker-v2] | LambdaMART features, NDCG trade-offs |
| offline evaluation | [project:ranker-v2], [project:search-eval] | replay design, metric choice |
| PySpark | [project:feature-pipeline] | partitioning the nightly job |
| SQL | Brightfield roles | session tables for the replay |
| PyTorch | MSc thesis, [publications] | contrastive pretraining code |

### Skill gaps [skills-gaps]

| Skill | Status (gap, or learning: project name) | Since |
|---|---|---|
| Kubernetes | gap | 2025-01-10 |
| A/B testing (online) | gap (offline replay only so far) | 2025-01-10 |
| LLM fine-tuning | learning: small retrieval side project | 2025-02-01 |

### Skill paraphrases [skill-paraphrases]

| Claimed skill | May also be written as | Approved on |
|---|---|---|
| learning to rank | ranking models, LTR | 2025-01-10 |
| offline evaluation | offline experimentation | 2025-01-10 |

### Hard lines [hard-lines]

| id | rule | allowed | banned | scope |
|---|---|---|---|---|
| HL-ranker-status | The v2 ranker was evaluated offline only | "evaluated offline on a 30-day replay" | `ranker.{0,60}\b(deploy\w*\|in production\|launch\w*\|ship(ped\|s)?\|live)\b\|\b(deploy\w*\|launch\w*\|ship(ped\|s)?)\b.{0,60}ranker` | all |
| HL-codename | The ranker's internal codename is confidential | "the v2 product ranker" | `\bkestrel\b` | all |
| HL-team-role | The search revamp was a team project led by someone else | "built the evaluation for the search revamp" | `\b(led\|owned\|spearheaded)\b.{0,40}\b(search\|revamp)` | resume, linkedin |

### Never print [never-print]

- Work authorization (EU citizen; for form answers only).
- Salary history.

### Platform-only facts [platform-facts]

- None.

### Open items [open-items]

- Whether the internal evaluation report may be mentioned by name in interviews (asked 2025-01-10).

---

## 2026-11-08: internship project added

- [project:query-classifier]: query category classifier built during the 2022 internship; top-1 accuracy 87% versus 71% for keyword rules on 2,000 held-out queries; labeled set of 12,000 queries; handed off in Aug 2022 (source: internship report of Aug 2022; confirmed by Alex on 2026-11-08).

## 2025-03-14: paper accepted

- [publications]: "Contrastive Pretraining for Sparse Product Catalogs" moved from under review to accepted at the Workshop on Retrieval for Commerce (source: acceptance email of 2025-03-13).

## 2025-02-01: skill gap added

- [skills-gaps]: LLM fine-tuning, status learning: small retrieval side project (source: said by Alex on 2025-02-01).

## 2025-01-10: Ledger created by /setup

- Sources read: resume of 2024-12, LinkedIn profile PDF, internship agreement, the paper preprint.
- Confirmed by Alex in the setup interview: all of section 0.
- [publications] status: under review. SUPERSEDED 2025-03-14 (see the 2025-03-14 entry).
- Left open: see [open-items].
