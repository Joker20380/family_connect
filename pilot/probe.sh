#!/bin/sh
set -eu
ip link add wg0 type wireguard
wg-quick strip /profile/client.conf > /tmp/wg.conf
wg setconf wg0 /tmp/wg.conf
ip address add "$CLIENT_ADDRESS" dev wg0
ip -6 address add "$CLIENT_IPV6" dev wg0
ip link set wg0 mtu 1380 up
original_gateway=$(ip -4 route show default | awk 'NR==1 {print $3}')
ip route add 185.251.89.19/32 via "$original_gateway" dev eth0
ip route replace default dev wg0
ip -6 route replace default dev wg0
printf 'nameserver 1.1.1.1\n' > /etc/resolv.conf
curl -4 -fsS --max-time 25 https://www.cloudflare.com/cdn-cgi/trace > /tmp/trace
sed -n '/^ip=/p; /^loc=/p' /tmp/trace
grep -q '^ip=185.251.89.19$' /tmp/trace
if curl -6 -fsS --max-time 3 https://www.cloudflare.com/cdn-cgi/trace >/dev/null 2>&1; then
  printf 'Unexpected IPv6 egress / неожиданный IPv6-выход\n' >&2
  exit 1
fi
printf 'ipv6_egress=blocked\n'
