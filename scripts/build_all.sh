#!/usr/bin/env bash
# Rebuild every AOI's processed artifacts from its raw year-files.
#
#   scripts/build_all.sh            # default: keep any existing daily caches
#   scripts/build_all.sh --rebuild  # force recompute of the daily aggregation
#
# Prints per-region wall-clock times and exits non-zero on any failure, so it
# is safe to run in CI or as the single "make the data" step.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
START=$(date +%s)
FAIL=0

echo "=== 0/5 data integrity ==="
"$PY" scripts/check_data.py || { echo "data check FAILED"; exit 1; }

i=1
for a in california north-india amazon australia-nsw east-siberia; do
  echo "=== $i/5 $a ==="
  T0=$(date +%s)
  if ! "$PY" scripts/build_pipeline.py --aoi "$a" "$@"; then
    echo "FAILED: $a"; FAIL=1
  fi
  T1=$(date +%s)
  echo "  $a took $(( (T1 - T0) / 60 ))m $(( (T1 - T0) % 60 ))s"
  i=$((i + 1))
done

END=$(date +%s)
echo "=== total $(( (END - START) / 60 ))m $(( (END - START) % 60 ))s ==="
[ "$FAIL" -ne 0 ] && echo "ONE OR MORE REGIONS FAILED" || echo "all regions rebuilt OK"
exit $FAIL