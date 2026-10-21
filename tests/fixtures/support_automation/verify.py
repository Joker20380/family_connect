"""Read-only support98 verification using existing identity and journal readers."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'state-client-build/support-automation-20261021'
sys.path.insert(0, str(ROOT))
from scripts.owner_android_support import save


def remote(host, code, interpreter='python3 -B'):
    result = subprocess.run(
        ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
         '-o', 'ConnectTimeout=8', 'root@' + host, interpreter + ' -'],
        input=code, text=True, capture_output=True, timeout=40)
    if result.returncode or len(result.stdout) > 1024 * 1024:
        raise RuntimeError('Read-only remote observation failed; no state change attempted')
    return json.loads(result.stdout)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True, type=Path)
    parser.add_argument('--readback', required=True, type=Path)
    parser.add_argument('--since', required=True)
    parser.add_argument('--until')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', args.since)
    datetime.strptime(args.since, '%Y-%m-%dT%H:%M:%SZ')
    if args.until:
        datetime.strptime(args.until, '%Y-%m-%dT%H:%M:%SZ')
        assert args.until > args.since
    phone = json.loads(args.snapshot.read_text())
    readback = json.loads(args.readback.read_text())
    tag = phone['restricted_session']['session_tag']
    assert re.fullmatch('[0-9a-f]{64}', tag)
    version = phone['version_code']
    assert version == readback['phone']['code'] and version in (98, 99)
    original = ROOT / 'state-client-build/beta87-product-fix-20261019/identity_readback88.py'
    syntax = ast.parse(original.read_text())
    code = next(ast.literal_eval(node.value) for node in syntax.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'remote' for target in node.targets))
    readiness_key = 'beta' + str(version) + '_readiness'
    code = code.replace("version_code')=88", "version_code')=" + str(version)).replace('beta88_readiness', readiness_key)
    identity = remote('185.251.89.19', code)
    reference = json.loads((ROOT / 'state-client-build/speed-candidate-20261021/identity-original.json').read_text())
    identity_preserved = all(identity[key] == reference[key] for key in
                             ('identity_bindings_sha256', 'support_id_sha256', 'owner_record_count'))
    journal_path = ROOT / 'tests/fixtures/queue_retry/journal.py'
    journal_source = journal_path.read_text()
    function = next(node for node in ast.parse(journal_source).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'reassemble')
    parameters = dict(tag=tag, invocation=readback['gateway']['state']['InvocationID'], since=args.since, until=args.until)
    code = 'import json\n' + ast.get_source_segment(journal_source, function) + '\n'
    code += 'parameters = ' + repr(parameters) + '\n' + '''
import subprocess
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
assert state['ActiveState']=='active' and state['InvocationID']==parameters['invocation']
command=['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','-o','json','-n','4000','_SYSTEMD_INVOCATION_ID='+parameters['invocation'],'--since',parameters['since']]
if parameters['until']: command.extend(['--until',parameters['until']])
raw=subprocess.check_output(command,timeout=20)
assert len(raw)<32*1024*1024
rows,errors=reassemble(raw.decode().splitlines())
selected=[]
latest=None
for row in rows:
 try: message=json.loads(row['MESSAGE'])
 except (ValueError,KeyError): continue
 diagnostic=message.get('diagnostic',{})
 if message.get('event') in ('session_profile','session_terminal') and diagnostic.get('session_tag')==parameters['tag']:
  selected.append(dict(journal_epoch_us=row['__REALTIME_TIMESTAMP'],**message))
 trace=message.get('trace',{})
 if message.get('event')=='restricted_trace' and trace.get('session_tag')==parameters['tag']:
  latest=dict(journal_epoch_us=row['__REALTIME_TIMESTAMP'],**trace)
print(json.dumps(dict(records=selected,latest_trace=latest,parser_errors=errors,input_bytes=len(raw),state=state,selection='last4000 entries exact invocation and session; bounded parser; absence is not zero',since_utc=parameters['since'],until_utc=parameters['until'])))
'''
    gateway = remote('186.246.45.246', code)
    artifact = '/opt/apps/family_connect/friends-access/support-21d64558e542ff6ad80fb9b13799fbcb333167ffb5a79ec841e7c94dc65d71fa.pyz'
    code = 'import sys,json,time,subprocess,hashlib\nfrom pathlib import Path\n'
    code += 'sys.path.insert(0,' + repr(artifact) + ')\n'
    code += 'from control.friends.diagnostics import read\n'
    code += 'report=read(Path("/opt/apps/family_connect/friends-access/diagnostics.sqlite"),' + repr(phone['device_support_id']) + ',int(time.time()))\n'
    code += '''
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-friends-http-candidate.service','-p','MainPID,InvocationID,ActiveState,ExecStart'],text=True).splitlines())
print(json.dumps(dict(report=report,state=state,artifact_sha256=hashlib.sha256(Path(sys.path[0]).read_bytes()).hexdigest())))
'''
    online = remote('185.251.89.19', code, '/opt/apps/family_connect/friends-access/venv/bin/python -I')
    result = dict(utc=datetime.now(timezone.utc).isoformat(), read_only=True,
                  identity=identity, identity_preserved=identity_preserved,
                  gateway=gateway, online=online,
                  inputs_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (args.snapshot, args.readback, journal_path)})
    save(args.output, result)
    safe_records = [dict(event=row['event'], **{key: row['diagnostic'].get(key) for key in
                    ('session_tag','speed_profile','reliable_limits','mux_profile','mux_window','protocol_errors','terminal_reason')})
                    for row in gateway['records']]
    print(json.dumps(dict(identity_preserved=identity_preserved, revoked=identity['owner_revoked'],
                          readiness=identity.get(readiness_key), gateway=safe_records,
                          parser_errors=gateway['parser_errors'], online=online['report'])))


if __name__ == '__main__':
    main()
