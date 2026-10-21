"""Read-only remote postflight, immutable evidence validation and private kit."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import tarfile
from prepare import ROOT, BASE, WORK, SOURCE, FIX, digest, patch_file
from run import production_state, ssh, rows


def main():
    build=json.loads((WORK/'build.json').read_text())
    parent=json.loads((BASE/'build.json').read_text())
    assert all(digest(SOURCE/name)==value for name,value in build['source_inventory'].items())
    assert all(digest(BASE/'source'/name)==value for name,value in parent['source_inventory'].items())
    assert digest(WORK/'telemost-capacity')==build['binary_sha256']
    assert digest(BASE/'telemost-capacity')==parent['binary_sha256']
    reservations=sorted(WORK.glob('*/reservation.json'),key=lambda path:path.stat().st_mtime)
    assert reservations
    first=json.loads(reservations[0].read_text())['production_before']
    expected=[]; failures=[]; traces={}; charged=0; source=0
    for path in reservations:
        directory=path.parent;reservation=json.loads(path.read_text());result=json.loads((directory/'phase-result.json').read_text())
        assert reservation['production_before']==first and result['production_after']==first
        assert result['production_equal'] and result['isolated_identities_removed']
        assert digest(directory/'telemost-capacity')==reservation['binary_sha256']
        assert reservation['binary_sha256']==(json.loads((WORK/'build.json.v1').read_text())['binary_sha256'] if directory.name=='CA1' else build['binary_sha256'])
        assert json.loads((directory/'cleanup.json').read_text())['stage_removed']
        assert not any((directory/name).exists() for name in ['room.input','family.json','isolated-identities'])
        source+=reservation['application_reserved'];charged+=result['wire_charged']
        if result['error']:failures.append(dict(phase=directory.name,error=result['error']))
        traces[directory.name]={}
        for side,prefix in [('client',''),('server','server-')]:
            events=rows(directory/(prefix+'peer.jsonl'))
            final=next((row for row in events if row.get('event')=='media_trace_end'),None)
            assert final and final['overflow']==0,(directory.name,side,'trace incomplete')
            assert final['policy']==reservation['config']['MediaPolicy']
            assert any(row.get('event')=='summary' and row.get('stats',{}).get('PublisherState')=='closed' for row in events),(directory.name,side,'not closed')
            snapshots=[row['transport']['lab_wire'] for row in events if 'lab_wire' in row.get('transport',{})]
            assert snapshots and not any(row['stopped'] for row in snapshots)
            assert not any(token in (directory/(prefix+'peer.jsonl')).read_text() for token in ['PRIVATE KEY-----','OAuth ','https://telemost.yandex.ru/j/'])
            traces[directory.name][side]=final
        expected.append(directory.name)
    assert source<=128*1024**2 and charged<=256*1024**2
    assert all((WORK/name/'phase-result.json').exists() for name in ['CA2','CB1','CB2','CA3','RA1','RB1','RB2','RA2'])
    local=[];collectors=[]
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:executable=os.readlink(process/'exe')
        except (OSError,PermissionError):continue
        if 'mesh-capacity-phase3-20261020/' in executable and executable.endswith('telemost-capacity'):local.append(int(process.name))
        try:command=(process/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        except OSError:continue
        if 'mesh_capacity_phase3/worker.py' in command and 'mesh-capacity-phase3-20261020/' in command:collectors.append(int(process.name))
    assert not local and not collectors
    remote=json.loads(ssh('186.246.45.246', '''import json,os,subprocess
from pathlib import Path
stages=[str(path) for path in Path('/opt/apps/family_connect').glob('capacity3-20261020-*')]
peers=[];collectors=[]
for process in Path('/proc').iterdir():
 if not process.name.isdigit() or int(process.name)==os.getpid():continue
 try:exe=os.readlink(process/'exe')
 except OSError:continue
 if '/capacity3-20261020-' in exe and exe.endswith('/telemost-capacity'):peers.append(int(process.name))
 try:command=(process/'cmdline').read_bytes().replace(b'\\0',b' ').decode(errors='replace')
 except OSError:continue
 if '/capacity3-20261020-' in command and '/worker.py' in command:collectors.append(int(process.name))
units=subprocess.check_output(['systemctl','list-units','--all','--no-legend','--plain','family-connect-capacity3-20261020-*'],text=True).strip()
print(json.dumps(dict(stages=stages,peers=peers,units=units,collectors=collectors)))
'''))
    assert not remote['stages'] and not remote['peers'] and not remote['units'] and not remote['collectors']
    after=production_state();assert after==first
    summary=json.loads((WORK/'summary.json').read_text())
    addresses=sorted({candidate['remote']['ip'] for phase in summary['phases'].values() for candidate in phase['endpoints']['client'].get('selected_paths',[]) if candidate.get('remote',{}).get('ip')})
    routes={address:json.loads(subprocess.check_output(['ip','-j','route','get',address],text=True,timeout=5)) for address in addresses}
    networks={}
    for path in reservations:
        network=json.loads((path.parent/'client-network.json').read_text())
        networks[path.parent.name]=dict(addresses=[dict(name=item['ifname'],ipv4=[address['local'] for address in item.get('addr_info',[]) if address['family']=='inet']) for item in network['addresses']],routes=network['routes'],rules=network['rules'])
    stable_network=all(value==next(iter(networks.values())) for value in networks.values())
    verification=dict(status='COMPLETED_LAB_ONLY_NO_PRODUCT_ADMISSION',utc=datetime.datetime.now(datetime.UTC).isoformat(),phases=expected,failures=failures,source_reserved=source,conservative_outgoing_media_charged=charged,production_before=first,production_after=after,production_equal=True,local_peers=local,remote=remote,trace_completeness=traces,parent_build_sha256=digest(BASE/'build.json'),parent_binary_sha256=digest(BASE/'telemost-capacity'),parent_kit_sha256=digest(BASE/'mesh-capacity-kit.tar.gz'),build_sha256=digest(WORK/'build.json'),fixture_inventory={str(path.relative_to(ROOT)):digest(path) for path in FIX.iterdir() if path.is_file()},provider_metadata_deletion='not supported by reused workflow; normal media session closure verified')
    verification.update(local_collectors=collectors,client_network_equal=stable_network,client_network_signatures=networks,postflight_selected_SFU_routes=routes,source_manifest_by_binary={build['binary_sha256']:'build.json',json.loads((WORK/'build.json.v1').read_text())['binary_sha256']:'build.json.v1'})
    patch_file(WORK/'verification.json',json.dumps(verification,indent=2))
    archive=WORK/'mesh-capacity-phase3-kit.tar.gz'
    assert not archive.exists()
    with tarfile.open(archive,'w:gz') as bundle:
        for path in sorted(WORK.rglob('*')):
            if not path.is_file() or path==archive or path.name in ['kit.json','final-validation.json']:continue
            if path.name=='telemost-capacity' and path.parent!=WORK:continue
            if '__pycache__' in path.parts:continue
            bundle.add(path,arcname=str(path.relative_to(WORK)),recursive=False)
        for path in sorted(FIX.iterdir()):
            if path.is_file():bundle.add(path,arcname='operator/'+path.name,recursive=False)
    patch_file(WORK/'kit.json',json.dumps(dict(file=archive.name,sha256=digest(archive),bytes=archive.stat().st_size),indent=2))
    print(json.dumps(dict(status=verification['status'],phases=len(expected),source_MiB=source/1024**2,wire_MiB=charged/1024**2,production_equal=True,kit_sha256=digest(archive))))


if __name__=='__main__':main()
