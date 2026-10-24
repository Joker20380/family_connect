"""Compile only pinned pure-Java projectors, never build or launch the Android app."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'clients/desktop'))
from backend import NativeDiagnostics106
from diagnostic106_vectors import cases, projected


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def run(arguments):
    reference = json.loads((ROOT/'clients/shared/android106-reference.json').read_text())
    capsule = ROOT/reference['reference']['source']
    inventory_path = ROOT/reference['reference']['source_inventory']
    assert digest(inventory_path.read_bytes()) == reference['reference']['source_inventory_sha256']
    inventory = json.loads(inventory_path.read_text())
    names = ['clients/android/app/src/main/java/com/familyconnect/app/'+name+'.java' for name in
             ('RestrictedTrace', 'RestrictedDelivery', 'SpeedReceipt', 'MuxLifecycle', 'RestrictedStartup')]
    hashes = {name: digest((capsule/name).read_bytes()) for name in names}
    for name, expected in hashes.items():
        assert inventory[name] == expected, name
    output = Path(arguments.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    vectors = cases()
    with tempfile.TemporaryDirectory(prefix='fc-diag106-reference-') as directory:
        command = [str(Path(arguments.jdk).resolve()/'bin/javac'), '-J-Xmx192m', '-J-XX:ActiveProcessorCount=1',
                   '-cp', str(Path(arguments.gson).resolve()), '-d', directory, *[str(capsule/name) for name in names],
                   str(ROOT/'tests/fixtures/desktop_diagnostics106/DiagnosticProjectionReference.java')]
        compiled = subprocess.run(command, capture_output=True, text=True, timeout=45)
        (output/'javac.stdout').write_text(compiled.stdout);(output/'javac.stderr').write_text(compiled.stderr)
        compiled.check_returncode()
        command = [str(Path(arguments.jdk).resolve()/'bin/java'), '-Xmx192m', '-XX:ActiveProcessorCount=1',
                   '-cp', directory+':'+str(Path(arguments.gson).resolve()), 'com.familyconnect.app.DiagnosticProjectionReference']
        executed = subprocess.run(command, input=json.dumps(vectors), capture_output=True, text=True, timeout=45)
        (output/'java.stderr').write_text(executed.stderr)
        executed.check_returncode()
        expected = json.loads(executed.stdout)
    actual = {name: projected(NativeDiagnostics106, value) for name, value in vectors.items()}
    (output/'java.json').write_text(json.dumps(expected, indent=2)+'\n')
    (output/'desktop.json').write_text(json.dumps(actual, indent=2)+'\n')
    differences = [name for name in vectors if expected[name] != actual[name]]
    contract = dict(schema=1, reference='android106-native105', accepted_sources=hashes,
        scope='Native valid-integer projection, profile receipts, ordered trace/delivery and Mux/startup; not online consent or OS acceptance',
        gson_sha256=digest(Path(arguments.gson).read_bytes()),
        expected_sha256={name: digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()) for name, value in expected.items()},
        differences=differences, vectors=len(vectors), status='PASS' if not differences else 'FAIL')
    saved_path = ROOT/'clients/shared/android106-diagnostics.json'
    if saved_path.exists():
        saved = json.loads(saved_path.read_text())
        assert saved['accepted_sources'] == hashes and saved['gson_sha256'] == contract['gson_sha256']
        assert saved['expected_sha256'] == contract['expected_sha256']
    (output/'result.json').write_text(json.dumps(contract, indent=2)+'\n')
    print(json.dumps(dict(vectors=len(vectors), differences=differences, status=contract['status'])))
    if differences:raise SystemExit(1)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--jdk', required=True);parser.add_argument('--gson', required=True);parser.add_argument('--output', required=True)
    run(parser.parse_args())
