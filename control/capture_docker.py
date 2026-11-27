"""Resource-scoped Docker AuthZ admission; not a process or native-file barrier."""
import argparse
import base64
import ctypes
import hashlib
import http.client
import http.server
import json
import os
from pathlib import Path
import re
import socket
import socketserver
import struct
import threading
from urllib.parse import unquote, urlsplit

from control.capture_native import record, require


class Engine:
    def __init__(self, path):
        self.path = str(path)

    def get(self, route):
        connection = http.client.HTTPConnection('localhost', timeout=3)
        channel = socket.socket(socket.AF_UNIX)
        channel.settimeout(3)
        try:
            channel.connect(self.path)
            connection.sock = channel
            connection.request('GET', route)
            response = connection.getresponse()
            raw = response.read(4 * 1024 * 1024 + 1)
            require(response.status == 200 and len(raw) <= 4 * 1024 * 1024, 'DOCKER_INSPECT_REFUSED')
            return json.loads(raw)
        finally:
            connection.close()
            channel.close()


def physical(path):
    path = Path(path).resolve()
    existing = path
    while not existing.exists():
        require(existing.parent != existing, 'DOCKER_RESOURCE_PATH_UNKNOWN')
        existing = existing.parent
    buffer = ctypes.create_string_buffer(256)
    result = ctypes.CDLL(None, use_errno=True).statx(-100, os.fsencode(existing), 0x800, 0x1000, buffer)
    require(result == 0 and struct.unpack_from('I', buffer.raw)[0] & 0x1000, 'DOCKER_MOUNT_ID_REQUIRED')
    mounted = struct.unpack_from('Q', buffer.raw, 144)[0]
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        fields = line.split()
        if int(fields[0]) != mounted:
            continue
        decode = lambda value: re.sub(r'\\([0-7]{3})', lambda found: chr(int(found[1], 8)), value)
        point = Path(decode(fields[4]))
        require(path == point or point in path.parents, 'DOCKER_RESOURCE_MOUNT_CHANGED')
        return fields[2], Path(decode(fields[3])) / path.relative_to(point)
    raise ValueError('DOCKER_RESOURCE_MOUNT_UNKNOWN')


class Scope:
    def __init__(self, engine, paths):
        require(0 < len(paths) <= 16, 'DOCKER_SCOPE_SIZE')
        self.engine, self.paths = engine, [Path(path) for path in paths]
        require(all(path.is_absolute() and path != Path('/') and path.exists() for path in self.paths),
                'DOCKER_SCOPE_PATH')
        self.pins = [physical(path) for path in self.paths]

    def overlaps(self, value):
        require(isinstance(value, str) and value.startswith('/'), 'DOCKER_RESOURCE_PATH')
        require([physical(path) for path in self.paths] == self.pins, 'DOCKER_SCOPE_CHANGED')
        device, path = physical(value)
        return any(device == expected_device and (path == expected or path in expected.parents or
            expected in path.parents) for expected_device, expected in self.pins)

    def volume(self, name):
        value = self.engine.get('/volumes/' + name)
        require(value['Driver'] == 'local', 'DOCKER_VOLUME_DRIVER_UNKNOWN')
        options = value.get('Options') or {}
        if options:
            require(options.get('type') == 'none' and options.get('o') in ('bind', 'bind,rw', 'bind,ro'),
                    'DOCKER_VOLUME_OPTIONS_UNKNOWN')
            return self.overlaps(options['device'])
        return self.overlaps(value['Mountpoint'])

    def container(self, identifier):
        value = self.engine.get('/containers/' + identifier + '/json')
        config = value['HostConfig']
        require(not config.get('Privileged') and config.get('PidMode') != 'host' and
                not config.get('Devices') and not config.get('CapAdd'), 'DOCKER_DOMAIN_PRIVILEGE_UNKNOWN')
        for mount in value['Mounts']:
            require(mount['Type'] in ('bind', 'volume', 'tmpfs'), 'DOCKER_MOUNT_TYPE_UNKNOWN')
            if mount['Type'] != 'tmpfs' and self.overlaps(mount['Source']):
                return True
        return False

    def create(self, value):
        host = value.get('HostConfig') or {}
        require(not host.get('Privileged') and host.get('PidMode') != 'host' and not host.get('Devices') and
                not host.get('CapAdd') and not host.get('DeviceRequests'), 'DOCKER_CREATE_PRIVILEGE_UNKNOWN')
        for entry in host.get('VolumesFrom') or []:
            if self.container(entry.split(':', 1)[0]):
                return True
        for entry in host.get('Binds') or []:
            parts = entry.split(':')
            require(len(parts) in (2, 3), 'DOCKER_BIND_FORM')
            if self.overlaps(parts[0]) if parts[0].startswith('/') else self.volume(parts[0]):
                return True
        for mount in host.get('Mounts') or []:
            kind, source = mount['Type'], mount.get('Source', '')
            require(kind in ('bind', 'volume', 'tmpfs'), 'DOCKER_MOUNT_TYPE_UNKNOWN')
            require(not mount.get('VolumeOptions', {}).get('DriverConfig'), 'DOCKER_INLINE_VOLUME_DRIVER_UNKNOWN')
            if kind == 'bind' and self.overlaps(source) or kind == 'volume' and source and self.volume(source):
                return True
        return False


