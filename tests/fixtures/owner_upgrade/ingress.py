"""Isolated Gunicorn TCP lease qualification with no product data or credentials."""
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import uuid

from scripts import control_ha_ingress as ingress
from scripts.control_ha_owner_upgrade import ROLES

APP = '''import time
def application(environ, start_response):
    start_response('200 OK', [('Content-Type','text/plain')])
    yield b'start'
    if environ['PATH_INFO'] == '/slow':
        time.sleep(1.5)
    yield b'finish'
'''


def request(port, path='/'):
    client = http.client.HTTPConnection('127.0.0.1', port, timeout=3)
    try:
        client.request('GET', path)
        return client, client.getresponse()
    except BaseException:
        client.close()
        raise


def unavailable(port):
    try:
        client, response = request(port)
    except (OSError, http.client.HTTPException):
        return True
    response.read()
    client.close()
    return False


def run(root, image):
    root = Path(root)
    root.mkdir(mode=0o700)
    app = root / 'fixture.py'
    app.write_text(APP)
    app.chmod(0o644)
    token = uuid.uuid4().hex
    label = 'family-connect.ha-ingress-fixture'
    name = 'fc-ha-ingress-fixture-' + token
    network = ingress.docker('network', 'create', '--label', label + '=' + token, name).decode().strip()
    container = None
    transports = []
    started_at_ns = time.time_ns()
    try:
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        container = ingress.docker('create', '--pull=never', '--name', name, '--label', label + '=' + token,
            '--network', network, '--publish', f'127.0.0.1:{port}:8000', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--user', 'console', '--memory', '256m', '--pids-limit', '32',
            '--tmpfs', '/tmp:rw,nosuid,size=16m', '--mount', 'type=bind,source=' + str(app) + ',target=/tmp/fixture.py,readonly',
            ROLES['console'], 'gunicorn', '--chdir', '/tmp', '--bind', '0.0.0.0:8000', '--workers', '2',
            '--timeout', '30', 'fixture:application').decode().strip()
        ingress.docker('start', container)
        deadline = time.monotonic() + 10
        while unavailable(port):
            ingress.require(time.monotonic() < deadline, 'LAB_START_TIMEOUT')
            time.sleep(0.05)
        journal = root / 'normal'
        journal.mkdir(mode=0o700)
        transport = ingress.Transport(container, image, journal)
        transports.append(transport)
        client, response = request(port, '/slow')
        ingress.require(response.read(5) == b'start', 'LAB_INFLIGHT_NOT_STARTED')
        with ingress.Lease(transport) as lease:
            ingress.require(unavailable(port), 'NEW_CONNECTION_ADMITTED')
            ingress.require(response.read() == b'finish', 'INFLIGHT_RESPONSE_INTERRUPTED')
            client.close()
            observed = lease.check()
            ingress.require(observed['rejected_packets'] > 0, 'NO_REJECT_COUNTER')
        ingress.require(not unavailable(port), 'EARLY_RELEASE_FAILED')
        journal = root / 'controller-death'
        journal.mkdir(mode=0o700)
        code = '''import sys,json,time
from pathlib import Path
from scripts.control_ha_ingress import Transport,Lease
with Lease(Transport(sys.argv[1],sys.argv[2],Path(sys.argv[3])), seconds=3) as lease:
    print(json.dumps({'token':lease.token}),flush=True)
    time.sleep(20)
'''
        controller = subprocess.Popen([sys.executable, '-c', code, container, image, str(journal)],
                                      cwd=Path(__file__).resolve().parents[3], stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True)
        try:
            import select
            ingress.require(bool(select.select([controller.stdout], [], [], 8)[0]), 'CONTROLLER_START_TIMEOUT')
            line = controller.stdout.readline()
            if not line:
                raise ValueError('CONTROLLER_FAILED_' + controller.stderr.read()[:1200])
            ownership = json.loads(line)
            controller.kill()
            controller.wait(timeout=5)
            ingress.require(controller.returncode == -signal.SIGKILL, 'CONTROLLER_NOT_KILLED')
            initially_closed = unavailable(port)
            ingress.require(initially_closed, 'CONTROLLER_DEATH_CASE_NOT_CLOSED')
            deadline = time.monotonic() + 5
            while unavailable(port):
                ingress.require(time.monotonic() < deadline, 'KERNEL_LEASE_DID_NOT_EXPIRE')
                time.sleep(0.05)
            transport = ingress.Transport(container, image, journal)
            transports.append(transport)
            for path in journal.glob('helper-*.json'):
                transport.helpers.append(json.loads(path.read_text())['id'])
            expired = ingress.Lease(transport, seconds=3, token=ownership['token'])
            readback = expired.observe()
            ingress.require(readback['remaining_seconds'] == 0, 'EXPIRED_ELEMENT_RETAINED')
            expired.release()
        finally:
            if controller.poll() is None:
                controller.kill()
                controller.wait(timeout=5)
            controller.stdout.close()
            controller.stderr.close()
        journal = root / 'collision-owner'
        journal.mkdir(mode=0o700)
        owner = ingress.Transport(container, image, journal)
        transports.append(owner)
        collision_token = uuid.uuid4().hex
        owner.run(ingress.create_request(collision_token, 1))
        time.sleep(1.2)
        listing = {'nftables': [{'list': {'table': dict(family='inet', name=ingress.table_name(collision_token))}}]}
        before = owner.run(listing)
        journal = root / 'collision-refusal'
        journal.mkdir(mode=0o700)
        collider = ingress.Transport(container, image, journal)
        transports.append(collider)
        try:
            collider.run(ingress.create_request(collision_token, 5))
        except ValueError:
            ingress.require(collider.unconfirmed and bool(collider.helpers), 'COLLISION_NOT_ATTEMPTED')
            collider.finished()
            ingress.require(collider.api.inspect(collider.helpers[-1])['State']['ExitCode'] != 0, 'COLLISION_NOT_REJECTED')
        else:
            raise ValueError('EXISTING_TABLE_REUSED')
        ingress.require(owner.run(listing) == before, 'COLLISION_CHANGED_EXISTING_TABLE')
        ingress.Lease(owner, token=collision_token, seconds=1).release()
        collider.cleanup_helpers()
        journal = root / 'lost-helper-response'
        journal.mkdir(mode=0o700)
        transport = ingress.Transport(container, image, journal)
        transports.append(transport)
        unknown = ingress.Lease(transport, seconds=3)
        real_docker = ingress.docker
        def lost_response(*args, **kwargs):
            result = real_docker(*args, **kwargs)
            if args[0] == 'start':
                raise TimeoutError('synthetic lost helper response after actual commit')
            return result
        ingress.docker = lost_response
        try:
            try:
                unknown.__enter__()
            except TimeoutError:
                ingress.require(transport.unconfirmed, 'UNKNOWN_RESPONSE_NOT_RETAINED')
            else:
                raise ValueError('LOST_RESPONSE_NOT_INJECTED')
        finally:
            ingress.docker = real_docker
        ingress.require(unavailable(port), 'UNKNOWN_COMMIT_NOT_ACTIVE')
        try:
            unknown.release()
        except ValueError as error:
            ingress.require(str(error) == 'INGRESS_OPERATION_UNCONFIRMED', 'UNEXPECTED_RELEASE_REFUSAL')
        else:
            raise ValueError('UNKNOWN_OPERATION_RELEASED')
        deadline = time.monotonic() + 5
        while unavailable(port):
            ingress.require(time.monotonic() < deadline, 'UNKNOWN_COMMIT_DID_NOT_EXPIRE')
            time.sleep(0.05)
        journal = root / 'lost-helper-readback'
        journal.mkdir(mode=0o700)
        reconciled = ingress.Transport(container, image, journal)
        reconciled.helpers = list(transport.helpers)
        transports.append(reconciled)
        ingress.Lease(reconciled, token=unknown.token, seconds=3).release()
        transport.helpers.clear()
        receipt = dict(started_at_ns=started_at_ns, finished_at_ns=time.time_ns(), helper_image=image,
                       early_release=True, inflight_response_completed=True, rejected_packets=observed['rejected_packets'],
                       controller_sigkill=True, closed_after_controller_death=initially_closed, kernel_expiry=True,
                       collision_preserved=True, lost_helper_response_expired=True, unknown_release_refused=True,
                       work_settlement_proven=False, capture_permitted=False)
        ingress.record(root, 'receipt', receipt)
        return receipt
    finally:
        for transport in transports:
            try:
                transport.cleanup_helpers()
            except (OSError, ValueError):
                pass
        if container:
            identifiers = ingress.docker('ps', '--all', '--quiet', '--no-trunc', '--filter',
                                          'label=' + ingress.LABEL + '=' + container).decode().split()
            for identifier in identifiers:
                item = ingress.Docker().inspect(identifier)
                ingress.require(item['Config']['Labels'].get(ingress.LABEL) == container and item['Image'] == image and
                                not item['State']['Running'], 'LAB_HELPER_CLEANUP_SCOPE')
                ingress.Docker().remove(identifier)
            item = ingress.Docker().inspect(container)
            ingress.require(item['Config']['Labels'].get(label) == token, 'LAB_CLEANUP_SCOPE')
            ingress.docker('rm', '--force', container)
        ingress.docker('network', 'rm', network)


if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1], sys.argv[2]), sort_keys=True))
