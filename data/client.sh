#!/bin/sh
set -eu
ip link add fcwg0 type wireguard
ip address add 10.78.0.2/32 dev fcwg0
ip -6 address add fd78:93::2/128 dev fcwg0
wg set fcwg0 listen-port 51822 private-key /keys/private.key peer "$(cat /keys/peer.pub)" allowed-ips 0.0.0.0/0,::/0 endpoint 127.0.0.1:51821 persistent-keepalive 5
ip link set fcwg0 mtu 1280 up
if [ "${REMOTE_RELAY_ROUTE:-0}" = 1 ]; then
  ip route replace 172.29.94.11/32 via 172.29.93.254
fi
ip route replace default dev fcwg0
ip -6 route replace default dev fcwg0
printf 'nameserver 1.1.1.1\n' > /etc/resolv.conf
trap 'ip link del fcwg0; exit 0' TERM INT
while :; do sleep 3600 & wait "$!"; done
