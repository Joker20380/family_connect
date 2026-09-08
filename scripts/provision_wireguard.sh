#!/bin/sh
set -eu
umask 077
mkdir -p state-v2/wireguard
test -s state-v2/wireguard/android.pub
test -s state-v2/wireguard/linux.pub
# RU: серверный ключ создаётся только на gateway. EN: server key stays on gateway.
docker run --rm --network none -v "$PWD/state-v2/wireguard:/keys:rw" \
  --entrypoint sh family-connect-wireguard:pilot1 -c '
    umask 077
    if [ ! -f /keys/server.key ]; then wg genkey > /keys/server.key; fi
    wg pubkey < /keys/server.key > /keys/server.pub
  '
