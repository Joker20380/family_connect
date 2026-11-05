import hashlib
import base64
import json
import os
import socket
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import threading
import zipfile

import pytest

from scripts import package_online_renewal as package


@pytest.fixture(scope='module')
def online_package(tmp_path_factory):
    go = os.environ.get('FC_ONLINE_GO')
    if not go:
        pytest.skip('explicit online package Go toolchain required')
    root = tmp_path_factory.mktemp('online-source')
    source = root/'source'
    frozen = os.environ.get('FC_TEST_ONLINE_PACKAGE')
    if frozen:
        archive = Path(frozen)
        with tarfile.open(archive) as bundle:
            raw = bundle.extractfile('source-manifest.json').read()
        manifest = json.loads(raw)
        subprocess.run(['git', 'clone', '-q', '--shared', '--no-checkout', str(package.ROOT), str(source)], check=True)
        subprocess.run(['git', 'checkout', '-q', '--detach', manifest['source_commit']], cwd=source, check=True)
        receipt = {name: manifest[name] for name in
                   ('source_commit', 'source_sha256', 'api_sha256', 'http_sha256', 'gateway_sha256')}
        receipt.update(sha256=package.digest(archive.read_bytes()), manifest_sha256=package.digest(raw))
    else:
        source.mkdir()
        native = subprocess.check_output(['git', 'ls-files', 'carrier'], cwd=package.ROOT, text=True).splitlines()
        names = set(package.SOURCES) | {name for name in native if name.endswith(('.go', '/go.mod', '/go.sum'))}
        names.update(json.loads((package.ROOT/'deploy/friends/restricted/http-runtime-files.json').read_bytes()))
        names.update(('deploy/friends/restricted/http-runtime-files.json', 'deploy/friends/access-api.py'))
        for name in names:
            target = source/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((package.ROOT/name).read_bytes())
        subprocess.run(['git', 'init', '-q', str(source)], check=True)
        subprocess.run(['git', 'add', '.'], cwd=source, check=True)
        subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'isolated source fixture'], cwd=source, check=True)
        archive = root/'online.tar.gz'
        receipt = package.build(archive, 'HEAD', go=Path(go), repository=source)
    extracted = root/'package'
    extracted.mkdir(mode=0o700)
    with tarfile.open(archive) as bundle:
        bundle.extractall(extracted, filter='data')
    return root, source, archive, extracted, receipt


@pytest.fixture(scope='module')
def core_driver(online_package):
    root, source, _, _, _ = online_package
    driver = root/'mesh-runtime'
    environment = dict(os.environ, CGO_ENABLED='0', GOTOOLCHAIN='local', GOOS='linux', GOARCH='amd64', GOFLAGS='')
    subprocess.run([os.environ['FC_ONLINE_GO'], 'build', '-mod=readonly', '-trimpath', '-buildvcs=false',
        '-ldflags=-buildid=', '-o', str(driver), './internal/qualification/cmd/mesh-runtime'],
        cwd=source/'carrier', env=environment, check=True)
    return driver


