#!/bin/sh
set -eu
ip link add fcwg0 type wireguard
ip address add 10.78.0.1/24 dev fcwg0
ip -6 address add fd78:93::1/64 dev fcwg0
wg set fcwg0 listen-port 51820 private-key /keys/private.key peer "$(cat /keys/peer.pub)" allowed-ips 10.78.0.2/32,fd78:93::2/128
ip link set fcwg0 mtu 1280 up
nft -f - <<'RULES'
table inet fc_data {
  chain input {
    type filter hook input priority 0; policy drop;
    iifname "lo" accept
    ct state established,related accept
    ip saddr 172.29.93.0/24 udp dport 4433 accept
    iifname "fcwg0" ip protocol icmp accept
  }
  chain forward {
    type filter hook forward priority 0; policy drop;
    ct state established,related accept
    iifname "fcwg0" ip daddr { 0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 224.0.0.0/4, 240.0.0.0/4 } drop
    iifname "fcwg0" tcp dport 25 drop
    iifname "fcwg0" oifname != "fcwg0" meta nfproto ipv4 accept
  }
}
table ip fc_data_nat {
  chain postrouting {
    type nat hook postrouting priority srcnat; policy accept;
    ip saddr 10.78.0.0/24 oifname != "fcwg0" masquerade
  }
}
RULES
trap 'ip link del fcwg0; exit 0' TERM INT
while :; do sleep 3600 & wait "$!"; done
