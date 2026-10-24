"""Package the Linux privileged MESH component without installing or publishing it."""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import zipfile

from scripts.package_system_python import collect
from scripts.build_desktop_mesh import sources as native_sources

ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def relay_payload(directory):
    build_raw = (directory / 'build.json').read_bytes()
    build = json.loads(build_raw)
    archive = (directory / 'fc-rns.pyz').read_bytes()
    if (build['schema'] != 1 or build['files']['fc-rns.pyz'] != dict(sha256=digest(archive), size=len(archive)) or
            digest(json.dumps(build['sources'], sort_keys=True, separators=(',', ':')).encode()) != build['source_digest']):
        raise ValueError('RNS build integrity mismatch')
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        if len(bundle.namelist()) != len(set(bundle.namelist())) or set(bundle.namelist()) != set(build['sources']):
            raise ValueError('RNS source inventory mismatch')
        for name, expected in build['sources'].items():
            if digest(bundle.read(name)) != expected:
                raise ValueError('RNS source digest mismatch')
        for name, source in (('__main__.py', 'launcher.py'), ('fc_rns_worker.py', 'worker.py'), ('fc_rns_transport.py', 'fc_rns_transport.py')):
            if bundle.read(name) != (ROOT / 'clients/rns' / source).read_bytes():
                raise ValueError('Stale RNS application sources')
    version = json.loads(subprocess.run(['/usr/bin/python3', '-I', '-S', str(directory / 'fc-rns.pyz'), '--version'],
                                       check=True, capture_output=True, timeout=10).stdout)
    if version != build['runtime'] or version != dict(rns_protocol=1, rns='1.5.1', pyserial='3.5', crypto_provider='internal'):
        raise ValueError('RNS runtime metadata mismatch')
    payload = {'rns/fc-rns.pyz': archive, 'rns/build.json': build_raw}
    for name in ('Reticulum.txt', 'PySerial.txt'):
        raw = (directory / 'licenses' / name).read_bytes()
        if digest(raw) != build['sources']['licenses/' + name]:
            raise ValueError('RNS notice mismatch')
        payload['licenses/rns/' + name] = raw
    return payload


