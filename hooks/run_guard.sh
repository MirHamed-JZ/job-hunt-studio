#!/bin/sh
# Starts the Job Hunt Studio guard (guard.py) with the first Python 3 that works: the workspace .venv, then
# python3, python and py -3 on the PATH. The hook's JSON arrives on stdin and passes straight through.
# With no Python 3 at all the guard cannot run: it says so and lets the call through (setup checks for Python).
here=$(cd "$(dirname "$0")" && pwd)
proj=${CLAUDE_PROJECT_DIR:-.}
for py in "$proj/.venv/Scripts/python.exe" "$proj/.venv/bin/python"; do
  if [ -x "$py" ]; then exec "$py" "$here/guard.py"; fi
done
for py in python3 python py; do
  if [ "$py" = py ]; then set -- -3; else set --; fi
  if command -v "$py" >/dev/null 2>&1 &&
     "$py" "$@" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' </dev/null >/dev/null 2>&1; then
    exec "$py" "$@" "$here/guard.py"
  fi
done
echo "Job Hunt Studio guard: no Python 3 found, so the workspace guards could not check this call." >&2
exit 1
