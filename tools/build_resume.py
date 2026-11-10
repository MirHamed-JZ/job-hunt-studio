"""Build a resume PDF with latexmk and put copies where they belong.

Usage (from the workspace folder, with the workspace Python):
    python build_resume.py RESUME.tex

- Builds with pdfLaTeX into the `build/` folder next to the .tex. If that PDF is open in a viewer that locks it
  (common on Windows), builds into `build/preview/` instead and says so.
- Copies the PDF to `build/<resume.output_name>` (the file employers receive).
- For the base resume (jhs.yaml resume.base_tex), when its source differs from the latest approved tag, also copies
  it to `resumes/draft/<name>_DRAFT.pdf` and notes it in `resumes/draft/README.md` (a draft is never sent).
- Prints the page count. Exit code 0 on success, 1 when the build fails (with the first LaTeX error).
"""
from __future__ import annotations

import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import git, have, latest_tag, load, utf8_stdout  # noqa: E402


def locked(pdf: Path) -> bool:
    if not pdf.exists():
        return False
    try:
        with open(pdf, "ab"):
            return False
    except PermissionError:
        return True


def first_error(log: Path) -> str:
    if not log.is_file():
        return "no log written"
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!"):
            where = next((ln for ln in lines[i:i + 12] if re.match(r"l\.\d+", ln)), "")
            return f"{line} {where}".strip()
    return "see the log: " + str(log)


def build(tex: Path, outdir: Path) -> Path | None:
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", f"-outdir={outdir}", tex.name]
    proc = subprocess.run(cmd, cwd=tex.parent, capture_output=True, text=True, encoding="utf-8", errors="replace")
    pdf = outdir / (tex.stem + ".pdf")
    if proc.returncode != 0 or not pdf.is_file():
        print(f"BUILD FAILED: {first_error(outdir / (tex.stem + '.log'))}")
        return None
    return pdf


def pages(pdf: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages)


def main() -> int:
    utf8_stdout()
    if len(sys.argv) != 2:
        print("usage: python build_resume.py RESUME.tex")
        return 2
    if not have("latexmk"):
        print("latexmk not found: install a TeX distribution (run /job-hunt-studio:setup tools for the steps), "
              "then restart Claude Code.")
        return 1
    cfg = load()
    tex = Path(sys.argv[1]).resolve()
    if not tex.is_file():
        print(f"No such file: {tex}")
        return 1
    outdir = tex.parent / "build"
    if locked(outdir / (tex.stem + ".pdf")) or locked(outdir / cfg.output_name):
        outdir = outdir / "preview"
        print(f"The PDF in {tex.parent / 'build'} is open in a viewer; building into {outdir}. "
              "Ask the user to close the viewer.")
    pdf = build(tex, outdir)
    if pdf is None:
        return 1
    submit = outdir / cfg.output_name
    if submit.resolve() != pdf.resolve():
        shutil.copyfile(pdf, submit)
    n = pages(pdf)
    want = int(cfg.get("resume.pages", 1) or 1)
    print(f"Built: {pdf}")
    print(f"File to send: {submit}")
    print(f"Pages: {n}" + ("" if n == want else f" (jhs.yaml resume.pages says {want})"))

    if tex == cfg.base_tex.resolve():
        tag = latest_tag(cfg.root, cfg.tag_prefix)
        rel = tex.relative_to(cfg.root).as_posix()
        changed = tag is None or git(cfg.root, "diff", "--quiet", tag, "--", rel).returncode != 0 or \
            bool(git(cfg.root, "status", "--porcelain", "--", rel).stdout.strip())
        if changed:
            draft_dir = cfg.root / "resumes" / "draft"
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft = draft_dir / (Path(cfg.output_name).stem + "_DRAFT.pdf")
            shutil.copyfile(pdf, draft)
            since = f"differs from {tag}" if tag else "no approved version yet"
            (draft_dir / "README.md").write_text(
                "# Draft resume (NOT approved, do not send)\n\n"
                f"`{draft.name}`: built {dt.date.today().isoformat()} from `{rel}` ({since}). "
                "Not reviewed yet: run /job-hunt-studio:review-resume.\n", encoding="utf-8")
            print(f"Draft copy (do not send): {draft}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
