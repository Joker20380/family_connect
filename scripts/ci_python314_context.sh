#!/usr/bin/env bash
set -euo pipefail
umask 022
source_python="${1:?Python 3.14 executable required}"
destination="${2:?Root-owned destination required}"
fixture_user="${3:?Unprivileged fixture account required}"
test "$(id -u)" = 0
test ! -e "$destination"
prefix="$("$source_python" -c 'import sys; assert sys.version_info[:2] == (3, 14); print(sys.base_prefix)')"
apt-get update -qq
apt-get install -y --no-install-recommends patchelf
cp -a "$prefix" "$destination"
chown -R root:root "$destination"
chmod -R go-w "$destination"
patchelf --set-rpath '$ORIGIN/../lib' "$destination/bin/python3.14"
unset LD_LIBRARY_PATH
"$destination/bin/python3.14" -m venv "$destination/test-env"
"$destination/test-env/bin/python" -m pip install -r control/requirements.lock
"$destination/test-env/bin/python" -c 'import sys,pytest; assert sys.version_info[:2] == (3,14); print(sys.executable, pytest.__version__)'
test "$(id -u "$fixture_user")" != 0
install -d -m 0755 -o "$fixture_user" /usr/local/lib/fc-ci-snapshot-fixtures
runuser -u "$fixture_user" -- env -i PATH=/usr/bin:/bin LANG=C "$destination/bin/python3.14" -I -B -c 'import sys; assert sys.version_info[:2] == (3,14); print(sys.executable)'
namei -l "$destination/bin/python3.14"
readelf -d "$destination/bin/python3.14" | grep -E 'RUNPATH|RPATH|NEEDED'
runuser -u "$fixture_user" -- "$destination/test-env/bin/python" -c 'import os,pwd; from scripts.build_profile_snapshot_launcher import Account,inspect_executable; import sys; from pathlib import Path; print(inspect_executable(str(Path(sys.executable).resolve()),Account.lookup(pwd.getpwuid(os.geteuid()).pw_name))["runtime"])'
