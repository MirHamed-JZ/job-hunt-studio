# Resume review rubric

Used by the `cv-reviewer` agent through `/job-hunt-studio:review-resume`. A resume is **READY** when every gate passes, the weighted score is at least `review.ready_threshold` in `jhs.yaml` (85 by default), and no category is rated below 3.

House rules: [RESUME_GUIDE.md](RESUME_GUIDE.md). Facts: the workspace's `docs/Evidence_Ledger.md`. Field emphasis: the pack named in `jhs.yaml` (`packs/<pack>/keywords.yaml`), when there is one. This file says only how to judge.

## Gates (any failure means NOT READY)

| Gate | How it is checked |
|---|---|
| G1 Truthful | Every number, status, title, date and skill traces to Ledger section 0 (newest entry wins). No wording a `[hard-lines]` rule forbids, no `[skills-gaps]` skill, no `[never-print]` item. Every warning of the fact and voice check is fixed or acknowledged with a reason that holds up against the Ledger. |
| G2 Parses | `tools/ats_check.py` PASS on both engines: contact details, standard headings, each entry's dates next to it, clean characters. |
| G3 Mechanics | `tools/resume_lint.py` has no FAIL (example content removed, page count, pronouns, final periods consistent, email present, links open; LinkedIn links are never requested by a tool, so open yours once by hand). |
| G4 Submission file | The page count matches `resume.pages`, and `build/<resume.output_name>` is the latest build. |

## Scored categories (1 to 5 each; weight in brackets; weights sum to 100)

1. **Six-second scan [15].** In the top third, can a recruiter see the target title, years of experience, the current employer and the strongest results? If there is a summary, is it specific, with no generic phrases?
2. **Impact bullets [20].** Each bullet: action verb, outcome, a measure with a baseline, the method. Outcomes before mechanics. Numbers mean something to a non-specialist. Verbs vary within a job. One or two lines, no orphan word.
3. **Clarity for a non-specialist [10].** A recruiter understands each bullet: jargon only where it is also a keyword; acronyms spelled out once; project names say what the work is for.
4. **Role fit [20].** Shows what hiring managers for the roles in Ledger `[positioning]` look for. With a pack, judge against its `rubric_emphasis` list and the coverage of its `keywords` that the candidate can claim (absent ones are noted, never added). For a tailored copy, judge against the posting's requirements in the application's `analysis.md`.
5. **Skills section [10].** Tools and domains, not methods; standard category names; no fillers; each term once; every item backed in `[skills-claimed]` or `[skill-paraphrases]`.
6. **Publications or projects [5].** One citation style; statuses and venues exactly as the Ledger allows; titles linked where public. Rate 5 when the section is rightly absent.
7. **Layout and consistency [5].** One column, standard section names, one date format, consistent punctuation and capitalization, the same term for the same thing everywhere, balanced white space.
8. **Visual hierarchy [10].** Judged on the rendered page and the blurred squint image from `tools/visual_check.py`: each job, project and section still stands out as its own block; no text block much taller than about 10% of the page; ink coverage near the reference (the original Jake's Resume, about 5%; a dense page is about 9%); one accent colour at most.
9. **Application readiness [5].** File named as `resume.output_name`; PDF title set; contact details complete as `jhs.yaml` lists them; nothing from `[never-print]`.

**Score** = sum over categories of (rating / 5 × weight).

## Report format

1. Verdict line: READY or NOT READY, the score, the gate results, the visual metrics (ink, blocks, longest block).
2. Table: category, rating, one-line reason.
3. Fixes, most important first, each quoting the current text exactly and giving a replacement that stays true to the Ledger and fits the page budget (if it adds a line, say what to cut). Mark each FIX (required) or CONSIDER (optional).
4. Fact and voice warnings: for each one still open, whether to fix it (with the fix) or acknowledge it (with the Ledger block that supports it).
5. Strengths to keep (3 to 5), so later edits do not break them.
6. Truthful gaps: skills the target roles ask for that are in `[skills-gaps]`, named as gaps, never as fixes.

## Sources

- Visual reference: Jake's Resume (github.com/jakegut/resume, MIT), compiled as `tools/assets/reference_jakes_resume.pdf`.
- Laszlo Bock's XYZ formula; recruiter eye-tracking research (TheLadders); career-centre guides for technical resumes (Carleton University, University at Buffalo).
