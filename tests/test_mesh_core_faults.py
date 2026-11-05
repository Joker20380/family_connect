import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from fixtures.mesh_supervisor import request
from mesh_core_stand import CoreStand
from online_package_stand import private_file
from scripts import package_online_renewal as package
from test_online_runtime_package import core_driver, online_package


def kill_at(stand, mode, state, approval=None):
    command = stand.command(mode)
    if approval is not None:
        command += ['--outage-approval', str(approval)]
    process = subprocess.Popen(command, cwd=stand.root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic()+90
    try:
        while True:
            journal = stand.root/'coordinator/transaction.json'
            record = json.loads(journal.read_bytes()) if journal.exists() else {}
            if record.get('state') == state:
                process.kill()
                assert process.wait(timeout=5) == -9
                return json.loads(journal.read_bytes())
            assert process.poll() is None and time.monotonic() < deadline, record.get('state')
            time.sleep(.001)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def pause_at(stand, mode, state):
    process = subprocess.Popen(stand.command(mode), cwd=stand.root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic()+90
    try:
        while True:
            path = stand.root/'coordinator/transaction.json'
            record = json.loads(path.read_bytes()) if path.exists() else {}
            if record.get('state') == state:
                process.send_signal(signal.SIGSTOP)
                return process, record
            assert process.poll() is None and time.monotonic() < deadline, record.get('state')
            time.sleep(.001)
    except BaseException:
        process.kill()
        process.wait(timeout=5)
        raise


def approved(stand, result):
    now = int(time.time())
    return private_file(stand.root/'approval.json', package.encode(dict(operation_id='test-packaged-ssh-controller',
        expected_state_sha256=result['request']['expected_state_sha256'], approved_at=now, expires_at=now+900,
        approval='OPERATOR_APPROVED_OUTAGE')))


def save_evidence(stand, name, value):
    destination = os.environ.get('FC_CORE_EVIDENCE')
    if destination:
        root = Path(destination)/name
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        private_file(root/'receipt.json', package.encode(dict(value, source=stand.manifest['source_commit'],
            runtime_scope='isolated-core-supervisor-not-systemd', driver_sha256=package.digest(stand.driver.read_bytes()))))
        for path in stand.root.glob('*.log'):
            private_file(root/path.name, path.read_bytes())


@pytest.mark.parametrize('boundary', ['EMERGENCY_HANDOFF', 'EMERGENCY_AUTHORIZED', 'EMERGENCY_COMMIT_DECIDED', 'CLEANING'])
def test_controller_death_at_emergency_durable_boundary(online_package, core_driver, tmp_path, boundary):
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    observations = dict(boundary=boundary, results=[])
    try:
        stand.start()
        origin = kill_at(stand, 'online', 'ONLINE_COMMIT_DECIDED')
        initial = request(dict(command='show', unit='test-NL2.service'))['state']
        request(dict(command='kill', unit='test-NL2.service'))
        assert not (tmp_path/'NL2-config/reader.sock').exists()
        replacement = request(dict(command='start', unit='test-NL2.service'))['state']
        assert replacement['MainPID'] != initial['MainPID'] and replacement['InvocationID'] != initial['InvocationID']
        deadline = time.monotonic()+5
        while not (tmp_path/'NL2-config/reader.sock').exists():
            assert time.monotonic() < deadline
            time.sleep(.02)
        code, result = stand.run('resume')
        observations['results'].append(result)
        assert code == 75 and result['result'] == 'ONLINE_EMERGENCY_REQUIRED', result
        approval = None
        if boundary != 'EMERGENCY_HANDOFF':
            code, required = stand.run('emergency')
            assert code == 75 and required['result'] == 'EMERGENCY_APPROVAL_REQUIRED', required
            approval = approved(stand, required)
        interrupted = kill_at(stand, 'emergency', boundary, approval)
        assert interrupted['online_parent']['decision'] == 'COMMIT'
        assert package.digest(package.encode(interrupted['online_parent']['plan'])) == origin['plan_sha256']
        if boundary == 'EMERGENCY_HANDOFF':
            code, required = stand.run('emergency')
            assert code == 75 and required['result'] == 'EMERGENCY_APPROVAL_REQUIRED', required
            approval = approved(stand, required)
        code, result = stand.run('emergency', approval)
        observations['results'].append(result)
        assert code == 0 and result['result'] == 'EMERGENCY_RECOVERED', result
        recovered = {slot: request(dict(command='show', unit='test-'+slot+'.service'))['state'] for slot in ('NL', 'NL2')}
        assert recovered['NL']['NRestarts'] == '1' and recovered['NL2']['NRestarts'] == '2', recovered
        clients = {slot: stand.client(slot, 2) for slot in recovered}
        for slot, client in clients.items():
            assert client.wait(timeout=40) == 0, (tmp_path/(slot+'-client.log')).read_text()
        code, replay = stand.run('emergency')
        assert code == 0 and replay['replay'], replay
        assert recovered == {slot: request(dict(command='show', unit='test-'+slot+'.service'))['state'] for slot in recovered}
        observations.update(outcome='SAME_COMMIT_EMERGENCY_RECOVERED', interrupted_state=interrupted['state'],
            original_plan_sha256=origin['plan_sha256'], original_fence=origin['fence'],
            recovery_fence=interrupted['online_parent']['fence'], initial=initial, replacement=replacement, recovered=recovered,
            traffic='new-sessions-only-DNS-verified-HTTPS', replay=replay)
    finally:
        stand.close()
        save_evidence(stand, 'controller-'+boundary.lower(), observations)


@pytest.mark.parametrize('after_commit', [False, True])
def test_unreachable_participant_blocks_then_continues_same_commit(online_package, core_driver, tmp_path, after_commit):
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    observations = dict(after_commit=after_commit)
    try:
        stand.start()
        origin = kill_at(stand, 'online', 'ONLINE_COMMIT_DECIDED') if after_commit else None
        journal = tmp_path/'coordinator/transaction.json'
        before = journal.read_bytes() if after_commit else None
        healthy = stand.controller.read_bytes()
        configuration = json.loads(healthy)
        configuration['ssh_routes']['NL2']['target'] = 'root@127.0.0.2'
        private_file(stand.controller, package.encode(configuration))
        code, result = stand.run('resume' if after_commit else 'online')
        assert code == 1 and result['result'] == 'FAIL_CLOSED' and result['cause'] == 'REMOTE_OUTCOME_UNKNOWN_READBACK_REQUIRED', result
        assert journal.read_bytes() == before if after_commit else not journal.exists()
        private_file(stand.controller, healthy)
        code, recovered = stand.run('resume' if after_commit else 'online')
        assert code == 0 and recovered['result'] == 'COMMITTED', recovered
        final = json.loads(journal.read_bytes())
        if origin:
            assert final['plan_sha256'] == origin['plan_sha256'] and final['fence'] > origin['fence']
        assert all(request(dict(command='show', unit='test-'+slot+'.service'))['state']['NRestarts'] == '0' for slot in ('NL', 'NL2'))
        observations.update(blocked=result, recovered=recovered, plan_sha256=final['plan_sha256'],
                            outcome='BLOCKED_NO_WRITES_THEN_SAME_COMMIT' if origin else 'BLOCKED_BEFORE_JOURNAL_THEN_NORMAL_COMMIT')
    finally:
        stand.close()
        save_evidence(stand, 'unreachable-'+str(after_commit).lower(), observations)


def test_directory_publisher_refuses_active_maintenance_owner(online_package, core_driver, tmp_path):
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    controller = None
    observations = {}
    try:
        stand.start()
        controller, prepared = pause_at(stand, 'online', 'ONLINE_PREPARED')
        before = {slot: (stand.fleet.nodes[slot].live/'directory.json').read_bytes() for slot in ('RU', 'NL', 'NL2')}
        result = subprocess.run([sys.executable, '-E', '-s', '-B', str(stand.extracted/'renewal/scheduled_evaluate.py'),
            '--config', str(stand.configs['RU']), '--ssh-key', str(tmp_path/'ssh/client'),
            '--known-hosts', str(tmp_path/'ssh/known_hosts'), '--directory-only'],
            cwd=tmp_path, capture_output=True, timeout=20)
        assert result.returncode == 0, result.stderr.decode()
        receipt = json.loads(result.stdout)
        assert receipt == dict(result='MAINTENANCE_IN_PROGRESS', mutations=0), receipt
        assert before == {slot: (stand.fleet.nodes[slot].live/'directory.json').read_bytes() for slot in before}
        controller.send_signal(signal.SIGCONT)
        assert controller.wait(timeout=90) == 0
        code, commit = stand.run('resume')
        assert code == 0 and commit['replay'], commit
        observations.update(outcome='PUBLISHER_BLOCKED_WITHOUT_MUTATIONS', publisher=receipt,
                            competing_controller_pid=controller.pid, owner_fence=prepared['fence'], commit=commit)
    finally:
        if controller and controller.poll() is None:
            controller.kill()
            controller.wait(timeout=5)
        stand.close()
        save_evidence(stand, 'publisher-owner-race', observations)


def test_paused_stale_rpc_writer_is_rejected_after_new_fence(online_package, core_driver, tmp_path):
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    controller, writer = None, None
    observations = {}
    try:
        stand.start()
        origin = kill_at(stand, 'online', 'ONLINE_COMMIT_DECIDED')
        program = '''import json,os,signal,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from production_transport import SshNode
from credential_renewal import Rejected
configuration=json.loads(Path(sys.argv[2]).read_bytes())
manifest=json.loads(Path(sys.argv[3]).read_bytes())
payload=dict(command='publish',fence=int(sys.argv[4]))
node=SshNode('NL',manifest['source_sha256'],route=configuration['ssh_routes']['NL'])
os.kill(os.getpid(),signal.SIGSTOP)
try:node.call('online','test-packaged-ssh-controller',payload)
except Rejected as error:
 print(json.dumps(dict(cause=str(error),pid=os.getpid(),fence=payload['fence'])))
 sys.exit(75)
sys.exit(1)
'''
        writer = subprocess.Popen([sys.executable, '-I', '-B', '-c', program, str(stand.extracted/'renewal'),
            str(stand.controller), str(stand.extracted/'source-manifest.json'), str(origin['fence'])],
            cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.monotonic()+10
        while 'State:\tT' not in Path('/proc/'+str(writer.pid)+'/status').read_text():
            assert writer.poll() is None and time.monotonic() < deadline
            time.sleep(.01)
        controller, resumed = pause_at(stand, 'resume', 'ONLINE_NL2_DECIDED')
        assert resumed['fence'] > origin['fence']
        owner_path = stand.fleet.nodes['NL'].state/'owner.json'
        owner = json.loads(owner_path.read_bytes())
        assert owner['fence'] == resumed['fence']
        writer.send_signal(signal.SIGCONT)
        output, error = writer.communicate(timeout=25)
        receipt = json.loads(output)
        assert writer.returncode == 75 and receipt['cause'] == 'ONLINE_STALE_WRITER', (receipt, error.decode())
        assert json.loads(owner_path.read_bytes())['fence'] == resumed['fence']
        controller.send_signal(signal.SIGCONT)
        assert controller.wait(timeout=90) == 0
        code, commit = stand.run('resume')
        assert code == 0 and commit['replay'], commit
        final = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
        assert final['plan_sha256'] == origin['plan_sha256'] and final['decision'] == 'COMMIT'
        assert all(request(dict(command='show', unit='test-'+slot+'.service'))['state']['NRestarts'] == '0' for slot in ('NL', 'NL2'))
        observations.update(outcome='STALE_RPC_WRITER_REJECTED_SAME_COMMIT', stale=receipt,
                            current_fence=resumed['fence'], plan_sha256=origin['plan_sha256'], commit=commit)
    finally:
        for process in (writer, controller):
            if process and process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        stand.close()
        save_evidence(stand, 'stale-rpc-writer', observations)


def test_receipt_from_killed_gateway_cannot_complete_online_commit(online_package, core_driver, tmp_path):
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    observations = {}
    try:
        stand.start()
        stand.rpc_fault('NL', 'publish', 'stale-runtime')
        code, result = stand.run('online')
        observations['online'] = result
        observations['replacement'] = json.loads((stand.configs['NL'].parent/'rpc-runtime-replaced.json').read_bytes())
        assert code == 75 and result['result'] == 'ONLINE_EMERGENCY_REQUIRED', result
        assert result['decision'] == 'COMMIT' and result['last_cause'] == 'ONLINE_RUNTIME_REPLACED', result
        code, required = stand.run('emergency')
        assert code == 75 and required['result'] == 'EMERGENCY_APPROVAL_REQUIRED', required
        code, recovered = stand.run('emergency', approved(stand, required))
        assert code == 0 and recovered['result'] == 'EMERGENCY_RECOVERED', recovered
        clients = {slot: stand.client(slot, 2) for slot in ('NL', 'NL2')}
        for slot, client in clients.items():
            assert client.wait(timeout=40) == 0, (tmp_path/(slot+'-client.log')).read_text()
        observations.update(outcome='DEAD_PROCESS_RECEIPT_EMERGENCY_HANDOFF', recovered=recovered,
                            traffic='new-sessions-only-DNS-verified-HTTPS')
    finally:
        stand.close()
        save_evidence(stand, 'dead-process-receipt', observations)


def test_dead_gateway_is_restarted_only_by_approved_recovery(online_package, core_driver, tmp_path):
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    observations = {}
    try:
        stand.start()
        origin = kill_at(stand, 'online', 'ONLINE_COMMIT_DECIDED')
        before = request(dict(command='show', unit='test-NL2.service'))['state']
        dead = request(dict(command='kill', unit='test-NL2.service'))
        assert dead['returncode'] == -9 and dead['state']['MainPID'] == '0'
        assert dead['state']['ActiveState'] == dead['state']['SubState'] == 'failed'
        assert not (tmp_path/'NL2-config/reader.sock').exists()
        code, result = stand.run('resume')
        observations['online'] = result
        assert code == 75 and result['result'] == 'ONLINE_EMERGENCY_REQUIRED' and result['last_cause'] == 'ONLINE_READER_STOPPED', result
        code, required = stand.run('emergency')
        assert code == 75 and required['result'] == 'EMERGENCY_APPROVAL_REQUIRED', required
        assert request(dict(command='show', unit='test-NL2.service'))['state']['MainPID'] == '0'
        code, result = stand.run('emergency', approved(stand, required))
        assert code == 0 and result['result'] == 'EMERGENCY_RECOVERED', result
        after = request(dict(command='show', unit='test-NL2.service'))['state']
        assert after['MainPID'] != before['MainPID'] and after['InvocationID'] != before['InvocationID'] and after['NRestarts'] == '1'
        clients = {slot: stand.client(slot, 2) for slot in ('NL', 'NL2')}
        for slot, client in clients.items():
            assert client.wait(timeout=40) == 0, (tmp_path/(slot+'-client.log')).read_text()
        final = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
        assert package.digest(package.encode(final['online_parent']['plan'])) == origin['plan_sha256']
        observations.update(outcome='DEAD_GATEWAY_APPROVAL_ONLY_RESTART', before=before, dead=dead, after=after,
                            recovery=result, traffic='new-sessions-only-DNS-verified-HTTPS')
    finally:
        stand.close()
        save_evidence(stand, 'gateway-killed-without-manual-restart', observations)


def test_corrupt_confirmation_blocks_delivery_then_resumes_same_commit(online_package, core_driver, tmp_path):
    stand = CoreStand(tmp_path, online_package[3], core_driver)
    observations = {}
    try:
        stand.start()
        stand.rpc_fault('NL2', 'confirm', 'wrong-slot')
        code, result = stand.run('online')
        assert code == 75 and result['result'] == 'ONLINE_RECOVERY_REQUIRED' and result['last_cause'] == 'ONLINE_RUNTIME_CONFIRMATION', result
        assert not (stand.fleet.nodes['RU'].live/'online-delivery.json').exists()
        origin = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
        code, recovered = stand.run('resume')
        assert code == 0 and recovered['result'] == 'COMMITTED', recovered
        final = json.loads((tmp_path/'coordinator/transaction.json').read_bytes())
        assert final['decision'] == origin['decision'] == 'COMMIT' and final['plan_sha256'] == origin['plan_sha256']
        observations.update(outcome='CORRUPT_CONFIRMATION_BLOCKED_BEFORE_DELIVERY', blocked=result, recovered=recovered)
    finally:
        stand.close()
        save_evidence(stand, 'corrupt-runtime-confirmation', observations)
