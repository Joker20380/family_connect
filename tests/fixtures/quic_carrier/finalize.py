import datetime
import importlib.util
from lab import *

def normal_network(value):
    if isinstance(value,list):return [normal_network(item) for item in value]
    if isinstance(value,dict):return {key:normal_network(item) for key,item in value.items() if key not in ['valid_life_time','preferred_life_time']}
    return value

spec=importlib.util.spec_from_file_location('host',ROOT/'tests/fixtures/host_compare/run.py');host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
reservations=sorted(WORK.glob('*/reservation.json'))
receipts=[json.loads((path.parent/'phase-result.json').read_text()) for path in reservations]
assert receipts and all(row['isolated_identities_removed'] for row in receipts)
build=json.loads((WORK/'build.json').read_text());assert digest(WORK/'telemost-capacity')==build['binary_sha256'];assert inventory(SOURCE)==build['source_inventory'];assert digest(WORK/'run_phase.py')==build['operator_sha256']
state=host.production_state()
remote=host.ssh('186.246.45.246','''import json,os,subprocess,signal
from pathlib import Path
peers=[];own_journal=[]
for process in Path('/proc').iterdir():
 if not process.name.isdigit():continue
 try:target=os.readlink(process/'exe');args=(process/'cmdline').read_bytes().split(b'\\0')
 except OSError:continue
 if '/quic-20261021-' in target:peers.append(int(process.name))
 if args and args[0]==b'journalctl' and b'family-connect-restricted-bootstrap.service' in args and b'2026-10-21 08:50:00 UTC' in args and b'100' in args:
  own_journal.append(int(process.name));os.kill(int(process.name),signal.SIGTERM)
units=subprocess.check_output(['systemctl','list-units','--all','--no-legend','--plain','family-connect-quic-20261021-*'],text=True,timeout=10).strip()
print(json.dumps(dict(peers=peers,units=units,stages=[str(path) for path in Path('/opt/apps/family_connect').glob('quic-20261021-*')],owned_old_journal_collectors_stopped=own_journal)))''',timeout=25)
cleanup=json.loads(remote);assert not cleanup['peers'] and not cleanup['units'] and not cleanup['stages']
local=[]
for process in Path('/proc').iterdir():
    if not process.name.isdigit():continue
    try:target=os.readlink(process/'exe');arguments=(process/'cmdline').read_bytes().split(b'\0')
    except OSError:continue
    if str(WORK) in target or str(WORK/'worker.py').encode() in arguments:local.append(int(process.name))
assert not local
network={name:json.loads(subprocess.check_output(command,text=True)) for name,command in [('addresses',['ip','-j','address']),('rules',['ip','-j','rule']),('routes',['ip','-j','route'])]}
first=json.loads((WORK/'AO/client-network.json').read_text())
source=sum(json.loads(path.read_text())['application_reserved'] for path in reservations);media=sum(row['wire_charged'] for row in receipts)
assert source<=64*2**20 and media<=128*2**20
save(WORK/'verification.json',dict(utc=datetime.datetime.now(datetime.UTC).isoformat(),phases=len(receipts),source_reserved_live=source,media_charged_live=media,local_tests='separate; no conditional reservation charged as Telemost traffic',production=state,live_epoch_equal_all=all(row['production_after']==state and row['production_equal'] for row in receipts),initial_epoch_equal=state==json.loads((WORK/'production-entry.json').read_text()),external_change_receipt='external-state-change.json',remote_cleanup=cleanup,local_peers=local,network_equivalent=normal_network(network)==normal_network(first),provider_room_metadata_deletion='not claimed; peer/WebSocket closure and owned credentials/processes/stages removed',binary_sha256=build['binary_sha256']))
print(dict(phases=len(receipts),source_mib=source/2**20,media_mib=media/2**20,production_live_equal=all(row['production_after']==state for row in receipts),network_equivalent=normal_network(network)==normal_network(first),cleanup=cleanup))
