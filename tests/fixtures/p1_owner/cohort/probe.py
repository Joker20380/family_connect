import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / 'state-client-build/tester-p1-cohort-20261023'


def main():
    assert len(sys.argv) == 3, 'unique label and fresh gateway acquisition directory required'
    build = json.loads((WORK/'gateway-build.json').read_text())
    policy = json.loads((WORK/'policy-readback.json').read_text())
    assert hashlib.sha256((WORK/'gateway-group').read_bytes()).hexdigest() == build['sha256'] == policy['binary']
    assert policy['result'] == 'EXACT_THREE_P1_POLICY_VERIFIED' and len(policy['targets']) == 3
    sys.path.insert(0,str(ROOT/'tests/fixtures/owner_disconnect'))
    import wifi_control
    wifi_control.previous.GATEWAY = build['sha256']
    sys.argv.append('probe')
    wifi_control.main()


if __name__ == '__main__':
    main()
