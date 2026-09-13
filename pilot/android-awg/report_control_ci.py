"""Confirm both protocol methods actually executed on Android, not only on the JVM."""
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2]
expected = {'immutableCorpus', 'strictJson'}
found = set()
for path in (root/'clients/android/app/build/outputs/androidTest-results').rglob('*.xml'):
    for case in ET.parse(path).iter('testcase'):
        if case.get('classname') != 'com.familyconnect.app.ControlProtocolRuntimeTest':
            continue
        assert not any(case.find(name) is not None for name in ('failure', 'error', 'skipped')), 'Android control test did not pass'
        found.add(case.get('name'))
assert found == expected, 'Android control runtime test results missing'
digest = hashlib.sha256((root/'tests/vectors/control-v1/manifest.json').read_bytes()).hexdigest()
assert digest == 'c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd'
print(f'::notice title=Android control conformance::30 configurations, 15 ACKs, 32 structure refusals; strict JSON passed; manifest SHA256 {digest}')
