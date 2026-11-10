"""Read an Evidence Ledger (format: docs/LEDGER_FORMAT.md). Standard library only.

    from ledger import anchors, hard_lines
    rules = hard_lines(Path("docs/Evidence_Ledger.md").read_text(encoding="utf-8"))

Command line, to check a Ledger after an edit:
    python ledger.py check docs/Evidence_Ledger.md
"""
from __future__ import annotations

import re
from dataclasses import dataclass

HEADING = re.compile(r"^#{2,4} .*\[(?P<anchor>[a-z0-9:_-]+)\]\s*$", re.MULTILINE)
PENDING = re.compile(r"TODO\(setup\)|<[a-z][^<>]*>", re.IGNORECASE)


@dataclass
class HardLine:
    id: str
    rule: str
    allowed: str
    banned: re.Pattern | None
    scope: list[str]


def section_zero(text: str) -> str:
    """Section 0 only (the current facts), up to the first dated entry."""
    start = text.find("## 0.")
    body = text[start:] if start >= 0 else text
    end = re.search(r"^## \d{4}-\d{2}-\d{2}", body, re.MULTILINE)
    return body[: end.start()] if end else body


def anchors(text: str) -> dict[str, str]:
    """Map each anchor in section 0 to its body text."""
    zero = section_zero(text)
    found = list(HEADING.finditer(zero))
    out = {}
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(zero)
        out[m["anchor"]] = zero[m.end():end].strip()
    return out


def is_pending(body: str) -> bool:
    """True if a block still holds setup placeholders such as <title> or TODO(setup)."""
    return bool(PENDING.search(body))


def _cells(row: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", row.strip())[1:-1]]


def table(body: str) -> list[list[str]]:
    """Data rows of the first markdown table in a block (header and separator skipped, placeholder rows dropped)."""
    rows = [r for r in body.splitlines() if r.strip().startswith("|")]
    return [_cells(r) for r in rows[2:] if not is_pending(r) and any(_cells(r))]


@dataclass
class Role:
    title: str
    organization: str
    location: str
    dates: str


def roles(text: str) -> list[Role]:
    """Rows of the [roles] table: title, organization, location, dates as printed."""
    body = anchors(text).get("roles", "")
    return [Role(*(c + ["", "", "", ""])[:4]) for c in table(body) if c and c[0]]


def table_column(text: str, anchor: str, column: int = 0) -> list[str]:
    """One column of the table in a block, for example the skill names in [skills-gaps]."""
    body = anchors(text).get(anchor, "")
    return [c[column] for c in table(body) if len(c) > column and c[column]]


def hard_lines(text: str) -> list[HardLine]:
    """Rows of the [hard-lines] table. Raises ValueError if the table is missing or a pattern is invalid."""
    body = anchors(text).get("hard-lines")
    if body is None:
        raise ValueError("Ledger has no '[hard-lines]' heading in section 0")
    rows = [r for r in body.splitlines() if r.strip().startswith("|")]
    rules = []
    for row in rows[2:]:  # skip the header and the |---| separator
        cells = _cells(row)
        if len(cells) < 5 or not cells[0] or is_pending(row):
            continue
        rule_id, rule, allowed, banned, scope = cells[:5]
        pattern = banned.strip().strip("`").replace("\\|", "|")
        try:
            compiled = re.compile(pattern, re.IGNORECASE) if pattern else None
        except re.error as exc:
            raise ValueError(f"{rule_id}: invalid banned pattern: {exc}") from exc
        rules.append(HardLine(rule_id, rule, allowed, compiled, [s.strip() for s in scope.split(",") if s.strip()]))
    return rules


def check(text: str) -> list[str]:
    """Problems that would stop the skills from reading this Ledger; empty when it parses."""
    problems = []
    if "## 0." not in text:
        problems.append("no '## 0.' section (the current facts)")
    found = anchors(text)
    for anchor in ("positioning", "identity", "roles", "skills-claimed", "skills-gaps", "hard-lines", "never-print",
                   "open-items"):
        if anchor not in found:
            problems.append(f"missing block [{anchor}]")
    try:
        hard_lines(text)
    except ValueError as exc:
        problems.append(str(exc))
    return problems


def _main(argv: list[str]) -> int:
    import sys
    from pathlib import Path

    if len(argv) != 3 or argv[1] != "check":
        print("usage: python ledger.py check <path to Evidence_Ledger.md>")
        return 2
    text = Path(argv[2]).read_text(encoding="utf-8")
    found = anchors(text)
    pending = sorted(a for a, body in found.items() if is_pending(body))
    problems = check(text)
    print(f"Blocks in section 0: {len(found)} ({', '.join(sorted(found))})")
    print(f"Still holding placeholders (treated as missing): {', '.join(pending) if pending else 'none'}")
    if not problems:
        print(f"Hard lines: {len(hard_lines(text))} rule(s), every pattern compiles")
    for p in problems:
        print(f"PROBLEM: {p}")
    print("RESULT:", "OK" if not problems else f"{len(problems)} problem(s)")
    sys.stdout.flush()
    return 0 if not problems else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv))
