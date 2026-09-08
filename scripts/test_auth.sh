#!/bin/sh
set -eu
mkdir -p artifacts
# RU: сертификат CA без членства должен быть отклонён сервером.
# EN: a CA-issued certificate without membership must be rejected by the server.
docker compose run --rm --no-deps outsider > artifacts/unauthorized.txt 2>&1
grep -q 'device not authorized' artifacts/unauthorized.txt
printf 'PASS: unlisted device rejected by relay / незарегистрированное устройство отклонено\n'
