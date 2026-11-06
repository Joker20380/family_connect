#!/usr/bin/env bash
set -euo pipefail
source_python="${1:?Python 3.14 executable required}"
destination="${2:?Root-owned destination required}"
test "$(id -u)" = 0
test ! -e "$destination"
prefix="$("$source_python" -c 'import sys; assert sys.version_info[:2] == (3, 14); print(sys.base_prefix)')"
cp -a "$prefix" "$destination"
chown -R root:root "$destination"
chmod -R go-w "$destination"
"$destination/bin/python3.14" -m venv "$destination/test-env"
"$destination/test-env/bin/python" -m pip install -r control/requirements.lock
"$destination/test-env/bin/python" -c 'import sys,pytest; assert sys.version_info[:2] == (3,14); print(sys.executable, pytest.__version__)'
