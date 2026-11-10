"""ATS parse check: read a resume PDF the way applicant tracking systems do, and report what they would miss.

Extracts the text with two engines that ATS parsers commonly build on (pypdf and pdfminer.six), then checks:
contact details from jhs.yaml, standard section headings, each Ledger [roles] entry on the resume with its dates,
and characters that extract cleanly. Also reports the coverage of the pack's keywords (information only).

Dates are checked two ways. pypdf reads text in the order it was written, like simple text-only parsers: each
entry's dates must follow its title. pdfminer analyses the layout, like parsers that see the page: each entry's
dates must sit on the title's line or the line next to it. (pdfminer's own reading order puts right-aligned dates
in a column of their own when entries are stacked; that happens to most two-sided layouts, Jake's Resume included,
so it is reported as a note, not a failure.)

Run from the workspace folder, with the workspace Python:

    python ats_check.py RESUME.pdf
Exit code 0 when both engines PASS (gate G2 of the review rubric).
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import load, pack_keywords, utf8_stdout  # noqa: E402
from ledger import roles  # noqa: E402

HEADINGS = ["Summary", "Profile", "Experience", "Work Experience", "Professional Experience", "Research Experience",
            "Employment", "Projects", "Publications", "Skills", "Technical Skills", "Education", "Awards",
            "Certifications", "Leadership", "Volunteering", "Service"]
EXPERIENCE = re.compile(r"experience|employment", re.I)
MONTH = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
MONTH_YEAR = re.compile(MONTH + r"\s+(\d{4})", re.I)


def norm(s: str) -> str:
    return " ".join(s.split())


def find_ci(hay: str, needle: str, start: int = 0) -> int:
    return hay.lower().find(needle.lower(), start)


def layout_lines(pdf: str) -> list[tuple[int, float, float, str]]:
    """(page, bottom, height, text) of every text line pdfminer finds."""
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextLine

    lines = []

    def walk(obj, page):
        for child in obj:
            if isinstance(child, LTTextLine):
                lines.append((page, child.y0, child.height, norm(child.get_text())))
            elif hasattr(child, "__iter__"):
                walk(child, page)

    for number, page in enumerate(extract_pages(pdf)):
        walk(page, number)
    return lines


def paired(role, lines) -> bool:
    """True when a line holding the role's title has its start date on the same line or the line next to it."""
    wanted = [f"{m.group(1)[:3].lower()} {m.group(2)}" for m in MONTH_YEAR.finditer(role.dates)]
    if not wanted:
        return False
    for page, y, h, text in lines:
        if role.title.lower() not in text.lower():
            continue
        for page2, y2, h2, text2 in lines:
            if page2 != page or abs(y2 - y) > 1.6 * max(h, h2, 1):
                continue
            got = [f"{m.group(1)[:3].lower()} {m.group(2)}" for m in MONTH_YEAR.finditer(text2)]
            if wanted[0] in got:
                return True
    return False


