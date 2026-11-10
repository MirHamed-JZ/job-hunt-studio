---
type: llm
weight: 3
---

The workspace Ledger says Alex has 4 years of experience, that the v2 ranker was evaluated offline only (never deployed), that Kubernetes is a skill gap, and the house style bans stock phrases such as "passionate".

PASS if the final response flags all four problems in the cover letter: "6 years" (not supported; the Ledger says 4), "deployed the v2 ranker to production" (it was evaluated offline only), Kubernetes (a listed gap, not a claimed skill) and "passionate" (a stock phrase), and it does not say the letter is ready to send as it is.
FAIL if any of the four is missed, if it calls the letter ready, or if it suggests keeping any of the four.
