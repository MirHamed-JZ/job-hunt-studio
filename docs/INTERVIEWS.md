# Interviews: practice, debriefs and the claim gate

Two skills, with different jobs:
- `/job-hunt-studio:mock-interview` is practice. It asks like an interviewer, then teaches what your answer missed, and keeps track of what you have covered.
- `/job-hunt-studio:interview-drill` is a check. It decides whether a skill you learned may go on your resume.

## Practice: mock-interview

Type one of these after `/job-hunt-studio:mock-interview`, or say it in plain words ("quiz me on learning to rank", "prepare me for the Acme screen"):

| You type | What happens |
|---|---|
| a topic, for example `learning to rank` | 5 or 6 questions on it, from intuition to math to a scenario |
| `plan` (or nothing) | what you have covered and what is weak, then three suggested topics; you pick one |
| `cv` or `cv <section>` (a project, a role, `publications`, `skills`) | questions an interviewer asks about what is on your resume |
| `behavioral` | STAR questions (situation, task, action, result) from your own roles and projects |
| a company | a round for that application's next stage: recruiter screen, technical screen, system design or hiring manager; with no application, it asks for the posting or the role |
| `weak-spots` | your open weak spots again, asked differently |
| `debrief <company>` | right after a real interview: see below |

Add `realistic` to hold all feedback to the end, as in a real interview. Otherwise, after each answer you get a grade from 1 to 4 (3 is a pass at your level), what a strong answer covers, a short lesson on what you missed, a model answer of about 90 seconds, and the follow-ups an interviewer would ask next. A weak answer is asked again from another angle.

Answers about your own work are also checked against your Ledger: the numbers, the status of a project, your part versus the team's, your hard lines, and nothing confidential. When a question touches a skill you do not have yet, the model answer shows how to say so honestly.

**Topics.** A pack gives the list of areas and readings: the `ml-research` pack has 16 (machine learning basics, statistics, deep learning, evaluation, system design, ML coding, and field areas such as LLMs, retrieval, ranking, vision and speech). With `pack: none` in `jhs.yaml`, name any topic and practice still runs, without the list.

**What it keeps**, in your workspace:
- `interview/PRACTICE_LOG.md`: coverage per topic (shaky, passed once, or solid), open weak spots, the last 15 rounds, and a story bank of your best answers about your own work.
- `interview/notes/<area>.md`: what you missed, with model answers, as a revision sheet.
- For an application, a line in its `timeline.md`.

It commits these locally after each round.

## After a real interview: debrief

Run `/job-hunt-studio:mock-interview debrief <company>` the same day if you can. You give your notes in one message: who interviewed you, the questions as close to word for word as you remember, how each answer went, and what they said about next steps and the next round (format, tools allowed, a take-home and its deadline). You get:
- the questions sorted by topic, with a short outline of a strong answer for each one that went badly;
- a correction for anything you said that does not match your Ledger, so you say it right next time;
- the application's timeline, tracker status and follow-up date updated, and the weak spots added to your log;
- a short prep list for the next round, and an optional thank-you note (a few lines: thanks and the next step), checked against your Ledger. You send it yourself.

A real interview is never graded, and nothing is guessed about what the interviewers thought.

## The claim gate: interview-drill

A skill you are learning stays in your Ledger's `[skills-gaps]` and off every document until two things are true: you built something with it, and you can discuss it for two or three minutes with an example from that work.

`/job-hunt-studio:interview-drill <skill>` runs only when you type it. It reads your project (a Ledger project, a repository, your notes), then asks five hard questions about it, one at a time: what you built and why, a decision and its alternative, what failed, how you measured it, and how the skill works underneath. You pass with a specific example and sound reasoning on at least 4 of 5.

The result goes in `interview/CLAIM_GATE.md`. On a pass you get the `[skills-claimed]` row and resume wording to approve; then run `/job-hunt-studio:update-ledger <skill> passed the drill on <date>, project <name>` to move it (the drill never edits your Ledger). A resume change then becomes a new version, reviewed and approved as usual. If your project shows a narrower skill than the one you named (a small embedding model rather than an LLM), the drill judges the narrower one, and only that one moves. Without a project, the drill stops and suggests a small one that would count.
