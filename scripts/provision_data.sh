#!/bin/sh
# RU: только отдельный серверный стенд. EN: isolated single-host test identities only.
set -eu
umask 077
for name in gateway-lab relay-a relay-b client outsider; do
  mkdir -p "state-v3/$name"
  docker run --rm --network none --read-only -v "$PWD/state-v3/$name:/device:rw" \
    family-connect-control:data3 python scripts/identity.py --directory /device --name "$name" >/dev/null
done
docker run --rm --network none --read-only -e LAB_NETWORK_PREFIX=172.29.93 \
  -v "$PWD/state-v3:/provision:rw" -v "$PWD/scripts/init_state.py:/app/scripts/init_state.py:ro" \
  family-connect-control:data3 python scripts/init_state.py
for name in gateway-lab relay-a relay-b client outsider; do
  mkdir -p "state-v3/cache-$name"
  chown -R 65532:65532 "state-v3/$name" "state-v3/cache-$name"
  chmod 700 "state-v3/$name" "state-v3/cache-$name"
done
chmod 755 state-v3/trust
chmod 444 state-v3/trust/*
for name in wg-client wg-gateway; do
  mkdir -p "state-v3/$name"
  if [ ! -f "state-v3/$name/private.key" ]; then
    docker run --rm --network none --entrypoint wg family-connect-wireguard:data3 genkey > "state-v3/$name/private.key"
  fi
  docker run --rm -i --network none --entrypoint wg family-connect-wireguard:data3 pubkey < "state-v3/$name/private.key" > "state-v3/$name/public.pub"
done
cp state-v3/wg-client/public.pub state-v3/wg-gateway/peer.pub
cp state-v3/wg-gateway/public.pub state-v3/wg-client/peer.pub
