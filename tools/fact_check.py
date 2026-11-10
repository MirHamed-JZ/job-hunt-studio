"""Fact and voice check: compare a resume, cover letter, form answer or message with the Evidence Ledger.

It never fails a build. It prints warnings; each one must be fixed, or acknowledged with a reason that cites the
Ledger, before /job-hunt-studio:review-resume can call a resume READY (/job-hunt-studio:audit-claims uses the
same check for other text). What it looks for:
  number       a number that does not appear in Ledger section 0 (with its unit when it has one: 3.1%, 2.4M, 12x,
               4 years, 30-day)
  date         a month and year that does not appear in Ledger section 0
  title        a job title, organization or date range in a resume entry that differs from Ledger [roles]
  hard-line    wording that matches a [hard-lines] pattern in this document's scope
  gap-skill    a skill listed in [skills-gaps]
  never-print  work authorization or another [never-print] topic in a resume or public text
  dash         em dashes, en dashes outside date ranges, double hyphens (as set in jhs.yaml writing.banned_punctuation)
  phrase       stock phrases: the built-in list, jhs.yaml writing.banned_phrases and the pack's buzzwords

Acknowledge a warning that is true (a number derived from Ledger facts, such as years of experience counted from
[roles] dates) with a line in the source, next to the text:
  in a .tex file:        % fact-ok: 5+ | years counted from the [roles] dates (Sep 2021 to present)
  in a .md or .txt file: <!-- fact-ok: 5+ | years counted from the [roles] dates -->
The reason must name a Ledger block in square brackets, or the date of a dated Ledger entry; otherwise the
acknowledgement is ignored. In a message, cover letter or form answer, a number or date about the person or company
written to (the year of their paper, a figure from the posting) is acknowledged with [recipient]:
<!-- fact-ok: 2025 | [recipient] the year of their paper -->. In a cover letter or form answer it holds only for a
number or date that the posting.md beside the file contains, and never for a duration ("6 years").
Gap skills, never-print items, job titles or dates that differ from [roles], dashes, stock phrases and example
content are never acknowledged: fix the text (or correct the Ledger). A hard-line acknowledgement must name the rule
id, which counts as its Ledger reference (for example "HL-ranker-status: says it was not deployed").

Usage (from the workspace folder):
    python fact_check.py FILE [--pdf PDF] [--kind resume|cover-letter|form|linkedin|message|interview]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ledger import anchors, hard_lines, roles, section_zero, table_column  # noqa: E402

SCOPES = {
    "resume": {"resume", "all"},
    "cover-letter": {"resume", "all"},
    "form": {"resume", "all"},
    "linkedin": {"linkedin", "public", "all"},
    "message": {"public", "all"},
    "interview": {"interview", "all"},
}
NEVER_PRINT_KINDS = {"resume", "cover-letter", "linkedin", "message"}

STOCK_PHRASES = [
    "passionate", "results-driven", "results-oriented", "detail-oriented", "team player", "self-starter",
    "go-getter", "hard-working", "hardworking", "synergy", "think outside the box", "proven track record",
    "best-in-class", "world-class", "cutting-edge", "delve", "tapestry", "seamless", "seamlessly",
    "dynamic professional", "highly motivated",
]
EXAMPLE_MARKER = "JHS-EXAMPLE-CONTENT"
RECIPIENT = "recipient"
# Warnings that are always fixed, never acknowledged: a gap skill, a never-print item, a job title or date that
# differs from [roles] (fix the text, or correct the Ledger with update-ledger), a dash or stock phrase (reword it),
# and leftover example content.
UNACKABLE = {"gap-skill", "never-print", "title", "dash", "phrase", "example"}
# Documents written to someone, where "[recipient]" may acknowledge a number or date about them.
RECIPIENT_KINDS = {"message", "cover-letter", "form"}

MONTH = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
MONTH_YEAR = re.compile(MONTH + r"\s+(\d{4})", re.I)
DATE_END = r"(?:" + MONTH + r"\s+\d{4}|\d{4}|present|now|current|today)"
DATE_RANGE = re.compile(r"(?:" + MONTH + r"\s+)?\d{4}\s*(?:–|—|--?|to)\s*" + DATE_END, re.I)
NUMBER = re.compile(
    r"(?<![\w@#/.,-])[+~≈]?(?P<core>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?P<suffix>\s?(?:%|percent\b|×|x\b|times\b|million\b|billion\b|[KMB]\b|k\b)|\+)?(?![\w])")
# A duration after a number ("4+ years", "30-day", "6 hours"): matched with its unit.
TIME_UNIT = re.compile(r"\s?-?\s?(years?|yrs?|months?|weeks?|days?|hours?|minutes?)\b", re.I)
URLISH = re.compile(r"https?://\S+|www\.\S+|[\w.+-]+@[\w-]+\.[\w.]+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|io|ai|dev|"
                    r"edu|co|me|app|fr|ca|uk|de|es|it|nl|eu)(?:/\S*)?", re.I)
PHONE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(\d{2,4}\)\s?)?\d{2,4}[\s.-]\d{2,4}[\s.-]\d{2,4}(?:[\s.-]\d{2,4})?")
ACK = re.compile(r"fact-ok:\s*(?P<token>[^|\n]+?)\s*\|\s*(?P<reason>[^\n]+?)\s*(?:-->)?\s*$", re.M)
ENTRY_DECL = re.compile(r"%\s*jhs-entry(?:\[(?P<section>[^\]]+)\])?:\s*\\(?P<macro>[A-Za-z]+)(?P<args>(?:\{[a-z-]+\})+)")


@dataclass
class Finding:
    kind: str
    match: str
    context: str
    detail: str
    rule: str = ""
    ack: str | None = None
    ack_problem: str = ""
    ackable: bool = True

    @property
    def resolved(self) -> bool:
        return self.ack is not None and self.ackable


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    kind: str = "resume"
    source: str = ""

    @property
    def open(self) -> list[Finding]:
        return [f for f in self.findings if not f.resolved]


# ---------- text extraction ----------

def tex_body(tex: str) -> str:
    body = "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in tex.splitlines())
    start = body.find(r"\begin{document}")
    end = body.find(r"\end{document}")
    return body[start + len(r"\begin{document}"): end if end > 0 else None] if start >= 0 else body


def tex_to_text(tex: str) -> str:
    """Rough plain text of a LaTeX resume body, used when no compiled PDF is given."""
    s = tex_body(tex)
    s = re.sub(r"\\href\{[^{}]*\}\{", "{", s)
    s = re.sub(r"\\url\{[^{}]*\}", "", s)
    s = re.sub(r"\\(begin|end)\{[^{}]*\}(\[[^\]]*\])?(\{[^{}]*\})*", "\n", s)
    s = re.sub(r"\\kern\s*-?[\d.]+\s*(pt|em|cm|mm|in|ex)", " ", s)
    s = re.sub(r"\\(vspace|hspace|vskip|hskip|fontsize|color|setlength|addtolength|includegraphics|label|ref|cite|"
               r"needspace|linespread|rule|raisebox|sbox|newsavebox|newcommand|renewcommand|titleformat|"
               r"titlespacing)\*?(\[[^\]]*\])?(\{[^{}]*\})+", " ", s)
    s = re.sub(r"\\section\*?\{([^{}]*)\}", r"\n\1\n", s)
    s = re.sub(r"\\(item|resumeItem)\b", "\n• ", s)
    s = re.sub(r"\\\\(\[[^\]]*\])?", "\n", s)
    for a, b in ((r"\%", "%"), (r"\&", "&"), (r"\$", "$"), (r"\#", "#"), (r"\_", "_"), (r"\{", ""), (r"\}", ""),
                 ("---", "—"), ("--", "–"), ("~", " "), ("``", '"'), ("''", '"')):
        s = s.replace(a, b)
    s = re.sub(r"\$\\(cdot|bullet)\$", "·", s)
    s = re.sub(r"\$([^$]*)\$", r"\1", s)
    s = re.sub(r"\\[A-Za-z@]+\*?(\[[^\]]*\])?", " ", s)
    s = re.sub(r"\}\s*\{", " ", s)  # macro arguments are separate words: \entry{Title}{Dates}
    s = s.replace("{", "").replace("}", "")
    return "\n".join(" ".join(line.split()) for line in s.splitlines() if line.strip())


def pdf_to_text(pdf: Path) -> str:
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], capture_output=True)
        if out.returncode == 0:
            return out.stdout.decode("utf-8", errors="replace")
    from pypdf import PdfReader
    return "\n".join(p.extract_text() or "" for p in PdfReader(str(pdf)).pages)


def md_to_text(md: str) -> str:
    """The claims in a Markdown draft. Headings (titles, form questions) and word-count notes are not claims."""
    s = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    s = re.sub(r"^\s{0,3}#{1,6}\s.*$", "", s, flags=re.M)
    s = re.sub(r"^\s*\(\d+ words?\)\s*$", "", s, flags=re.M | re.I)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*|__([^_]+)__", lambda m: m.group(1) or m.group(2), s)
    return s


def flatten(text: str) -> str:
    text = re.sub(r"(\w)-\n(\w)", r"\1-\2", text)
    return " ".join(text.split())


# ---------- Ledger side ----------

def _norm_numbers(text: str) -> str:
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    s = s.replace("×", "x")
    s = re.sub(r"(\d)\s?percent\b", r"\1%", s, flags=re.I)
    s = re.sub(r"(\d)\s+%", r"\1%", s)
    s = re.sub(r"(\d)\s?million\b", r"\1M", s, flags=re.I)
    s = re.sub(r"(\d)\s?billion\b", r"\1B", s, flags=re.I)
    s = re.sub(r"(\d)\s?k\b", r"\1K", s)
    s = re.sub(r"(\d)\s?times\b", r"\1x", s, flags=re.I)
    return s


def _month_years(text: str) -> set[str]:
    return {f"{m.group(1)[:3].title()} {m.group(2)}" for m in MONTH_YEAR.finditer(text)}


def _norm_label(s: str) -> str:
    return " ".join(re.sub(r"[^\w&+/ ]", " ", s.lower()).split())


def _range(text: str) -> tuple[str, str]:
    """(start, end) of a date range such as 'Sep 2023 to present' or 'Sep 2023 -- Present'."""
    found = [f"{m.group(1)[:3].title()} {m.group(2)}" for m in MONTH_YEAR.finditer(text)]
    end_present = re.search(r"present|now|current", text, re.I)
    start = found[0] if found else ""
    end = "present" if end_present else (found[1] if len(found) > 1 else "")
    return start, end


# ---------- resume entries (titles, organizations, dates) ----------

def _read_group(s: str, i: int) -> tuple[str, int] | None:
    while i < len(s) and s[i] in " \t\r\n":
        i += 1
    if i >= len(s) or s[i] != "{":
        return None
    depth, j = 0, i
    while j < len(s):
        if s[j] == "{" and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif s[j] == "}" and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return None


def entries(tex: str) -> tuple[list[dict], bool]:
    """Resume entries found through `% jhs-entry:` declarations; (entries, declarations found)."""
    decls = [(m.group("section"), m.group("macro"), re.findall(r"\{([a-z-]+)\}", m.group("args")))
             for m in ENTRY_DECL.finditer(tex)]
    if not decls:
        return [], False
    body = tex_body(tex)
    sections = [(m.start(), m.group(1)) for m in re.finditer(r"\\section\*?\{([^{}]*)\}", body)]
    found = []
    for section, macro, roles_ in decls:
        for m in re.finditer(r"\\" + macro + r"(?![A-Za-z])", body):
            current = next((name for pos, name in reversed(sections) if pos < m.start()), "")
            if section and section.lower() not in current.lower():
                continue
            args, i = [], m.end()
            for _ in roles_:
                group = _read_group(body, i)
                if not group:
                    break
                args.append(group[0])
                i = group[1]
            if len(args) == len(roles_):
                found.append({r: tex_to_text(a).replace("\n", " ") for r, a in zip(roles_, args) if r != "ignore"})
    return found, True


def check_entries(tex: str, ledger_text: str) -> list[Finding]:
    out = []
    found, declared = entries(tex)
    ledger_roles = roles(ledger_text)
    for e in found:
        title = e.get("title", "")
        org = e.get("organization", "")
        where = f"{title} | {org}"
        match = [r for r in ledger_roles if _norm_label(r.title) == _norm_label(title)]
        if title and not match:
            out.append(Finding("title", title, where, "job title is not in Ledger [roles] as printed"))
            continue
        if org:
            match_org = [r for r in match or ledger_roles if _norm_label(r.organization) in _norm_label(org)
                         or _norm_label(org) in _norm_label(r.organization)]
            if not match_org:
                out.append(Finding("title", org, where, "organization is not in Ledger [roles] for this title"))
                continue
            match = match_org
        if "dates" in e and match:
            got = _range(e["dates"])
            if not any(_range(r.dates) == got for r in match):
                out.append(Finding("title", e["dates"], where,
                                   f"dates differ from Ledger [roles] ({'; '.join(r.dates for r in match)})"))
    return out


# ---------- the check ----------

INFLECTION = r"(?:e|es|ed|ing|s|er|ers)?"


def _stem(word: str) -> str:
    """A word without a common English ending, so tests, tested and testing all match "testing"."""
    for end in ("ing", "ed", "es", "s"):
        if word.lower().endswith(end) and len(word) - len(end) >= 3 and word[-len(end) - 1].isalpha():
            return word[: -len(end)]
    return word


def _word_pattern(word: str) -> str:
    """One word of a skill name: its hyphenated parts may also be written apart, and its last part inflected."""
    parts = word.split("-")
    out = [re.escape(p) for p in parts[:-1]]
    last = parts[-1]
    out.append(re.escape(_stem(last)) + (INFLECTION if last[-1:].isalpha() else ""))
    return r"[\s-]?".join(out)


def gap_pattern(name: str) -> re.Pattern:
    """A [skills-gaps] name in any common inflection ("ran A/B tests" for "A/B testing"); a two-word name also in
    reverse order with up to three words between ("fine-tuned two LLMs" for "LLM fine-tuning")."""
    words = name.split()
    forward = r"[\s-]+".join(_word_pattern(w) for w in words)
    alternatives = [forward]
    if len(words) == 2:
        alternatives.append(_word_pattern(words[1]) + r"(?:\W+\w+){0,3}?\W+" + _word_pattern(words[0]))
    return re.compile(r"(?<![\w])(?:" + "|".join(alternatives) + r")(?![\w])", re.I)


def acks(source: str) -> dict[str, str]:
    return {m.group("token").strip().lower(): m.group("reason").strip() for m in ACK.finditer(source)}


def _ctx(text: str, start: int, end: int) -> str:
    return text[max(0, start - 45):min(len(text), end + 45)].strip()


def check(text: str, ledger_text: str, kind: str = "resume", cfg=None, pack: dict | None = None,
          tex_source: str = "", source: str = "", posting: str | None = None) -> Report:
    """Run every check on `text` (the document as a reader sees it). `tex_source` adds the resume entry check.
    `posting` is the text of the posting.md beside a cover letter or form answer: a [recipient] acknowledgement
    there holds only for a number or date that the posting itself contains."""
    report = Report(kind=kind, source=source)
    add = report.findings.append
    flat = flatten(text)
    zero = section_zero(ledger_text)
    blocks = anchors(ledger_text)

    if EXAMPLE_MARKER in source or EXAMPLE_MARKER in text:
        add(Finding("example", EXAMPLE_MARKER, "", "the file still holds the fictional example content; replace it "
                    "with your Ledger facts and delete the marker line", ackable=False))

    # dates and numbers
    ledger_dates = _month_years(zero)
    scrubbed = URLISH.sub(" ", flat)
    scrubbed = PHONE.sub(lambda m: " " if len(re.sub(r"\D", "", m.group(0))) >= 8 else m.group(0), scrubbed)
    taken = []
    for m in MONTH_YEAR.finditer(scrubbed):
        taken.append((m.start(), m.end()))
        token = f"{m.group(1)[:3].title()} {m.group(2)}"
        if token not in ledger_dates:
            add(Finding("date", m.group(0), _ctx(scrubbed, m.start(), m.end()), "month and year not in Ledger section 0"))
    norm_zero = _norm_numbers(zero)
    for m in NUMBER.finditer(scrubbed):
        if any(a <= m.start() < b for a, b in taken):
            continue
        core = m.group("core").replace(",", "")
        suffix = (m.group("suffix") or "").strip().lower()
        unit = {"%": "%", "percent": "%", "×": "x", "x": "x", "times": "x", "million": "M", "m": "M",
                "billion": "B", "b": "B", "k": "K"}.get(suffix, "")
        pattern = r"(?<![\d.])" + re.escape(core) + (r"\s?" + re.escape(unit) if unit else "") + r"(?![\d])"
        span = TIME_UNIT.match(scrubbed, m.end()) if not unit else None
        if span:  # "6 years" is not backed by "6 hours": a duration must match with its unit
            unit = {"yr": "year"}.get(span.group(1).lower().rstrip("s"), span.group(1).lower().rstrip("s"))
            pattern = r"(?<![\d.])" + re.escape(core) + r"\+?\s?-?\s?" + ("(?:year|yr)" if unit == "year" else unit) + r"s?\b"
        if not re.search(pattern, norm_zero, re.I if unit in ("", "x") or span else 0):
            add(Finding("number", m.group(0).strip(), _ctx(scrubbed, m.start(), m.end()),
                        "not in Ledger section 0" + (f" with the unit {unit}" if unit else "")))

    # resume entries
    if tex_source:
        report.findings.extend(check_entries(tex_source, ledger_text))

    # hard lines
    scopes = SCOPES.get(kind, SCOPES["message"])
    for rule in hard_lines(ledger_text):
        if rule.banned is None or not (set(rule.scope) & scopes):
            continue
        for m in rule.banned.finditer(flat):
            add(Finding("hard-line", m.group(0), _ctx(flat, m.start(), m.end()), rule.rule, rule=rule.id))

    # gap skills
    for skill in table_column(ledger_text, "skills-gaps"):
        name = re.sub(r"\s*\(.*?\)\s*", " ", skill).strip()
        if not name:
            continue
        for m in gap_pattern(name).finditer(flat):
            add(Finding("gap-skill", m.group(0), _ctx(flat, m.start(), m.end()),
                        "listed in [skills-gaps]; stays off until /job-hunt-studio:interview-drill passes"))

    # never print
    if kind in NEVER_PRINT_KINDS:
        banned = []
        auth = (cfg.get("candidate.work_authorization") if cfg else "") or ""
        if auth.strip():
            banned.append(re.escape(auth.strip()))
        never = blocks.get("never-print", "").lower()
        if "authori" in never or "visa" in never or "citizen" in never:
            banned.append(r"work authori[sz]ation|work permit|\bvisa\b|citizen(ship)?\b|permanent resident")
        if "salary" in never or "compensation" in never:
            banned.append(r"\bsalary\b|current compensation")
        banned += [re.escape(q) for q in re.findall(r'"([^"]{3,})"', blocks.get("never-print", ""))]
        spans: list[tuple[int, int]] = []
        for pat in banned:
            for m in re.finditer(pat, flat, re.I):
                if any(a < m.end() and m.start() < b for a, b in spans):
                    continue  # already reported inside a longer match
                spans.append((m.start(), m.end()))
                add(Finding("never-print", m.group(0), _ctx(flat, m.start(), m.end()), "a [never-print] item"))

    # voice: dashes
    punct = set((cfg.get("writing.banned_punctuation") if cfg else None) or ["em-dash", "en-dash", "double-hyphen"])
    prose = DATE_RANGE.sub(" ", flat)
    checks = []
    if "em-dash" in punct:
        checks.append(("—", "em dash"))
    if "en-dash" in punct:
        checks.append(("–", "en dash outside a date range"))
    if "double-hyphen" in punct and kind != "resume":
        checks.append(("--", "double hyphen"))
    for mark, label in checks:
        for m in re.finditer(re.escape(mark), prose):
            add(Finding("dash", mark, _ctx(prose, m.start(), m.end()), label))

    # voice: stock phrases
    phrases = list(STOCK_PHRASES)
    phrases += list((cfg.get("writing.banned_phrases") if cfg else None) or [])
    phrases += list((pack or {}).get("buzzwords_to_avoid") or [])
    for phrase in dict.fromkeys(p.strip() for p in phrases if p and p.strip()):
        for m in re.finditer(r"(?<![\w])" + re.escape(phrase) + r"(?![\w])", flat, re.I):
            add(Finding("phrase", m.group(0), _ctx(flat, m.start(), m.end()), "stock phrase"))

    # acknowledgements in the source
    ledger_refs = set(blocks) | set(re.findall(r"^## (\d{4}-\d{2}-\d{2})", ledger_text, re.M))
    for token, reason in acks(source).items():
        cites = re.findall(r"\[([a-z0-9:_-]+)\]", reason) + re.findall(r"\d{4}-\d{2}-\d{2}", reason)
        valid = any(c in ledger_refs for c in cites)
        # In a message, cover letter or form answer, a number or date about the person or company written to (their
        # paper's year, a figure from the posting) is not a claim about the user; "[recipient]" acknowledges only
        # those two kinds of warning.
        about_recipient = kind in RECIPIENT_KINDS and RECIPIENT in cites
        for f in report.findings:
            if not (token == f.match.lower() or (len(token) >= 4 and token in f.match.lower())):
                continue
            if f.kind in UNACKABLE:
                f.ackable = False
                f.ack_problem = f"acknowledgement ignored: a {f.kind} warning is fixed in the text (or the Ledger), " \
                                "never acknowledged"
            elif f.kind == "hard-line" and f.rule not in reason:
                f.ack_problem = f"acknowledgement ignored: a hard-line acknowledgement must name the rule ({f.rule}) " \
                                "and say why the sentence keeps it"
            elif valid or f.kind == "hard-line":  # a hard line's rule id is its [hard-lines] reference
                f.ack = reason
            elif about_recipient and f.kind in ("number", "date"):
                problem = recipient_problem(f, kind, posting)
                if problem:
                    f.ack_problem = problem
                else:
                    f.ack = reason
            else:
                f.ack_problem = "acknowledgement ignored: its reason cites no Ledger block or dated entry"
    return report


def recipient_problem(f: Finding, kind: str, posting: str | None) -> str:
    """Why a [recipient] acknowledgement does not hold for this finding, or "" when it does."""
    if re.search(r"with the unit (year|month|week|day|hour|minute)", f.detail):
        return ("acknowledgement ignored: [recipient] never covers a duration (years of experience are about you; "
                "they must match the Ledger)")
    if kind in ("cover-letter", "form"):
        # the same number, whole (17 is not backed by 2017), in the posting's text (not in a link)
        wanted = _norm_numbers(f.match).replace(",", "").strip().lower()
        body = _norm_numbers(URLISH.sub(" ", posting or "")).replace(",", "").lower()
        if posting is None or not re.search(r"(?<![\w.])" + re.escape(wanted) + r"(?![\w]|\.\d)", body):
            return ("acknowledgement ignored: in a cover letter or form answer, [recipient] covers only a number or "
                    "date that the posting.md beside it contains")
    return ""


def format_report(report: Report) -> str:
    lines = [f"Fact and voice check ({report.kind}): warnings to resolve before READY; they never fail the build"]
    for f in sorted(report.findings, key=lambda f: (f.resolved, f.kind)):
        status = "OK  " if f.resolved else "WARN"
        rule = f" {f.rule}" if f.rule else ""
        lines.append(f"  {status} {f.kind}{rule}: \"{f.match}\" ({f.detail})")
        if f.context and f.context != f.match:
            lines.append(f"       in: ...{f.context}...")
        if f.resolved:
            lines.append(f"       acknowledged: {f.ack}")
        elif f.ack_problem:
            lines.append(f"       {f.ack_problem}")
    n_open, n_ok = len(report.open), len(report.findings) - len(report.open)
    lines.append(f"  FACTS: {'CLEAN' if not n_open else f'{n_open} TO RESOLVE'}"
                 f" ({n_ok} acknowledged; fix each warning, or acknowledge a true one with a fact-ok line citing "
                 "the Ledger)")
    return "\n".join(lines)


def infer_kind(path: Path) -> str:
    name = path.name.lower()
    if path.suffix == ".tex":
        return "resume"
    for key, kind in (("linkedin", "linkedin"), ("cover", "cover-letter"), ("form", "form"),
                      ("interview", "interview"), ("drill", "interview")):
        if key in name:
            return kind
    return "message"


def run_file(path: Path, pdf: Path | None = None, kind: str | None = None) -> Report:
    from config import ConfigError, load, pack_keywords

    try:
        cfg = load(path.parent)
    except ConfigError:  # a file outside the workspace: use the one we run in
        cfg = load()
    source = path.read_text(encoding="utf-8")
    kind = kind or infer_kind(path)
    if path.suffix == ".tex":
        if pdf is None:
            guess = path.parent / "build" / (path.stem + ".pdf")
            if guess.is_file() and guess.stat().st_mtime >= path.stat().st_mtime:
                pdf = guess
        text = pdf_to_text(pdf) if pdf else tex_to_text(source)
        tex_source = source
    else:
        text, tex_source = md_to_text(source), ""
    posting_file = path.parent / "posting.md"
    posting = posting_file.read_text(encoding="utf-8") if posting_file.is_file() else None
    return check(text, cfg.ledger_text(), kind=kind, cfg=cfg, pack=pack_keywords(cfg), tex_source=tex_source,
                 source=source, posting=posting)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Compare a document with the Evidence Ledger (warnings only).")
    parser.add_argument("file", type=Path)
    parser.add_argument("--pdf", type=Path, help="compiled PDF of a .tex file (default: build/<name>.pdf if newer)")
    parser.add_argument("--kind", choices=sorted(SCOPES))
    args = parser.parse_args()
    from config import ConfigError

    try:
        report = run_file(args.file.resolve(), args.pdf, args.kind)
    except ConfigError as exc:
        print(f"MISSING  {exc}")
        return 1
    print(f"File: {args.file}")
    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
