"""Bounded JVM regressions for provisioning selection and retained cleanup causes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pipeline', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    tools, output = args.tools.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    classes = output / 'classes'
    classes.mkdir()
    java = root / 'clients/android/app/src/main/java'
    tests = root / 'clients/android/app/src/test/java'
    names = ['ReadinessFetchTraceTest', 'ReadinessBootstrapRouteTest', 'ConnectivityOrchestratorTest', 'DiagnosticRingTest',
             'RestrictedBootstrapTest', 'ReadinessStopTest', 'RestrictedGatewayTest', 'RestrictedCacheTest',
             'ReadinessProductTest', 'FriendsReadinessProtocolTest']
    jars = [next((tools / 'gradle-home/caches/modules-2/files-2.1').rglob(name)) for name in
            ('gson-2.13.2.jar', 'junit-4.13.2.jar', 'hamcrest-core-1.3.jar', 'bcprov-jdk18on-1.85.2.jar')]
    classpath = os.pathsep.join(map(str, [*jars, root / 'tests/vectors', root / 'clients/android/app/src/test/resources']))
    commands = [[str(tools / 'jdk/bin/javac'), '-J-Xmx256m', '-J-XX:ActiveProcessorCount=2',
                 '-sourcepath', os.pathsep.join(map(str, (java, tests))), '-cp', classpath, '-d', str(classes),
                 *[str(tests / 'com/familyconnect/app' / (name + '.java')) for name in names]],
                [str(tools / 'jdk/bin/java'), '-Xmx128m', '-XX:ActiveProcessorCount=2', '-cp', str(classes) + os.pathsep + classpath,
                 'org.junit.runner.JUnitCore', *['com.familyconnect.app.' + name for name in names]]]
    if args.pipeline:
        fixture = Path(__file__).resolve().parent / 'provision_platform'
        disabled = root / 'clients/android/app/src/provisioningDisabled/java'
        selected = ['FriendsAccessAndroid', 'FriendsRestricted', 'FriendsIdentityVault', 'RestrictedVault',
                    'RestrictedTunnelEngine', 'AutomaticVpnOwner', 'ProvisioningCarrier']
        commands = [[str(tools / 'jdk/bin/javac'), '-J-Xmx256m', '-J-XX:ActiveProcessorCount=2',
                     '-sourcepath', os.pathsep.join(map(str, (java, disabled))), '-cp', classpath,
                     '-d', str(classes), *map(str, sorted(fixture.glob('*.java'))),
                     *[str(java / 'com/familyconnect/app' / (name + '.java')) for name in selected]]]
    else:
        network = Path(__file__).resolve().parent / 'network_fixture'
        network_classes = output / 'network-classes'
        network_classes.mkdir()
        commands += [[str(tools / 'jdk/bin/javac'), '-J-Xmx128m', '-cp', classpath, '-d', str(network_classes),
                      *map(str, sorted(network.glob('*.java'))), str(java / 'com/familyconnect/app/ChatNetworkAndroid.java')],
                     [str(tools / 'jdk/bin/java'), '-Xmx64m', '-cp', str(network_classes)+os.pathsep+classpath, 'com.familyconnect.app.NetworkProbe']]
    receipts = []
    for index, command in enumerate(commands):
        log = output / f'check-{index}.log'
        with log.open('xb') as stream:
            result = subprocess.run(['nice', '-n', '10', *command], cwd=root, stdout=stream, stderr=subprocess.STDOUT, timeout=90)
        receipts.append(dict(command=command, exit=result.returncode, log=log.name, sha256=hashlib.sha256(log.read_bytes()).hexdigest()))
        (output / 'receipt.json').write_text(json.dumps(receipts, indent=2) + '\n')
        print(log.name, result.returncode, flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