def route(request):
    path = unquote(urlsplit(request['RequestURI']).path)
    require('..' not in path.split('/') and '//' not in path, 'DOCKER_ROUTE_FORM')
    return re.sub(r'^/v[0-9]+\.[0-9]+(?=/)', '', path)


def request_key(request):
    value = {name: request.get(name) for name in ('RequestMethod', 'RequestURI', 'RequestBody', 'RequestHeaders')}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class Admission:
    def __init__(self, engine, paths, pidfile, journal, *, config=None, plugin=None):
        self.scope, self.pidfile, self.journal = Scope(engine, paths), Path(pidfile), Path(journal)
        self.journal.mkdir(mode=0o700, exist_ok=False)
        self.generation = self.daemon()
        self.lock = threading.RLock()
        self.phase, self.pending, self.serial = 'OPEN', {}, 0
        self.config = Path(config) if config is not None else None
        self.plugin, self.watch, self.released = plugin, None, None
        self.lease = os.urandom(32).hex()
        record(self.journal, 'started', dict(generation=self.generation, resource_admission_only=True))

    def daemon(self):
        pid = int(self.pidfile.read_text())
        return dict(pid=pid, start=Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19],
            boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            namespace=os.stat(f'/proc/{pid}/ns/mnt').st_ino)

    def changed(self):
        try:
            require(self.daemon() == self.generation, 'DOCKER_DAEMON_GENERATION_CHANGED')
            require(self.phase != 'FAILED', 'DOCKER_ADMISSION_FAILED')
            require([physical(path) for path in self.scope.paths] == self.scope.pins, 'DOCKER_SCOPE_CHANGED')
            if self.watch is not None:
                try:
                    event = os.read(self.watch, 65536)
                except BlockingIOError:
                    event = b''
                require(not event and self.config_pin() == self.config_identity, 'DOCKER_HOOK_CONFIGURATION_CHANGED')
        except Exception as error:
            self.fail(error)
            raise

    def fail(self, error):
        self.phase = 'FAILED'
        if not (self.journal / 'failed').exists():
            reason = str(error) if re.fullmatch(r'DOCKER_[A-Z_]+', str(error)) else 'DOCKER_CHECK_REFUSED'
            try:
                record(self.journal, 'failed', dict(reason=reason, lease=self.lease, release_confirmed=False))
            except OSError:
                pass

    def config_pin(self):
        info = self.config.stat()
        require(not self.config.is_symlink() and info.st_nlink == 1 and not info.st_mode & 0o022,
                'DOCKER_HOOK_CONFIGURATION_FILE')
        raw = self.config.read_bytes()
        require(self.plugin in json.loads(raw).get('authorization-plugins', []), 'DOCKER_HOOK_NOT_CONFIGURED')
        return [info.st_dev, info.st_ino, hashlib.sha256(raw).hexdigest()]

    def watch_configuration(self):
        require(self.config is not None and self.plugin, 'DOCKER_HOOK_CONFIGURATION_REQUIRED')
        library = ctypes.CDLL(None, use_errno=True)
        self.watch = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        require(self.watch >= 0 and library.inotify_add_watch(self.watch,
                os.fsencode(self.config), 0x00000002 | 0x00000004 | 0x00000008 | 0x00000400 | 0x00000800) >= 0,
                'DOCKER_HOOK_WATCH_REQUIRED')
        self.config_identity = self.config_pin()

    def selected(self, request):
        method, path = request['RequestMethod'], route(request)
        if method in ('GET', 'HEAD') and not path.endswith('/attach/ws'):
            return False
        if path == '/containers/create':
            return self.scope.create(json.loads(base64.b64decode(request.get('RequestBody') or '', validate=True)))
        found = re.fullmatch(r'/containers/([^/]+)(?:/(.*))?', path)
        if found:
            return self.scope.container(found[1])
        found = re.fullmatch(r'/exec/([^/]+)/.*', path)
        if found:
            value = self.scope.engine.get('/exec/' + found[1] + '/json')
            return self.scope.container(value['ContainerID'])
        if path == '/volumes/create':
            return True
        found = re.fullmatch(r'/volumes/([^/]+)', path)
        if found:
            return self.scope.volume(found[1])
        require(path.startswith('/images/') or path in ('/commit',), 'DOCKER_MUTATION_UNCLASSIFIED')
        return path == '/commit'

    def request(self, request):
        if request['RequestMethod'] in ('GET', 'HEAD') and not route(request).endswith('/attach/ws'):
            return dict(Allow=True, Msg='', Err='')
        with self.lock:
            try:
                self.changed()
                selected = self.selected(request)
                if selected and self.phase not in ('OPEN', 'RELEASED'):
                    return dict(Allow=False, Msg='FC_RESOURCE_ADMISSION_CLOSED', Err='')
                if selected:
                    identity = request_key(request)
                    self.pending[identity] = self.pending.get(identity, 0) + 1
                    self.serial += 1
                    record(self.journal, f'permit-{self.serial:08d}', dict(identity=identity))
                return dict(Allow=True, Msg='', Err='')
            except Exception:
                return dict(Allow=False, Msg='FC_RESOURCE_SCOPE_REFUSED', Err='')

    def response(self, request):
        if request['RequestMethod'] in ('GET', 'HEAD') and not route(request).endswith('/attach/ws'):
            return dict(Allow=True, Msg='', Err='')
        with self.lock:
            identity = request_key(request)
            if identity in self.pending:
                self.serial += 1
                record(self.journal, f'response-{self.serial:08d}', dict(identity=identity))
                self.pending[identity] -= 1
                if not self.pending[identity]:
                    del self.pending[identity]
            return dict(Allow=True, Msg='', Err='')

    def control(self, command):
        with self.lock:
            if command == 'RELEASE' and self.released is not None:
                return self.released
            try:
                self.changed()
                if command == 'CLOSE':
                    require(self.phase == 'OPEN', 'DOCKER_CLOSE_REPLAY_REFUSED')
                    self.watch_configuration()
                    record(self.journal, 'closed', dict(lease=self.lease, generation=self.generation))
                    self.phase = 'CLOSED'
                elif command == 'RELEASE':
                    require(self.phase in ('CLOSED', 'RELEASED') and not self.pending, 'DOCKER_RELEASE_UNCERTAIN')
                    if self.phase == 'CLOSED':
                        record(self.journal, 'released', dict(lease=self.lease))
                        self.phase = 'RELEASED'
                        os.close(self.watch)
                        self.watch = None
                else:
                    require(command == 'CHECK', 'DOCKER_CONTROL_COMMAND')
                result = dict(phase=self.phase, lease=self.lease, pending=sum(self.pending.values()),
                    resource_admission_only=True, process_containment=False, fleet_capture=False)
                if command == 'RELEASE':
                    self.released = result
                return result
            except Exception as error:
                self.fail(error)
                raise


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def body(self):
        encoding = self.headers.get('Transfer-Encoding')
        if encoding is None:
            size = int(self.headers.get('Content-Length', '-1'))
            require(0 <= size <= 4 * 1024 * 1024, 'DOCKER_PLUGIN_BODY_SIZE')
            raw = self.rfile.read(size)
            require(len(raw) == size, 'DOCKER_PLUGIN_BODY_INCOMPLETE')
            return raw
        require(encoding.lower() == 'chunked' and self.headers.get('Content-Length') is None,
                'DOCKER_PLUGIN_BODY_ENCODING')
        raw = bytearray()
        while True:
            line = self.rfile.readline(128)
            require(line.endswith(b'\r\n') and len(line) < 128, 'DOCKER_PLUGIN_CHUNK_HEADER')
            size = int(line.split(b';', 1)[0], 16)
            require(0 <= size <= 4 * 1024 * 1024 - len(raw), 'DOCKER_PLUGIN_BODY_SIZE')
            if size == 0:
                require(self.rfile.readline(3) == b'\r\n', 'DOCKER_PLUGIN_TRAILERS_UNSUPPORTED')
                return bytes(raw)
            chunk = self.rfile.read(size)
            require(len(chunk) == size and self.rfile.read(2) == b'\r\n', 'DOCKER_PLUGIN_BODY_INCOMPLETE')
            raw.extend(chunk)

    def do_POST(self):
        try:
            self.connection.settimeout(5)
            if self.path == '/Plugin.Activate':
                result = dict(Implements=['authz'])
            else:
                request = json.loads(self.body())
                if 'RequestUri' in request:
                    require('RequestURI' not in request or request['RequestURI'] == request['RequestUri'],
                            'DOCKER_URI_ALIAS_CONFLICT')
                    request['RequestURI'] = request['RequestUri']
                if self.path == '/AuthZPlugin.AuthZReq':
                    result = self.server.admission.request(request)
                elif self.path == '/AuthZPlugin.AuthZRes':
                    result = self.server.admission.response(request)
                elif self.path == '/fc-control':
                    result = self.server.admission.control(request['command'])
                else:
                    raise ValueError('DOCKER_PLUGIN_ROUTE')
            raw = json.dumps(result, sort_keys=True).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except Exception as error:
            code = str(error) if re.fullmatch(r'DOCKER_[A-Z_]+', str(error)) else type(error).__name__
            if isinstance(error, KeyError) and error.args[0] in ('RequestMethod', 'RequestURI', 'RequestUri'):
                code += ':' + error.args[0]
            print('AUTHZ_PROTOCOL_REFUSED', code, flush=True)
            raw = b'{"Err":"FC_AUTHZ_REFUSED"}'
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)


def main(admission_type=Admission):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--socket', required=True)
    parser.add_argument('--engine', required=True)
    parser.add_argument('--pidfile', required=True)
    parser.add_argument('--journal', required=True)
    parser.add_argument('--daemon-config', required=True)
    parser.add_argument('--protect', action='append', required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0, 'DOCKER_PLUGIN_ROOT_REQUIRED')
    os.umask(0o077)
    admission = admission_type(Engine(args.engine), args.protect, args.pidfile, args.journal,
                               config=args.daemon_config, plugin=Path(args.socket).stem)
    with Server(args.socket, Handler) as server:
        server.admission = admission
        server.serve_forever(poll_interval=0.1)


if __name__ == '__main__':
    main()
