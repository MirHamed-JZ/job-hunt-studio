# Applications: folders and tracker

How `/job-hunt-studio:apply-job` keeps each application in your workspace. You rarely touch these files by hand.

## The flow

Paste a posting (or its link) into a session, or run `/job-hunt-studio:apply-job <text or link>`. For a LinkedIn posting, paste its text: Claude never opens LinkedIn links. Claude always waits for you at stages 2 and 4, and at stages 3 and 5 only when they apply:

| Stage | What happens | Stop |
|---|---|---|
| 1. Score | The posting guard saves a clean copy; two scores (what your Ledger supports, and what a recruiter sees on your approved resume), strengths, gaps, red flags | |
| 2. Propose | The resume edits that would matter, each with exact before and after text and the Ledger fact behind it | **You reply OK or ask for changes** |
| 3. Build | A tailored copy of your approved resume with only the approved edits, reviewed until READY | only if a reviewer fix goes beyond what you approved |
| 4. Hand over | The PDF path, form answers that need care | **You submit, then say so** |
| 5. Cover letter | Only when asked or required | You edit or approve |
| 6. Record | Status `Applied`, the date, which resume, a follow-up date | |
| 7. Update | "Acme: phone screen on Friday" updates the status, the timeline and the next follow-up | |

Other uses: `apply-job applied <company>` (or "I applied to Acme"), `apply-job update <company> <news>`, `apply-job status` (open applications and follow-ups due). A folder name alone continues an application where it stopped, so a session can end at any stop.

## One folder per posting

`applications/<Company>_<Role>_<YYYY-MM-DD>/`, short CamelCase names, the date it was scored, for example `Acme_MLEngineerRanking_2026-03-20/`.

| File | What it holds |
|---|---|
| `posting.md` | The posting as the posting guard saved it: clean text, link, date (postings disappear) |
| `posting_hidden.txt` | Hidden text the posting guard removed, for you to read (only when there was some; not committed) |
| `analysis.md` | The scores and, at the end, `## Proposed tailoring` as you approved it |
| `<Company>_<Role>_<date>.tex` | The tailored copy |
| `changes.md` | What changed against the approved version, and why |
| `diff_vs_v<N>.tex` | Change-tracked LaTeX against the approved version (when latexdiff is installed) |
| `form_answers.md` | Drafts for form questions that need care |
| `cover_letter.md` | Only when one was needed |
| `timeline.md` | One dated line per event |
| `thank_you_<date>.md` | The thank-you note from an interview debrief |
| `build/<resume.output_name>` | The PDF to send, and the review report (not committed) |

## TRACKER.md

One row per posting: company and role, folder, status, score (evidence fit / resume fit), resume (the tag, tailored or unchanged), applied date, next follow-up, notes.

Statuses: `Scored`, `Do Not Apply`, `On hold`, `Ready to submit`, `Applied`, `Followed up`, `Screen`, `Interview`, `Offer`, `Rejected`, `Withdrawn`, `Closed (no response)`.

Follow-ups: `applications.followup_days` in `jhs.yaml` (7 by default) after applying, after a follow-up and after a screen, unless you give another date; none once a row is closed.
