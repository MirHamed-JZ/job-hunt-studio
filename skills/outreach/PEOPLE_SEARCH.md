# Finding people: the free playbook

How outreach step 3 finds people at a company with free, keyless sources only: no paid data services, no accounts, and never linkedin.com itself. Run the layers in order and stop once you have 2 or 3 strong people.

## Layer 1: the script

```
<workspace Python> ${CLAUDE_PLUGIN_ROOT}/tools/find_people.py "<Company>" [--location <City>] [--github <org>] [--institution I<id>]
```

Several companies at once: `"Acme, Globex"` (then `--github` and `--institution` cannot be used). One run costs about $0.003 of OpenAlex's small keyless daily budget, so dozens of companies a day fit. It prints a markdown summary and saves `applications/outreach/raw/people_<company>_<date>.json` (git ignores it).

| Source | Finds | Watch for |
|---|---|---|
| `connections` | The user's first-degree LinkedIn connections at the company, from their export (`outreach.connections_csv`; optional, added through outreach setup). Other names of a company come from `outreach.aliases` | The company is as of the export date; the run reports the file's age and flags it after 90 days |
| `research` | OpenAlex authors with the company as their affiliation, ranked by papers whose titles match `outreach.topics`, last-author papers (often team leads) and recency | People from community or academic programs and people who have left still carry the affiliation; skip authors with no on-topic paper unless the company barely publishes. Companies that do not publish return little or noise |
| `github` | Public members of the company's GitHub organizations and the main contributors to its most active repositories, with name, company, location and website from their profiles | Detected organizations can be wrong (`(detected; check)`); pass `--github` when you know the organization. "Low (profile names X)" usually means the person left |

If the script names the wrong OpenAlex institution, run it again with `--institution` set to one of the `other_matches` ids in the JSON.

## Layer 2: web search

The script prints the queries for the company.

- `site:` inside the query is ignored. Restrict domains with the WebSearch `allowed_domains` parameter instead: with `["linkedin.com"]`, results are indexed LinkedIn profiles as titles ("Name - Company") and snippets (current title, recent posts such as "we're hiring in my team").
- Use only the search result titles and snippets. Never fetch a linkedin.com address, never open LinkedIn in a browser tool, never page through LinkedIn: LinkedIn's User Agreement (section 8.2) forbids it, and the user's account is the one at risk.
- Shared ties: the script adds one LinkedIn-domain query per school and past employer in `candidate.schools` and `candidate.past_employers`. Treat a tie as a fact only when the snippet shows it, and check that the company is the person's current one, not a past job.
- News, press releases, conference speaker pages, podcasts and engineering blog bylines name directors and team leads that profile snippets miss.
- TheOrg (`allowed_domains: ["theorg.com"]`) lists executives; it rarely reaches team leads, so it is the last query.
- Cross-check: for the best 3 to 5 people from layer 1, search `"<Name>" <Company>` with the LinkedIn domain to get their current title and profile link. A person found by two independent sources moves up.
- If WebSearch is not available in this session, say so and go to layer 3.

Budget: about 10 to 15 searches per company.

## Layer 3: a paste from the user (30 seconds)

When layers 1 and 2 give fewer than two people of the top two kinds (someone on the team behind a role the user applied to, or a manager or lead of a matching team), ask once, with the exact requests the script prints:

- a LinkedIn people search (current company, location, keywords for the user's field, then "manager"): select all on the results page, copy, paste;
- their school's LinkedIn alumni page filtered to the company;
- "Meet the hiring team" on the posting they applied to.

Read names, headlines, locations and mutual connections from the paste. A person browsing and pasting is ordinary use, not automation.

After the hand-over, for any target shown as 2nd degree, the user can paste the "mutual connections" list from that person's profile; SKILL.md step 7 turns the one they know best into an introduction request, which beats a cold note.

## Merge and rank

One row per person (merge the same person across sources by name plus company). Give each a confidence:

- **High:** in the user's connections export; named in the posting or its "Meet the hiring team"; or found in two independent sources with a current title.
- **Medium:** one source showing the company now: a LinkedIn snippet, a paper with the affiliation in the last 12 months, a GitHub profile naming the company, a dated talk or article from the last 12 months.
- **Low:** older evidence, an inferred team, or a profile that names another company.

Then rank by the value order in SKILL.md step 3 (a connection, an introduction through a mutual connection, the team behind an applied role, a matching team lead, a paper author close to the user's work, a shared tie, a recruiter for a posted role); a shared tie lifts a person within their kind, and confidence breaks the remaining ties. Never draft for a Low person without saying why; the user opens every profile and confirms the person is still there before sending.
