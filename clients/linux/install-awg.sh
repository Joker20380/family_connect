#!/bin/sh
set -eu
# Arguments: reviewed source checkout and directory of binaries from the pinned build.
[ "$(id -u)" = 0 ]
[ "$#" = 2 ]
source_dir=$1
binary_dir=$2
command -v resolvconf >/dev/null
command -v nft >/dev/null
command -v curl >/dev/null
test -c /dev/net/tun
# Verify the complete pinned bundle before changing the installed helper.
python3 "$source_dir/clients/linux/check-awg-bundle.py" "$binary_dir"
for interface in /sys/class/net/fcawg*; do
 if [ -e "$interface" ]; then echo 'Disconnect AWG before updating its helper.' >&2; exit 1; fi
done
destination=/usr/local/lib/family-connect-awg
install -d -m 755 "$destination" /etc/family-connect/awg
for name in awg amneziawg-go awg-quick; do
 install -o root -g root -m 755 "$binary_dir/$name" "$destination/$name"
done
# In containers /proc/sys may be read-only even when the namespace was created
# with src_valid_mark=1. Avoid rewriting an already-correct value.
python3 - "$destination/awg-quick" <<'PY'
from pathlib import Path
import sys
path=Path(sys.argv[1]);text=path.read_text()
old='[[ $proto == -4 ]] && cmd sysctl -q net.ipv4.conf.all.src_valid_mark=1'
new='if [[ $proto == -4 && $(sysctl -n net.ipv4.conf.all.src_valid_mark) != 1 ]]; then cmd sysctl -q net.ipv4.conf.all.src_valid_mark=1; fi'
if text.count(old)!=1:raise ValueError('Unexpected awg-quick source')
text=text.replace(old,new)
old='\n\tlocal ret\n\tif ! cmd ip link add "$INTERFACE" type amneziawg; then\n\t\tret=$?\n\t\t[[ -e /sys/module/amneziawg ]] || ! command -v "${WG_QUICK_USERSPACE_IMPLEMENTATION:-amneziawg-go}" >/dev/null && exit $ret\n\t\techo "[!] Missing WireGuard (Amnezia VPN) kernel module. Falling back to slow userspace implementation." >&2\n\t\tcmd "${WG_QUICK_USERSPACE_IMPLEMENTATION:-amneziawg-go}" "$INTERFACE"\n\tfi'
new='\n\tcmd "${WG_QUICK_USERSPACE_IMPLEMENTATION:-amneziawg-go}" "$INTERFACE"'
if text.count(old)!=1:raise ValueError('Unexpected awg-quick interface creation')
text=text.replace(old,new)
path.write_text(text)
PY
install -o root -g root -m 755 "$source_dir/clients/linux/awg-helper.py" "$destination/helper"
install -o root -g root -m 644 "$source_dir/clients/desktop/profile_config.py" "$destination/profile_config.py"
install -o root -g root -m 644 "$source_dir/clients/desktop/backend.py" "$destination/backend.py"
for name in LICENSE-go LICENSE-tools; do
 install -o root -g root -m 644 "$binary_dir/$name" "$destination/$name"
done

install -o root -g root -m 644 "$binary_dir/awg31.json" "$destination/awg31.json"
