#!/bin/bash
set -euo pipefail
test "$(id -u)" = 0
test "${FC_L022_ISOLATED:-}" = yes
test -f /.dockerenv
test -n "${FC_L022_HOST_NETNS:-}"
test "$(stat -Lc %i /proc/self/ns/net)" != "$FC_L022_HOST_NETNS"
test "$(ip -o link show | wc -l)" = 1
test ! -S /run/dbus/system_bus_socket
printf 'nameserver 127.0.0.53\n' > /etc/resolv.conf
mkdir -p /run/dbus /run/systemd
install -d -o systemd-resolve -g systemd-resolve -m 755 /run/systemd/resolve
dbus-daemon --system --nofork &
bus_pid=$!
for attempt in $(seq 1 50); do
    test -S /run/dbus/system_bus_socket && break
    sleep .1
done
/usr/lib/systemd/systemd-resolved &
resolver_pid=$!
trap 'kill "$resolver_pid" "$bus_pid" 2>/dev/null || true; wait || true' EXIT
for attempt in $(seq 1 50); do
    kill -0 "$resolver_pid"
    if resolvectl status >/dev/null 2>&1; then break; fi
    sleep .1
done
resolvectl status
ip link set lo up
ip link add eth0 type dummy
ip address add 192.0.2.1/24 dev eth0
ip link set eth0 up
ip route add default via 192.0.2.2
mkdir -p /dev/net
test -c /dev/net/tun || mknod /dev/net/tun c 10 200
timeout --signal=TERM --kill-after=5s 240 python -m pytest -s -q --tb=short -p no:cacheprovider "$@"
