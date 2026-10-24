"""Require applied limits on both endpoints before any new metered traffic."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

from observe import ROOT,WORK,remote_observation
from scripts.owner_android_support import snapshot,save


def main():
    os.umask(0o077);parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label');parser.add_argument('--profile',choices=['P0','P1'],required=True)
    parser.add_argument('--gateway-sha256',required=True);args=parser.parse_args()
    assert re.fullmatch('[a-zA-Z0-9-]+',args.label) and re.fullmatch('[0-9a-f]{64}',args.gateway_sha256)
    phone=snapshot('31ce63ba');save(WORK/(args.label+'-gate-phone.json'),phone)
    assert phone['version_code']==100 and phone['state']=='CONNECTED' and phone['vpn_capture_open'] and phone['restricted_readiness']=='READY'
    android=phone['restricted_session'];tag=android['session_tag']
    assert android['terminal_reason']=='NONE' and 'terminal_observed_at_ms' not in android
    gateway=remote_observation(tag,10000);save(WORK/(args.label+'-gate-gateway.json'),gateway)
    assert gateway['binary_sha256']==args.gateway_sha256 and not gateway['parser_errors']
    matching=[row for row in gateway['records'] if row['event']=='session_profile' and row['invocation']==gateway['state']['InvocationID']]
    assert len(matching)==1 and not any(row['event']=='session_terminal' for row in gateway['records'])
    limits=dict(local_send=8,local_receive=16,peer_receive=16,effective_send=8,local_write_completion=False) if args.profile=='P0' else dict(local_send=32,local_receive=32,peer_receive=32,effective_send=32,local_write_completion=False)
    window=65536 if args.profile=='P0' else 131072
    for endpoint in (android,matching[0]['diagnostic']):
        assert endpoint['speed_profile']==args.profile and endpoint['reliable_limits']==limits
        assert endpoint['mux_window']==window and endpoint['mux_profile']==('LEGACY64' if window==65536 else 'CREDIT128')
    source=ROOT/'tests/fixtures/mesh_throughput_trace/measure.py';syntax=ast.parse(source.read_text())
    helpers=[node for node in syntax.body if isinstance(node,ast.FunctionDef) and node.name in ('adb','topology')]
    namespace=dict(subprocess=subprocess,re=re);exec(compile(ast.Module(body=helpers,type_ignores=[]),str(source),'exec'),namespace)
    adb=namespace['adb'];apk=adb('pm path com.familyconnect.app.friends').stdout.strip().removeprefix('package:')
    assert apk.startswith('/data/app/') and '\n' not in apk
    digest=adb('sha256sum '+shlex.quote(apk)).stdout.split()[0]
    gate=dict(observed_epoch=time.time(),profile=args.profile,both_limits_verified=True,limits=limits,mux_window=window,session_tag=tag,topology=namespace['topology'](),apk_sha256=digest,gateway_sha256=args.gateway_sha256,gateway_invocation=gateway['state']['InvocationID'],gateway_pid=gateway['state']['MainPID'],phone_errors=android['protocol_errors'],gateway_startup=matching[0]['diagnostic'],terminal_acceptance=False)
    save(WORK/(args.label+'-gate.json'),gate);print('BOTH_LIMITS_VERIFIED',args.profile,tag)


if __name__=='__main__':main()
