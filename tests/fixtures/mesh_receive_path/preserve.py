"""Preserve exact beta90/b9 and index existing evidence without a live mutation."""

import collections
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/mesh-receive-path-20261020'
PARENT = ROOT / 'state-client-build/tunnel-restart-20261019'
QUEUE = ROOT / 'state-client-build/queue-retry-20261019'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.umask(0o077)
    gateway = json.loads((PARENT / 'gateway-build.json').read_text())
    android = json.loads((PARENT / 'android-build/source-inventory.json').read_text())
    assert gateway['source_inventory'] == '4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6'
    assert all(digest(PARENT / 'gateway-source/carrier' / name) == value for name, value in gateway['files'].items())
    assert all(digest(PARENT / 'android-source' / name) == value for name, value in android.items())
    assert digest(PARENT / 'gateway-seed-recovery') == 'b9ae880731517753e456637e52dcc421b9f7d7b881b400c856989ae93193e9ba'
    assert digest(PARENT / 'delivery/FamilyConnect-0.1.18-beta90-stability.apk') == '68cbcccfb5adf8656e8203436126330e780de099670ee2031d71019baadc3e9a'
    WORK.mkdir(mode=0o700, exist_ok=False)
    (WORK / 'entry-status.txt').write_text(subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True))
    shutil.copyfile(PARENT / 'gateway-seed-recovery', WORK / 'gateway-baseline-b9')
    preserved = {}
    for name in ('a-head597-summary.json', 'a-tail-summary.json', 'a-tail-private.jsonl',
                 'b-phone-private.txt', 'final-vpn-observation.jsonl', 'final-post-readback.json',
                 'final-phone-services-private.txt', 'a-measure-fixed/analysis.json',
                 'a-measure-fixed/capture-private.jsonl'):
        source = QUEUE / name
        target = WORK / 'previous-evidence' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        preserved[name] = dict(sha256=digest(source), bytes=source.stat().st_size)
    exports = []
    for directory in (QUEUE, PARENT, Path('/mnt/data/joker/Загрузки'),
                      Path('/home/joker/snap/telegram-desktop/7169/.local/share/TelegramDesktop/tdata/temp_data')):
        for path in sorted(directory.glob('*.json')):
            if 'export' not in path.name and 'diagnostics' not in path.name:
                continue
            try:
                value = json.loads(path.read_text())
                ring = value.get('ring', {})
                exports.append(dict(path=str(path), sha256=digest(path), bytes=path.stat().st_size,
                                    code=ring.get('version_code'), events=len(ring.get('events', [])),
                                    target_session_present='2219e060af8bc8a0532e29b7e55e5e2bda5eb68f592264d98400d174de714b5c' in path.read_text()))
            except (ValueError, OSError) as error:
                exports.append(dict(path=str(path), error=type(error).__name__))
    result = dict(gateway_inventory=gateway['source_inventory'], android_inventory=android,
                  preserved=preserved, exports=exports)
    (WORK / 'preservation.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(result='EXACT_INPUTS_PRESERVED', preserved_files=len(preserved),
                          export_versions=dict(collections.Counter(str(item.get('code')) for item in exports)),
                          matching_exports=sum(item.get('target_session_present', False) for item in exports))))


if __name__ == '__main__':
    main()
