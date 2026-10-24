#!/bin/bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
worker=$(realpath "$1")
test -x "$worker/fc-mesh-fixture"
cd "$root"
image=fc-l022-system:check
tar -c tests/fixtures/mesh_combined/Dockerfile control/requirements.lock device_identity/requirements.lock \
    provisioning/requirements.lock messenger/requirements.lock | \
    timeout 300 docker build -f tests/fixtures/mesh_combined/Dockerfile -t "$image" -
evidence=$(mktemp -d)
container=fc-l022-$$-$(date +%s)
underlays=$(ip -j route show default | python3 -c 'import json,sys; print(" ".join(sorted({route["dev"] for route in json.load(sys.stdin)})))')
snapshot() {
    ip -j route show default
    ip -j rule show
    cat /etc/resolv.conf
    for interface in $underlays; do
        ip -j route show table all dev "$interface"
        if command -v resolvectl >/dev/null; then resolvectl status --no-pager "$interface"; fi
    done
    if command -v resolvectl >/dev/null; then resolvectl dns | sed -n '/^Global:/p'; fi
}
snapshot > "$evidence/before"
finish() {
    result=$?
    docker rm -f "$container" >/dev/null 2>&1 || true
    snapshot > "$evidence/after"
    if ! cmp -s "$evidence/before" "$evidence/after"; then
        echo 'Host underlay routing or resolver configuration changed' >&2
        result=1
    fi
    rm -r "$evidence"
    exit "$result"
}
trap finish EXIT
timeout --signal=TERM --kill-after=10s 270 docker run --name "$container" --rm --privileged --network none \
    -e FC_L022_ISOLATED=yes -e FC_L022_HOST_NETNS="$(stat -Lc %i /proc/self/ns/net)" \
    -e FC_L021_WORKER=/fixture/fc-mesh-fixture \
    -v "$root:/workspace:ro" -v "$worker:/fixture:ro" "$image" \
    clients/desktop/tests/test_mesh_chat_combined_native.py \
    clients/desktop/tests/test_mesh_chat_release_native.py
