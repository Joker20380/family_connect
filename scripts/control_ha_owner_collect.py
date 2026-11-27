"""Closed local OWNER input collection; no Compose invocation or service changes."""
import base64
import json
from pathlib import Path
import subprocess
import time

from scripts import control_ha_owner_capture as capture
from scripts import control_ha_owner_runtime as custody
from scripts.control_ha_installed_inventory import Reader
from scripts.control_ha_live_sqlite import require

RUNTIME = Path('/mnt/data/fc-subscription-operations-20261107/collector-runtime/control_plane')
ORIGINAL = Path('/home/joker/PycharmProjects/family_connect/control_plane')
PROJECT = Path('/mnt/data/PycharmProjects/family_connect')
TOKEN = PROJECT / 'state-client-build/system-enable-20261111/system-publisher.token'
COMPOSE = frozenset(map(str, (RUNTIME / 'compose.yaml', ORIGINAL / 'compose.yaml',
    PROJECT / 'state-client-build/system-enable-20261111/compose.publisher.yaml',
    PROJECT / 'state-client-build/support-live-20261111/compose.support.yaml',
    Path('/opt/family-connect-support/compose.notifications.yaml'),
    RUNTIME / '.local/compose.hmac-generation.yaml', RUNTIME / '.local/compose.technical-metadata.json',
    RUNTIME / '.local/compose.nlgeo-20261122.json')))


def policy(baseline):
    if baseline is None:
        return custody
    from scripts import control_ha_owner_runtime_current as current
    require(baseline == current.BASELINE, 'OWNER_BASELINE_UNKNOWN')
    return current


def selected(raw, *, baseline=None):
    runtime = policy(baseline)
    require(type(raw) is list and len(raw) == 3, 'CONTAINER_CENSUS')
    result = {}
    for item in raw:
        roles = [role for role in runtime.IMAGES if item['Name'] == f'/fc-control-plane-0-{role}-1']
        require(len(roles) == 1 and item['State']['Running'] is True, 'RUNNING_OWNER_REQUIRED')
        role = roles[0]
        require(role not in result and item['Image'] == runtime.IMAGES[role], 'CONTAINER_IMAGE')
        result[role] = dict(name=item['Name'], id=item['Id'], image=item['Image'], started=item['State']['StartedAt'],
                           environment=item['Config']['Env'], command=item['Config']['Cmd'],
                           entrypoint=item['Config']['Entrypoint'], labels=item['Config']['Labels'],
                           mounts=sorted(item['Mounts'], key=lambda mount: mount['Destination']))
    return result


def inspect(*, baseline=None):
    runtime = policy(baseline)
    process = subprocess.run(['docker', 'inspect', *(f'fc-control-plane-0-{role}-1' for role in runtime.IMAGES)],
                             capture_output=True, timeout=15)
    require(process.returncode == 0 and len(process.stdout) < capture.LIMIT, 'CONTAINER_INSPECT')
    raw = custody.document(process.stdout)
    selected(raw, baseline=baseline)
    return raw


def streamed(container, action):
    modules = {}
    for name in ('control_ha_installed_inventory', 'control_ha_live_sqlite', 'control_ha_owner_capture'):
        modules[name] = Path(__file__).with_name(name + '.py').read_text()
    setup = '''import sys,types,json,base64,resource
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
package=types.ModuleType('scripts');package.__path__=[];sys.modules['scripts']=package
'''
    setup += 'sources=' + repr(modules) + '\n'
    setup += '''try:
    for name,source in sources.items():
        module=types.ModuleType('scripts.'+name);sys.modules[module.__name__]=module
        setattr(package,name,module);exec(compile(source,name+'.py','exec'),module.__dict__)
'''
    setup += '    ' + action + '\n'
    setup += "except Exception:\n    print('OWNER_CAPTURE_REFUSED',file=sys.stderr);sys.exit(1)\n"
    process = subprocess.run(['docker', 'exec', '-i', container, 'python', '-I', '-B', '-'],
                             input=setup.encode(), capture_output=True, timeout=10)
    require(process.returncode == 0 and len(process.stdout) <= 3 * capture.LIMIT, 'OWNER_CAPTURE_REFUSED')
    return custody.document(process.stdout)


def collect(expected, *, baseline=None, extra_reader=None):
    runtime = policy(baseline)
    require((baseline is None and extra_reader is None) or (baseline is not None and callable(extra_reader)),
            'OWNER_EXTRA_READER')
    started = time.time_ns()
    extra = {} if extra_reader is None else extra_reader()
    require(type(extra) is dict and set(extra) == runtime.FILES - custody.FILES and
            all(type(raw) is bytes for raw in extra.values()), 'OWNER_EXTRA_COVERAGE')
    before = inspect() if baseline is None else inspect(baseline=baseline)
    containers = selected(before, baseline=baseline)
    require(containers == selected(expected, baseline=baseline), 'OWNER_CHANGED_SINCE_PREFLIGHT')
    paths = set()
    for item in containers.values():
        paths.update(item['labels']['com.docker.compose.project.config_files'].split(','))
    require(paths == COMPOSE, 'COMPOSE_SCOPE_CHANGED')
    paths = {f'compose-{number}.config': Path(name) for number, name in enumerate(sorted(paths))}
    paths.update({'env-original': ORIGINAL / '.env', 'env-runtime': RUNTIME / '.env',
                  'publisher.token': TOKEN, 'collector-aliases.json': RUNTIME / '.local/pseudonym-aliases.json'})
    for name in ('subscriptions-source.json', 'technical-metadata-source.json', 'transport-source.json', 'inventory-hmac.key'):
        paths[name] = RUNTIME / '.local' / name
    resolved = {name: path.resolve(strict=True) for name, path in paths.items()}
    reader = Reader()
    files = {name: reader.raw(path) for name, path in resolved.items()}
    mounted = streamed(containers['system_publisher']['id'],
        "print(json.dumps(base64.b64encode(package.control_ha_installed_inventory.Reader().raw("
        "package.control_ha_installed_inventory.Path('/run/secrets/system-publisher.token'))).decode()))")
    require(base64.b64decode(mounted, validate=True) == files['publisher.token'], 'PUBLISHER_MOUNT_CHANGED')
    snapshot = streamed(containers['console']['id'], 'print(json.dumps(package.control_ha_owner_capture.capture()))')
    reader.verify()
    require(resolved == {name: path.resolve(strict=True) for name, path in paths.items()}, 'INPUT_PATH_CHANGED')
    after = inspect() if baseline is None else inspect(baseline=baseline)
    require(containers == selected(after, baseline=baseline), 'OWNER_RUNTIME_CHANGED')
    state = lambda rows: {item['Id']: (item['State']['Pid'], item['State']['StartedAt'], item['RestartCount']) for item in rows}
    require(state(before) == state(after), 'OWNER_RESTARTED')
    files['containers.json'] = capture.encoded(containers)
    origins = {name: str(paths[name]) + ' => ' + str(path) for name, path in resolved.items()}
    origins.update({'synthetic.sqlite': containers['console']['id'] + ':' + str(capture.ROOT / 'registry.sqlite3'),
                    'panel-aliases.json': containers['console']['id'] + ':' + str(capture.ALIASES),
                    'containers.json': 'docker-inspect:three-fixed-owner-containers'})
    require(extra_reader is None or extra_reader() == extra, 'OWNER_EXTRA_CHANGED')
    files.update(extra)
    origins.update({name: 'explicit-custody-reader:' + name for name in extra})
    files['origins.json'] = capture.encoded(origins)
    return runtime.build(snapshot, files, started, time.time_ns())
