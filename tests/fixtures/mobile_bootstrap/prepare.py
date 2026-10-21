"""Preserve accepted beta95 sources and hash-verified tester exports, without mutation."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/mobile-bootstrap-20261020'
BASE = ROOT / 'state-client-build/mux-profile-20261020'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    WORK.mkdir(exist_ok=True, mode=0o700)
    inputs = {}
    events = {}
    scopes = []
    for number, expected in [(19, '6d95570be64d8bf4875049ac6992e842de33f38386f9dda26da03e1ad4d81f8f'),
                             (20, '95ce765751371aebacda3c66cac90a1cdba7f4a5345446810f65c3b1fc7ead47')]:
        source = Path('/mnt/data/joker/Загрузки') / f'FamilyConnect-diagnostics({number}).json'
        assert digest(source) == expected
        target = WORK / f'export{number}.json'
        shutil.copyfile(source, target)
        inputs[str(number)] = dict(path=str(source), sha256=expected)
        for scope, value in json.loads(source.read_text()).items():
            scopes.append(dict(export=number, scope=scope, **{key: value.get(key) for key in (
                'app_version', 'version_code', 'os_api', 'device_support_id', 'network_class',
                'connection_id', 'restricted_readiness', 'bootstrap_directory')}))
            for event in value.get('events', []):
                key = json.dumps(event, sort_keys=True)
                events.setdefault(key, dict(event=event, sources=[]))['sources'].append(f'{number}:{scope}')
    relevant = [value for value in events.values() if value['event']['connection_id'] == 'b624ca0b-8aed-4414-9746-ebd568f03cb1'
                or value['event'].get('component') == 'READINESS']
    record = dict(inputs=inputs, scopes=scopes, unique_events=len(events), relevant=sorted(relevant, key=lambda value:value['event']['timestamp']))
    (WORK / 'input-evidence.json').write_text(json.dumps(record, indent=2))
    source = BASE / 'android-source'
    target = WORK / 'android-source'
    assert not target.exists()
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git', '__pycache__', '.gradle', 'build'))
    inventory = {str(path.relative_to(target)): digest(path) for path in target.rglob('*') if path.is_file()}
    (WORK / 'baseline-inventory.json').write_text(json.dumps(inventory, indent=2, sort_keys=True))
    print(json.dumps(dict(inputs_verified=2, unique_events=len(events), source_files=len(inventory))))


if __name__ == '__main__':
    main()
