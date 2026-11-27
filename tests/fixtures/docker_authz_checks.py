"""Native disposable Engine checks. Requires an explicitly isolated Engine and AuthZ service."""
import argparse
import io
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import tarfile
import time


class API:
    def __init__(self, socket_path):
        self.path = str(socket_path)

    def call(self, method, route, value=None, *, raw=None, content_type=None, headers=None):
        connection = http.client.HTTPConnection('localhost', timeout=10)
        channel = socket.socket(socket.AF_UNIX)
        channel.settimeout(10)
        channel.connect(self.path)
        connection.sock = channel
        try:
            payload = raw if raw is not None else json.dumps(value).encode() if value is not None else None
            headers = {'Content-Type': content_type or 'application/json', **(headers or {})}
            connection.request(method, route, payload, headers)
            response = connection.getresponse()
            body = response.read(4 * 1024 * 1024)
            return response.status, body
        finally:
            connection.close()

    def json(self, method, route, value=None, expected=200):
        status, raw = self.call(method, route, value)
        assert status == expected, (method, route, status)
        return json.loads(raw) if raw else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', required=True)
    parser.add_argument('--plugin', required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    assert os.geteuid() == 0
    api, plugin, root = API(args.engine), API(args.plugin), args.root
    info = api.json('GET', '/info')
    assert Path(info['DockerRootDir']) == root / 'engine2-data'
    assert api.json('GET', '/version')['Version'] == '29.1.3'
    source = root / 'protected'
    assert source.is_dir() and root.name.startswith('fc-owner-executor-')
    results = {}
    def create(name, host=None, command=None):
        value = dict(Image='python:3.12-slim-bookworm', Cmd=command or ['sleep', 'infinity'],
                     HostConfig=dict(NetworkMode='none', **(host or {})))
        return api.json('POST', '/containers/create?name=fc-authz-' + name, value, 201)['Id']
    def execute(container, command, detach=True):
        identifier = api.json('POST', f'/containers/{container}/exec',
            dict(Cmd=command, AttachStdout=False, AttachStderr=False), 201)['Id']
        api.json('POST', f'/exec/{identifier}/start', dict(Detach=detach, Tty=False))
        return identifier
    protected = 'fc-authz-protected'
    new_id = create('new-id', dict(Binds=[str(source) + ':/data']))
    paused_id = create('paused', dict(Binds=[str(source) + ':/data']))
    api.json('POST', f'/containers/{paused_id}/start', expected=204)
    api.json('POST', f'/containers/{paused_id}/pause', expected=204)
    api.json('POST', '/volumes/create', dict(Name='fc-authz-store', Driver='local',
        DriverOpts=dict(type='none', o='bind', device=str(source))), 201)
    old_exec = api.json('POST', f'/containers/{protected}/exec',
        dict(Cmd=['sh', '-c', 'echo forbidden >/data/late-exec'], AttachStdout=False), 201)['Id']
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w') as archive:
        member = tarfile.TarInfo('archive-proof')
        member.size = 6
        archive.addfile(member, io.BytesIO(b'before'))
    status, unused = api.call('PUT', f'/containers/{protected}/archive?path=/data',
                             raw=raw.getvalue(), content_type='application/x-tar')
    assert status == 200 and (source / 'archive-proof').read_bytes() == b'before'
    results['archive_api_can_write_protected_mount'] = True
    child = execute(protected, ['python', '-c',
        'import os,time,mmap\nfd=os.open("/data/old-fd",os.O_RDWR|os.O_CREAT,0o600)\n'
        'os.ftruncate(fd,4096)\nview=mmap.mmap(fd,4096)\nview[0:1]=b"a"\n'
        'pid=os.fork()\nif pid: os._exit(0)\nos.setsid()\n'
        'open("/data/child-ready","w").close()\n'
        'while not os.path.exists("/data/go"):\n time.sleep(.02)\n'
        'os.write(fd,b"late-fd")\nview[20:24]=b"late"\nview.flush()\n'
        'open("/data/temporary","w").write("late-rename")\n'
        'os.rename("/data/temporary","/data/renamed")\nopen("/data/child-done","w").close()'])
    deadline = time.monotonic() + 5
    while not (source / 'child-ready').exists() and time.monotonic() < deadline:
        time.sleep(.02)
    assert (source / 'child-ready').exists()
    assert not api.json('GET', f'/exec/{child}/json')['Running']
    auto = create('auto', dict(Binds=[str(source) + ':/data'], RestartPolicy=dict(Name='always')),
        ['python', '-c', 'import time; open("/data/auto-count","a").write("start\\n"); time.sleep(300)'])
    api.json('POST', f'/containers/{auto}/start', expected=204)
    time.sleep(.3)
    previous_pid = api.json('GET', f'/containers/{auto}/json')['State']['Pid']
    status = plugin.json('POST', '/fc-control', dict(command='CLOSE'))
    assert status['pending'] == 0 and not status['process_containment']
    calls = [
        ('exec-create', 'POST', f'/containers/{protected}/exec', dict(Cmd=['true'])),
        ('old-exec-start', 'POST', f'/exec/{old_exec}/start', dict(Detach=True, Tty=False)),
        ('new-id-start', 'POST', f'/containers/{new_id}/start', None),
        ('restart', 'POST', f'/containers/{protected}/restart', None),
        ('unpause', 'POST', f'/containers/{paused_id}/unpause', None),
        ('restart-policy', 'POST', f'/containers/{protected}/update', dict(RestartPolicy=dict(Name='always'))),
    ]
    variants = [dict(Binds=[str(source) + ':/data']),
        dict(Mounts=[dict(Type='bind', Source=str(source), Target='/data')]),
        dict(Binds=['fc-authz-store:/data']),
        dict(Mounts=[dict(Type='volume', Source='fc-authz-store', Target='/data')]),
        dict(VolumesFrom=[protected]), dict(Binds=[str(source.parent) + ':/parent'])]
    for index, host in enumerate(variants):
        calls.append((f'new-resource-{index}', 'POST', '/containers/create',
                      dict(Image='python:3.12-slim-bookworm', Cmd=['true'], HostConfig=host)))
    for name, method, route, value in calls:
        code, unused = api.call(method, route, value)
        assert code == 403, (name, code)
        results[name] = 'DENIED'
    code, unused = api.call('PUT', f'/containers/{protected}/archive?path=/data',
                           raw=raw.getvalue(), content_type='application/x-tar')
    assert code == 403
    results['archive-closed'] = 'DENIED'
    execute('fc-authz-neighbor', ['sh', '-c', 'echo normal >>/data/held-neighbor'])
    deadline = time.monotonic() + 3
    while not (root / 'neighbor/held-neighbor').exists() and time.monotonic() < deadline:
        time.sleep(.02)
    assert (root / 'neighbor/held-neighbor').exists()
    results['neighbor_exec_with_live_policy'] = 'PASS'
    (source / 'go').touch()
    deadline = time.monotonic() + 3
    while not (source / 'child-done').exists() and time.monotonic() < deadline:
        time.sleep(.02)
    assert (source / 'old-fd').read_bytes().startswith(b'late-fd')
    assert (source / 'old-fd').read_bytes()[20:24] == b'late'
    assert (source / 'renamed').read_text() == 'late-rename'
    results['old_fd_mmap_detached_child_rename'] = 'NOT_CONTAINED_BY_AUTHZ'
    prior_effect = (source / 'auto-count').read_bytes()
    os.kill(previous_pid, signal.SIGKILL)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        state = api.json('GET', f'/containers/{auto}/json')
        if state['State']['Running'] and state['State']['Pid'] != previous_pid and (source / 'auto-count').read_bytes() != prior_effect:
            break
        time.sleep(.05)
    assert state['State']['Running'] and state['State']['Pid'] != previous_pid
    assert (source / 'auto-count').read_bytes() != prior_effect
    results['automatic_restart'] = 'BYPASSES_AUTHZ'
    assert plugin.json('POST', '/fc-control', dict(command='CHECK'))['pending'] == 0
    results.update(engine_version='29.1.3', common_kit=False, process_containment=False)
    output = root / 'authz-native.json'
    with output.open('x') as stream:
        json.dump(results, stream, sort_keys=True)
    print(json.dumps(results, sort_keys=True))


if __name__ == '__main__':
    main()