def test_online_package_reproducible_without_working_checkout_imports(online_package):
    root, source, archive, extracted, receipt = online_package
    (source/'control/friends/restricted.py').write_text('raise RuntimeError("dirty source must not ship")\n')
    second = root/'second.tar.gz'
    assert package.build(second, 'HEAD', go=Path(os.environ['FC_ONLINE_GO']), repository=source) == receipt
    assert archive.read_bytes() == second.read_bytes()
    manifest = json.loads((extracted/'source-manifest.json').read_bytes())
    assert manifest['default_online'] is False and manifest['production_configuration'] == 'absent'
    assert manifest['package_contract'] == package.PACKAGE and manifest['operation_permit'] is None
    assert (extracted/'ONLINE_RUNTIME.md').read_bytes() == (package.ROOT/package.DIRECTORY/'ONLINE_RUNTIME.md').read_bytes()
    assert set(manifest['source_files']) == set(package.ONLINE_MODULES)
    for name, expected in manifest['files'].items():
        assert hashlib.sha256((extracted/name).read_bytes()).hexdigest() == expected
    with zipfile.ZipFile(extracted/'api.pyz') as api:
        assert api.read('control/friends/restricted.py') == (package.ROOT/'control/friends/restricted.py').read_bytes()
        assert 'control/friends/paid_beta.py' in api.namelist()
    probe = ('import sys;sys.path.insert(0,sys.argv[1]);sys.path.insert(0,sys.argv[2]);'
             'from control.friends import restricted;import online_runtime,online_cli;'
             'assert callable(restricted.online_generation);'
             'assert restricted.__file__.startswith(sys.argv[1]+"/");'
             'from production_node import ProductionNode;'
             'assert "online_qualification" not in open(online_cli.__file__).read()')
    subprocess.run([sys.executable, '-I', '-B', '-c', probe, str(extracted/'api.pyz'), str(extracted/'renewal')],
                   cwd=root, check=True, capture_output=True)
    for entry in ('online_cli.py', 'node.py', 'runtime_controller.py'):
        subprocess.run([sys.executable, '-E', '-s', '-B', str(extracted/'renewal'/entry), '--help'],
                       cwd=root, check=True, capture_output=True)
    subprocess.run([str(extracted/'gateway'), '-h'], cwd=root, check=True, capture_output=True)
    subprocess.run([sys.executable, '-I', '-B', str(extracted/'http.pyz'), '--help'], cwd=root,
                   check=True, capture_output=True)
    with pytest.raises(FileExistsError):
        package.build(archive, 'HEAD', go=Path(os.environ['FC_ONLINE_GO']), repository=source)


