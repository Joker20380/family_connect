"""Bounded replacement-controller and ordinary domain cycle in the already enrolled guest."""
import argparse
import json
import os
from pathlib import Path
import signal
import stat
import time

from docker_cold_guest import API, IMAGE, PARENT, ROOT, Transition, boot, digest, publish, safe
from control.capture_docker_domain import DomainClient, ExecutorBoundary
from control.capture_domain import LaunchLock


def run(action):
    safe()
    root = Path(json.loads((ROOT / 'current.json').read_bytes())['root'])
    api = API('/run/fc-new.sock')
    if action == 'cycle':
        api.json('POST', '/containers/enrolled/stop?t=1', expected=204)
        spec = dict(Image=IMAGE, Cmd=['python', '-c',
            'import signal,time,sys; signal.signal(signal.SIGTERM,lambda *args:sys.exit(0)); '
            'open("/data/normal-starts","a").write("start\\n"); time.sleep(300)'],
            HostConfig=dict(NetworkMode='none', Binds=[str(ROOT / 'protected') + ':/data'],
                            CgroupParent=PARENT, RestartPolicy=dict(Name='no')))
        identifier = api.json('POST', '/containers/create?name=normal-cycle', spec, 201)['Id']
        api.json('POST', '/containers/' + identifier + '/start', expected=204)
        lock = root / 'ordinary-cycle.lock'
        lock.touch(mode=0o600, exist_ok=False)
        pin = lock.stat()
        client = DomainClient(Transition(root).plan['plugin_socket'], PARENT)
        with LaunchLock(lock, [pin.st_dev, pin.st_ino, pin.st_uid, stat.S_IMODE(pin.st_mode)]) as launch:
            boundary = ExecutorBoundary(client, launch, Path('/sys/fs/cgroup') / PARENT, root / 'ordinary-cycle')
            boundary.acquire()
            try:
                lease = boundary.check()
                state = api.json('GET', '/containers/' + identifier + '/json')['State']
                assert not state['Running'] and state['ExitCode'] == 0
                before = {path.name: digest(path) for path in (ROOT / 'protected').iterdir() if path.is_file()}
                assert api.call('POST', '/containers/' + identifier + '/start')[0] == 403
                time.sleep(.3)
                assert before == {path.name: digest(path) for path in (ROOT / 'protected').iterdir() if path.is_file()}
                assert boundary.check() == lease
            finally:
                released = boundary.release()
                assert boundary.release() == released
        api.json('POST', '/containers/' + identifier + '/start', expected=204)
        assert api.json('GET', '/containers/' + identifier + '/json')['State']['Running']
        publish(root / 'ordinary-cycle-result.json', dict(boot=boot(), operation=Transition(root).plan['operation'],
            same_boot=True, new_capture_lease=lease, normal_resume=True, application_recovery=False))
        return
    name = 'crash' if action.startswith('crash') else 'lost-response'
    container = 'cold-' + name
    spec = dict(Image=IMAGE, Cmd=['sleep', 'infinity'], Labels={'fc-cold-operation': root.name},
        HostConfig=dict(NetworkMode='none', Binds=[str(ROOT / 'protected') + ':/data'],
                        CgroupParent=PARENT, RestartPolicy=dict(Name='no')))
    def observe():
        status, raw = api.call('GET', '/containers/' + container + '/json')
        if status == 404:
            return None
        assert status == 200
        value = json.loads(raw)
        assert value['Config']['Labels'] == spec['Labels'] and value['HostConfig']['CgroupParent'] == PARENT
        assert value['Config']['Image'] == IMAGE and value['HostConfig']['Binds'] == spec['HostConfig']['Binds']
        assert value['HostConfig']['RestartPolicy']['Name'] == 'no'
        return dict(id=value['Id'], image=value['Image'], labels=value['Config']['Labels'], parent=PARENT)
    def effect():
        api.json('POST', '/containers/create?name=' + container, spec, 201)
        if action == 'crash':
            os.kill(os.getpid(), signal.SIGKILL)
        if action == 'lost-response':
            raise TimeoutError('SYNTHETIC_RESPONSE_LOST_AFTER_CREATE')
        raise AssertionError('RECONCILIATION_MUST_NOT_REPLAY')
    with Transition(root) as transition:
        result = transition.step(name, observe, effect)
        assert transition.step(name, observe, effect) == result
        print(json.dumps(dict(operation=transition.plan['operation'], result=result, capture_lease=None)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['crash', 'crash-reconcile', 'lost-response', 'lost-response-reconcile', 'cycle'])
    run(parser.parse_args().action)
