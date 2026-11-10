"""Check that a skill has what it needs before it starts: settings, Ledger blocks, files, tools.

Usage (from the workspace folder, with the workspace Python):
    .venv/Scripts/python <plugin>/tools/preflight.py <skill> [--tex PATH]      (Windows)
    .venv/bin/python     <plugin>/tools/preflight.py <skill> [--tex PATH]      (macOS, Linux)

Prints one line per check: OK, WARN (the skill runs, with a limit it states) or MISSING (the skill stops and
names the fix). A Ledger block that still holds setup placeholders counts as missing. Exit code 0 when
nothing is missing, 1 otherwise. Skills: update-ledger, audit-claims, score-job, tailor-resume, tailor-base,
apply-job, compile-resume, review-resume, approve, find-jobs, find-jobs-add, outreach, mock-interview (topic, plan
and weak-spots modes), mock-interview-cv (cv, behavioral, application and debrief modes), interview-drill,
linkedin-refresh.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import ConfigError, have, latest_tag, load, utf8_stdout  # noqa: E402
from ledger import anchors, hard_lines, is_pending  # noqa: E402

SETUP = "/job-hunt-studio:setup"

# Ledger block -> the setup section that fills it
BLOCK_FIX = {
    "positioning": "ledger", "identity": "ledger", "roles": "ledger", "publications": "ledger", "summary": "ledger",
    "hard-lines": "hard-lines", "never-print": "hard-lines",
    "skills-claimed": "skills", "skills-gaps": "skills", "skill-paraphrases": "skills",
}
# jhs.yaml key -> the setup section that sets it
KEY_FIX = {"candidate": "profile", "target": "search", "search": "search", "resume.template": "options",
           "resume": "profile", "review": "profile"}

FACT_BLOCKS = ["identity", "roles", "skills-claimed", "skills-gaps", "hard-lines", "never-print"]
NEEDS = {
    "update-ledger": dict(keys=[], blocks=[], optional=[], tools=[], resume=None),
    "audit-claims": dict(keys=["candidate.name"], blocks=["roles", "skills-claimed", "skills-gaps", "hard-lines",
                                                          "never-print"],
                         optional=["publications", "skill-paraphrases"], tools=[], resume=None),
    "score-job": dict(keys=["candidate.name", "target.titles", "search.tiers"],
                      blocks=["positioning", "roles", "skills-claimed", "skills-gaps", "hard-lines"],
                      optional=["publications", "summary", "skill-paraphrases"], tools=[], resume="approved-optional"),
    "tailor-resume": dict(keys=["candidate.name", "candidate.email", "resume.base_tex", "resume.tag_prefix"],
                          blocks=["positioning", *FACT_BLOCKS], optional=["publications", "summary",
                                                                          "skill-paraphrases"],
                          tools=["latexmk"], resume="approved"),
    "tailor-base": dict(keys=["candidate.name", "candidate.email", "resume.base_tex", "resume.tag_prefix"],
                        blocks=["positioning", *FACT_BLOCKS], optional=["publications", "summary",
                                                                        "skill-paraphrases"],
                        tools=["latexmk"], resume=None),
    "compile-resume": dict(keys=["candidate.name", "resume.base_tex"], blocks=[], optional=["roles"],
                           tools=["latexmk"], resume="tex"),
    "review-resume": dict(keys=["candidate.name", "candidate.email", "resume.base_tex", "resume.tag_prefix"],
                          blocks=FACT_BLOCKS, optional=["publications", "summary", "skill-paraphrases"],
                          tools=["latexmk", "pdftotext", "pdfinfo", "pdftoppm"], resume="tex"),
    "approve": dict(keys=["candidate.name", "resume.base_tex", "resume.tag_prefix"], blocks=[], optional=[],
                    tools=["latexmk", "git"], resume="base"),
}
NEEDS["apply-job"] = NEEDS["score-job"]
NEEDS["find-jobs"] = dict(keys=["target.titles", "search.tiers"],
                          blocks=["positioning", "skills-claimed", "skills-gaps"], optional=["skill-paraphrases"],
                          tools=[], resume=None)
NEEDS["find-jobs-add"] = dict(keys=[], blocks=[], optional=[], tools=[], resume=None)
NEEDS["mock-interview"] = dict(keys=["candidate.name"], blocks=["positioning"],
                               optional=["skills-claimed", "skills-gaps", "skill-paraphrases"], tools=[], resume=None)
NEEDS["mock-interview-cv"] = dict(keys=["candidate.name", "resume.base_tex", "resume.tag_prefix"],
                                  blocks=["positioning", *FACT_BLOCKS],
                                  optional=["publications", "summary", "skill-paraphrases"], tools=[],
                                  resume="approved-optional")
NEEDS["interview-drill"] = dict(keys=["candidate.name"], blocks=["skills-claimed", "skills-gaps", "hard-lines"],
                                optional=["skill-paraphrases"], tools=[], resume=None)
NEEDS["linkedin-refresh"] = dict(keys=["candidate.name"],
                                 blocks=["positioning", "identity", "roles", "skills-claimed", "skills-gaps",
                                         "hard-lines", "never-print"],
                                 optional=["publications", "summary", "skill-paraphrases", "platform-facts"],
                                 tools=[], resume="approved-optional")
NEEDS["outreach"] = dict(keys=["candidate.name"], blocks=["positioning", "roles", "skills-claimed", "skills-gaps",
                                                         "hard-lines", "never-print"],
                         optional=["publications", "summary", "skill-paraphrases", "platform-facts"], tools=[],
                         resume=None)

TOOL_FIX = {
    "latexmk": "a TeX distribution with latexmk (MiKTeX plus Strawberry Perl on Windows, MacTeX, or TeX Live); "
               f"{SETUP} tools explains, then restart Claude Code",
    "pdftotext": "Poppler (MiKTeX ships it; on macOS `brew install poppler`, on Linux `poppler-utils`); without it the checks read the PDF with pypdf",
    "pdfinfo": "Poppler (as pdftotext); without it the page count comes from pypdf",
    "pdftoppm": "Poppler (as pdftotext); without it the visual check is skipped",
    "git": "Git (git-scm.com)",
}
OPTIONAL_TOOLS = {"pdftoppm", "pdftotext", "pdfinfo"}
# What a skill does when the optional approved resume is missing
NO_APPROVED = {
    "mock-interview-cv": "No approved resume yet: resume questions come from the base draft if one exists, else "
                         "from the Ledger",
    "linkedin-refresh": "No approved resume yet: the LinkedIn text is written from the Ledger alone (titles and "
                        "dates must match the resume you send, so approve one first if you can)",
}


def search_checks(cfg, missing: list, warn: list, ok: list) -> None:
    """find-jobs: tiers that work, something to scan, JobSpy installed only when the user chose it."""
    from find_jobs import tier_problems

    if cfg.is_set("search.tiers"):
        for problem in tier_problems(cfg.get("search.tiers")):
            missing.append(f"jhs.yaml {problem}. Fix: {SETUP} search, or ask Claude to set it")
    watchlist = cfg.get("search.watchlist") or []
    jobspy = bool(cfg.get("search.jobspy.enabled"))
    if watchlist:
        ok.append(f"watchlist: {len(watchlist)} compan{'y' if len(watchlist) == 1 else 'ies'}")
    elif not jobspy:
        missing.append("No companies to scan: search.watchlist is empty. "
                       "Fix: /job-hunt-studio:find-jobs add <company>")
    if jobspy:
        try:
            import jobspy as _  # noqa: F401
        except ImportError:
            warn.append(f"JobSpy is enabled in jhs.yaml but not installed; the scan uses company boards only. "
                        f"Fix: {SETUP} tools")
        if not cfg.get("search.jobspy.searches") or not cfg.get("search.jobspy.sites"):
            warn.append(f"JobSpy is enabled but search.jobspy has no sites or searches; it is skipped. "
                        f"Fix: {SETUP} options")


def outreach_checks(cfg, warn: list) -> None:
    """outreach: what makes the people search weaker when it is missing (nothing here stops it)."""
    if not cfg.is_set("outreach.topics"):
        warn.append("outreach.topics is empty: paper authors are ranked by paper count and recency only. "
                    "Fix: /job-hunt-studio:outreach setup")
    if not (cfg.is_set("candidate.schools") or cfg.is_set("candidate.past_employers")):
        warn.append(f"candidate.schools and candidate.past_employers are empty: no shared-tie searches. "
                    f"Fix: {SETUP} profile")
    status = str(cfg.get("outreach.connections") or "unset")
    path = cfg.root / (cfg.get("outreach.connections_csv") or "applications/outreach/private/Connections.csv")
    if status == "added" and not path.is_file():
        warn.append(f"The connections export is set up but {path.name} is missing; runs skip your connections. "
                    "Fix: /job-hunt-studio:outreach setup")
    elif status == "unset":
        warn.append("The LinkedIn connections export is not set up (optional); outreach offers it once")


def pack_checks(cfg, warn: list, ok: list) -> None:
    """mock-interview: the pack's topic list (practice runs without one, on any topic the user names)."""
    from practice import pack_topics, parse_topics

    path, note = pack_topics(cfg)
    if not path:
        warn.append(f"{note}. Fix (optional): set `pack:` in jhs.yaml to a pack with a TOPICS.md ({SETUP} profile)")
        return
    areas, problems = parse_topics(path.read_text(encoding="utf-8"))
    ok.append(f"pack {cfg.get('pack')}: {len(areas)} interview areas")
    for problem in problems:
        warn.append(f"pack TOPICS.md: {problem}")