@pytest.mark.parametrize('opt_in', [None, 'wrong-contract', package.CONTRACT])
def test_packaged_cli_requires_opt_in_and_full_membership(online_package, tmp_path, opt_in):
    root, source, archive, extracted, receipt = online_package
    config = dict(schema=1, online=opt_in, state=str(tmp_path/'state'), anchor='AA==',
                  gateway_ids={'NL': 'a'*32, 'NL2': 'b'*32}, schedule_seconds=0, ssh_routes={})
    path = tmp_path/'controller.json'
    path.write_bytes(package.encode(config))
    path.chmod(0o600)
    result = subprocess.run([sys.executable, '-E', '-s', '-B', str(extracted/'renewal/online_cli.py'),
                            '--config', str(path), '--operation', 'test-online-packaged-0001', '--mode', 'online'],
                           cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1, result.stdout
    expected = 'ONLINE_OPT_IN_REQUIRED' if opt_in != package.CONTRACT else 'ONLINE_MEMBERSHIP_REQUIRED'
    if os.geteuid() != 0:
        expected = 'ROOT_REQUIRED'
    assert json.loads(result.stdout)['cause'] == expected, result.stdout
    assert not (tmp_path/'state').exists()


def test_participant_contract_fails_before_writes():
    from test_online_renewal import CONTRACT
    from online_runtime import verify_participants, PACKAGE, FEATURES
    from credential_renewal import Rejected
    from types import SimpleNamespace
    manifest = dict(source_sha256='a'*64, api_sha256='b'*64, gateway_sha256='c'*64)
    members = {'NL': 'a'*32, 'NL2': 'b'*32}
    def response(slot):
        value = dict(contract=CONTRACT, package_contract=PACKAGE, features=FEATURES, slot=slot,
                     gateway_ids=members, **manifest)
        if slot != 'RU':
            value['runtime'] = dict(contract=CONTRACT, gateway=members[slot], profile_sha256='d'*64, instance='e'*64)
        return value
    receipts = {slot: response(slot) for slot in ('RU', 'NL', 'NL2')}
    nodes = {slot: SimpleNamespace(call=lambda *args, slot=slot: receipts[slot]) for slot in receipts}
    verify_participants(nodes, 'test-online-capabilities', manifest, members, running=True)
    for field in ('contract', 'source_sha256', 'api_sha256', 'slot', 'gateway_ids', 'features'):
        previous = receipts['NL2'][field]
        receipts['NL2'][field] = None
        with pytest.raises(Rejected, match='ONLINE_PARTICIPANT_CAPABILITIES'):
            verify_participants(nodes, 'test-online-capabilities', manifest, members, running=True)
        receipts['NL2'][field] = previous
    receipts['NL2']['runtime'] = None
    with pytest.raises(Rejected, match='ONLINE_READER_STOPPED'):
        verify_participants(nodes, 'test-online-capabilities', manifest, members, running=True)
    verify_participants(nodes, 'test-online-capabilities', manifest, members, running=False)


@pytest.mark.parametrize('response', [b'', b'{', b'{"contract":"one","contract":"two"}', b'\xff', b' '*4097])
def test_malformed_reader_returns_bounded_explicit_cause(tmp_path, response):
    from test_online_renewal import Rejected
    from online_reader import RuntimeReader
    path = str(tmp_path/'reader.sock')
    listener = socket.socket(socket.AF_UNIX)
    listener.bind(path)
    listener.listen(1)
    def serve():
        with listener.accept()[0] as connection:
            while connection.recv(4096):
                pass
            connection.sendall(response)
    worker = threading.Thread(target=serve)
    worker.start()
    try:
        with pytest.raises(Rejected, match='ONLINE_RUNTIME_RECEIPT'):
            RuntimeReader(path)(None)
    finally:
        listener.close()
        worker.join(timeout=5)
        assert not worker.is_alive()


def test_missing_reader_is_explicitly_unavailable(tmp_path):
    from test_online_renewal import Rejected
    from online_reader import RuntimeReader
    with pytest.raises(Rejected, match='ONLINE_RUNTIME_UNAVAILABLE'):
        RuntimeReader(tmp_path/'absent.sock')(None)


def test_packaged_node_checks_actual_gateway_process(online_package, tmp_path):
    if os.environ.get('FC_ONLINE_ISOLATED') != '1':
        pytest.skip('explicit disposable root container required')
    assert os.geteuid() == 0 and Path('/.dockerenv').exists()
    assert tmp_path.is_relative_to('/run')
    from test_multi_gateway_renewal import make_fleet
    from control.friends.profile_store import metadata
    root, source, archive, extracted, receipt = online_package
    fleet = make_fleet(tmp_path, now=int(time.time()))
    node = fleet.nodes['NL']
    manifest = json.loads((extracted/'source-manifest.json').read_bytes())
    profile_directory = tmp_path/'canonical-profile'
    profile_directory.mkdir(mode=0o750)
    os.chown(profile_directory, 0, 41003)
    profile = profile_directory/'gateway.json'
    profile.write_bytes((node.live/'gateway.json').read_bytes())
    os.chown(profile, 0, 41003)
    profile.chmod(0o640)
    private = tmp_path/'private-config'
    private.mkdir(mode=0o700)
    lock = private/'profile.lock'
    lock.touch(mode=0o600)
    operations = private/'operations'
    operations.mkdir(mode=0o700)
    publisher = node.live.stat()
    gateway = extracted/'gateway'
    locator = dict(schema=1, lock_version=1, profile=str(profile), lock=str(lock), operations=str(operations),
        reader_gid=41003, directory=dict(path=str(node.live/'directory.json'),
            metadata=metadata((node.live/'directory.json').stat()), publisher_parent=dict(path=str(node.live),
                **metadata(publisher), device=publisher.st_dev, inode=publisher.st_ino),
            publisher_contract=[[str(gateway), manifest['gateway_sha256'], metadata(gateway.stat())]]))
    def private_file(name, value):
        path = private/name
        path.write_bytes(value)
        path.chmod(0o600)
        return path
    locator_path = private_file('locator.json', package.encode(locator))
    anchor_path = private_file('anchor', base64.b64encode(fleet.service.anchor))
    observer = private/'reader.sock'
    config = dict(schema=1, role='NL', live=str(node.live), state=str(node.state), database=None,
        anchor=str(anchor_path), anchor_sha256=package.digest(fleet.service.anchor), api_archive=str(extracted/'api.pyz'),
        api_sha256=manifest['api_sha256'], service_units=['synthetic-gateway.service'],
        source_files=manifest['source_files'], source_sha256=manifest['source_sha256'], admission_mode='all_activated',
        profile_locator=str(locator_path), profile_locator_sha256=package.digest(locator_path.read_bytes()),
        gateway_ids=fleet.identities, gateway_slot='NL', online=dict(contract=package.CONTRACT,
            reader_socket=str(observer), reader_uid=0, reader_executable_sha256=manifest['gateway_sha256']))
    config_path = private_file('node.json', package.encode(config))
    systemctl = Path('/usr/bin/systemctl')
    prior = systemctl.read_bytes() if systemctl.exists() else None
    prior_mode = systemctl.stat().st_mode & 0o777 if prior is not None else None
    service_state = Path('/run/fc-online-service-state.json')
    assert not service_state.exists()
    proxy = socket.socket()
    proxy.bind(('127.0.0.1', 0))
    proxy.listen(1)
    environment = dict(os.environ, YANDEX_TELEMOST_OAUTH_TOKEN='synthetic-isolated-unused',
                       HTTPS_PROXY='http://127.0.0.1:'+str(proxy.getsockname()[1]), NO_PROXY='')
    process = subprocess.Popen([str(gateway), '-family-config', str(profile), '-listen', '127.0.0.1:0',
        '-publication-observer', str(observer)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=environment)
    try:
        deadline = time.monotonic()+10
        while not observer.exists():
            assert process.poll() is None, 'packaged gateway failed to start'
            assert time.monotonic() < deadline
            time.sleep(.05)
        state = {'synthetic-gateway.service': dict(ActiveState='active', SubState='running', MainPID=str(process.pid),
                                                  InvocationID='synthetic', NRestarts='0', Result='success')}
        service_state.write_bytes(package.encode(state))
        systemctl.write_bytes(b'#!/usr/local/bin/python\n'+(package.ROOT/'tests/fixtures/online_systemctl.py').read_bytes())
        systemctl.chmod(0o755)
        request = dict(schema=1, role='NL', action='online', operation_id='test-online-package-reader',
            expected_source_sha256=manifest['source_sha256'], payload=dict(command='capabilities'))
        def rpc():
            result = subprocess.run([sys.executable, '-E', '-s', '-B', str(extracted/'renewal/node.py'),
                '--config', str(config_path)], cwd=private, input=package.encode(request), capture_output=True)
            return result.returncode, json.loads(result.stdout)
        code, result = rpc()
        assert code == 0, result
        runtime = result['payload']['runtime']
        assert runtime['gateway'] == fleet.identities['NL']
        assert runtime['profile_sha256'] == package.digest(profile.read_bytes())
        assert len(runtime['instance']) == 64
        state['synthetic-gateway.service']['MainPID'] = str(os.getpid())
        service_state.write_bytes(package.encode(state))
        code, result = rpc()
        assert code == 1, result
        assert result.get('cause', result.get('payload', {}).get('cause')) == 'ONLINE_READER_PROCESS', result
        config.pop('online')
        config_path.write_bytes(package.encode(config))
        code, result = rpc()
        assert code == 1 and result['payload']['cause'] == 'ONLINE_QUALIFICATION_ONLY', result
        assert not (node.state/'owner.json').exists()
    finally:
        process.terminate()
        process.wait(timeout=10)
        proxy.close()
        service_state.unlink(missing_ok=True)
        if prior is None:
            systemctl.unlink(missing_ok=True)
        else:
            systemctl.write_bytes(prior)
            systemctl.chmod(prior_mode)


def test_controller_entrypoint_reaches_three_ssh_handlers_and_enforces_budget(online_package, tmp_path):
    if os.environ.get('FC_ONLINE_SSH') != '1':
        pytest.skip('explicit network-none SSH container required')
    from online_package_stand import PackageStand
    stand = PackageStand(tmp_path, online_package[3], age=13001)
    try:
        stand.start()
        code, result = stand.run('inspect')
        assert code == 0 and result == dict(result='ONLINE_CAPABILITIES_READY', mutations=0), result
        code, result = stand.run('online')
        assert code == 1 and result['cause'] == 'ONLINE_WINDOW_INSUFFICIENT', result
        assert not (tmp_path/'coordinator/transaction.json').exists()
        assert not any((node.state/'owner.json').exists() for node in stand.fleet.nodes.values())
    finally:
        stand.close()


def test_packaged_online_commit_and_replay_over_ssh(online_package, core_driver, tmp_path):
    if os.environ.get('FC_ONLINE_SSH') != '1':
        pytest.skip('explicit network-none SSH container required')
    from mesh_core_stand import CoreStand
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    try:
        stand.start()
        code, result = stand.run('online')
        assert code == 0 and result['result'] == 'COMMITTED', result
        record = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
        assert record['decision'] == 'COMMIT'
        marker = json.loads((stand.fleet.nodes['RU'].live/'online-delivery.json').read_bytes())
        assert marker['ready'] is True
        before = (tmp_path/'coordinator/plan.json').read_bytes()
        code, result = stand.run('resume')
        assert code == 0 and result['result'] == 'COMMITTED' and result['replay'], result
        assert (tmp_path/'coordinator/plan.json').read_bytes() == before
        assert not any((node.state/'start-intent-0.json').exists() for node in stand.fleet.nodes.values())
    finally:
        stand.close()


@pytest.mark.parametrize('failure,cause', [('missing-opt-in', 'ONLINE_QUALIFICATION_ONLY'),
    ('incompatible', 'RPC_RESPONSE_SCHEMA'), ('gateway-exit', 'ONLINE_RUNTIME_UNAVAILABLE')])
def test_packaged_nl_failure_rejects_before_owner_or_journal(online_package, tmp_path, failure, cause):
    if os.environ.get('FC_ONLINE_SSH') != '1':
        pytest.skip('explicit network-none SSH container required')
    from online_package_stand import PackageStand, private_file
    stand = PackageStand(tmp_path, online_package[3], age=12000)
    try:
        stand.start()
        if failure == 'gateway-exit':
            process = next(process for process in stand.processes
                           if process.pid == int(stand.states['test-NL2.service']['MainPID']))
            process.kill()
            process.wait(timeout=5)
        else:
            configuration = json.loads(stand.configs['NL2'].read_bytes())
            if failure == 'missing-opt-in':
                configuration.pop('online')
            else:
                configuration['online']['contract'] = 'incompatible'
            private_file(stand.configs['NL2'], package.encode(configuration))
        code, result = stand.run('online')
        assert code == 1 and result['result'] == 'FAIL_CLOSED' and result['cause'] == cause, result
        assert not (tmp_path/'coordinator/transaction.json').exists()
        assert not any((node.state/'owner.json').exists() for node in stand.fleet.nodes.values())
        assert not (stand.fleet.nodes['RU'].live/'online-delivery.json').exists()
        if failure == 'incompatible':
            request = dict(schema=1, role='NL', action='online', operation_id='test-packaged-ssh-controller',
                expected_source_sha256=stand.manifest['source_sha256'], payload=dict(command='capabilities'))
            rejected = subprocess.run([sys.executable, '-E', '-s', '-B', str(stand.extracted/'renewal/node.py'),
                '--config', str(stand.configs['NL2'])], input=package.encode(request), capture_output=True, timeout=5)
            assert rejected.returncode == 1 and json.loads(rejected.stdout) == dict(
                result='REJECTED', cause='ONLINE_OPT_IN_REQUIRED')
    finally:
        stand.close()


@pytest.mark.parametrize('boundary', ['ONLINE_FENCING', 'ONLINE_PREPARED', 'ONLINE_COMMIT_DECIDED',
                                    'ONLINE_NL2_DECIDED', 'ONLINE_NL2_PUBLISHED', 'ONLINE_RUNTIME_CONFIRMED', 'ONLINE_CLEANING'])
def test_packaged_controller_sigkill_resumes_same_decision(online_package, core_driver, tmp_path, boundary):
    if os.environ.get('FC_ONLINE_SSH') != '1':
        pytest.skip('explicit network-none SSH container required')
    from mesh_core_stand import CoreStand
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    process = None
    try:
        stand.start()
        process = subprocess.Popen(stand.command('online'), cwd=tmp_path,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        journal = tmp_path/'coordinator/transaction.json'
        deadline = time.monotonic()+45
        while True:
            record = json.loads(journal.read_bytes()) if journal.exists() else {}
            if record.get('state') == boundary:
                process.kill()
                process.wait(timeout=5)
                break
            assert process.poll() is None and time.monotonic() < deadline, record.get('state')
            time.sleep(.001)
        before = json.loads(journal.read_bytes())
        code, result = stand.run('resume')
        assert code == 0 and result['result'] == 'COMMITTED', result
        final = json.loads(journal.read_bytes())
        assert final['decision'] == 'COMMIT' and final['operation_id'] == before['operation_id']
        if before['commit_decided']:
            assert final['plan_sha256'] == before['plan_sha256']
        assert not any((node.state/'start-intent-0.json').exists() for node in stand.fleet.nodes.values())
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        stand.close()


def test_packaged_seed_timeout_is_not_a_ready_traffic_runtime(online_package, tmp_path):
    if os.environ.get('FC_ONLINE_SSH') != '1':
        pytest.skip('explicit network-none SSH container required')
    from online_package_stand import PackageStand
    stand = PackageStand(tmp_path, online_package[3], age=12000)
    try:
        started = time.monotonic()
        stand.start()
        gateways = {int(stand.states['test-'+slot+'.service']['MainPID']) for slot in ('NL', 'NL2')}
        for process in stand.processes:
            if process.pid in gateways:
                assert process.wait(timeout=20) != 0
        assert time.monotonic()-started >= 15
        code, result = stand.run('online')
        assert code == 1 and result['cause'] == 'ONLINE_RUNTIME_UNAVAILABLE', result
        assert not (tmp_path/'coordinator/transaction.json').exists()
        assert not any((node.state/'owner.json').exists() for node in stand.fleet.nodes.values())
    finally:
        stand.close()


@pytest.mark.parametrize('slot,command,kind', [('RU', 'prepare', 'drop'), ('NL', 'stage', 'drop'),
    ('NL2', 'decide', 'drop'), ('NL', 'publish', 'drop'), ('NL2', 'confirm', 'drop'),
    ('RU', 'publish', 'drop'), ('NL2', 'stage', 'wrong-slot')])
def test_packaged_rpc_lost_reply_and_participant_corruption(online_package, core_driver, tmp_path, slot, command, kind):
    if os.environ.get('FC_ONLINE_SSH') != '1':
        pytest.skip('explicit network-none SSH container required')
    from mesh_core_stand import CoreStand
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    try:
        stand.start()
        stand.rpc_fault(slot, command, kind)
        code, result = stand.run('online')
        assert code == 75 and result['result'] == 'ONLINE_RECOVERY_REQUIRED', result
        expected = 'ONLINE_PREPARED_RECEIPT' if kind == 'wrong-slot' else 'REMOTE_OUTCOME_UNKNOWN_READBACK_REQUIRED'
        assert result['cause'] == expected, result
        before = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
        code, result = stand.run('abort' if kind == 'wrong-slot' else 'resume')
        assert code == 0 and result['result'] == ('ABORTED' if kind == 'wrong-slot' else 'COMMITTED'), result
        final = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
        if before['commit_decided']:
            assert final['plan_sha256'] == before['plan_sha256'] and final['decision'] == 'COMMIT'
        if kind == 'wrong-slot':
            assert not before['commit_decided'] and not (stand.fleet.nodes['RU'].live/'online-delivery.json').exists()
    finally:
        stand.close()
