#!/bin/sh
set -eu
test "$(id -u)" = 0
source_dir=$(realpath "$1")
binary_dir=$(realpath "$2")
test -c /dev/net/tun
command -v resolvectl >/dev/null
command -v curl >/dev/null
command -v sysctl >/dev/null
command -v systemctl >/dev/null
# Refuse replacement before any file mutation while a service/cleanup owns routing.
test ! -e /run/family-connect-tcp/active
active_units=$(systemctl list-units 'family-connect-tcp@*.service' --state=active,activating,deactivating --no-legend --plain)
if [ -n "$active_units" ]; then
    echo 'Stop TCP services and finish cleanup before installation.' >&2
    exit 1
fi
install -d -o root -g root -m 755 /usr/local/lib/family-connect-tcp /etc/family-connect/tcp
install -o root -g root -m 755 "$binary_dir/xray" /usr/local/lib/family-connect-tcp/xray
install -o root -g root -m 644 "$source_dir/pilot/tcp/LICENSE-Xray" /usr/local/lib/family-connect-tcp/LICENSE
install -o root -g root -m 755 "$source_dir/clients/linux/tcp-helper.py" /usr/local/lib/family-connect-tcp/helper
install -o root -g root -m 644 "$source_dir/clients/desktop/profile_config.py" "$source_dir/clients/desktop/backend.py" /usr/local/lib/family-connect-tcp/
install -o root -g root -m 644 "$source_dir/clients/linux/family-connect-tcp@.service" /etc/systemd/system/
systemctl daemon-reload