def linkedin_checks(cfg, warn: list, ok: list) -> None:
    """linkedin-refresh: the current profile to compare with (optional)."""
    folder = cfg.root / "linkedin"
    pdfs = sorted(folder.glob("*.pdf")) if folder.is_dir() else []
    if (folder / "PROFILE.md").is_file():
        ok.append("current profile: linkedin/PROFILE.md")
    elif pdfs:
        ok.append(f"current profile: linkedin/{pdfs[-1].name}")
    else:
        warn.append("No current LinkedIn profile in linkedin/ (PROFILE.md or a PDF): the draft is written from the "
                    "Ledger without comparing. Fix (optional): on your profile, More (or Resources) > Save to PDF, "
                    "and put the file in linkedin/")


def run(skill: str, tex: str | None) -> int:
    utf8_stdout()
    need = NEEDS[skill]
    missing, warn, ok = [], [], []

    try:
        cfg = load()
    except ConfigError as exc:
        print(f"Job Hunt Studio preflight: {skill}\n  MISSING  {exc}\nRESULT: STOP (1 missing)")
        return 1
    ok.append(f"jhs.yaml ({cfg.root})")

    for key in need["keys"]:
        if not cfg.is_set(key):
            section = KEY_FIX.get(key, KEY_FIX.get(key.split(".")[0], "profile"))
            missing.append(f"jhs.yaml `{key}` is empty. Fix: {SETUP} {section}, or ask Claude to set it")

    if not cfg.ledger_path.is_file():
        missing.append(f"docs/Evidence_Ledger.md does not exist. Fix: {SETUP} ledger")
    else:
        text = cfg.ledger_text()
        found = anchors(text)
        for block in need["blocks"]:
            if block not in found:
                missing.append(f"Ledger block [{block}] is missing. Fix: {SETUP} {BLOCK_FIX.get(block, 'ledger')}")
            elif is_pending(found[block]):
                missing.append(f"Ledger block [{block}] still holds setup placeholders. "
                               f"Fix: {SETUP} {BLOCK_FIX.get(block, 'ledger')}")
        for block in need["optional"]:
            if block in found and is_pending(found[block]):
                warn.append(f"Ledger block [{block}] is not set up yet; it is ignored until "
                            f"{SETUP} {BLOCK_FIX.get(block, 'ledger')}")
        if "hard-lines" in need["blocks"] or skill == "update-ledger":
            try:
                hard_lines(text)
            except ValueError as exc:
                missing.append(f"Ledger [hard-lines] cannot be read: {exc}. Fix: ask Claude to correct the row")
        if not missing and need["blocks"]:
            ok.append("Ledger blocks this skill reads")

    for tool in need["tools"]:
        if have(tool):
            continue
        (warn if tool in OPTIONAL_TOOLS else missing).append(f"`{tool}` not found. Fix: install {TOOL_FIX[tool]}")

    if need["resume"] in ("approved", "approved-optional"):
        tag = latest_tag(cfg.root, cfg.tag_prefix)
        if tag:
            ok.append(f"approved resume {tag}")
        elif need["resume"] == "approved":
            missing.append(f"No approved resume yet (no `{cfg.tag_prefix}<N>` tag); tailored copies start from one. "
                           "Fix: /job-hunt-studio:tailor-resume base, review it to READY, then approve it")
        else:
            warn.append(NO_APPROVED.get(skill, "No approved resume yet: resume fit is scored on the base draft if one "
                                               "exists, else skipped"))
    if need["resume"] in ("tex", "base"):
        target = Path(tex) if tex else cfg.base_tex
        if not target.is_absolute():
            target = (Path.cwd() / target).resolve()
        if not target.is_file():
            hint = ("/job-hunt-studio:tailor-resume base builds it from your Ledger"
                    if target == cfg.base_tex.resolve() else "check the path")
            missing.append(f"Resume source {target} does not exist. Fix: {hint}")
        else:
            ok.append(f"resume source {target.name}")

    if skill == "find-jobs":
        search_checks(cfg, missing, warn, ok)
    if skill == "outreach":
        outreach_checks(cfg, warn)
    if skill in ("mock-interview", "mock-interview-cv"):
        pack_checks(cfg, warn, ok)
    if skill == "linkedin-refresh":
        linkedin_checks(cfg, warn, ok)

    if skill in ("compile-resume", "review-resume", "approve", "tailor-resume", "tailor-base"):
        try:
            import pdfminer  # noqa: F401
            import pypdf  # noqa: F401
        except ImportError:
            missing.append(f"Python packages pypdf and pdfminer.six are missing. Fix: {SETUP} tools")

    print(f"Job Hunt Studio preflight: {skill}")
    for line in ok:
        print(f"  OK       {line}")
    for line in warn:
        print(f"  WARN     {line}")
    for line in missing:
        print(f"  MISSING  {line}")
    print("RESULT:", f"STOP ({len(missing)} missing)" if missing else "READY TO RUN")
    return 1 if missing else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skill", choices=sorted(NEEDS))
    parser.add_argument("--tex", help="resume source the skill will use (default: resume.base_tex)")
    args = parser.parse_args()
    return run(args.skill, args.tex)


if __name__ == "__main__":
    raise SystemExit(main())
