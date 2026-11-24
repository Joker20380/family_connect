"""Exact-Xray RPC boundary experiments, only inside the disposable systemd fixture."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import pwd
import socket
import subprocess
import sys
import threading
import time

sys.path.insert(0, '/rpc/proto')
sys.path.insert(0, '/rpc/lib')
sys.path.insert(0, '/kit/paid-transport.pyz')
import grpc
from app.proxyman.command import command_pb2
from proxy.vless import account_pb2
from control.friends import transport_gateway as module

BINARY = '/opt/apps/family_connect/friends-tcp/xray'
SHA = '4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940'
RPC = '/xray.app.proxyman.command.HandlerService/GetInboundUsers'
COMMAND = [BINARY, 'api', 'inbounduser', '--server=127.0.0.1:18085', '-tag=friends']


def request(channel):
    return channel.unary_unary(RPC,
        request_serializer=command_pb2.GetInboundUserRequest.SerializeToString,
        response_deserializer=command_pb2.GetInboundUserResponse.FromString)


def users(response):
    result = set()
    for user in response.users:
        assert user.account.type == 'xray.proxy.vless.Account'
        account = account_pb2.Account.FromString(user.account.value)
        result.add((account.id, user.email, account.flow))
    assert len(result) == len(response.users)
    return result


def command_case(arguments, seconds=8, spawn_delay=0):
    observation = {}
    original = subprocess.Popen

    class ObservedChild(original):
        def __init__(self, *values, **keywords):
            if spawn_delay:
                time.sleep(spawn_delay)
            super().__init__(*values, **keywords)

        def communicate(self, *values, **keywords):
            try:
                output, errors = super().communicate(*values, **keywords)
                observation['dial_error'] = b'failed to dial' in errors
                observation['rpc_deadline'] = b'DeadlineExceeded' in errors
                return output, errors
            except subprocess.TimeoutExpired as error:
                observation['partial_stdout_bytes'] = len(error.output or b'')
                observation['leader_returncode_at_timeout'] = self.poll()
                raise

    operation = module.Operation(seconds)
    token = module.CURRENT_OPERATION.set(operation)
    module.subprocess.Popen = ObservedChild
    output = None
    started = time.monotonic()
    try:
        with operation.stage('engine_query'):
            output = module.execute(arguments)
        observation['result'] = 'complete'
    except (TimeoutError, subprocess.SubprocessError) as error:
        observation['result'] = type(error).__name__
        observation['failure'] = module.failure_record(error, 'watch')
    finally:
        module.subprocess.Popen = original
        module.CURRENT_OPERATION.reset(token)
    observation.update(duration=time.monotonic()-started, calls=operation.calls)
    return observation, output


def run():
    assert os.geteuid() == 0
    assert hashlib.sha256(Path(BINARY).read_bytes()).hexdigest() == SHA
    result = dict(xray_sha256=SHA, source='d2758a023cd7f4174a5a5fa4ff66e487d4342ba0',
        uid=os.geteuid(), limits=Path('/proc/self/limits').read_text(),
        cgroup=Path('/proc/self/cgroup').read_text(), cases={})
    service = 'family-connect-friends-tcp.service'
    properties = subprocess.check_output(['systemctl', 'show', service, '-p',
        'MainPID,User,MemoryMax,TasksMax,NoNewPrivileges,ProtectSystem,ProtectHome,PrivateTmp,ExecStart,ExecStartPre'], timeout=3).decode()
    properties = dict(line.split('=', 1) for line in properties.splitlines() if '=' in line)
    assert properties['User'] == 'fc-friends' and properties['MemoryMax'] == '268435456'
    assert properties['TasksMax'] == '128' and properties['ProtectSystem'] == 'strict'
    assert properties['NoNewPrivileges'] == 'yes' and 'paid-preflight' in properties['ExecStartPre']
    process = Path('/proc') / properties['MainPID']
    assert BINARY in properties['ExecStart'] and (process/'comm').read_text().strip() == 'xray'
    assert (process/'status').read_text().split('Uid:')[1].split()[0] == str(pwd.getpwnam('fc-friends').pw_uid)
    result['engine_properties'] = properties
    result['engine_executable_evidence'] = 'exact image binary; unit ExecStart and actual main comm/UID; no ptrace capability'
    result['engine_limits'] = (process/'limits').read_text()
    with grpc.insecure_channel('127.0.0.1:18085') as channel:
        call = request(channel)
        started = time.monotonic()
        response = call(command_pb2.GetInboundUserRequest(tag='friends'), timeout=3)
        result['direct_rpc_seconds'] = time.monotonic()-started
        expected = users(response)
        baseline, output = command_case(COMMAND)
        assert baseline['result'] == 'complete'
        actual = {(user['account']['id'], user.get('email', ''), user['account'].get('flow', ''))
            for user in json.loads(output)['users']}
        assert actual == expected and expected
        result['same_rpc_exact_id_email_flow'] = True
        result['cases']['baseline'] = baseline

        expired, _ = command_case(COMMAND, seconds=.2, spawn_delay=.3)
        assert expired['result'] == 'TimeoutError'
        assert not expired['calls'][0]['process']['communicate']['completed']
        assert expired['calls'][0]['process']['reaped']
        result['cases']['spawn_exhausts_operation_before_wait'] = expired

        delayed = '/tmp/query-delay.py'
        Path(delayed).write_text('import os,sys,time\ntime.sleep(.4)\nos.execv(sys.argv[1],sys.argv[1:])\n')
        before_cli, output = command_case([sys.executable, delayed, *COMMAND])
        assert before_cli['result'] == 'complete' and before_cli['duration'] > .4
        result['cases']['synthetic_before_cli_exec'] = before_cli

        unavailable = COMMAND.copy()
        unavailable[3] = '--server=127.0.0.1:18086'
        refused, _ = command_case(unavailable)
        assert refused['result'] == 'CalledProcessError' and refused['dial_error']
        assert 2.8 < refused['duration'] < 4.5
        result['cases']['api_unavailable'] = refused

        listener = socket.socket()
        listener.bind(('127.0.0.1', 18086))
        listener.listen()
        listener.settimeout(5)
        events = {}
        def no_settings():
            connection, _ = listener.accept()
            with connection:
                events['tcp_accepted'] = time.monotonic()
                time.sleep(3.5)
        thread = threading.Thread(target=no_settings)
        thread.start()
        try:
            stalled, _ = command_case(unavailable)
            assert stalled['dial_error'] and events.get('tcp_accepted')
            result['cases']['tcp_connected_no_http2_settings'] = stalled
        finally:
            thread.join(6)
            listener.close()
            assert not thread.is_alive()

        relay_events = []
        def delayed_response(message, context):
            event = dict(request_received=time.monotonic())
            relay_events.append(event)
            response = call(message, timeout=2)
            event['upstream_response_received'] = time.monotonic()
            time.sleep(3.5)
            event['reply_attempt'] = time.monotonic()
            return response
        executor = ThreadPoolExecutor(max_workers=2)
        server = grpc.server(executor)
        server.add_generic_rpc_handlers((grpc.method_handlers_generic_handler(
            'xray.app.proxyman.command.HandlerService', {'GetInboundUsers': grpc.unary_unary_rpc_method_handler(
                delayed_response, request_deserializer=command_pb2.GetInboundUserRequest.FromString,
                response_serializer=command_pb2.GetInboundUserResponse.SerializeToString)}),))
        assert server.add_insecure_port('127.0.0.1:18087')
        server.start()
        try:
            slow = COMMAND.copy()
            slow[3] = '--server=127.0.0.1:18087'
            delayed_reply, _ = command_case(slow)
            assert delayed_reply['rpc_deadline'] and delayed_reply['duration'] < 4.5
            result['cases']['synthetic_response_delay'] = delayed_reply
            with grpc.insecure_channel('127.0.0.1:18087') as delayed_channel:
                try:
                    request(delayed_channel)(command_pb2.GetInboundUserRequest(tag='friends'), timeout=3)
                    raise AssertionError('direct RPC must also expire')
                except grpc.RpcError as error:
                    assert error.code() == grpc.StatusCode.DEADLINE_EXCEEDED
            result['direct_rpc_same_delayed_response'] = 'DEADLINE_EXCEEDED'
        finally:
            server.stop(0).wait(2)
            executor.shutdown(wait=True)
        assert len(relay_events) == 2 and all('upstream_response_received' in event for event in relay_events)
        result['relay_boundaries'] = relay_events

        held = '/tmp/query-held-pipe.py'
        Path(held).write_text('import os,sys,time\nif os.fork()==0:\n time.sleep(6);os._exit(0)\n'
            'os.execv(sys.argv[1],sys.argv[1:])\n')
        blocked, _ = command_case([sys.executable, held, *COMMAND], seconds=1)
        assert blocked['result'] == 'TimeoutExpired'
        assert blocked['partial_stdout_bytes'] > 0 and blocked['leader_returncode_at_timeout'] == 0
        assert blocked['calls'][0]['process']['reaped'] is True
        assert blocked['duration'] < 1.5
        group = blocked['calls'][0]['process']['pid']
        deadline = time.monotonic()+1
        live = []
        while time.monotonic() < deadline:
            live = []
            for path in Path('/proc').glob('[0-9]*/stat'):
                try:
                    fields = path.read_text().rsplit(')', 1)[1].split()
                except FileNotFoundError:
                    continue
                if int(fields[2]) == group and fields[0] != 'Z':
                    live.append(path.parent.name)
            if not live:
                break
            time.sleep(.01)
        assert not live
        blocked['no_live_own_descendants'] = True
        result['cases']['response_received_inherited_pipe_open'] = blocked
    result['result'] = 'PASS'
    return result


if __name__ == '__main__':
    Path('/run/tcp-query-result.json').write_text(json.dumps(run(), indent=2))
