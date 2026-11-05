from pathlib import Path
import re
import sys
import zipfile

from credential_renewal import canonical, digest, parse, read_private, require
from online_contract import CONTRACT


PACKAGE = 'MESH_ONLINE_RUNTIME_V1'
FEATURES = ['durable-commit', 'emergency-continuation', 'fencing', 'pre-delivery-runtime-confirmation',
            'readiness-generation', 'runtime-reader']


def runtime_binding(manifest, path=None):
    if path is None:
        return {}
    from production_node import pinned
    raw = pinned(Path(path), {0})[0]
    artifact = parse(raw)
    require(type(artifact) is dict and set(artifact) == {'schema', 'scope', 'source_commit', 'native_sources',
            'entrypoint', 'executable_sha256'} and type(artifact['schema']) is int and artifact['schema'] == 1,
            'ONLINE_ISOLATED_ARTIFACT_SCHEMA')
    require(artifact['scope'] == 'isolated-core-not-production' and
            artifact['entrypoint'] == 'carrier/internal/qualification/cmd/mesh-runtime' and
            artifact['source_commit'] == manifest['source_commit'] and
            artifact['native_sources'] == manifest['native_sources'] and
            type(artifact['executable_sha256']) is str and re.fullmatch('[0-9a-f]{64}', artifact['executable_sha256']),
            'ONLINE_ISOLATED_ARTIFACT_BINDING')
    return dict(runtime_scope=artifact['scope'], reader_sha256=artifact['executable_sha256'],
                runtime_manifest_sha256=digest(raw))


def package_manifest(source):
    from production_node import pinned
    manifest = parse(read_private(source.parent/'source-manifest.json'))
    require(manifest.get('package_contract') == PACKAGE and manifest.get('online_contract') == CONTRACT
            and manifest['production_configuration'] == 'absent' and manifest['binding'] == 'unbound'
            and manifest['operation_permit'] is None, 'ONLINE_PACKAGE_REQUIRED')
    require('online_runtime.py' in manifest['source_files'] and 'online_cli.py' in manifest['source_files'],
            'SOURCE_MANIFEST_INCOMPLETE')
    for name, expected in manifest['source_files'].items():
        require(type(name) is str and re.fullmatch('[a-z_]+\\.py', name), 'SOURCE_PATH')
        require(digest(pinned(source/name, {0})[0]) == expected, 'SOURCE_IDENTITY_MISMATCH')
    require(digest(canonical(manifest['source_files'])) == manifest['source_sha256'], 'SOURCE_IDENTITY_MISMATCH')
    return manifest


def load_api(archive, expected):
    from production_node import pinned
    raw = pinned(archive, {0})[0]
    require(digest(raw) == expected, 'API_IDENTITY_MISMATCH')
    with zipfile.ZipFile(archive) as library:
        manifest = parse(library.read('source-manifest.json'))
        require(manifest.get('package_contract') == PACKAGE and manifest.get('online_contract') == CONTRACT,
                'ONLINE_API_REQUIRED')
        require(set(library.namelist()) == set(manifest['files']) | {'source-manifest.json'}, 'ONLINE_API_INVENTORY')
        for name, checksum in manifest['files'].items():
            require(digest(library.read(name)) == checksum, 'API_IDENTITY_MISMATCH')
    sys.path.insert(0, str(archive))
    from control.friends import restricted
    require(str(restricted.__file__).startswith(str(archive)+'/') or
            str(restricted.__file__).startswith('/proc/self/fd/'), 'ONLINE_API_IMPORT_BOUNDARY')
    require(callable(getattr(restricted, 'online_generation', None)), 'ONLINE_API_REQUIRED')


def activate(node, config, source):
    manifest = package_manifest(source)
    require(config['source_files'] == manifest['source_files'] and config['source_sha256'] == manifest['source_sha256']
            and config['api_sha256'] == manifest['api_sha256'], 'ONLINE_PACKAGE_BINDING')
    settings = config['online']
    expected = {'contract'} | ({'reader_socket', 'reader_uid', 'reader_executable_sha256'} if node.role == 'NL' else set())
    if type(settings) is dict and 'isolated_runtime' in settings:
        expected.add('isolated_runtime')
    require(type(settings) is dict and set(settings) == expected and settings['contract'] == CONTRACT,
            'ONLINE_OPT_IN_REQUIRED')
    require(node.validator.all_activated and node.gateway_ids is not None, 'ONLINE_MEMBERSHIP_REQUIRED')
    load_api(Path(config['api_archive']), manifest['api_sha256'])
    binding = runtime_binding(manifest, settings.get('isolated_runtime'))
    if node.role == 'NL':
        from online_reader import RuntimeReader
        require(type(settings['reader_uid']) is int and settings['reader_uid'] >= 0
                and settings['reader_executable_sha256'] == binding.get('reader_sha256', manifest['gateway_sha256']),
                'ONLINE_READER_BINDING')
        node.online_reader = RuntimeReader(settings['reader_socket'], expected_uid=settings['reader_uid'],
            expected_executable=settings['reader_executable_sha256'],
            service_state=lambda: node.barrier.state(node.barrier.units[0]))
    node.online_runtime = dict(contract=CONTRACT, package_contract=PACKAGE, features=FEATURES,
        slot=node.gateway_slot, gateway_ids=node.gateway_ids, source_sha256=manifest['source_sha256'],
        api_sha256=manifest['api_sha256'], gateway_sha256=manifest['gateway_sha256'])
    node.online_runtime.update(binding)


def capabilities(node):
    require(getattr(node, 'online_runtime', None) is not None, 'ONLINE_OPT_IN_REQUIRED')
    result = dict(node.online_runtime)
    if node.role == 'NL':
        from online_node import reader
        result['runtime'] = None if node.barrier.stopped() else reader(node)
    return result


def verify_participants(nodes, operation, manifest, membership, *, running, binding=None):
    require(set(nodes) == {'RU', 'NL', 'NL2'}, 'ONLINE_MEMBERSHIP_REQUIRED')
    for slot, remote in nodes.items():
        received = remote.call('online', operation, dict(command='capabilities'))
        expected = dict(contract=CONTRACT, package_contract=PACKAGE, features=FEATURES, slot=slot,
            gateway_ids=membership, source_sha256=manifest['source_sha256'], api_sha256=manifest['api_sha256'],
            gateway_sha256=manifest['gateway_sha256'])
        expected.update(binding or {})
        require(type(received) is dict and {name: value for name, value in received.items() if name != 'runtime'} == expected,
                'ONLINE_PARTICIPANT_CAPABILITIES')
        if slot != 'RU':
            require('runtime' in received and (received['runtime'] is not None or not running), 'ONLINE_READER_STOPPED')
            if received['runtime'] is not None:
                runtime = received['runtime']
                require(type(runtime) is dict and set(runtime) == {'contract', 'gateway', 'profile_sha256', 'instance'}
                        and runtime['contract'] == CONTRACT and runtime['gateway'] == membership[slot]
                        and all(type(runtime[name]) is str and re.fullmatch('[0-9a-f]{64}', runtime[name])
                                for name in ('profile_sha256', 'instance')), 'ONLINE_RUNTIME_RECEIPT')
