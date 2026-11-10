"""Interview practice: the pack's topic areas and where the user stands on each. Used by mock-interview.

Usage (from the workspace folder, with the workspace Python):
    python practice.py plan                 coverage per area from interview/PRACTICE_LOG.md: never practiced,
                                            shaky, once (passed in one round), solid
    python practice.py areas                the pack's areas (pack: in jhs.yaml)
    python practice.py check TOPICS.md      check a pack's TOPICS.md (for pack authors; no workspace needed)

A pack's TOPICS.md lists areas as numbered items whose name is in bold, `1. **ml-fundamentals**: ...`, under `##`
headings (the heading is the area's group, for example "Core areas"), each followed by an indented `Reading:` or
`Practice:` line. The area names are the file names under interview/notes/ and the area column of the log.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

LOG = Path("interview") / "PRACTICE_LOG.md"
AREA = re.compile(r"^\d+\.\s+\*\*(?P<slug>[^*]+)\*\*:\s*(?P<what>.+)$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class Area:
    slug: str
    group: str
    what: str
    reading: str = ""


@dataclass
class Standing:
    area: str
    group: str = "your own"
    rows: list[dict] = field(default_factory=list)
    weak_spots: list[dict] = field(default_factory=list)

    @property
    def last(self) -> str:
        dates = [r["Last practiced"] for r in self.rows if re.match(r"\d{4}-\d{2}-\d{2}", r.get("Last practiced", ""))]
        return max(dates) if dates else ""

    @property
    def status(self) -> str:
        if not self.rows:
            return "never"
        statuses = [r.get("Status", "").lower() for r in self.rows]
        if self.weak_spots or any(not s.startswith(("solid", "passed")) for s in statuses):
            return "shaky"
        return "solid" if all(s.startswith("solid") for s in statuses) else "once"


def parse_topics(text: str) -> tuple[list[Area], list[str]]:
    """The areas in a TOPICS.md, and the problems found (bad or repeated names, an area without a reading line)."""
    areas, problems, group = [], [], ""
    for line in text.splitlines():
        if line.startswith("## "):
            group = line[3:].strip()
            continue
        m = AREA.match(line.strip()) if not line.startswith((" ", "\t")) else None
        if m:
            slug = m["slug"].strip()
            if not SLUG.match(slug):
                problems.append(f"area name `{slug}` must be lowercase words joined by hyphens")
            if any(a.slug == slug for a in areas):
                problems.append(f"area `{slug}` appears twice")
            areas.append(Area(slug, group, m["what"].strip()))
        elif areas and line.strip().startswith(("Reading:", "Practice:")):
            areas[-1].reading = line.strip()
    for a in areas:
        if not a.reading:
            problems.append(f"area `{a.slug}` has no indented `Reading:` or `Practice:` line")
    if not areas:
        problems.append("no areas found (numbered items like `1. **area-name**: what it covers`)")
    return areas, problems


def table_rows(text: str, heading: str) -> list[dict]:
    """Rows of the first table under a `## <heading>` (matched by its start), as dicts keyed by the header cells."""
    m = re.search(rf"^## {re.escape(heading)}.*$", text, re.M)
    if not m:
        return []
    body = text[m.end():]
    nxt = re.search(r"^## ", body, re.M)
    body = body[: nxt.start()] if nxt else body
    lines = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []
    split = lambda ln: [c.strip() for c in re.split(r"(?<!\\)\|", ln)[1:-1]]  # noqa: E731
    head = split(lines[0])
    return [dict(zip(head, split(ln))) for ln in lines[2:] if any(split(ln))]


def standings(areas: list[Area], log_text: str) -> list[Standing]:
    """One Standing per pack area, plus one per area the log names that the pack does not have. Sorted never
    practiced, then shaky, then solid; inside each, the pack's groups in order (your own topics last), oldest first."""
    by_name = {a.slug: Standing(a.slug, a.group) for a in areas}
    for row in table_rows(log_text, "Coverage"):
        name = row.get("Area", "").strip().strip("`")
        if name:
            by_name.setdefault(name, Standing(name)).rows.append(row)
    for row in table_rows(log_text, "Open weak spots"):
        name = row.get("Area", "").strip().strip("`")
        if name:
            by_name.setdefault(name, Standing(name)).weak_spots.append(row)
    order = {"never": 0, "shaky": 1, "once": 2, "solid": 3}
    groups = list(dict.fromkeys(a.group for a in areas))  # pack order: core areas before field areas
    rank = lambda s: groups.index(s.group) if s.group in groups else len(groups)  # noqa: E731
    return sorted(by_name.values(), key=lambda s: (order[s.status], rank(s), s.last or "0000", s.area))


