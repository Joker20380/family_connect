#!/bin/sh
set -eu
mkdir -p artifacts
# Leave both relays running even if the test fails.
trap 'docker compose start relay-a >/dev/null' EXIT
docker compose up -d gateway relay-a relay-b
docker compose run --rm --no-deps client > artifacts/failover.json 2> artifacts/failover.stderr &
client_pid=$!
sleep 4
docker compose kill -s SIGKILL relay-a
wait "$client_pid"
python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('artifacts/failover.json').read_text())
assert r['bytes']==16*1024*1024
assert r['quic_connections']==1
assert r['path_switches']>=1
print('PASS: 16 MiB transfer survived relay loss over the same QUIC connection')
PY
