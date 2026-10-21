import datetime
import importlib.util
import json
import os
import subprocess
from lab import ROOT, WORK, SOURCE, save, digest, inventory


def normal_network(value):
    if isinstance(value,list):return [normal_network(item) for item in value]
    if isinstance(value,dict):return {key:normal_network(item) for key,item in value.items() if key not in ['valid_life_time','preferred_life_time']}
    return value


def main():
    reservations=sorted(WORK.glob('*/reservation.json'))
    assert len(reservations)==12
    receipts=[json.loads((path.parent/'phase-result.json').read_text()) for path in reservations]
    assert all(row['isolated_identities_removed'] for row in receipts)
    build=json.loads((WORK/'build.json').read_text())
    assert digest(WORK/'telemost-capacity')==build['binary_sha256']
    assert inventory(SOURCE)==build['source_inventory']
    assert digest(WORK/'run_phase.py')==build['operator_sha256']
    spec=importlib.util.spec_from_file_location('host_operator',ROOT/'tests/fixtures/host_compare/run.py')
    host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    production=host.production_state()
    remote=host.ssh('186.246.45.246','''import json,os,subprocess
from pathlib import Path
peers=[]
for process in Path('/proc').iterdir():
 if not process.name.isdigit():continue
 try:target=os.readlink(process/'exe')
 except OSError:continue
 if '/fec-20261021-' in target:peers.append(int(process.name))
units=subprocess.check_output(['systemctl','list-units','--all','--no-legend','--plain','family-connect-fec-20261021-*'],text=True).strip()
print(json.dumps(dict(peers=peers,units=units,stages=[str(path) for path in Path('/opt/apps/family_connect').glob('fec-20261021-*')])))''')
    cleanup=json.loads(remote);assert not any(cleanup.values())
    local=[]
    for process in (ROOT/'/proc').iterdir():
        if not process.name.isdigit():continue
        try:target=os.readlink(process/'exe');arguments=(process/'cmdline').read_bytes().split(b'\0')
        except OSError:continue
        if str(WORK) in target or str(WORK/'worker.py').encode() in arguments:local.append(int(process.name))
    assert not local
    network={}
    for name,command in [('addresses',['ip','-j','address']),('rules',['ip','-j','rule']),('routes',['ip','-j','route'])]:network[name]=json.loads(subprocess.check_output(command,text=True))
    first=json.loads((WORK/'CL/client-network.json').read_text())
    source=sum(json.loads(path.read_text())['application_reserved'] for path in reservations)
    media=sum(row['wire_charged'] for row in receipts)
    assert source+64*1024**2<=128*1024**2 and media+128*1024**2<=256*1024**2
    save(WORK/'verification.json',dict(utc=datetime.datetime.now(datetime.UTC).isoformat(),phases=len(receipts),source_reserved_live=source,media_charged_live=media,local_source_reservation=64*1024**2,local_media_reservation=128*1024**2,production=production,production_equal_all=all(row['production_after']==production and row['production_equal'] for row in receipts),remote_cleanup=cleanup,local_peers=local,network_raw_equal=network==first,network_equivalent=normal_network(network)==normal_network(first),network_after=network,provider_room_metadata_deletion='not claimed; owned peers normally closed, identifiers/credentials/stages removed',binary_sha256=build['binary_sha256']))
    print(dict(phases=len(receipts),live_source_mib=source/2**20,live_media_mib=media/2**20,production_equal_all=all(row['production_after']==production for row in receipts),network_equivalent=normal_network(network)==normal_network(first)))


if __name__=='__main__':main()
