# Finding jobs

`/job-hunt-studio:find-jobs` looks for new postings at the companies you watch, keeps the ones that fit your settings, ranks them against your Ledger, and has Claude read the best ones and sort them into Strong, Possible and Skip. You pick; then `apply-job` scores each pick in depth. It never applies for you.

## First: companies to watch

The scan reads the public job boards that many companies publish through Greenhouse, Lever or Ashby. These boards are made to be read by anyone, so no account or key is needed.

Add a company: `/job-hunt-studio:find-jobs add Acme`. Claude finds its board, shows a few of its open postings so you can check it is the right company, and adds it to `search.watchlist` in `jhs.yaml`. If no board is found, the company uses another system (Workday, SmartRecruiters, its own site); open its careers page, and paste any posting link into `apply-job` instead.

## What a run does

| Step | What happens |
|---|---|
| Fetch | Every open posting at the watched companies; LinkedIn and Indeed too, only if you chose JobSpy at setup |
| Clean | Each description passes the posting guard: hidden text and invisible characters removed, instruction-like lines quoted |
| Filter | Your target titles (`target.titles`, `target.exclude_titles`), the level a title shows (intern, junior, mid, senior, staff) against `target.seniority.levels`, the years of experience asked against `target.seniority.max_years_required`, your location tiers, and age (postings older than `search.max_age_days`; 180 days on company boards, where a listed posting is still open) |
| Score | Overlap with your Ledger: +3 for each claimed skill (or an approved paraphrase), +1 for each term of your pack that your evidence mentions, -2 for each gap skill the posting names |
| Flag | A senior title without years stated, a language requirement, a work authorization or residence requirement, a PhD requirement, anything the posting guard removed, a very short description |
| Hide | Postings already in your tracker, and leads shown in earlier runs (`all` shows them again) |
| Triage | Claude reads the top leads against your Ledger and marks each **Strong**, **Possible** or **Skip**, with what you miss and any blocker |

The score is a screen, not a fit score: `apply-job` scores a posting properly, against your evidence and your approved resume.

## Location tiers

`search.tiers` in `jhs.yaml` lists where you want to work, best first. A posting goes into the first tier it matches:
- **Place names** (`location_regex`, separated by `|`): a posting whose location names one of them, whatever the work type.
- **Remote** (`remote_ok: true`): a remote posting whose location names one of `remote_regions`. A posting that says only "Remote" is kept when its description names one of your regions, with a flag to confirm it hires there.

Example: tier 1 `lyon|villeurbanne`; tier 2 remote, regions `France`, `EU`, `Europe`; tier 3 `paris`. A Paris office job lands in tier 3, a remote job open across the EU in tier 2, and a "Remote, US only" job is dropped.

## Commands

| Say | What happens |
|---|---|
| `find-jobs` | Full run (about a minute; about 10 with JobSpy) |
| `find-jobs quick` | Company boards only |
| `find-jobs tiers 1,2` | Only those tiers |
| `find-jobs all` | Also show leads from earlier runs |
| `find-jobs reuse` | Re-filter today's scan after a settings change, without fetching again |
| `find-jobs add <company>` | Watch a company |

## Tuning

Too many leads, or the wrong ones? Change `target` (titles, exclusions, levels, years) or `search` (`min_score`, the threshold under which leads are listed separately; `extra_keywords`, your own terms with points, negative to push postings down), then run `find-jobs reuse` to see the effect at once.

## LinkedIn and Indeed (JobSpy)

Off unless you chose it at setup, because LinkedIn's User Agreement (section 8.2) forbids scraping and automated access: turning it on is your decision and your account's risk. It uses the third-party [JobSpy](https://github.com/speedyapply/JobSpy) library, which Job Hunt Studio does not include. To change your answer, run `/job-hunt-studio:setup options`. Without it, you can still bring any LinkedIn or Indeed posting to `apply-job`: paste an Indeed link, or the text of a LinkedIn posting (Claude never opens LinkedIn links).

## Files

In `applications/leads/`: `LEADS_<date>.md` (the ranked list with the triage), `seen.json` (leads already shown), and `raw/` (the cleaned descriptions; git ignores it).
