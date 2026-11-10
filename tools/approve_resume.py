"""Approve the base resume as the next version, after the user has said so explicitly.

Usage (from the workspace folder, with the workspace Python):
    python approve_resume.py "<one-line summary of what changed>" "<review score, for example 88/100 READY>"

1. Refuses when the base source (jhs.yaml resume.base_tex) has uncommitted changes, still holds the fictional
   example content, or does not build. The tag must point at the approved text.
2. Builds it with pdfLaTeX.
3. Tags the current commit <resume.tag_prefix><N> (next N). Approved tags are never moved or deleted.
4. Archives the version in resumes/approved/v<N>_<date>/ (PDF, source, NOTES.md).
5. Replaces resumes/current/<resume.output_name> (the file to send) and empties resumes/draft/.
6. Commits the archive locally. Never pushes.
"""
from __future__ import annotations

import datetime as dt
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_resume import build, pages  # noqa: E402
from config import approved_tags, git, have, load, utf8_stdout  # noqa: E402
from fact_check import EXAMPLE_MARKER  # noqa: E402


def fail(msg: str) -> int:
    print(f"NOT APPROVED: {msg}")
    return 1


def main() -> int:
    utf8_stdout()
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print('usage: python approve_resume.py "<what changed>" "<review score>"')
        return 2
    summary, score = sys.argv[1].strip(), (sys.argv[2].strip() if len(sys.argv) > 2 else "")
    if not have("latexmk"):
        return fail("latexmk not found")
    cfg = load()
    root, base = cfg.root, cfg.base_tex
    if git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        return fail("this workspace is not a git repository")
    if not base.is_file():
        return fail(f"{base} does not exist")
    rel = base.relative_to(root).as_posix()
    if git(root, "ls-files", "--error-unmatch", rel).returncode != 0:
        return fail(f"{rel} is not committed yet; commit it first so the tag points at the approved text")
    if git(root, "status", "--porcelain", "--", rel).stdout.strip():
        return fail(f"{rel} has uncommitted changes; commit them first so the tag points at the approved text")
    if EXAMPLE_MARKER in base.read_text(encoding="utf-8"):
        return fail("the base still holds the fictional example content")

    tags = approved_tags(root, cfg.tag_prefix)
    if tags and git(root, "diff", "--quiet", tags[-1][1], "HEAD", "--", rel).returncode == 0:
        return fail(f"{rel} is unchanged since {tags[-1][1]}; there is nothing new to approve")
    n = (tags[-1][0] if tags else 0) + 1
    tag = f"{cfg.tag_prefix}{n}"
    day = dt.date.today().isoformat()
    dest = root / "resumes" / "approved" / f"v{n}_{day}"
    if git(root, "rev-parse", "-q", "--verify", f"refs/tags/{tag}").returncode == 0 or dest.exists():
        return fail(f"{tag} or {dest} already exists; nothing was changed")

    pdf = build(base, base.parent / "build")
    if pdf is None:
        return fail("the base did not build")
    want = int(cfg.get("resume.pages", 1) or 1)
    if pages(pdf) != want:
        return fail(f"the PDF has {pages(pdf)} pages; jhs.yaml resume.pages says {want}")

    stem = Path(cfg.output_name).stem
    dest.mkdir(parents=True)
    current = root / "resumes" / "current"
    current.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf, dest / f"{stem}_v{n}.pdf")
    shutil.copyfile(base, dest / f"{base.stem}_v{n}.tex")
    shutil.copyfile(pdf, current / cfg.output_name)
    for old in current.glob("*.pdf"):
        if old.name != cfg.output_name:
            old.unlink()
    tagged = git(root, "tag", "-a", tag, "-m", f"Approved for applications: {summary}")
    if tagged.returncode != 0:
        shutil.rmtree(dest)
        return fail(f"git tag failed: {tagged.stderr.strip()}")
    commit = git(root, "rev-parse", "--short", f"{tag}^{{commit}}").stdout.strip()
    (dest / "NOTES.md").write_text(
        f"# Resume v{n} (approved {day})\n\n"
        f"- Git tag: `{tag}` (commit {commit})\n"
        f"- What changed: {summary}\n"
        f"- Readiness review: {score or 'see the review report in the build folder'}\n"
        f"- Files: `{stem}_v{n}.pdf` (as sent), `{base.stem}_v{n}.tex` (source)\n", encoding="utf-8")
    (current / "README.md").write_text(
        "# Current resume\n\n"
        f"`{cfg.output_name}` is the latest approved version: **v{n}**, approved {day} (tag `{tag}`).\n"
        "Every approved version is archived in `resumes/approved/`.\n", encoding="utf-8")
    draft = root / "resumes" / "draft"
    draft.mkdir(parents=True, exist_ok=True)
    for old in draft.glob("*.pdf"):
        if git(root, "ls-files", "--error-unmatch", old.relative_to(root).as_posix()).returncode == 0:
            git(root, "rm", "-q", "--cached", old.relative_to(root).as_posix())
        old.unlink()
    (draft / "README.md").write_text(
        "# Draft resume (NOT approved, do not send)\n\n"
        f"No draft is pending: v{n} was approved {day} and is in `resumes/current/`.\n", encoding="utf-8")
    git(root, "add", "--", dest.relative_to(root).as_posix(), "resumes/current", "resumes/draft/README.md")
    done = git(root, "commit", "-q", "-m", f"Archive approved resume v{n} ({day})")
    if done.returncode != 0:
        print(f"Tagged {tag}, but the archive commit failed: {done.stderr.strip() or done.stdout.strip()}")
        return 1
    print(f"Approved: {tag} -> {dest.relative_to(root).as_posix()}; resumes/current/{cfg.output_name} updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
