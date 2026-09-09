#!/bin/sh
set -eu
ip link add fcsite0 type wireguard
wg set fcsite0 private-key /keys/private.key listen-port 51830 peer "$(cat /keys/peer.pub)" endpoint "$PEER_ENDPOINT" allowed-ips "$REMOTE_NETWORK" persistent-keepalive 15
ip link set fcsite0 mtu 1440 up
ip route replace "$REMOTE_NETWORK" dev fcsite0
nft -f - <<'RULES'
table inet fc_site {
  chain forward {
    type filter hook forward priority 0; policy drop;
    ct state established,related accept
    ip saddr 172.29.93.0/24 ip daddr 172.29.94.11 udp dport 4444 accept
    ip saddr 172.29.94.11 ip daddr 172.29.93.10 udp dport 4433 accept
    ip saddr 172.29.94.11 ip daddr 172.29.93.2 tcp dport 8080 accept
  }
}
RULES
if [ "$SITE_ROLE" = primary ]; then
  nft -f - <<'RULES'
table ip fc_site_nat {
  chain postrouting {
    type nat hook postrouting priority srcnat; policy accept;
    ip saddr 172.29.94.11 ip daddr { 172.29.93.2, 172.29.93.10 } oifname != "fcsite0" snat to 172.29.93.254
  }
}
RULES
fi
trap 'ip link del fcsite0; exit 0' TERM INT
while :; do sleep 3600 & wait "$!"; done
