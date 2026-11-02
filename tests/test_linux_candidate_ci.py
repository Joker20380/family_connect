from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('dbus_ready,resolved_ready,passes', [(1, 1, True), (3, 1, True), (1, 3, True), (99, 1, False), (1, 99, False)])
def test_container_wait_requires_both_services(dbus_ready, resolved_ready, passes):
    source = (ROOT / 'scripts/ci_linux_candidate.sh').read_text()
    boundary = source[source.index('  ready=0\n'):source.index('  docker exec -e FC_L031_HOST_NETNS=')]
    script = '''set -eu
name=isolated-test
ticks=1
sleep() { ticks=$((ticks+1)); }
docker() {
  case "$*" in
    'exec isolated-test systemctl is-active --quiet dbus') [ "$ticks" -ge "$1_READY" ] ;;
    'exec isolated-test systemctl is-active --quiet systemd-resolved') [ "$ticks" -ge "$2_READY" ] ;;
    'exec isolated-test systemctl status dbus systemd-resolved --no-pager') return 0 ;;
    *) return 97 ;;
  esac
}
'''.replace('$1_READY', str(dbus_ready)).replace('$2_READY', str(resolved_ready))
    result = subprocess.run(['bash', '-c', script + boundary + '\nprintf "%s" "$ticks"\n'], capture_output=True, text=True, timeout=5)
    assert (result.returncode == 0) == passes
    if passes:
        assert int(result.stdout) == max(dbus_ready, resolved_ready)
