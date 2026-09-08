#!/bin/sh
set -eu
umask 077
mkdir -p state-v2
# RU: ключи создаются отдельно; в issuer передаётся только CSR.
# EN: keys are created separately; only the CSR is consumed by the issuer.
for name in gateway-lab relay-a relay-b client outsider; do
  mkdir -p "state-v2/$name"
  docker run --rm --network none --read-only \
    -v "$PWD/state-v2/$name:/device:rw" family-connect-control:auth2 \
    python scripts/identity.py --directory /device --name "$name" >/dev/null
done
docker run --rm --network none --read-only \
  -v "$PWD/state-v2:/provision:rw" family-connect-control:auth2 python scripts/init_state.py
for name in gateway-lab relay-a relay-b client outsider; do
  mkdir -p "state-v2/cache-$name"
  chown -R 65532:65532 "state-v2/$name" "state-v2/cache-$name"
  chmod 700 "state-v2/$name" "state-v2/cache-$name"
done
chmod 755 state-v2/trust
chmod 444 state-v2/trust/*
