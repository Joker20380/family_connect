"""Compare desktop online snapshots to the unmodified accepted106 pure Java projector."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from provisioning.support import SupportSnapshot
from scripts.diagnostic106_vectors import support_cases


def run(arguments):
    reference = json.loads((ROOT/'clients/shared/android106-reference.json').read_text())['reference']
    inventory_path = ROOT/reference['source_inventory']
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest(inventory_path) == reference['source_inventory_sha256']
    name = 'clients/android/app/src/main/java/com/familyconnect/app/SupportSnapshot.java'
    source = ROOT/reference['source']/name
    assert digest(source) == json.loads(inventory_path.read_text())[name]
    output = Path(arguments.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    gson = str(Path(arguments.gson).resolve())
    jdk = Path(arguments.jdk).resolve()/'bin'
    vectors = support_cases()
    with tempfile.TemporaryDirectory(prefix='fc-support106-reference-') as directory:
        compiled = subprocess.run([str(jdk/'javac'), '-J-Xmx192m', '-J-XX:ActiveProcessorCount=1',
            '-cp', gson, '-d', directory, str(source), str(ROOT/'tests/fixtures/desktop_diagnostics106/SupportProjectionReference.java')],
            capture_output=True, text=True, timeout=45)
        (output/'javac.stderr').write_text(compiled.stderr)
        compiled.check_returncode()
        executed = subprocess.run([str(jdk/'java'), '-Xmx192m', '-XX:ActiveProcessorCount=1',
            '-cp', directory+':'+gson, 'com.familyconnect.app.SupportProjectionReference'], input=json.dumps(vectors),
            capture_output=True, text=True, timeout=45)
        (output/'java.stderr').write_text(executed.stderr)
        executed.check_returncode()
    expected = json.loads(executed.stdout)
    (output/'java.json').write_text(json.dumps(expected, indent=2)+'\n')
    for report in expected.values():
        assert report['platform'] == 'android'
        report['platform'] = 'linux'
    actual = {name: SupportSnapshot.project(value, 2011, 1000000, report_id='a'*32) for name, value in vectors.items()}
    (output/'desktop.json').write_text(json.dumps(actual, indent=2)+'\n')
    differences = [name for name in vectors if expected[name] != actual[name]]
    result = dict(schema=1, reference='android106-native105', accepted_source={name:digest(source)},
        gson_sha256=digest(Path(gson)), adaptation='platform android to linux; report_id fixed only in fixture',
        vectors=len(vectors), differences=differences, status='FAIL' if differences else 'PASS',
        expected_sha256={name:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',', ':')).encode()).hexdigest() for name,value in expected.items()})
    saved = ROOT/'clients/shared/android106-support.json'
    if saved.exists():
        contract = json.loads(saved.read_text())
        assert contract['expected_sha256'] == result['expected_sha256']
        assert contract['gson_sha256'] == result['gson_sha256']
        inventory = json.loads(inventory_path.read_text())
        for relative, expected_hash in contract['accepted_source'].items():
            assert digest(ROOT/reference['source']/relative) == expected_hash == inventory[relative]
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('status','vectors','differences')}))
    if differences:raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--jdk', required=True)
    parser.add_argument('--gson', required=True)
    parser.add_argument('--output', required=True)
    run(parser.parse_args())
