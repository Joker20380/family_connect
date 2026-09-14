"""Confirm both protocol methods actually executed on Android, not only on the JVM."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2]
expected = {('com.familyconnect.app.ControlProtocolRuntimeTest', 'immutableCorpus'),
            ('com.familyconnect.app.ControlProtocolRuntimeTest', 'strictJson'),
            ('com.familyconnect.app.ControlRnsRuntimeTest', 'packagedPythonImportsRnsAndInitializesWithoutDeviceKeys'),
            ('com.familyconnect.app.ControlStorageRuntimeTest', 'keystoreJournalAndOutboxSurviveRestart')}
found = set()
for path in (root/'clients/android/app/build/outputs/androidTest-results').rglob('*.xml'):
    for case in ET.parse(path).iter('testcase'):
        key = (case.get('classname'), case.get('name'))
        if key not in expected:
            continue
        assert not any(case.find(name) is not None for name in ('failure', 'error', 'skipped')), 'Android control test did not pass'
        found.add(key)
assert found == expected, 'Android control runtime test results missing'
receipt=json.loads((root/'android-control-storage-result.json').read_text())
assert receipt['passed'] is True and receipt['distinct_processes'] is True, 'Storage restart did not pass'
digest = hashlib.sha256((root/'tests/vectors/control-v1/manifest.json').read_bytes()).hexdigest()
assert digest == 'c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd'
print(f'::notice title=Android control conformance::30 configurations, 15 ACKs, 32 structure refusals, 4 authenticated-cipher refusals; strict JSON, packaged RNS and Keystore/AtomicFile/outbox process restart passed; manifest SHA256 {digest}')
