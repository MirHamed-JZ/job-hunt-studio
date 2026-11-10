"""Resume lint: the writing rules a script can check, plus the fact and voice check against the Ledger.

Usage (from the workspace folder, with the workspace Python):
    python resume_lint.py RESUME.tex RESUME.pdf [--links]
      --links  also open every link in the PDF (needs the network)

Two parts:
  1. Mechanics (gate G3 of the review rubric): FAIL items must be fixed; WARN items are judgment calls for the
     reviewer. FAIL: example content left in, page count, pronouns in bullets, bullets that mix final periods,
     missing email, broken links.
  2. Fact and voice check (tools/fact_check.py): warnings that must be fixed or acknowledged before READY.
Exit code 1 when a mechanics item FAILs; the fact and voice check never changes the exit code.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import load, pack_keywords, utf8_stdout  # noqa: E402
from fact_check import EXAMPLE_MARKER, check, format_report, pdf_to_text, tex_body, tex_to_text  # noqa: E402

PRONOUNS = re.compile(r"\b(I|me|my|mine|we|our|ours|us)\b")
SPELLED = re.compile(r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|hundred|thousand)\b", re.I)
WEAK = re.compile(r"\b(helped|assisted|worked on|responsible for|involved in|participated|various|several)\b", re.I)
NOT_A_VERB = {"the", "a", "an", "my", "our", "this", "that", "responsible", "various", "several", "team", "duties",
              "tasks", "worked", "helped", "assisted"}
BULLET_SECTIONS = re.compile(r"experience|employment|work|project|research|education|leadership|volunteer|activit",
                             re.I)
NO_VERB_SECTIONS = re.compile(r"education", re.I)
SKIP_SECTIONS = re.compile(r"skill|publication|summary|profile|interest|language|certification", re.I)
BULLET_GLYPHS = "•∙●▪◦·"

results: list[tuple[str, str, str]] = []


def report(level: str, rule: str, detail: str) -> None:
    results.append((level, rule, detail))


def bullets(tex: str) -> list[tuple[str, int, str]]:
    """(section, list number, plain text) for every bullet in sections that hold bullets."""
    body = tex_body(tex)
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"\\section\*?\{([^{}]*)\}", body)]
    names = [name for _, name in marks]
    use_named = any(BULLET_SECTIONS.search(n) for n in names)
    out = []
    for k, (pos, name) in enumerate(marks):
        if SKIP_SECTIONS.search(name) or (use_named and not BULLET_SECTIONS.search(name)):
            continue
        chunk = body[pos:marks[k + 1][0] if k + 1 < len(marks) else len(body)]
        for m in re.finditer(r"\\(item|resumeItem)(?![A-Za-z])", chunk):
            rest = chunk[m.end():]
            if m.group(1) == "resumeItem" or rest.lstrip().startswith("{"):
                text, depth = "", 0
                for i, ch in enumerate(rest.lstrip()):
                    depth += (ch == "{") - (ch == "}")
                    text += ch
                    if depth == 0 and i > 0:
                        break
            else:
                text = re.split(r"\\item(?![A-Za-z])|\\end\{|\\resumeItem|\n\s*\n", rest, maxsplit=1)[0]
            plain = " ".join(tex_to_text(text).replace("•", " ").split())
            group = len(re.findall(r"\\end\{(itemize|highlights)\}|\\resumeItemListEnd", chunk[:m.start()]))
            if plain:
                out.append((name, group, plain))
    return out


def lint_bullets(tex: str) -> int:
    found = bullets(tex)
    verbs: dict[tuple[str, int], list[str]] = {}
    for section, group, text in found:
        if PRONOUNS.search(text):
            report("FAIL", "no pronouns in bullets", text[:80])
        if SPELLED.search(text):
            report("WARN", "digits for numbers", text[:80])
        if WEAK.search(text):
            report("WARN", "weak phrasing", text[:80])
        first = text.split()[0].strip(",.:;").lower() if text.split() else ""
        if not NO_VERB_SECTIONS.search(section):
            if first in NOT_A_VERB or not first[:1].isalpha():
                report("WARN", "start with an action verb", f"'{first}' in: {text[:60]}")
            verbs.setdefault((section, group), []).append(first)
    for (section, _), words in verbs.items():
        repeated = sorted({w for w in words if words.count(w) > 1})
        if repeated:
            report("WARN", "vary verbs within an entry", f"{section}: {repeated}")
    with_period = [t for _, _, t in found if t.endswith(".")]
    without = [t for _, _, t in found if not t.endswith(".")]
    if with_period and without:
        minority = without if len(without) <= len(with_period) else with_period
        for t in minority[:3]:
            report("FAIL", "bullets end the same way (all with a final period, or none)", t[:80])
    return len(found)


def lint_pdf(pdf: Path, pages_wanted: int, cfg) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf))
    if len(reader.pages) != pages_wanted:
        report("FAIL", f"page count is {pages_wanted} (jhs.yaml resume.pages)", f"{len(reader.pages)} pages")
    text = pdf_to_text(pdf)
    email = cfg.get("candidate.email") or ""
    if email and email.lower() not in text.lower():
        report("FAIL", "email from jhs.yaml on the resume", f"{email} not found")
    links = []
    for page in reader.pages:
        for a in page.get("/Annots") or []:
            uri = a.get_object().get("/A", {}).get("/URI")
            if uri:
                links.append(str(uri))
    linkedin = cfg.get("candidate.linkedin") or ""
    if linkedin and not any("linkedin.com/in/" in u for u in links):
        report("WARN", "LinkedIn link", "jhs.yaml has a LinkedIn URL but the PDF has no LinkedIn link")
    if shutil.which("pdftotext"):
        layout = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"],
                                capture_output=True).stdout.decode("utf-8", errors="replace")
        lines = [ln for ln in layout.splitlines() if ln.strip()]
        groups, current, indent = [], None, 0
        for ln in lines:
            stripped = ln.lstrip()
            if stripped[:1] in BULLET_GLYPHS:
                indent = len(ln) - len(stripped) + 2
                current = [stripped]
                groups.append(current)
            elif current is not None and len(ln) - len(stripped) >= indent - 1 and len(ln) - len(stripped) < 20:
                current.append(stripped)
            else:
                current = None
        for g in groups:
            if len(g) > 2:
                report("WARN", "bullets 1 to 2 lines", f"{len(g)} lines: {g[0][:60]}")
            if len(g) >= 2 and len(g[-1].strip()) < 18:
                report("WARN", "no orphan word on a bullet's last line", f"'{g[-1].strip()}' after: {g[0][:50]}")
        heads = [i for i, ln in enumerate(lines) if ln.strip() in ("Summary", "Profile", "SUMMARY", "PROFILE")]
        if heads:
            i = heads[0]
            nxt = next((j for j in range(i + 1, len(lines)) if lines[j].strip() and lines[j].strip()[0].isupper()
                        and len(lines[j].strip().split()) <= 3 and not lines[j].strip().endswith(".")), None)
            if nxt and nxt - i - 1 > 4:
                report("WARN", "summary 2 to 4 lines", f"{nxt - i - 1} lines")
    else:
        report("NOTE", "layout checks", "pdftotext not found; bullet length and orphan checks skipped")
    return links


RESERVED = re.compile(r"^https?://([^/]+\.)?example\.(com|org|net)(/|$)", re.I)  # RFC 2606 example domains
# LinkedIn forbids automated access (User Agreement 8.2) and answers bots with status 999: never request it
# (the posting guard's hostname check: linkedin.com and its short links, any subdomain, port or trailing dot).
from posting_guard import LinkedInLink, NoLinkedInRedirects, is_linkedin  # noqa: E402


def check_links(links: list[str]) -> None:
    for u in links:
        if u.startswith(("mailto:", "tel:")):
            continue
        if RESERVED.match(u):
            print(f"  link skipped (reserved example domain): {u}")
            continue
        if is_linkedin(u):
            print(f"  link not checked (LinkedIn forbids automated access; open it yourself): {u}")
            continue
        try:
            req = urllib.request.Request(u, method="GET", headers={"User-Agent": "Mozilla/5.0 (job-hunt-studio)"})
            code = urllib.request.build_opener(NoLinkedInRedirects()).open(req, timeout=15).status
        except LinkedInLink:  # the link redirects to LinkedIn: not followed
            print(f"  link not checked (it leads to LinkedIn, which forbids automated access; open it yourself): {u}")
            continue
        except urllib.error.HTTPError as exc:
            code = exc.code
        except Exception as exc:  # no answer: offline, a proxy, or certificates this Python cannot verify
            report("WARN", "link could not be checked from this computer (open it in a browser)",
                   f"{u} -> {str(getattr(exc, 'reason', exc))[:90]}")
            print(f"  link not checked: {u}")
            continue
        if code != 200:  # LinkedIn answers 999 to scripts: unverifiable, not broken
            report("WARN" if "linkedin.com" in u else "FAIL", "link opens", f"{u} -> {code}")
        print(f"  link {code}: {u}")


def main() -> int:
    utf8_stdout()
    parser = argparse.ArgumentParser(description="Resume lint and fact check.")
    parser.add_argument("tex", type=Path)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--links", action="store_true")
    args = parser.parse_args()
    cfg = load()
    tex = args.tex.read_text(encoding="utf-8")

    if EXAMPLE_MARKER in tex:
        report("FAIL", "no example content", f"{EXAMPLE_MARKER} line found: the file still holds the fictional "
                                             "example; replace every fact with your Ledger facts, then delete it")
    n = lint_bullets(tex)
    links = lint_pdf(args.pdf, int(cfg.get("resume.pages", 1) or 1), cfg)
    if args.links:
        check_links(links)

    print(f"Resume lint: {args.tex}")
    for level, rule, detail in results:
        print(f"  {level:4} {rule}: {detail}")
    fails = [r for r in results if r[0] == "FAIL"]
    warns = [r for r in results if r[0] == "WARN"]
    print(f"  links found: {len(links)}; bullets checked: {n}")
    print(f"  RESULT: {'PASS' if not fails else f'{len(fails)} FAIL'} ({len(warns)} WARN)")
    print()
    facts = check(pdf_to_text(args.pdf), cfg.ledger_text(), kind="resume", cfg=cfg, pack=pack_keywords(cfg),
                  tex_source=tex, source=tex)
    print(format_report(facts))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
