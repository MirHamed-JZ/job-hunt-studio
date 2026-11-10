# Outreach

`/job-hunt-studio:outreach` finds people at the companies you name and drafts short messages for you to send yourself: a LinkedIn connection note, a message for after they accept, and an email when their address is public. It keeps a log of who you contacted, so nobody gets two cold messages and no follow-up is missed. It never sends, connects or signs in anywhere for you.

## Commands

| Say | What happens |
|---|---|
| `outreach Acme, Globex` (or `outreach Acme \| Paris`) | People and drafts for those companies, near your default location or the one you give |
| `outreach applied` | The same for companies you applied to that have no contact yet |
| `outreach log <name> <news>`, or "Sam replied" | Updates the contact and sets the next follow-up |
| `outreach status` | Follow-ups due |
| `outreach setup` | Your settings and the optional connections export; the first run asks once by itself |

## How people are found

Free public sources only, with no accounts or keys, and never LinkedIn's own pages:
1. **Your connections export** (optional): people you already know at the company come first.
2. **Paper authors** from OpenAlex, an open index of research papers, ranked by how close their papers are to your work (`outreach.topics`).
3. **GitHub**: public members and main contributors of the company's organizations.
4. **Web search** limited to LinkedIn, which returns public profile titles and short snippets, including people who list your schools or past employers (`candidate.schools`, `candidate.past_employers`); then news, talks and blogs.
5. **A paste from you**, when the rest falls short: a LinkedIn people search you run yourself, copied and pasted.

Claude picks 2 or 3 people per company, best first: someone you know there; someone on the team behind a role you applied to; a lead of a team that matches your work; an author of a paper close to yours; an alumnus or former colleague; a recruiter, only for a posted role. Each comes with where they were found and how sure that is (High, Medium, Low). Open each profile yourself before sending: people change jobs.

## The messages

Every fact about you comes from your Ledger and follows your hard lines; gap skills and never-print items never appear. The drafts go through the humanizer (if you installed it) and then the fact and voice check ([what it checks](RESUME_GUIDE.md#the-fact-and-voice-check)), before you see them. A number about the person you write to (the year of their paper) is checked too, and marked as being about them.

- **Connection note:** at most 200 characters. Free LinkedIn accounts get only a few notes a month, so Claude says when a note is worth it and when to connect without one and send the message after.
- **Message after they accept:** 60 to 120 words, one specific line about their work, one proof point from your Ledger, one clear ask (a short call, a referral to a named posting, or whether the team is hiring), never "do you have any role for me".
- **Introduction request:** when a target is a 2nd-degree connection, paste the mutual connections from their profile, and Claude drafts a note to the one you know best.

A send plan spreads new messages over the week (about 10 new people a week at most).

## Your connections export (optional)

On the LinkedIn desktop site: **Me** > **Settings & Privacy** > **Data privacy** > **Get a copy of your data** (or https://www.linkedin.com/mypreferences/d/download-my-data); choose **Want something in particular?**, tick **Connections**, then **Request archive**. LinkedIn emails a link, usually within 10 minutes. Unzip it and put `Connections.csv` in `applications/outreach/private/` (git ignores that folder; nothing is uploaded). Runs remind you when the file is more than 90 days old.

## Files

In `applications/outreach/`:

| File | What it holds |
|---|---|
| `OUTREACH_<date>.md` | One run: per company, the context; per person, title, team, why them, a shared tie, the public link; then the send plan |
| `OUTREACH_<date>_messages.md` | The drafts only, which is what the fact check reads |
| `CONTACTS.md` | Everyone contacted: name, company, title, found via, channel, status, last date, next action, notes |
| `private/Connections.csv` | Your connections export (optional, never committed) |
| `raw/` | What the people search found, one file per company and run (never committed) |

Statuses: `Drafted`, `Sent`, `Accepted`, `Replied`, `Referred`, `Declined`, `No reply`. One follow-up `applications.followup_days` (7 by default) after `Sent` or `Accepted` without a reply; after that, `No reply` and no more messages.

## Why this approach

- **Referrals help.** In one large firm's records, referred candidates were more likely to be hired and stayed longer (Brown, Setren and Topa, *Journal of Labor Economics*, 2016).
- **New, weak ties matter.** Randomized experiments on 20 million LinkedIn users found that moderately weak ties drive job moves, more so in digital industries (Rajkumar et al., *Science* 377, 2022). A new contact at a company is that kind of tie.
- **Replies are rare, so aim well.** There is no rigorous study of job seekers messaging managers; plan on roughly one reply per 5 to 10 well-targeted messages. A specific ask to a relevant person beats a generic one.
- **LinkedIn's rules.** Its User Agreement (section 8.2) forbids scraping and automated activity. Here, you browse and send; Claude only reads public search results and what you paste.
