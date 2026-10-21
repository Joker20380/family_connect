"""Bounded read-only READY and gateway receipts after a manual owner action."""

import ast
import datetime
import json
import os
import re
import subprocess
import sys
from prepare import ROOT, WORK, digest


def main():
    os.umask(0o077)
    assert len(sys.argv) in (2,3)
    label = sys.argv[1]
    since = sys.argv[2] if len(sys.argv) == 3 else None
    if since is not None:
        assert re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',since)
        datetime.datetime.strptime(since,'%Y-%m-%dT%H:%M:%SZ')
    assert re.fullmatch('[a-z0-9-]+', label)
    destination = WORK / ('observation-' + label + '.json')
    assert not destination.exists()
    readback_path = WORK / (label + '-readback.json')
    readback = json.loads(readback_path.read_text())
    original = ROOT / 'state-client-build/beta87-product-fix-20261019/identity_readback88.py'
    syntax = ast.parse(original.read_text())
    remote = next(ast.literal_eval(node.value) for node in syntax.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'remote' for target in node.targets))
    remote = remote.replace("version_code')=88", "version_code')=97").replace('beta88_readiness', 'beta97_readiness')
    identity = json.loads(subprocess.check_output(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                                                   'root@185.251.89.19', 'python3 -B -'], input=remote, text=True, timeout=30))
    reference = json.loads((WORK / 'identity-original.json').read_text())
    assert all(identity[key] == reference[key] for key in ('identity_bindings_sha256', 'support_id_sha256', 'owner_record_count'))
    assert not identity['owner_revoked']
    parser_path = ROOT / 'tests/fixtures/queue_retry/journal.py'
    parser_text = parser_path.read_text()
    parser_node = next(node for node in ast.parse(parser_text).body if isinstance(node, ast.FunctionDef) and node.name == 'reassemble')
    remote = 'import json\n' + ast.get_source_segment(parser_text, parser_node) + '\n' + r'''
import hashlib,subprocess
from pathlib import Path
invocation=EXPECTED_INVOCATION
since=EXPECTED_SINCE
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','family-connect-restricted-bootstrap.service','-p','MainPID,InvocationID,ActiveState'],text=True).splitlines())
assert state['ActiveState']=='active' and state['InvocationID']==invocation
command=['journalctl','--file=/var/log/journal/*/system.journal','--no-pager','--all','-o','json','-n','4000','_SYSTEMD_INVOCATION_ID='+invocation]
if since is not None:command.extend(['--since',since])
raw=subprocess.check_output(command,timeout=20)
assert len(raw)<32*1024*1024
rows,errors=reassemble(raw.decode().splitlines())
selected=[]
latest_trace={}
for row in rows:
 try:message=json.loads(row['MESSAGE'])
 except (ValueError,KeyError):continue
 if message.get('event') in ('session_profile','session_terminal'):
  selected.append(dict(journal_epoch_us=row['__REALTIME_TIMESTAMP'],**message))
 if message.get('event')=='restricted_trace':
  trace=message.get('trace',{})
  tag=trace.get('session_tag')
  if isinstance(tag,str) and len(tag)==64:
   latest_trace[tag]=dict(journal_epoch_us=row['__REALTIME_TIMESTAMP'],**trace)
print(json.dumps(dict(records=selected,latest_trace=latest_trace,parser_errors=errors,input_bytes=len(raw),state=state,selection='last4000 entries exact invocation; bounded continuation parser',since_utc=since)))
'''.replace('EXPECTED_INVOCATION', repr(readback['gateway']['state']['InvocationID'])).replace('EXPECTED_SINCE',repr(since))
    compile(remote, '<gateway-receipts>', 'exec')
    gateway = json.loads(subprocess.check_output(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                                                  'root@186.246.45.246', 'python3 -B -'], input=remote, text=True, timeout=30))
    record = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), identity=identity, gateway=gateway,
                  readback_sha256=digest(readback_path), parser_sha256=digest(parser_path), read_only=True)
    with destination.open('x') as output:
        json.dump(record, output, indent=2)
    projected = []
    for row in gateway['records']:
        diagnostic = row.get('diagnostic', {})
        projected.append(dict(event=row['event'], utc=row.get('utc'), **{key: diagnostic.get(key) for key in
            ('session_tag', 'speed_profile', 'reliable_limits', 'mux_profile', 'mux_window', 'protocol_errors', 'terminal_reason')}))
    print(json.dumps(dict(utc=record['utc'], identity_preserved=True, ready=identity.get('beta97_readiness'),
                          gateway_receipts=projected, parser_errors=gateway['parser_errors'], android_applied_receipt='EXPORT_REQUIRED')))


if __name__ == '__main__':
    main()
