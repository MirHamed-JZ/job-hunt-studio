#!/usr/bin/env bash
set -euo pipefail
bash "$(dirname "$0")/../persona_workspace.sh" --no-venv
# an approved version, so tailor-resume treats the request as a revision of the base
git tag resume-approved-v1
