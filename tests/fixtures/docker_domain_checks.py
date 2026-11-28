"""Real disposable container descendants plus the continuous enrolled-domain boundary."""
import argparse
import json
import multiprocessing
import os
from pathlib import Path
import signal
import stat
import time

from control.capture_docker_domain import DomainClient, ExecutorBoundary
from control.capture_domain import LaunchLock, reconcile_domain
from control.capture_native import fingerprint
from docker_authz_checks import API


def wait(test, seconds=5):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if test():
            return
        time.sleep(.02)
    raise AssertionError('DOMAIN_FIXTURE_DEADLINE')


def run(engine, plugin, root, parent):
    source = root / 'protected'
    host = dict(Binds=[str(source) + ':/data'], CgroupParent=parent,
                RestartPolicy=dict(Name='no'), CgroupnsMode='private')
    base = dict(Image='python:3.12-slim-bookworm', HostConfig=host,
        Cmd=['python', '-c', 'import signal,sys,time; signal.signal(signal.SIGTERM,lambda *args:sys.exit(0)); '
             'open("/data/domain-starts","a").write("start\\n"); time.sleep(300)'])
    rejected = {**base, 'HostConfig': {**host, 'CgroupParent': ''}}
    assert engine.call('POST', '/containers/create?name=fc-authz-bypass', rejected)[0] == 403
    container = engine.json('POST', '/containers/create?name=fc-authz-domain', base, 201)['Id']
    engine.json('POST', '/containers/' + container + '/start', expected=204)
    for index in range(206):
        neighbor = engine.json('POST', '/containers/create?name=fc-authz-inventory-' + str(index),
            dict(Image='python:3.12-slim-bookworm', Cmd=['sleep', '300'],
                HostConfig=dict(NetworkMode='none', RestartPolicy=dict(Name='no'))), 201)['Id']
        if index < 16:
            engine.json('POST', '/containers/' + neighbor + '/start', expected=204)
    inventory = engine.json('GET', '/containers/json?all=1')
    assert len(inventory) == 207 and sum(row['State'] == 'running' for row in inventory) == 17
    assert engine.call('POST', '/containers/' + container + '/update',
        dict(RestartPolicy=dict(Name='always')))[0] == 403
    child_code = ('import os,time,mmap,signal\n'
        'fd=os.open("/data/domain-fd",os.O_CREAT|os.O_RDWR,0o600)\nos.ftruncate(fd,4096)\n'
        'view=mmap.mmap(fd,4096)\nview[0:1]=b"a"\n'
        'pid=os.fork()\nif pid: os._exit(0)\nos.setsid()\n'
        'def finish(*args):\n os.write(fd,b"clean"); view[20:24]=b"done"; view.flush(); '
        'open("/data/domain-child-finished","w").close(); os._exit(0)\n'
        'signal.signal(signal.SIGTERM,finish)\n'
        'open("/data/domain-child-ready","w").close()\n'
        'while True:\n time.sleep(.03)\n')
    child = engine.json('POST', '/containers/' + container + '/exec', dict(Cmd=['python', '-c', child_code]), 201)['Id']
    engine.json('POST', '/exec/' + child + '/start', dict(Detach=True, Tty=False))
    wait(lambda: (source / 'domain-child-ready').exists())
    wait(lambda: not engine.json('GET', '/exec/' + child + '/json')['Running'])
    initial = engine.json('GET', '/containers/' + container + '/json')['State']['Pid']
    directory = Path('/sys/fs/cgroup') / parent
    assert Path(f'/proc/{initial}/cgroup').read_text().strip().startswith('0::/' + parent + '/')
    lock_path = root / 'domain-launch.lock'
    lock_path.touch(mode=0o600)
    info = lock_path.stat()
    expected = [info.st_dev, info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode)]
    client = DomainClient(plugin, parent)
    with LaunchLock(lock_path, expected) as launch:
        boundary = ExecutorBoundary(client, launch, directory, root / 'executor-boundary')
        started = time.monotonic()
        boundary.acquire()
        acquisition_seconds = time.monotonic() - started
        assert boundary.check() == boundary.lease
        assert (source / 'domain-child-finished').exists()
        assert (source / 'domain-fd').read_bytes().startswith(b'clean')
        assert (source / 'domain-fd').read_bytes()[20:24] == b'done'
        before = {path.name: path.read_bytes() for path in source.iterdir() if path.is_file()}
        assert engine.call('POST', '/containers/' + container + '/start')[0] == 403
        assert engine.call('POST', '/containers/create?name=fc-authz-late', base)[0] == 403
        time.sleep(.25)
        assert before == {path.name: path.read_bytes() for path in source.iterdir() if path.is_file()}
        assert boundary.check() == boundary.lease
        released = boundary.release()
        assert boundary.release() == released
    engine.json('POST', '/containers/' + container + '/start', expected=204)
    wait(lambda: len((source / 'domain-starts').read_text().splitlines()) == 2)
    engine.json('POST', '/containers/' + container + '/stop?t=3', expected=204)
    state = engine.json('GET', '/containers/' + container + '/json')['State']
    assert not state['Running'] and state['ExitCode'] == 0
    return dict(resource_domain_parent=parent, clean_full_domain=True, old_fd_mmap_child='GRACEFUL_EXIT_BEFORE_HELD',
        complete_inventory=207, initial_running=17, acquisition_seconds=acquisition_seconds,
        automatic_restart_policy='DENIED_BEFORE_HOLD', direct_start_create='DENIED_WHILE_HELD',
        same_cgroup_lease=True, repeat_release='NO_EFFECT_REPLAY', normal_container_resume=True,
        initial_production_admission_coverage=False, installed_owner_adapter=False, common_kit=False)


