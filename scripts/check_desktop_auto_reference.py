"""Compare a synthetic Go policy trace with exact accepted Java sources, not an APK."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(command, destination, name, timeout, cwd=ROOT):
    result = subprocess.run(command, cwd=cwd, timeout=timeout, capture_output=True, text=True)
    (destination / (name + '.stdout')).write_text(result.stdout)
    (destination / (name + '.stderr')).write_text(result.stderr)
    result.check_returncode()
    return result


def run(arguments):
    reference = json.loads((ROOT / 'clients/shared/android106-reference.json').read_text())['reference']
    contract = json.loads((ROOT / 'clients/shared/android106-auto.json').read_text())
    capsule = ROOT / reference['source']
    names = ['clients/android/app/src/main/java/com/familyconnect/app/' + name + '.java'
             for name in ('ConnectivityOrchestrator', 'Transport')]
    for name in names:
        if digest(capsule / name) != contract['accepted_sources'][name]:
            raise ValueError('Accepted source drift: ' + name)
    destination = Path(arguments.output).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    harness = ROOT / 'tests/fixtures/desktop_auto/AutoPolicyReference.java'
    with tempfile.TemporaryDirectory(prefix='fc-auto-') as temporary:
        execute([str(Path(arguments.jdk).resolve() / 'bin/javac'), '-J-Xmx192m', '-J-XX:ActiveProcessorCount=1',
                        '-encoding', 'UTF-8', '-d', temporary, *[str(capsule / name) for name in names], str(harness)],
                       destination, 'javac', 45)
        java = execute([str(Path(arguments.jdk).resolve() / 'bin/java'), '-Xmx64m', '-XX:ActiveProcessorCount=1',
                               '-XX:+UseSerialGC', '-cp', temporary, 'com.familyconnect.app.AutoPolicyReference'],
                              destination, 'java', 30)
    go = execute([str(Path(arguments.go).resolve()), 'test', '-count=1', '-json', '-run', '^TestAcceptedReferenceTrace$', './desktopauto'],
                 destination, 'go', 90, cwd=ROOT / 'carrier')
    actual = []
    for line in go.stdout.splitlines():
        entry = json.loads(line)
        output = entry.get('Output', '')
        for marker in ('AUTO_EVENT|', 'AUTO_STATE|'):
            if marker in output:
                actual.append(marker + output.split(marker, 1)[1].strip())
    expected = java.stdout.splitlines()
    (destination / 'accepted-traces.json').write_text(json.dumps(expected, indent=2) + '\n')
    (destination / 'desktop-traces.json').write_text(json.dumps(actual, indent=2) + '\n')
    scenarios = {line.split('|')[1] for line in expected if line.startswith('AUTO_STATE|')}
    result = dict(result='PASS' if expected == actual and len(scenarios) == 17 else 'FAIL',
                  scenarios=len(scenarios), records=len(expected),
                  accepted_sources={name: digest(capsule / name) for name in names},
                  harness_sha256=digest(harness),
                  scope='synthetic policy transitions only; no VPN, GUI, Android APK build or device contact')
    (destination / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    if result['result'] != 'PASS':
        raise SystemExit('Auto policy trace differs; compare the two retained trace files')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--go', required=True)
    parser.add_argument('--jdk', required=True)
    parser.add_argument('--output', required=True)
    run(parser.parse_args())
