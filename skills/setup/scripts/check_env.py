#!/usr/bin/env python3
"""Check the tools Job Hunt Studio needs and print what is missing.

Standard library only. Run with any Python 3.9+:
    python check_env.py [--python PATH_TO_VENV_PYTHON] [--json]

--python checks the Python packages inside that interpreter (the workspace venv);
without it, the interpreter running this script is checked.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SYSTEM = platform.system()  # "Windows", "Darwin", "Linux"

TEX_HINT = {
    "Windows": "install MiKTeX (miktex.org) or TeX Live (tug.org/texlive)",
    "Darwin": "install MacTeX (tug.org/mactex) or BasicTeX plus latexmk",
    "Linux": "install TeX Live, e.g. 'sudo apt install texlive-latex-extra latexmk'",
}[SYSTEM if SYSTEM in ("Windows", "Darwin", "Linux") else "Linux"]

POPPLER_HINT = {
    "Windows": "MiKTeX ships pdftoppm; otherwise install Poppler for Windows",
    "Darwin": "'brew install poppler'",
    "Linux": "'sudo apt install poppler-utils'",
}[SYSTEM if SYSTEM in ("Windows", "Darwin", "Linux") else "Linux"]

# (name, required, what it is for, how to get it)
BINARIES = [
    ("git", True, "versions and approved-resume tags", "git-scm.com"),
    ("latexmk", True, "builds the resume PDF", TEX_HINT),
    ("pdflatex", True, "resume engine", TEX_HINT),
    ("pdftoppm", False, "visual check of the resume (page images)", POPPLER_HINT),
    ("pdftotext", False, "reads the resume as a recruiter's tools do (the checks fall back to pypdf)", POPPLER_HINT),
    ("pdfinfo", False, "PDF details for the reviewer (page count also comes from pypdf)", POPPLER_HINT),
    ("latexdiff", False, "change-tracked PDF against the approved version", "ships with TeX Live and MiKTeX"),
    ("gh", False, "higher GitHub API limits for /outreach", "cli.github.com"),
]

# (import name, pip name, required, what it is for)
PACKAGES = [
    ("pypdf", "pypdf", True, "ATS parse check"),
    ("pdfminer", "pdfminer.six", True, "ATS parse check (second extractor)"),
    ("PIL", "pillow", True, "visual check"),
    ("yaml", "pyyaml", True, "reads jhs.yaml"),
    ("jobspy", "python-jobspy", False, "LinkedIn and Indeed search (only if chosen at setup)"),
]


def resolve_python(python: str) -> str | None:
    """Return an absolute path to the interpreter, or None if it does not exist.

    Relative paths with forward slashes (".venv/Scripts/python") fail on Windows,
    so resolve them and add ".exe" where needed.
    """
    found = shutil.which(python)
    if found:
        return found
    p = Path(python).expanduser().resolve()
    for candidate in (p, p.with_suffix(".exe")):
        if candidate.is_file():
            return str(candidate)
    return None


def check_packages(python: str) -> dict[str, bool]:
    code = (
        "import importlib.util, json, sys;"
        f"names={[p[0] for p in PACKAGES]!r};"
        "print(json.dumps({n: importlib.util.find_spec(n) is not None for n in names}))"
    )
    out = subprocess.run([python, "-c", code], capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or "{}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--python", default=sys.executable, help="interpreter whose packages to check")
    ap.add_argument("--json", action="store_true", help="print machine-readable results")
    args = ap.parse_args()

    python = resolve_python(args.python)
    if python is None:
        print(f"Interpreter not found: {args.python}. Check the venv path (Windows: .venv\\Scripts\\python.exe; "
              "macOS and Linux: .venv/bin/python).", file=sys.stderr)
        return 2
    try:
        found = check_packages(python)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Could not run {python}: {exc}", file=sys.stderr)
        return 2

    results = {"system": SYSTEM, "python": sys.version.split()[0], "binaries": [], "packages": []}
    binaries = list(BINARIES)
    if SYSTEM == "Windows":
        # MiKTeX's latexmk is a Perl script: it is on PATH but fails without Perl.
        binaries.append(("perl", True, "latexmk needs it on Windows", "install Strawberry Perl (strawberryperl.com)"))
    for name, required, purpose, hint in binaries:
        results["binaries"].append(
            {"name": name, "found": shutil.which(name) is not None, "required": required, "purpose": purpose, "hint": hint}
        )
    for mod, pip_name, required, purpose in PACKAGES:
        results["packages"].append(
            {"name": pip_name, "found": bool(found.get(mod)), "required": required, "purpose": purpose,
             "hint": f"{python} -m pip install {pip_name}"}
        )
    missing_required = [x["name"] for x in results["binaries"] + results["packages"] if x["required"] and not x["found"]]
    results["ok"] = not missing_required

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"System: {SYSTEM}; Python {results['python']}; packages checked in: {python}")
        for group in ("binaries", "packages"):
            for x in results[group]:
                mark = "ok     " if x["found"] else ("MISSING" if x["required"] else "absent ")
                need = "required" if x["required"] else "optional"
                line = f"  {mark} {x['name']:<14} {need:<8} {x['purpose']}"
                if not x["found"]:
                    line += f"  ->  {x['hint']}"
                print(line)
        print("All required tools found." if results["ok"] else "Missing required: " + ", ".join(missing_required))
    return 0 if results["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