def controller(plugin, root, parent, channel):
    lock_path = Path(root) / 'fault-launch.lock'
    info = lock_path.stat()
    expected = [info.st_dev, info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode)]
    with LaunchLock(lock_path, expected) as launch:
        boundary = ExecutorBoundary(DomainClient(plugin, parent), launch,
            Path('/sys/fs/cgroup') / parent, Path(root) / 'fault-controller')
        boundary.acquire()
        channel.send(boundary.lease)
        time.sleep(60)


def fault(plugin, root, parent, mode, enforcer):
    directory = Path('/sys/fs/cgroup') / parent
    lock_path = root / 'fault-launch.lock'
    lock_path.touch(mode=0o600)
    info = lock_path.stat()
    expected = [info.st_dev, info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode)]
    if mode == 'controller-death':
        context = multiprocessing.get_context('spawn')
        reader, sender = context.Pipe()
        process = context.Process(target=controller, args=(plugin, str(root), parent, sender))
        process.start()
        sender.close()
        try:
            assert reader.poll(12)
            lease = reader.recv()
            assert lease and (directory / 'cgroup.freeze').read_text().strip() == '1'
            process.kill()
            process.join(5)
            assert not process.is_alive() and (directory / 'cgroup.freeze').read_text().strip() == '1'
            domain = root / 'fault-controller/domain'
            assert not (domain / 'released.json').exists()
            plan = json.loads((domain / 'plan.json').read_bytes())
            time.sleep(.1)
            with LaunchLock(lock_path, expected) as launch:
                result = reconcile_domain(domain, fingerprint(plan), launch)
                assert result['capture_permitted'] is False
            assert API(plugin).json('POST', '/fc-control', dict(command='RELEASE'))['phase'] == 'RELEASED'
        finally:
            if process.is_alive():
                process.kill()
                process.join(5)
            reader.close()
    else:
        with LaunchLock(lock_path, expected) as launch:
            boundary = ExecutorBoundary(DomainClient(plugin, parent), launch, directory, root / ('fault-' + mode))
            boundary.acquire()
            os.kill(enforcer, signal.SIGKILL if mode == 'enforcer-death' else signal.SIGSTOP)
            started = time.monotonic()
            try:
                boundary.check()
                raise AssertionError('LOST_ENFORCEMENT_ACCEPTED')
            except (OSError, ValueError):
                assert time.monotonic() - started < 6 and boundary.failed
            finally:
                if mode == 'enforcer-hang':
                    os.kill(enforcer, signal.SIGCONT)
            assert (directory / 'cgroup.freeze').read_text().strip() == '1'
            assert not (boundary.journal / 'domain/released.json').exists()
            boundary.domain.__exit__(None, None, None)
            if mode == 'enforcer-hang':
                assert API(plugin).json('POST', '/fc-control', dict(command='RELEASE'))['phase'] == 'RELEASED'
    assert (directory / 'cgroup.freeze').read_text().strip() == '0'
    return dict(mode=mode, loss_not_cleanup=True, old_lease_not_adopted=True, explicit_physical_cleanup=True,
                normal_writer_resume=False, common_kit=False)


def main():
    parser = argparse.ArgumentParser()
    for name in ('engine', 'plugin', 'root', 'parent'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--mode', default='normal', choices=['normal', 'enforcer-death', 'enforcer-hang', 'controller-death'])
    parser.add_argument('--enforcer', type=int)
    args = parser.parse_args()
    root = Path(args.root)
    assert os.geteuid() == 0 and root.name.startswith('fc-owner-executor-')
    result = run(API(args.engine), args.plugin, root, args.parent) if args.mode == 'normal' else fault(
        args.plugin, root, args.parent, args.mode, args.enforcer)
    (root / ('domain-' + args.mode + '.json')).write_text(json.dumps(result, sort_keys=True))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
