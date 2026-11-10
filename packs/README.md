# Packs

A pack tunes the plugin to one field: interview topics for `mock-interview`, keywords for job search and scoring, and what the resume reviewer weighs most. Setup offers the packs in this folder (`pack:` in `jhs.yaml`); `none` uses general questions.

| Pack | For | Includes |
|---|---|---|
| [`ml-research`](ml-research/README.md) | machine learning engineers, applied and research scientists | keywords and 16 interview areas |

A pack is a folder with a `README.md`, `keywords.yaml` (titles, keywords, buzzwords to avoid, what the resume reviewer weighs) and `TOPICS.md` (interview areas, probe styles and readings for `mock-interview`; the format is described at the top of `tools/practice.py`, and `python tools/practice.py check <TOPICS.md>` checks it). Packs for other fields are welcome.
