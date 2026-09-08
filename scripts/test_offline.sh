#!/bin/sh
set -eu
mkdir -p artifacts
trap 'docker compose start control >/dev/null' EXIT
# RU: сначала клиент получает подписанный кэш. EN: prime the signed cache.
docker compose run --rm --no-deps client verify-state > artifacts/catalog.txt
docker compose stop control
docker compose run --rm --no-deps client > artifacts/offline.json
python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('artifacts/offline.json').read_text())
assert r['bytes']==16777216 and r['mutual_tls']
print('PASS: signed-cache startup without backend / запуск из кэша без backend')
PY