def pack_topics(cfg) -> tuple[Path | None, str]:
    """(path of the pack's TOPICS.md or None, a note on why there is none)."""
    from config import PLUGIN_ROOT

    pack = str(cfg.get("pack") or "none")
    if pack == "none":
        return None, "pack: none in jhs.yaml, so there is no topic list; name any topic and practice still runs"
    path = PLUGIN_ROOT / "packs" / pack / "TOPICS.md"
    if not (PLUGIN_ROOT / "packs" / pack).is_dir():
        return None, f"pack `{pack}` is not in the plugin's packs/ folder; check `pack:` in jhs.yaml"
    if not path.is_file():
        return None, f"pack `{pack}` has no TOPICS.md, so there is no topic list; name any topic and practice still runs"
    return path, ""


def cmd_plan() -> int:
    from config import ConfigError, load, utf8_stdout

    utf8_stdout()
    try:
        cfg = load()
    except ConfigError as exc:
        print(f"MISSING  {exc}")
        return 1
    path, note = pack_topics(cfg)
    areas = parse_topics(path.read_text(encoding="utf-8"))[0] if path else []
    log = cfg.root / LOG
    log_text = log.read_text(encoding="utf-8") if log.is_file() else ""
    rows = standings(areas, log_text)
    print(f"Practice plan ({'pack ' + str(cfg.get('pack')) + ', ' + str(len(areas)) + ' areas' if path else note})")
    print(f"Log: {LOG.as_posix()}" + ("" if log_text else " (not created yet: every area is never practiced)"))
    if not rows:
        print("Nothing practiced yet.")
        return 0
    width = max(len(s.area) for s in rows)
    print(f"  {'Area':<{width}}  {'Group':<12}  {'Status':<6}  {'Last':<10}  Subtopics  Open weak spots")
    for s in rows:
        group = s.group.replace(" areas", "")[:12]
        print(f"  {s.area:<{width}}  {group:<12}  {s.status:<6}  {s.last or '-':<10}  {len(s.rows):>9}  "
              f"{len(s.weak_spots):>15}")
    spots = [(s.area, w) for s in rows for w in s.weak_spots]
    if spots:
        print(f"Open weak spots ({len(spots)}):")
        for area, w in sorted(spots, key=lambda x: x[1].get("Added", "")):
            print(f"  - {area}: {w.get('Question', '')} ({w.get('Added', '')})")
    return 0


def cmd_areas() -> int:
    from config import ConfigError, load, utf8_stdout

    utf8_stdout()
    try:
        cfg = load()
    except ConfigError as exc:
        print(f"MISSING  {exc}")
        return 1
    path, note = pack_topics(cfg)
    if not path:
        print(note)
        return 0
    areas, problems = parse_topics(path.read_text(encoding="utf-8"))
    group = None
    for a in areas:
        if a.group != group:
            group = a.group
            print(f"{group}:")
        print(f"  {a.slug}: {a.what[:110]}{'...' if len(a.what) > 110 else ''}")
    for p in problems:
        print(f"PROBLEM  {p}")
    return 1 if problems else 0


def cmd_check(path: Path) -> int:
    from config import utf8_stdout

    utf8_stdout()
    areas, problems = parse_topics(path.read_text(encoding="utf-8"))
    for p in problems:
        print(f"PROBLEM  {p}")
    print(f"{len(areas)} areas; RESULT: {'OK' if not problems else 'FIX (' + str(len(problems)) + ')'}")
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    sub.add_parser("areas")
    check = sub.add_parser("check")
    check.add_argument("topics", type=Path)
    args = parser.parse_args()
    if args.cmd == "plan":
        return cmd_plan()
    if args.cmd == "areas":
        return cmd_areas()
    return cmd_check(args.topics)


if __name__ == "__main__":
    raise SystemExit(main())
