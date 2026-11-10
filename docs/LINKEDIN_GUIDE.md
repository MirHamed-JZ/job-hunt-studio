# LinkedIn guide

The rules `/job-hunt-studio:linkedin-refresh` follows when it writes your LinkedIn text. Facts come only from your Ledger. Tags: **[LI]** LinkedIn's own documentation; **[Practice]** consistent advice from career offices and recruiters; **[Default]** a choice made here that you can change by telling Claude. Lengths LinkedIn does not document are marked unverified.

## How it works

Run `/job-hunt-studio:linkedin-refresh`, or name one field (`headline`, `about`, `experience`, `skills`). It compares your current profile (`linkedin/PROFILE.md`, or a profile PDF you saved into `linkedin/`, or text you paste) with your Ledger and asks about every difference; a true new fact is recorded with `update-ledger` first, and a fact for LinkedIn only goes to `[platform-facts]`. The draft, with character counts, goes to `linkedin/LINKEDIN_<date>.md`, checked by the humanizer (if installed) and the fact and voice check ([what it checks](RESUME_GUIDE.md#the-fact-and-voice-check)). You paste it by hand, then run `linkedin-refresh updated` so `linkedin/PROFILE.md` matches your live profile.

## Purpose

- LinkedIn is where a recruiter checks who you are after a search hit or a resume. It should read like a person telling a short story about their work, not the resume pasted in: "complement your resume rather than repeat it" (MIT CAPD). [Practice]
- The resume proves; LinkedIn invites. Baselines and the full set of numbers stay on the resume and in interviews; on LinkedIn, say what the work was, why it mattered and where it stands, in plain words. [Default]
- Facts match the resume exactly: titles, dates, venues, statuses. LinkedIn may add context, never a new claim. Facts allowed on LinkedIn only (an older role, a volunteer position) live in the Ledger's `[platform-facts]`. [Practice]

## Headline (220 characters at most [LI])

- **Pattern:** a standard job title, then your specialty, then one or two searchable terms; three or four parts separated by " | ". More reads as keyword soup. [Practice]
- **Standard title first.** "Standard job titles may be boring, but they are what other members search for" [LI]. Use the title in your Ledger `[identity]`.
- **Front-load:** title and main specialty in the first 60 to 80 characters, roughly what search cards show (unverified).
- **Specialty in recruiter vocabulary:** the methods and domains people search for, not internal project names.
- **No number in the headline:** numbers need context, so they live in About and Experience. [Default]
- **Never:** self-describing adjectives (passionate, innovative, results-driven, expert), emojis, hashtags, strings of acronyms, "Aspiring", "Open to work", "Seeking opportunities". [Practice]

## About (2,600 characters at most [LI])

- **Shape:** first-person prose, one short paragraph per idea, a blank line between paragraphs; 900 to 1,600 characters. Not a list of results. [Default]
- **The first sentence stands alone.** Only the first two or three lines show before "see more" (length unverified): who you are and what you build, or the problem you work on. Never "My name is", never a buzzword. [LI]
- **Arc:** who you are and what you build; one paragraph per main project, each with the same rhythm (what it is and why it matters, how it was checked, where it stands now); earlier work in one sentence; the kind of work that interests you, in general terms; links (a portfolio, Google Scholar).
- **Keywords:** each project in two or three sentences built around the terms recruiters search (from your pack's keywords and the postings you target), and only terms your Ledger supports. A few searchable terms in natural sentences help; stuffing does not: "Adding more keywords to your profile doesn't automatically improve your appearance in search results" [LI].
- **Numbers:** one or two in the whole About, public ones only. Qualitative wording is the default. [Default]
- **Tone:** write how you speak; cut jargon a recruiter cannot parse; read it aloud and cut template phrases ("at the intersection of", "leveraging cutting-edge", "passionate about", groups of three adjectives). [Practice]
- **The job search stays quiet:** describe the work that interests you; never "open to work", "seeking", "next chapter". [Practice]

## Experience (about 2,000 characters per description; the form's counter wins if LinkedIn changes it)

- **Recent role:** one line of context (the team, what it builds), then each main project with two or three short outcome bullets. Tag five or six skills on the role; they feed the Skills section [LI].
- **Older roles:** one or two sentences, outcome first, mostly qualitative.
- Outcomes, not duties; first person or no pronoun, the same throughout. Bullets with or without final periods, one style throughout.
- Recruiter search matches words in titles and descriptions [LI], so use the real terms of the work.
- Attach a paper or project link to the role when one is public. [Practice]
- Same titles, dates and status wording as the resume.

## Education, publications, featured, volunteering

- **Education:** degree, school and dates as in `[roles]`; a thesis or honors only if the Ledger has them.
- **Publications:** each paper in `[publications]` with its link; venue and status exactly as allowed there; co-authors in order; one line on your part.
- **Featured:** two or three items at most, each one you can defend for three minutes. [Practice]
- **Volunteering and organizations:** from `[roles]` or `[platform-facts]`.

## Skills (up to 100; up to five Top skills [LI])

- Your `[skills-claimed]` and approved paraphrases, plus true extras you confirm you could discuss with an example. Nothing from `[skills-gaps]`. [Default]
- Top skills: the five a recruiter for your target roles searches first. "Skills are among the most common queries performed by recruiters" [LI].

## Settings and editing

- Before editing, turn off **Share profile updates** (Settings & Privacy > Visibility > Visibility of your LinkedIn activity), and "Notify network" in any edit form that shows it. Viewers still see saved edits, so make them in one sitting. [LI]
- **Open to Work:** "Recruiters only" visibility, never the public photo frame while employed. LinkedIn tries to hide it from recruiters at your current employer but "can't guarantee complete privacy" [LI].
- A custom profile URL, a professional photo and a simple banner help credibility. [LI]
- Edit by hand. LinkedIn's User Agreement (section 8.2) forbids bots and unauthorized automated methods, so no tool edits your profile. [LI]
- Afterwards, tell Claude what you pasted (or save the profile as a PDF again), so `linkedin/PROFILE.md` matches what is live.

## Checklist before pasting

1. Every fact traces to Ledger section 0 and matches the resume; `/job-hunt-studio:audit-claims` passes.
2. Headline: title first, at most four parts, no number, 220 characters or fewer.
3. About: the first sentence stands alone; 900 to 1,600 characters; one or two public numbers at most; no banned adjectives or job-seeking phrases.
4. No em dashes, en dashes or double hyphens.
5. Settings: profile-update sharing off; Open to Work for recruiters only.

## Sources

- LinkedIn Help Center (checked 2026-10): search appearance tips (a521944), profile best practices (a554351), Open to Work (a507508), sharing profile updates (a529062), Skills (a549047). Recruiter Help: keyword stuffing (a524188), where keywords match (a415295). Talent Blog: headline examples and the 220-character limit (2025-02-27); profile summaries, the 2,600-character limit and "Make your first sentence count" (2024-04-30). User Agreement, section 8.2 (effective 2025-11-03).
- Practice: the MIT Career Advising and Professional Development LinkedIn guide; recruiter and career-office advice on LinkedIn versus resume experience sections and on overused words.
- The "see more" cut-off and the length a search card shows come from third-party estimates and are unverified.
