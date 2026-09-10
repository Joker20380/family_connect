#!/bin/sh
set -eu
# Separate network namespace, port, subnet and keys from the original WG pilot.
amneziawg-go awg0
awg setconf awg0 /keys/server.conf
ip address add 10.78.0.1/24 dev awg0
ip -6 address add fd78:92::1/64 dev awg0
ip link set awg0 mtu 1280 up
nft -f - <<'RULES'
table inet family_connect_awg {
 chain input {
  type filter hook input priority 0; policy drop;
  iifname "lo" accept
  ct state established,related accept
  udp dport 51821 accept
  iifname "awg0" ip protocol icmp accept
 }
 chain forward {
  type filter hook forward priority 0; policy drop;
  ct state established,related accept
  iifname "awg0" ip daddr { 0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 224.0.0.0/4, 240.0.0.0/4 } drop
  iifname "awg0" tcp dport 25 drop
  iifname "awg0" oifname "eth0" meta nfproto ipv4 accept
 }
}
table ip family_connect_awg_nat {
 chain postrouting {
  type nat hook postrouting priority srcnat; policy accept;
  ip saddr 10.78.0.0/24 oifname "eth0" masquerade
 }
}
RULES
trap 'ip link del awg0; exit 0' TERM INT
while :; do sleep 3600 & wait "$!"; done
