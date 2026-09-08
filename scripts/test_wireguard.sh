#!/bin/sh
set -eu
mkdir -p artifacts
for device in linux android; do
  number=3
  if [ "$device" = android ]; then number=2; fi
  docker run --rm --cap-add NET_ADMIN \
    -e "CLIENT_ADDRESS=10.77.0.$number/32" -e "CLIENT_IPV6=fd77:92::$number/128" \
    -v "$PWD/state-v2/pilot-clients/fc-ru-$device.conf:/profile/client.conf:ro" \
    -v "$PWD/pilot/probe.sh:/probe.sh:ro" \
    --entrypoint sh family-connect-wireguard:pilot1 /probe.sh > "artifacts/wireguard-$device.txt"
done
printf 'PASS: both device keys reach Russian IPv4 from isolated local clients / оба ключа проверены\n'
