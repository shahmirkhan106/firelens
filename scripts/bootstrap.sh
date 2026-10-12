#!/usr/bin/env bash
# One-shot environment setup for FireLens.
#
#   scripts/bootstrap.sh          # runtime + frontend deps
#   scripts/bootstrap.sh --dev    # also install pytest/httpx for tests
#
# Idempotent: safe to re-run. Does not download data or build artifacts.
set -euo pipefail
cd "$(dirname "$0")/.."
WANT_DEV=0
[ "${1:-}" = "--dev" ] && WANT_DEV=1

command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    sys.exit("Python 3.11+ required (found %d.%d)" % sys.version_info[:2])
PY

if [ ! -d .venv ]; then
  echo "[bootstrap] creating .venv"
  python3 -m venv .venv
fi
echo "[bootstrap] installing runtime deps"
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r backend/requirements.txt
if [ "$WANT_DEV" = "1" ]; then
  echo "[bootstrap] installing dev deps"
  .venv/bin/pip install -q -r requirements-dev.txt
fi

if [ -f frontend/package-lock.json ]; then
  echo "[bootstrap] installing frontend deps (npm ci)"
  ( cd frontend && npm ci --no-audit --no-fund )
else
  echo "[bootstrap] frontend deps: run 'cd frontend && npm install'"
fi

echo
echo "Done. Next:"
echo "  scripts/build_all.sh            # integrity check + rebuild artifacts"
echo "  .venv/bin/uvicorn backend.app:app --port 8000   # serve the API"
echo "  cd frontend && npm run build && npm run preview  # serve the UI"