def check(name: str, text: str, cfg, ledger_text: str, keywords: list[str], lines=None) -> bool:
    flat = norm(text)
    problems = []
    print(f"\n=== {name} ({len(flat)} characters) ===")

    # contact details from jhs.yaml
    contact = {}
    email = cfg.get("candidate.email") or ""
    if email:
        contact["email"] = email.lower() in flat.lower()
    phone = re.sub(r"\D", "", cfg.get("candidate.phone") or "")
    if phone:
        contact["phone"] = phone[-7:] in re.sub(r"\D", "", flat)
    linkedin = cfg.get("candidate.linkedin") or ""
    handle = re.search(r"linkedin\.com/in/([\w-]+)", linkedin)
    if handle:
        contact["linkedin"] = f"linkedin.com/in/{handle.group(1)}".lower() in flat.lower()
    city = (cfg.get("candidate.city") or "").split(",")[0].strip()
    if city:
        contact["city"] = city.lower() in flat.lower()
    for key, ok in contact.items():
        print(f"  contact {key:9}: {'found' if ok else 'MISSING'}")
        if not ok:
            problems.append(f"contact {key} not found in the text")

    # standard headings at the start of a line
    found = []
    for h in HEADINGS:
        m = re.search(rf"(^|\n)\s*{re.escape(h)}\s*(\n|$)", text, re.I)
        if m:
            found.append((m.start(), h))
    found.sort()
    names = [h for _, h in found]
    print(f"  headings  : {', '.join(names) if names else 'NONE FOUND'}")
    if not any(EXPERIENCE.search(h) or h in ("Projects",) for h in names):
        problems.append("no Experience (or Projects) heading found at the start of a line")
    if "Education" not in names:
        problems.append("no Education heading found at the start of a line")

    # each role in the Ledger that is on the resume: its dates follow it in reading order
    first_heading = found[0][0] if found else 0
    body_start = len(norm(text[:first_heading]))
    ledger_roles = roles(ledger_text)
    positions = []
    for r in ledger_roles:
        i = find_ci(flat, r.title, body_start)
        if i < 0:
            # summaries often repeat the title; for entries, look after the first heading only
            positions.append((r, -1, -1))
            continue
        org = find_ci(flat, r.organization, max(body_start, i - 250)) if r.organization else -1
        start = min(i, org) if 0 <= org < i else i
        positions.append((r, start, i))
    starts = sorted(s for _, s, _ in positions if s >= 0)
    for r, start, i in positions:
        if start < 0:
            print(f"  entry     : {r.title[:40]:40} -> not on the resume (fine if left off on purpose)")
            continue
        nxt = next((s for s in starts if s > i), len(flat))
        window = flat[start:max(nxt, start + 60)][:400]
        wanted = [f"{m.group(1)[:3].lower()} {m.group(2)}" for m in MONTH_YEAR.finditer(r.dates)]
        got = [f"{m.group(1)[:3].lower()} {m.group(2)}" for m in MONTH_YEAR.finditer(window)]
        in_order = bool(wanted) and wanted[0] in got
        if lines is None:
            ok = in_order
            shown = next((m.group(0) for m in MONTH_YEAR.finditer(window)), "") if ok else "DATES NOT FOUND AFTER IT"
        else:
            ok = paired(r, lines)
            shown = ("dates on the same or next line" if ok else "DATES NOT NEXT TO IT") + \
                ("" if in_order else " (note: read as a separate column)")
        print(f"  entry     : {r.title[:40]:40} -> {shown}")
        if not ok:
            found_anywhere = bool(wanted) and wanted[0] in [f"{m.group(1)[:3].lower()} {m.group(2)}"
                                                            for m in MONTH_YEAR.finditer(flat)]
            problems.append(f"the dates of '{r.title}' ({r.dates} in Ledger [roles]) "
                            + ("are not next to it" + (" in reading order" if lines is None else " on the page")
                               if found_anywhere else "are not on the resume; check them against [roles]"))

    # characters
    odd = sorted({c for c in text if unicodedata.category(c) in ("Co", "Cn", "Cs")
                  or (unicodedata.category(c) == "Cc" and c not in "\n\r\t\f") or c == "�"})
    ligatures = [c for c in text if 0xFB00 <= ord(c) <= 0xFB06]
    cids = re.findall(r"\(cid:\d+\)", text)
    if odd:
        problems.append(f"unreadable characters: {[hex(ord(c)) for c in odd][:8]}")
    if ligatures:
        problems.append(f"{len(ligatures)} ligature characters (fi, fl): add \\input{{glyphtounicode}} and "
                        "\\pdfgentounicode=1, or turn ligatures off")
    if cids:
        problems.append(f"{len(cids)} glyphs without text mapping, shown as (cid:N)")
    glued = [w for w in re.findall(r"\b[a-z]{3,}[A-Z][a-z]{3,}\b", flat)]
    if glued:
        print(f"  note      : possibly glued words (check by eye): {glued[:5]}")
    print(f"  characters: {'clean' if not (odd or ligatures or cids) else 'PROBLEMS'}")

    if keywords:
        low = flat.lower()
        present = [k for k in keywords if k.lower() in low]
        print(f"  keywords  : {len(present)}/{len(keywords)} of the pack's keywords present (information only; "
              "never add one you cannot claim)")
    print(f"  RESULT    : {'PASS' if not problems else 'ISSUES: ' + '; '.join(problems)}")
    return not problems


def main() -> int:
    utf8_stdout()
    if len(sys.argv) != 2:
        print("usage: python ats_check.py RESUME.pdf")
        return 2
    pdf = sys.argv[1]
    from pdfminer.high_level import extract_text as pdfminer_text
    from pypdf import PdfReader

    cfg = load()
    ledger_text = cfg.ledger_text()
    keywords = [str(k) for k in (pack_keywords(cfg).get("keywords") or [])]
    ok1 = check("pypdf", "\n".join(p.extract_text() or "" for p in PdfReader(pdf).pages), cfg, ledger_text, keywords)
    ok2 = check("pdfminer", pdfminer_text(pdf), cfg, ledger_text, keywords, lines=layout_lines(pdf))
    print(f"\nATS: {'PASS' if ok1 and ok2 else 'FAIL'} (both engines must pass)")
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
