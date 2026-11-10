#!/usr/bin/env bash
# Shared eval fixture: turns the run's empty workspace into the fictional persona's workspace, the way
# `/job-hunt-studio:setup example` would: jhs.yaml, the Ledger, the workspace templates, a base resume from the
# jakes layout, a venv with the plugin's packages, and a git repository with one commit.
# Each case's fixture.sh runs it; it needs --scaffold, Python 3 and git (and the network for pip).
# With --no-venv it skips the venv, for cases that do not let Claude run commands.
set -euo pipefail
plugin=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

cp -R "$plugin/templates/workspace/." .
cp "$plugin/examples/persona/jhs.yaml" jhs.yaml
cp "$plugin/examples/persona/docs/Evidence_Ledger.md" docs/Evidence_Ledger.md
for f in $(grep -rl '{{' . || true); do
  sed -e 's/{{candidate.name}}/Alex Rivera/g' -e "s/{{date}}/$(date +%F)/g" \
      -e 's/{{resume.tag_prefix}}/resume-approved-v/g' -e 's/{{applications.followup_days}}/7/g' "$f" > "$f.tmp"
  mv "$f.tmp" "$f"
done
for d in applications/leads interview/notes linkedin resumes/base resumes/draft; do
  mkdir -p "$d" && touch "$d/.gitkeep"
done
grep -v 'JHS-EXAMPLE-CONTENT' "$plugin/templates/resume/jakes/Resume.tex" > resumes/base/Resume.tex

if [ "${1:-}" != "--no-venv" ]; then
  py=""  # the first Python 3 that runs (on Windows, python3 is often a Microsoft Store stub)
  for candidate in python3 python "py -3"; do
    if $candidate -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then py=$candidate; break; fi
  done
  [ -n "$py" ] || { echo "no Python 3 found" >&2; exit 1; }
  $py -m venv .venv
  vpy=.venv/bin/python
  [ -x "$vpy" ] || vpy=.venv/Scripts/python.exe
  PIP_DISABLE_PIP_VERSION_CHECK=1 "$vpy" -m pip install -q -r "$plugin/requirements.txt"
fi

git init -q
git config user.name "Alex Rivera (fictional)"
git config user.email "alex.rivera@example.com"
git add -A
git commit -q -m "Job Hunt Studio demo workspace (fictional example)"
