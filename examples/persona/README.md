# Example candidate: Alex Rivera (fictional)

Everything here is invented: the person, employers, schools, projects, paper, numbers and links. It shows what setup produces, and the tests use it.

To try the plugin on Alex, run `/job-hunt-studio:setup example` in an empty folder: it builds a demo workspace from these files.

- [`jhs.yaml`](jhs.yaml): settings (contact, targets, location tiers, options), as after a finished setup.
- [`docs/Evidence_Ledger.md`](docs/Evidence_Ledger.md): the facts with their sources, three hard lines, claimed skills and gaps, and one correction kept as history (the paper moved from under review to accepted).

What to notice in the Ledger:
- **Exact numbers with their baseline:** "NDCG@10 +3.1% over the production scorer on a 30-day offline replay of 2.4M search sessions", not "improved ranking".
- **Status said plainly:** the v2 ranker was evaluated offline only, and a hard line flags any text that calls it deployed.
- **Confidential names stay out:** the ranker's internal codename is recorded once, with a hard line that keeps it off every document.
- **Own part versus the team's:** Alex built the evaluation for the search revamp, which someone else led, so "led" is flagged there.
- **Gaps are listed, not hidden:** Kubernetes and A/B testing (online) stay off the resume until Alex has done them. A gap is written as the bare term with any qualifier in parentheses, so the check catches every mention of the term.
