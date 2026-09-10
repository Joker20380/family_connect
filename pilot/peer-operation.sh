#!/bin/sh
# family-connect-peer-sync-v1
# Re-read current persisted intent under the same lock as the host adapter.
# A timed-out Docker exec may finish late: never replay its stale action payload.
set -eu
identity=${1:?identity required}
public=${2:?public key required}
[ "${#identity}" -eq 32 ] || exit 2
case "$identity" in *[!0-9a-f]*) exit 2;; esac
# The host creates the lock first. Read-only open supports /keys:ro in the gateway.
exec 9</keys/.enrollment.lock
flock -w 3 -x 9
record=/keys/peers/product-$identity.conf
if [ -f "$record" ]; then
    grep -Fqx "PublicKey = $public" "$record"
    wg addconf wg0 "$record"
else
    wg set wg0 peer "$public" remove
fi
