#!/usr/bin/env bash
set -euo pipefail
export FC_CI_LIFECYCLE_LOG="$RUNNER_TEMP/full-pytest-lifecycle.jsonl"
python3 scripts/ci_lifecycle.py "$FC_CI_LIFECYCLE_LOG" "$RUNNER_TEMP/full-pytest-processes.json" >"$RUNNER_TEMP/full-pytest-monitor.log" 2>&1 &
monitor=$!
trap 'kill "$monitor" 2>/dev/null || true; wait "$monitor" 2>/dev/null || true' EXIT
set +e
"$@" 2>&1 | tee "$RUNNER_TEMP/full-pytest.log" | python3 scripts/ci_console.py
codes=("${PIPESTATUS[@]}")
set -e
python3 - "${codes[@]}" <<'PY'
import sys
from scripts.ci_lifecycle import mark
mark('pipeline_end', command_returncode=int(sys.argv[1]), tee_returncode=int(sys.argv[2]),
     console_returncode=int(sys.argv[3]))
PY
if (( codes[0] != 0 )); then exit "${codes[0]}"; fi
if (( codes[1] != 0 )); then exit "${codes[1]}"; fi
exit "${codes[2]}"
