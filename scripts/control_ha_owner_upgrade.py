"""Source-only OWNER image overlay; no container creation or production activation."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile

from scripts import control_ha_owner_source_binding as source

require = source.require
ROLES = dict(zip(('console', 'system_publisher'), source.IMAGES.values()))
USERS = {'console': 'console', 'system_publisher': '1000:1000'}
CONSOLE = ('python manage.py migrate --noinput && python manage.py collectstatic --noinput && '
           'exec gunicorn fc_control_plane.wsgi:application --bind 0.0.0.0:8000 --workers 2 '
           '--timeout 30 --access-logfile - --access-logformat "%(m)s %(U)s %(s)s %(D)s"')
PUBLISHER = ('while :; do python manage.py publish_system_messages --origin {origin} '
             '--token-file /run/secrets/system-publisher.token --limit 1 '
             '&& date +%s > /tmp/publisher-cycle; sleep 10; done')


def tokens(command):
    parser = shlex.shlex(command, posix=True, punctuation_chars=True)
    parser.whitespace_split = True
    parser.commenters = ''
    return list(parser)


def workload(item, role):
    require(role in ROLES, 'OWNER_ROLE')
    name = f'fc-control-plane-0-{role}-1'
    binding = source.preflight.binding(item, name)
    config = item['Config']
    require(item['Image'] == ROLES[role] and not binding['gate_configured'] and
            binding['readonly_rootfs'] and config['User'] == USERS[role] and
            config['WorkingDir'] == '/app/control_plane' and not config['Entrypoint'], 'OWNER_BASELINE')
    command = config['Cmd']
    require(type(command) is list and len(command) == 3 and command[:2] == ['sh', '-ec'] and
            type(command[2]) is str and len(command[2]) <= 4096, 'OWNER_COMMAND')
    parsed = tokens(command[2])
    expected = CONSOLE
    if role == 'system_publisher':
        require(parsed.count('--origin') == 1 and parsed.index('--origin') + 1 < len(parsed), 'PUBLISHER_ORIGIN')
        origin = parsed[parsed.index('--origin') + 1]
        require(origin == '$FC_SYSTEM_PUBLISHER_ORIGIN' or
                re.fullmatch(r'https://[a-z0-9]+(?:[.-][a-z0-9]+)*', origin), 'PUBLISHER_ORIGIN')
        expected = PUBLISHER.format(origin=origin)
    require(parsed == tokens(expected), 'UNREVIEWED_STARTUP_COMMAND')
    return binding


def context(role, root=source.ROOT):
    require(role in ROLES, 'OWNER_ROLE')
    root = Path(root)
    require(root.is_absolute(), 'SOURCE_ROOT')
    payload = {'Dockerfile': (f'FROM {ROLES[role]}\nCOPY --chown=0:0 app/ /app/\n').encode()}
    records = {}
    for name in source.SOURCES:
        candidate = root / name
        require(all(not parent.is_symlink() for parent in (candidate, *candidate.parents)) and
                candidate.is_file(), 'SOURCE_PATH')
        with candidate.open('rb') as stream:
            raw = stream.read(source.FILE_LIMIT + 1)
        records[name] = source.source_record(raw)
        payload['app/' + name] = raw
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, raw in sorted(payload.items()):
            info = tarfile.TarInfo(name)
            info.mode, info.size = 0o644, len(raw)
            archive.addfile(info, io.BytesIO(raw))
    return output.getvalue(), records


def docker(*arguments, data=None, timeout=180):
    environment = {name: value for name, value in os.environ.items() if not name.startswith('DOCKER_')}
    result = subprocess.run(['docker', '--host', 'unix:///var/run/docker.sock', *arguments],
                            input=data, capture_output=True, env=environment, timeout=timeout)
    require(result.returncode == 0, 'OWNER_IMAGE_COMMAND_FAILED')
    return result.stdout


def image(image_id):
    require(re.fullmatch(r'sha256:[0-9a-f]{64}', image_id), 'IMAGE_ID')
    result = json.loads(docker('image', 'inspect', image_id))
    require(len(result) == 1 and result[0]['Id'] == image_id, 'IMAGE_INSPECT')
    return result[0]


def verify(base, candidate):
    require(base['Id'] in ROLES.values() and candidate['Id'] != base['Id'], 'IMAGE_BASELINE')
    require(base['Config'] == candidate['Config'], 'IMAGE_RUNTIME_CHANGED')
    require(all(base.get(field) == candidate.get(field) for field in ('Os', 'Architecture', 'Variant')),
            'IMAGE_PLATFORM_CHANGED')
    layers = base['RootFS']['Layers']
    require(base['RootFS']['Type'] == candidate['RootFS']['Type'] == 'layers' and
            candidate['RootFS']['Layers'][:-1] == layers and
            len(candidate['RootFS']['Layers']) == len(layers) + 1, 'IMAGE_LAYERS_CHANGED')


def build(role, root=source.ROOT):
    require(role in ROLES, 'OWNER_ROLE')
    archive, records = context(role, root)
    baseline = image(ROLES[role])
    result = docker('build', '--pull=false', '--network=none', '--quiet', '-', data=archive).decode().strip()
    candidate = image(result)
    verify(baseline, candidate)
    return dict(role=role, baseline_image=baseline['Id'], candidate_image=candidate['Id'],
                context_sha256=hashlib.sha256(archive).hexdigest(), sources=records,
                runtime_config_sha256=source.preflight.digest(baseline['Config']),
                rollback_image=baseline['Id'], independent_approval=False, deployed=False)
