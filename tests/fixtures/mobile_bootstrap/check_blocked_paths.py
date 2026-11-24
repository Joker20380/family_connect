"""Run the shipped Android entrypoints with blocked I/O; no APK, device or network."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


SOURCE = 'd2882cde4c50b15085b925007c04c48f4de61bf0'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--tools', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source = args.source_root.resolve()
    tools = args.tools.resolve()
    output = args.output.resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    fixtures = Path(__file__).resolve().parent / 'blocked_paths'
    repository = Path(__file__).resolve().parents[3]
    java = source / 'clients/android/app/src/main/java'
    tests = source / 'clients/android/app/src/test/java'
    disabled = source / 'clients/android/app/src/provisioningDisabled/java'
    selected = [java / 'com/familyconnect/app' / (name + '.java') for name in
                ('FriendsAccessAndroid', 'ChatCarrier', 'ReadinessBootstrapRoute',
                 'RestrictedBootstrap', 'RestrictedCache', 'FriendsReadinessProtocol')]
    selected += [disabled / 'com/familyconnect/app/ProvisioningTestGate.java']
    inventory = []
    for path in selected:
        relative = path.relative_to(source).as_posix()
        expected = subprocess.check_output(['git', 'show', SOURCE + ':' + relative], cwd=repository)
        if path.read_bytes() != expected:
            raise SystemExit('Source mismatch: ' + relative)
        inventory.append({'path': relative, 'sha256': hashlib.sha256(expected).hexdigest()})
    jars = [next((tools / 'gradle-home/caches/modules-2/files-2.1').rglob(name)) for name in
            ('gson-2.13.2.jar', 'junit-4.13.2.jar', 'hamcrest-core-1.3.jar', 'bcprov-jdk18on-1.85.2.jar')]
    classpath = os.pathsep.join(map(str, jars))
    classes = output / 'classes'
    classes.mkdir()
    state = output / 'state'
    state.mkdir()
    commands = [
        [str(tools / 'jdk/bin/javac'), '-J-Xmx256m', '-J-XX:ActiveProcessorCount=2', '-cp', classpath,
         '-sourcepath', os.pathsep.join(map(str, (java, tests, disabled))), '-d', str(classes),
         *map(str, sorted(fixtures.glob('*.java'))), *map(str, selected)],
        [str(tools / 'jdk/bin/java'), '-Xmx128m', '-XX:ActiveProcessorCount=2', '-Dfixture.state=' + str(state),
         '-cp', str(classes) + os.pathsep + classpath, 'org.junit.runner.JUnitCore',
         'com.familyconnect.app.BlockedPathsTest'],
    ]
    receipt = {'source': SOURCE, 'scope': 'JVM entrypoint flow; platform, socket and native-validator seams are fixtures',
               'source_inventory': inventory, 'fixture_inventory': [
                   {'path': path.relative_to(repository).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                   for path in sorted(fixtures.glob('*.java'))], 'commands': []}
    for index, command in enumerate(commands):
        log = output / ('check-' + str(index) + '.log')
        with log.open('xb') as stream:
            result = subprocess.run(['nice', '-n', '10', *command], cwd=repository, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=90)
        receipt['commands'].append({'argv': command, 'exit': result.returncode, 'log': log.name,
                                    'sha256': hashlib.sha256(log.read_bytes()).hexdigest()})
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(log.name, 'exit=' + str(result.returncode), flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
