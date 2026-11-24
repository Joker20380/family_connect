"""Cold source/dependency readback of retained canonical inputs; no database dispatch."""
import base64
import importlib
import importlib.metadata
import json
from pathlib import Path
import sys

from scripts import control_ha_recovery_kit as kit

MODULES = ('control.app', 'device_identity.device',
    'scripts.control_ha_installed_composite', 'scripts.control_ha_joint_nodes',
    'scripts.control_ha_owner_joint', 'scripts.control_ha_worker_qualify',
    'scripts.control_ha_mailbox_custody', 'scripts.control_ha_forward_archive',
    'scripts.control_ha_handoff_rehearsal', 'scripts.control_ha_owner_image_bootstrap')


def dependency_probe(source):
    kit.require(sys.version_info[:2] == (3, 13) and sys.prefix != sys.base_prefix, 'COLD_PYTHON_VENV')
    expected = kit.requirements({name: (source / name).read_bytes()
                                for name in kit.LOCKS + kit.SCHEMAS + kit.NATIVE + (kit.BOOTSTRAP,)})
    for name, version in expected.items():
        kit.require(importlib.metadata.version(name) == version, 'COLD_DEPENDENCY_VERSION')
        distribution = importlib.metadata.distribution(name)
        kit.require(Path(sys.prefix) in Path(distribution.locate_file('')).resolve().parents, 'COLD_DEPENDENCY_ORIGIN')
    for name in MODULES:
        module = importlib.import_module(name)
        kit.require(source in Path(module.__file__).resolve().parents, 'COLD_SOURCE_ORIGIN')
    import psycopg
    kit.require(psycopg.pq.__impl__ == 'binary', 'COLD_LIBPQ_IMPLEMENTATION')
    return dict(locked_distributions=len(expected), entry_modules=len(MODULES), libpq=psycopg.pq.version())


def canonical_probe(inputs):
    from scripts import control_ha_file_custody as custody
    from scripts import control_ha_live_sqlite_restore as sqlite
    from scripts import control_ha_installed_composite as native
    stores, manifest = sqlite.unpack((inputs / 'stores.aesgcm').read_bytes(), (inputs / 'stores.key').read_bytes(),
                                    kit.document((inputs / 'stores.checkpoint.json').read_bytes()))
    sqlite.validate(stores, manifest)
    external = custody.unseal((inputs / 'RU.aesgcm').read_bytes(), (inputs / 'RU.key').read_bytes(),
                             kit.document((inputs / 'RU.checkpoint.json').read_bytes()))
    files = {name: base64.b64decode(entry['body'], validate=True) for name, entry in external['entries'].items()
             if entry['kind'] == 'file' and (name in native.FIXED or name.startswith('routing/'))}
    prepared = prepare_canonical(stores, files, now=manifest['captured_at_ns'] // 1000000000)
    return prepared.summary()


def prepare_canonical(stores, files, *, now):
    from scripts import control_ha_installed_composite as native
    store_pins = {name: kit.digest(raw) for name, raw in stores.items()}
    file_pins = {name: kit.digest(raw) for name, raw in files.items()}
    reference = kit.digest(kit.encoded(dict(purpose='cold-native-readback-reference-only',
                                          stores=store_pins, files=file_pins)))[:32]
    return native.preflight(stores, files, store_pins, file_pins, reference, now=now)


def fleet_probe(inputs, scratch):
    from scripts import control_ha_file_custody as custody
    from scripts import control_ha_node_restore as nodes
    from scripts import control_ha_node_qualify as native
    from scripts import control_ha_worker_custody as worker
    from scripts import control_ha_worker_qualify as worker_native
    from scripts import control_ha_mailbox_custody as mailbox

    def unseal(role, loader):
        return loader((inputs / (role + '.aesgcm')).read_bytes(), (inputs / (role + '.key')).read_bytes(),
                      kit.document((inputs / (role + '.checkpoint.json')).read_bytes()))

    results = {}
    for slot in ('RU', 'NL1', 'NL2'):
        files, manifest = unseal('node-' + slot, nodes.unseal)
        kit.require(manifest['slot'] == slot, 'COLD_NODE_SLOT')
        results[slot] = native.qualify(files, manifest, scratch / slot)
    results['worker'] = worker_native.qualify(unseal('worker', worker.unseal), scratch / 'worker')
    results['mailbox'] = mailbox.validate(unseal('mailbox', custody.unseal))
    return results


def probe(inputs, scratch):
    denied = []

    def audit(event, arguments):
        if event.startswith(('socket.connect', 'socket.getaddrinfo', 'subprocess.', 'os.exec', 'os.spawn')) or event == 'os.system':
            denied.append(event)
            raise RuntimeError('DISPATCH_FORBIDDEN')

    sys.addaudithook(audit)
    import ctypes.util
    ctypes.util.find_library = lambda name: 'libc.so.6' if name == 'c' else None
    source = Path(__file__).resolve().parents[1]
    dependencies = dependency_probe(source)
    canonical = canonical_probe(Path(inputs))
    fleet = fleet_probe(Path(inputs), Path(scratch))
    kit.require(not denied, 'UNEXPECTED_DISPATCH')
    return dict(result='COLD_RECOVERY_SOURCE_DEPENDENCIES_PASS', dependencies=dependencies, canonical=canonical, fleet=fleet,
                dispatch_calls=0, original_source_mounted=False, developer_venv_mounted=False,
                activation=False, full_recovery=False)


if __name__ == '__main__':
    try:
        kit.require(len(sys.argv) == 3, 'PROBE_ARGUMENTS')
        print(json.dumps(probe(*sys.argv[1:]), sort_keys=True))
    except Exception as error:
        print(json.dumps(dict(result='COLD_RECOVERY_SOURCE_DEPENDENCIES_REFUSED', error=type(error).__name__)), file=sys.stderr)
        raise SystemExit(1) from None
