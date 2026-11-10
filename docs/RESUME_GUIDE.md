# Resume writing guide

The rules every resume follows, the base and each tailored copy. Facts and their exact wording come only from your Ledger's current facts (section 0; see [LEDGER_FORMAT.md](LEDGER_FORMAT.md)). Your own layout decisions (what to cut first, header wording, lines kept in reserve) live in your workspace's `docs/Resume_Notes.md`. The review rubric ([REVIEW_RUBRIC.md](REVIEW_RUBRIC.md)) says how a resume is judged.

## What a bullet is for

A bullet shows what the work was and why it matters to the next employer. Write it so it transfers: what you built, what changed because of it, one strong number. Leave methods, subsets and caveats for the interview and the Ledger. A simpler true phrasing beats a complete technical one, but a number or claim is never broader than its source.

## Bullets

- **Formula:** "Accomplished [X] as measured by [Y], by doing [Z]" (Laszlo Bock, Google). Start with a strong verb, give the result with a number, then say how.
- **STAR is for interviews.** On the page, compress the situation and task into a few words and keep the action and result. Each bullet should still map to a story you can tell.
- **Lead with impact** where it fits: "Cut X by 40% by ...". For a design bullet, say what was built and why it matters, then the strongest evidence.
- **Give a baseline** so the number means something: "from 6 hours to 1.5 hours", "+3.1% over the production scorer".
- **Verbs:** vary them within a job. Never "helped with", "worked on", "responsible for".
- **Mechanics:** no pronouns; digits for numbers; one or two lines with no single word alone on the last line; past tense for finished work, present tense only for ongoing duties.
- **Final periods:** every bullet ends with a period, or none does. Periods are the default.
- **Order:** the most impressive bullet first within each job.

## Summary (optional)

Two or three connected sentences: who you are and your years of experience, what you built and why it mattered, what sets the work apart. No generic phrases ("passionate", "results-driven", "team player") and no list-like tails. If your Ledger has an approved `[summary]`, use it word for word unless a tailoring proposal changes it with your OK.

## Skills

- Tools, frameworks and domain areas, not methods; methods belong in bullets, where they have context.
- Every item passes the interview test: you can discuss it for 2 to 3 minutes with a specific example (Ledger `[skills-claimed]`). Gaps (`[skills-gaps]`) never appear. Other names for a skill only as approved in `[skill-paraphrases]`.
- Standard category names; each term once; no office tools, operating systems, soft skills or skill bars.
- Skills lines are keyword lists: no final period.

## Publications

One citation style throughout: authors (your name in bold), the title (linked when there is a public link), the venue in italics with the year and status. Venue and status exactly as Ledger `[publications]` allows. When a paper has several versions with different results (a preprint and the accepted version), every number comes from the version the text names or links.

## What applicant tracking systems need

- A text PDF from LaTeX, one column, standard section names, contact details in the page body.
- Dates as "Mon YYYY – Mon YYYY" (in LaTeX: `Sep 2022 -- Present`); a date range is the one place an en dash is used.
- Spell out each key acronym once next to its short form ("learning to rank (LTR)") so a search for either matches.
- In a tailored copy, use the posting's exact term where it is true ("ranking models" for "learning to rank" only if that paraphrase is approved).
- Send the file named in `jhs.yaml` `resume.output_name`, never the build name.

`/job-hunt-studio:review-resume` checks all of this with two text engines (`tools/ats_check.py`).

## Layout

- One page unless `resume.pages` says otherwise; one column; at most one accent colour; a 10 to 11 pt body font.
- Dates at the right margin are fine: the included layouts use `\datefill`, which keeps each date in reading order for text extraction.
- The header city is where you live, optionally with "(open to relocation)" or "(relocating to <city>)" when true. Never a city you do not live in.

## Tailoring

- A tailored copy starts from the latest approved version (its git tag), never from the working base file, and changes only that copy.
- Add only true lines: Ledger facts, or the reserve lines in `docs/Resume_Notes.md`.
- When a line must go to stay on the page, follow the cut order in `docs/Resume_Notes.md`; if it has none, cut the weakest bullet of the oldest job first.
- Never add a gap skill, a never-print item, or wording a hard line forbids, whatever the posting asks for.

## The fact and voice check

`tools/fact_check.py` compares the resume with the Ledger and warns about: numbers or dates not in Ledger section 0 (a duration must match with its unit: "6 years" is not backed by "6 hours"), titles or dates that differ from `[roles]`, hard-line wording, gap skills, never-print items, dashes and stock phrases. It never fails a build, but a resume is READY only when every warning is fixed or acknowledged. Acknowledge a true one (for example "5+ years", counted from your `[roles]` dates) with a comment line in the `.tex`, citing the Ledger:

```
% fact-ok: 5+ | years counted from the [roles] dates (Sep 2021 to present)
```

In Markdown or text files (cover letters, form answers, messages), use `<!-- fact-ok: 5+ | ... -->`. A reason that names no Ledger block (`[roles]`) or dated entry is ignored. In a message, cover letter or form answer, a number or date about the person or company you write to (the year of their paper, a figure from the posting) is not a claim about you: acknowledge it with `[recipient]`, for example `<!-- fact-ok: 2025 | [recipient] the year of their paper -->`; this works only for numbers and dates, never for a duration ("6 years" is about you), never on a resume or LinkedIn text, and in a cover letter or form answer only for a number or date that the application's `posting.md` contains.

Some warnings are never acknowledged, only fixed: a gap skill, a never-print item, a job title or date that differs from `[roles]` (if the Ledger is wrong, correct it with `update-ledger`), a dash or stock phrase (reword it), and leftover example content. A hard-line warning can be acknowledged only when the sentence keeps the rule ("evaluated offline, not deployed"), and the reason must name the rule id, which counts as the Ledger reference: `% fact-ok: deployed | HL-ranker-status: says it was not deployed`.

## Sources

- Laszlo Bock's XYZ formula, as reported by Inc. and Business Insider (2014 to 2016).
- Career-centre guides for data and ML resumes (Carleton University, University at Buffalo, University of Florida) and recruiter eye-tracking research (TheLadders, the "six-second scan").
