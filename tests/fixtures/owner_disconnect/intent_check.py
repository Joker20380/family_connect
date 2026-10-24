"""One explicit owner Disconnect/Connect; not evidence of automatic reconnect."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/owner-disconnections-20261022'
sys.path.insert(0, str(ROOT))
from scripts.owner_android_support import command, snapshot, save


def main():
    os.umask(0o077)
    candidate=int(sys.argv[1]) if len(sys.argv)>1 else 102
    assert candidate in (102,106)
    out = WORK / ('explicit-intent-check' if candidate==102 else 'explicit-intent-check-106')
    out.mkdir(exist_ok=False)
    serial = '31ce63ba'
    original=json.loads((WORK/'raw-entry-20261022T095450Z/diagnostic.json').read_text())

    def observe(name):
        current = snapshot(serial)
        save(out / (name + '.json'), dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            monotonic=time.monotonic(), snapshot=current))
        assert current['device_support_id'] == original['device_support_id'] and current['version_code'] == candidate
        return current

    def issue(action):
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = command(serial, action)
        save(out / (action + '-receipt.json'), dict(started=started,
            completed=datetime.datetime.now(datetime.timezone.utc).isoformat(), result=result))
        print(action.upper(), result, flush=True)

    observe('before')
    issue('disconnect')
    deadline = time.monotonic() + 45
    index = 0
    observed = []
    while time.monotonic() < deadline:
        time.sleep(min(5, max(0, deadline - time.monotonic())))
        current = observe('disconnected-%02d' % index)
        observed.append(current)
        assert current['state'] == 'DISCONNECTED' and not current['vpn_capture_open']
        index += 1
    save(out / 'disconnect-result.json', dict(result='PASS_BOUNDED', samples=index,
        duration_bound_seconds=45, states=[current['state'] for current in observed]))
    issue('connect')
    deadline = time.monotonic() + 90
    for index in range(45):
        current = observe('reconnect-%02d' % index)
        if current['state'] == 'CONNECTED':
            diagnostic = current['restricted_session']
            assert diagnostic['speed_profile'] == 'P1' and diagnostic['mux_window'] == 131072
            assert diagnostic['reliable_limits']['effective_send'] == 32 and current['vpn_capture_open']
            save(out / 'reconnect-result.json', dict(result='EXPLICIT_CONNECT_P1_NOT_AUTO_RECOVERY',
                session_tag=diagnostic['session_tag'], current=current['state']))
            print('EXPLICIT_CONNECT_P1', flush=True)
            return
        assert time.monotonic() < deadline
        time.sleep(2)
    raise RuntimeError('Bounded manual reconnect did not reach CONNECTED')


if __name__ == '__main__':
    main()
