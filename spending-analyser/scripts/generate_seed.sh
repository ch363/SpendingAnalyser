#!/usr/bin/env zsh
set -euo pipefail

# Script: generate_seed.sh
# Purpose: Activate project venv, ensure numpy/pandas are installed into the venv,
# run data.synth to regenerate data/fixtures/seed.csv with 6 full months of
# 8-10 daily card transactions. If macOS permissions prevent writing into the
# Documents path, fall back to writing /tmp/generated_seed.csv and inform the user.

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
# venv may be at REPO_ROOT/.venv or at workspace parent (.venv)
if [ -n "${VIRTUAL_ENV:-}" ]; then
  PY="$VIRTUAL_ENV/bin/python"
else
  if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
    PY="$REPO_ROOT/.venv/bin/python"
  elif [ -x "$(dirname "$REPO_ROOT")/.venv/bin/python" ]; then
    PY="$(dirname "$REPO_ROOT")/.venv/bin/python"
  else
    PY=""
  fi
fi


if [ -z "$PY" ] || [ ! -x "$PY" ]; then
  echo "No virtualenv python found at $PY"
  echo "Please create the venv or activate it before running this script." >&2
  exit 1
fi

echo "Using python: $($PY -V)"
echo "Installing numpy and pandas into the venv (no --user)..."
$PY -m pip install --upgrade pip >/dev/null
$PY -m pip install numpy pandas >/dev/null

echo "Running synthesizer to write data/fixtures/seed.csv (6 full months, 8-10 card txns/day)"

# Try writing in-place first
$PY - <<'PY'
import sys
try:
    from data import synth
    synth.write_transactions_csv(path="data/fixtures/seed.csv", seed=123,
        months_full=6, include_current_partial=False,
        min_daily_txns=8, max_daily_txns=10, card_only=True)
    print("OK: wrote data/fixtures/seed.csv")
except Exception as e:
    print("ERROR_IN_PLACE:", e, file=sys.stderr)
    sys.exit(2)
PY

rc=$? || true
if [ "$rc" -eq 0 ]; then
  echo "Seed file updated in-place: $REPO_ROOT/data/fixtures/seed.csv"
  exit 0
fi

echo "In-place write failed (probably macOS permission). Writing fallback to /tmp/generated_seed.csv"
$PY - <<'PY'
from data import synth
synth.write_transactions_csv(path="/tmp/generated_seed.csv", seed=123,
    months_full=6, include_current_partial=False,
    min_daily_txns=8, max_daily_txns=10, card_only=True)
print("WROTE:/tmp/generated_seed.csv")
PY

echo "Fallback file written to /tmp/generated_seed.csv"
echo "Please copy it into $REPO_ROOT/data/fixtures/seed.csv using Finder if macOS blocks direct write."
