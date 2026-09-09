#!/bin/sh
set -eu
ip link add wg0 type wireguard
ip address add 10.77.0.1/24 dev wg0
ip -6 address add fd77:92::1/64 dev wg0
wg set wg0 listen-port 51820 private-key /keys/server.key \
  peer "$(cat /keys/android.pub)" allowed-ips 10.77.0.2/32,fd77:92::2/128 \
  peer "$(cat /keys/linux.pub)" allowed-ips 10.77.0.3/32,fd77:92::3/128
# family-connect-dynamic-peers-v1
# Public enrollment records only; preserve the original Android/Linux peers.
for peer in /keys/peers/*.conf; do
  [ -f "$peer" ] || continue
  wg addconf wg0 "$peer"
done
ip link set wg0 mtu 1380 up
nft -f - <<'RULES'
table inet family_connect {
  chain input {
    type filter hook input priority 0; policy drop;
    iifname "lo" accept
    ct state established,related accept
    udp dport 51820 accept
    iifname "wg0" ip protocol icmp accept
  }
  chain forward {
    type filter hook forward priority 0; policy drop;
    ct state established,related accept
    iifname "wg0" ip daddr { 0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.168.0.0/16, 224.0.0.0/4, 240.0.0.0/4 } drop
    iifname "wg0" tcp dport 25 drop
    iifname "wg0" oifname "eth0" meta nfproto ipv4 accept
    # IPv6 is routed into the tunnel but not forwarded without tested IPv6 egress.
  }
}
table ip family_connect_nat {
  chain postrouting {
    type nat hook postrouting priority srcnat; policy accept;
    ip saddr 10.77.0.0/24 oifname "eth0" masquerade
  }
}
RULES
# RU: только трафик controlled gateway. EN: controlled gateway traffic only.
trap 'ip link del wg0; exit 0' TERM INT
while :; do sleep 3600 & wait "$!"; done
