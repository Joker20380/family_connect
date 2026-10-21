"""Read back restored b9/94 and issue one bounded 64KiB phone control."""

import ast
import json
import os
import sys

import measure
from prepare import ROOT, WORK, APK, GATEWAY, digest


def main():
    os.umask(0o077)
    helper = ROOT/'tests/fixtures/queue_retry/readback.py'
    assert digest(helper) == '85d5b502f3e46779c3be16bdb064e7068f3240c89a13fece3ce769ae3a3cb2c1'
    source = helper.read_text().replace("phone['code']==90", "phone['code']==94")
    namespace = dict(__name__='mux_credit_readback', __file__=str(helper))
    exec(compile(source, str(helper), 'exec'), namespace)
    namespace.update(WORK=WORK, APK=APK, GATEWAY=GATEWAY)
    sys.argv = [str(helper), 'final']
    namespace['main']()
    target = WORK/'return-control'
    target.mkdir(mode=0o700, exist_ok=False)
    original = ROOT/'tests/fixtures/mesh_throughput_trace/measure.py'
    assert digest(original) == '17e76fb9f3d8c46b5e7e4b5c55fa0f8098b59aef63e0e66c94cbce81b2c2a5ef'
    tree = ast.parse(original.read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('adb', 'topology')]
    request = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'request')
    namespace = dict(vars(measure))
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(original), 'exec'), namespace)
    topology = namespace['topology']()
    remote_root = '/data/local/tmp/fc-mux-credit-return-20261020'
    namespace['adb']('umask 077; mkdir '+remote_root).check_returncode()
    namespace.update(out=target, remote_root=remote_root, stop=measure.threading.Event(),
                     lock=measure.threading.Lock(), requests=[],
                     fields=('http_code', 'http_version', 'ssl_verify_result', 'remote_ip', 'local_port', 'num_connects', 'size_download', 'time_namelookup', 'time_connect', 'time_appconnect', 'time_starttransfer', 'time_total'))
    with (WORK/'traffic-return-reservation.json').open('x') as output:
        json.dump(dict(intended_bytes=65536, no_retries=True), output)
    exec(compile(ast.Module(body=[request], type_ignores=[]), str(original), 'exec'), namespace)
    result = namespace['request']('return-64k', 65536)
    namespace['adb']('rmdir '+remote_root).check_returncode()
    assert topology == namespace['topology']()
    with (target/'summary.json').open('x') as output:
        json.dump(dict(valid=result['valid'], topology=topology, metrics=result['metrics']), output, indent=2)
    assert result['valid']
    print('RESTORED_B9_94_PHONE_CONTROL_PASS')


if __name__ == '__main__':
    main()
