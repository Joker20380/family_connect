import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

import pytest


@pytest.mark.skipif(os.environ.get('FC_PRIVATE_HOOK_TEST') != 'canary58', reason='explicit private-device acceptance only')
def test_private_hook_on_off_and_fresh_process():
    package = 'com.familyconnect.app.friends'
    command = [os.environ['FC_ADB'], '-s', os.environ['FC_ADB_SERIAL']]
    evidence = Path(os.environ['FC_HOOK_EVIDENCE'])

    def adb(*arguments):
        return subprocess.run(command + list(arguments), capture_output=True, timeout=30)

    def flags():
        result = adb('shell', 'run-as', package, 'cat', 'shared_prefs/orchestrator-diagnostic.xml')
        assert result.returncode == 0
        return {item.attrib['name']: item.attrib.get('value') for item in ET.fromstring(result.stdout)}

    def prepare(enabled):
        result = adb('shell', 'am', 'start', '-n', package + '/com.familyconnect.app.OrchestratorDiagnosticActivity',
                     '--es', 'mode', 'prepare', '--ez', 'deny_normal', str(enabled).lower())
        assert result.returncode == 0 and b'Error' not in result.stdout
        expected = 'ON' if enabled else 'OFF'
        for iteration in range(20):
            time.sleep(0.25)
            result = adb('shell', 'run-as', package, 'cat', 'files/orchestrator-prepared.json')
            if result.returncode == 0:
                record = json.loads(result.stdout)
                if record.get('ready') and record.get('acceptance_override') == expected:
                    break
        assert record.get('ready') and record.get('acceptance_override') == expected
        assert all(flags().get('deny_' + transport) == str(enabled).lower() for transport in ('awg', 'wg', 'tcp'))
        return record

    metadata = adb('shell', 'dumpsys', 'package', package).stdout
    assert b'versionCode=58 ' in metadata
    assert b'DEBUGGABLE' in metadata
    for transport in ('awg', 'wg', 'tcp'):
        assert adb('shell', 'run-as', package, 'test', '-e', 'no_backup/auto-' + transport + '.profile').returncode == 1
    launcher = adb('shell', 'cmd', 'package', 'resolve-activity', '--brief', package).stdout.decode().strip().splitlines()[-1]
    assert launcher.startswith(package + '/') and 'MainActivity' not in launcher
    records = {'launcher': launcher}
    try:
        records['enabled'] = prepare(True)
    finally:
        records['disabled'] = prepare(False)
        with evidence.open('x') as stream:
            json.dump(records, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
    previous = adb('shell', 'pidof', package).stdout.strip()
    assert adb('shell', 'am', 'force-stop', package).returncode == 0
    assert adb('shell', 'am', 'start', '-n', launcher).returncode == 0
    time.sleep(3)
    current = adb('shell', 'pidof', package).stdout.strip()
    assert current and current != previous
    assert all(flags().get('deny_' + transport) == 'false' for transport in ('awg', 'wg', 'tcp'))
    with evidence.with_suffix('.fresh.json').open('x') as stream:
        json.dump({'fresh_process': True, 'acceptance_override': 'OFF', 'launcher': launcher}, stream)
        stream.flush()
        os.fsync(stream.fileno())
