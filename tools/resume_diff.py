"""Change-tracked PDF of a resume against an approved version (latexdiff): deletions struck out, additions underlined.

Usage (from the workspace folder, with the workspace Python):
    python resume_diff.py NEW.tex [--rev TAG] [--old-path PATH] [--copy-to FILE.tex]
      --rev       the version to compare with (default: the latest approved tag)
      --old-path  the file to read at that version (default: jhs.yaml resume.base_tex; a tailored copy does not
                  exist at the tag, so the base is the right old file)
      --copy-to   also copy the diff .tex there (an application folder keeps it as diff_vs_v<N>.tex)
Output: build/<name>_diff_vs_<TAG>.tex and .pdf next to NEW.tex.

Optional: needs latexdiff (with Perl) and LuaLaTeX. When they are missing or the diff does not compile, it says so
and exits 0; the application's changes.md still records what changed.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import git, have, latest_tag, load, utf8_stdout  # noqa: E402


def main() -> int:
    utf8_stdout()
    parser = argparse.ArgumentParser(description="latexdiff of a resume against an approved version")
    parser.add_argument("tex", type=Path)
    parser.add_argument("--rev")
    parser.add_argument("--old-path")
    parser.add_argument("--copy-to", type=Path)
    args = parser.parse_args()
    cfg = load()
    rev = args.rev or latest_tag(cfg.root, cfg.tag_prefix)
    if not rev:
        print("SKIPPED: no approved version to compare with.")
        return 0
    if not (have("latexdiff") and have("latexmk") and have("lualatex")):
        print("SKIPPED: latexdiff, latexmk or lualatex not found; changes.md records the changes instead.")
        return 0
    tex = args.tex.resolve()
    old_path = args.old_path or cfg.base_tex.relative_to(cfg.root).as_posix()
    out = tex.parent / "build"
    out.mkdir(parents=True, exist_ok=True)
    old = git(cfg.root, "show", f"{rev}:{old_path}")
    if old.returncode != 0:
        print(f"SKIPPED: cannot read {old_path} at {rev}: {old.stderr.strip()}")
        return 0
    old_file, new_file = out / f"{tex.stem}_old.tex", out / f"{tex.stem}_new.tex"
    old_file.write_text(old.stdout, encoding="utf-8")
    shutil.copyfile(tex, new_file)
    name = f"{tex.stem}_diff_vs_{rev}"
    diff = subprocess.run(["latexdiff", "--type=LUAUNDERLINE", "--exclude-textcmd=textbf,textit",
                           str(old_file), str(new_file)], capture_output=True)
    if diff.returncode != 0 or not diff.stdout:
        print(f"SKIPPED: latexdiff failed: {diff.stderr.decode('utf-8', errors='replace').strip()[:300]}")
        return 0
    (out / f"{name}.tex").write_bytes(diff.stdout)
    build = subprocess.run(["latexmk", "-lualatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
                           cwd=out, capture_output=True)
    if args.copy_to:
        shutil.copyfile(out / f"{name}.tex", args.copy_to)
        print(f"Diff source copied to: {args.copy_to}")
    if build.returncode != 0:
        print(f"PARTIAL: the diff .tex is in {out}, but it did not compile (see {name}.log); "
              "changes.md records the changes.")
        return 0
    print(f"Diff PDF: {out / (name + '.pdf')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