def normal_payload(awg, tcp):
    spec = importlib.util.spec_from_file_location('awg_bundle_check', ROOT / 'clients/linux/check-awg-bundle.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    checker.check(awg)
    binary = tcp.read_bytes()
    if binary[:6] != b'\x7fELF\x02\x01' or binary[18:20] != b'\x3e\x00':
        raise ValueError('TCP requires Linux amd64 Xray')
    version = subprocess.run([str(tcp), 'version'], check=True, capture_output=True, text=True, timeout=10).stdout.splitlines()[0]
    if 'Xray 26.3.27 ' not in version or 'd2758a0' not in version or 'go1.26.1 linux/amd64' not in version:
        raise ValueError('Pinned Xray runtime required')
    payload = {'normal/awg/' + name: (awg / name).read_bytes() for name in
               ('awg', 'amneziawg-go', 'awg-quick', 'awg31.json', 'LICENSE-go', 'LICENSE-tools')}
    payload['normal/awg/awg-quick'] = checker.adapt_quick(payload['normal/awg/awg-quick'])
    payload['normal/tcp/xray'] = binary
    payload['normal/tcp/LICENSE'] = (ROOT / 'pilot/tcp/LICENSE-Xray').read_bytes()
    payload['systemd/family-connect-tcp@.service'] = (ROOT / 'clients/linux/family-connect-tcp@.service').read_bytes()
    record = dict(awg=json.loads((awg / 'awg31.json').read_text()), xray_version=version,
                  xray_revision='d2758a023cd7f4174a5a5fa4ff66e487d4342ba0',
                  provenance='Pinned pilot/awg31 and pilot/tcp Docker builders; operator-provided inputs, not a signature',
                  files={name: digest(raw) for name, raw in sorted(payload.items())})
    payload['normal/build.json'] = (json.dumps(record, sort_keys=True, indent=2) + '\n').encode()
    return payload


def assemble(native, relay, destination, awg, tcp):
    if destination.exists():
        raise ValueError('Use a fresh delivery directory')
    build = json.loads((native / 'build.json').read_bytes())
    sources = json.loads((native / 'source-inventory.json').read_bytes())
    if (build.get('build_tags') != [] or
            sources != native_sources(ROOT / 'clients/mesh') or
            digest(json.dumps(sources, sort_keys=True, separators=(',', ':')).encode()) != build['source_digest']):
        raise ValueError('Standard native source inventory required')
    binary = (native / 'fc-mesh').read_bytes()
    if (build['os'] != 'linux' or build['arch'] != 'amd64' or build['local_packet_ipc_tests'] != 'PASS' or
            digest(binary) != build['files']['fc-mesh']['sha256'] or len(binary) != build['files']['fc-mesh']['size']):
        raise ValueError('Native artifact verification failed')
    version = json.loads(subprocess.run([str((native / 'fc-mesh').resolve()), '--version'], check=True,
                                       capture_output=True, timeout=5).stdout)
    if (version['source_manifest'] != build['source_digest'] or version['core_reference'] != 'android106-native105' or
            version['bridge_protocol'] != 1 or version['materials_protocol'] != 1 or version.get('auto_policy_protocol') != 1 or
            version.get('normal_configuration_protocol') != 1 or version.get('chat_ipc_protocol') != 1 or
            version.get('private_chat_endpoint') != 'inherited-unix-stream'):
        raise ValueError('Native metadata mismatch')
    spec = importlib.util.spec_from_file_location('mesh_component_installer', ROOT / 'clients/linux/install-mesh-bundle.py')
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    payload = {'bin/fc-mesh': binary, 'lib/helper': (ROOT / 'clients/linux/mesh-helper.py').read_bytes(),
               **{'systemd/family-connect-' + name + '@.service': (ROOT / ('clients/linux/family-connect-' + name + '@.service')).read_bytes()
                  for name in installer.UNITS},
               'install.py': (ROOT / 'clients/linux/install-mesh-bundle.py').read_bytes()}
    payload.update(collect())
    payload.update(normal_payload(awg, tcp))
    payload['lib/update.pub'] = (ROOT / 'clients/desktop/update.pub').read_bytes()
    for name in ('build.json', 'source-inventory.json', 'dependencies.json'):
        payload['native/' + name] = (native / name).read_bytes()
    payload.update(relay_payload(relay))
    for name in installer.MODULES:
        path = ROOT / ('clients/desktop' if name in ('backend.py', 'profile_config.py') else 'clients/linux') / name
        payload['lib/' + name] = path.read_bytes()
    for name in installer.COMMON:
        payload['lib/' + name] = (ROOT / name).read_bytes()
    for kind in ('awg', 'tcp'):
        payload['compat/' + kind + '-helper.py'] = (ROOT / 'clients/linux' / (kind + '-helper.py')).read_bytes()
    for path in sorted((native / 'licenses').rglob('*')):
        if path.is_symlink():
            raise ValueError('Unsafe native license artifact')
        if path.is_file():
            payload['licenses/' + str(path.relative_to(native / 'licenses'))] = path.read_bytes()
    if not any(name.startswith('licenses/') for name in payload):
        raise ValueError('Native licenses are missing')
    dependencies = json.loads(payload['native/dependencies.json'])
    for dependency in dependencies.values():
        if not dependency['notices']:
            raise ValueError('Native dependency notice is missing')
        for name, checksum in dependency['notices'].items():
            if 'licenses/' + name not in payload or digest(payload['licenses/' + name]) != checksum:
                raise ValueError('Native dependency notice mismatch')
    if not {'licenses/Go.txt', 'licenses/Xray-modifications.patch'} <= set(payload):
        raise ValueError('Native toolchain/patch notices missing')
    payload['README.txt'] = ("Family Connect L03.1 system/runtime component — private internal build.\n"
        "Not a complete desktop installer or a runtime-accepted VPN release. Unsigned; hashes are integrity only.\n"
        "Includes manual MESH, Auto, protected DIRECT and service-only chat hosts, units, packaged public anchor and locked isolated Python runtime.\n"
        "Includes pinned AWG3.1 and Xray26.3.27 binaries/helpers/notices; no developer binary search is required at installation.\n"
        "The GUI application is delivered separately; this archive does not update or bundle the full desktop UI.\n"
        "Linux x86_64, matching Python ABI (python-runtime.json), systemd254+, systemd-resolved/resolvconf, iproute2, nftables, curl, bash, procps, polkit, /dev/net/tun required.\n"
        "Recovery retains private session material only in a systemd-held memory descriptor, not a new key file.\n"
        "Disconnect Family Connect first. Explicit installation: pkexec /usr/bin/python3 -I ./install.py\n"
        "GUI never runs as root. Installation does not start services or alter user identity/configuration.\n"
        "AWG/TCP components are installed together under their locks. Failure restores previous own files.\n"
        "Root-owned template masks plus shared lifetime admission exclude starts throughout installation. Live owners and sticky MESH cleanup are refused, never stopped/cleared.\n"
        "Explicit Chat settings / Prepare protected chat access uses existing polkit authorization for the caller UID only; starts only the two idle chat hosts, without enabling VPN or changing background settings. Repeat setup after reboot; no boot-time enablement is added.\n"
        "Capabilities schema2 bind all installed files and build ID, not just native source_digest. Old schema1 hosts are unavailable to this client.\n"
        "AWG teardown uses a private ownership journal and remains required after TUN/process death.\n"
        "Setup refuses pending AWG cleanup; never remove its journal or flush unrelated routing/firewall rules.\n"
        "After successful install, rollback by reinstalling the previous verified component while disconnected.\n"
        "Retain the printed root-owned backup directory for operator recovery. No public catalog was changed.\n\n"
        "Компонент для закрытой разработки, не готовый desktop-релиз. Установщик не подписан.\n"
        "Отключите Family Connect; разрешите штатный pkexec только для этого проверенного пакета.\n"
        "Identity и пользовательские данные не переносятся и не удаляются. Служба не запускается.\n").encode()
    manifest = dict(schema=2, architecture='amd64', source_digest=build['source_digest'], signing='unsigned-private-component',
                    sha256={name: digest(raw) for name, raw in sorted(payload.items())},
                    sizes={name: len(raw) for name, raw in sorted(payload.items())})
    manifest['build_id'] = digest(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode())
    destination.mkdir(parents=True)
    directory = destination / 'FamilyConnect-MESH-system-amd64'
    directory.mkdir()
    for name, raw in payload.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o755 if name in ('bin/fc-mesh', 'lib/helper') else 0o644)
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    installer.verify(directory)
    archive = destination / 'FamilyConnect-MESH-system-amd64.tar.gz'
    with archive.open('wb') as sink, gzip.GzipFile(fileobj=sink, mode='wb', filename='', mtime=0) as compressed, tarfile.open(fileobj=compressed, mode='w') as output:
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                raw = path.read_bytes()
                entry = tarfile.TarInfo(directory.name + '/' + str(path.relative_to(directory)))
                entry.size, entry.mode, entry.mtime = len(raw), path.stat().st_mode & 0o777, 0
                output.addfile(entry, io.BytesIO(raw))
    with tempfile.TemporaryDirectory(prefix='fc-mesh-archive-') as scratch:
        with tarfile.open(archive) as source:
            expected = {directory.name + '/' + name for name in (*payload, 'manifest.json')}
            members = source.getmembers()
            if len(members) != len(expected) or {entry.name for entry in members} != expected or not all(entry.isfile() for entry in members):
                raise ValueError('Unexpected packaged archive members')
            source.extractall(scratch, filter='data')
        unpacked_manifest, unpacked_payload = installer.verify(Path(scratch) / directory.name)
        if unpacked_manifest != manifest or unpacked_payload != payload:
            raise ValueError('Packaged archive readback mismatch')
    record = dict(file=archive.name, sha256=digest(archive.read_bytes()), size=archive.stat().st_size,
                  source_digest=build['source_digest'], build_id=manifest['build_id'], installed=False, published=False, runtime_acceptance='NOT_RUN',
                  complete_desktop_installer=False, signature='none', archive_verified=True)
    (destination / 'delivery.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--rns', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--awg', type=Path, required=True)
    parser.add_argument('--tcp', type=Path, required=True)
    args = parser.parse_args()
    assemble(args.native.resolve(), args.rns.resolve(), args.out.resolve(), args.awg.resolve(), args.tcp.resolve())


if __name__ == '__main__':
    main()
