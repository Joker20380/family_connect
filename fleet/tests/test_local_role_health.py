import datetime
import base64
import io
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from fleet.contracts import FleetError, canonical, load
from fleet.private_files import write_private
from fleet.rehearsal_templates import UNIT_NAMES
from fleet.role_config import PORTS
from fleet.tests.test_permit import authority
from fleet.tests.test_role_runtime import runtime


@pytest.fixture
def healthy(runtime,monkeypatch):
    target=runtime.manifest['bundle_id']
    runtime.stage(target)
    runtime.configure(target)
    runtime.switch(target)
    config=runtime.verify_configuration(target)
    processes={name:100+index for index,name in enumerate(UNIT_NAMES)}
    for role,binary in (('awg','amneziawg-go'),('tcp','xray'),('mesh','gateway')):
        directory=runtime.root/'proc'/str(processes[role])
        directory.mkdir(parents=True)
        (directory/'exe').write_bytes(runtime.contents['bin/'+binary])
        unit=(runtime.configuration/target/'units'/('fc-rehearsal-'+role+'.service')).read_text()
        argv=next(line.removeprefix('ExecStart=').split() for line in unit.splitlines() if line.startswith('ExecStart='))
        (directory/'cmdline').write_bytes(b'\x00'.join(argument.encode() for argument in argv)+b'\x00')
    awg=load((runtime.directory/'slots/awg-material').read_bytes())
    peer=awg['peer_public_key']
    public=base64.b64encode(X25519PrivateKey.from_private_bytes(base64.b64decode(awg['server_private_key'])).public_key().public_bytes(
        serialization.Encoding.Raw,serialization.PublicFormat.Raw))
    original=runtime.executor.run
    fault={'kind':None}
    def execute(argv,*,input=None,check=True):
        output=None
        if argv[:2]==['systemctl','show']:
            name=argv[2].removeprefix('fc-rehearsal-').removesuffix('.service')
            output=('ActiveState=active\nSubState=running\nNRestarts='+('3' if fault['kind']=='restarts' else '0')+'\nMainPID='+str(processes[name])+'\n').encode()
        if argv[:2]==['ss','-H']:
            output=('\n'.join('udp LISTEN 0 128 *:'+str(port)+' *:* users:(("fixture",pid='+str(processes[name])+',fd=3))' for name,port in PORTS.items())).encode()
            if fault['kind']=='listener':
                output=output.replace(b'pid=',b'wrong=')
        if argv[:4]==['ip','-j','address','show']:
            output=canonical([dict(mtu=1280,addr_info=[dict(local='10.203.217.1',prefixlen=30)])])
        if argv[0].endswith('/bin/awg') and argv[1:3]==['show','fcrh0']:
            output={'peers':peer.encode(),'public-key':public,'listen-port':b'51827','allowed-ips':(peer+' 10.203.217.2/32').encode()}[argv[3]]
            if fault['kind']=='peer' and argv[3]=='peers':
                output+=b' '+peer.encode()
            if fault['kind']=='server-key' and argv[3]=='public-key':
                output=peer.encode()
        if output is not None:
            return SimpleNamespace(returncode=0,stdout=output,stderr=b'')
        return original(argv,input=input,check=check)
    runtime.executor.run=execute
    iso=lambda value:datetime.datetime.fromtimestamp(value,datetime.timezone.utc).isoformat()
    ready=dict(version=1,family=config['mesh']['family'],issued_at=iso(1000),expires_at=iso(15400),
               seeds=[dict(transport='telemost-webrtc',join_url='https://telemost.yandex.ru/j/offline-fixture',gateway=config['mesh']['gateway'])])
    write_private(runtime.run_directory/'ready.json',canonical(ready))
    observations=dict(instance_id=runtime.permit['instance_id'],bundle_id=target,material_expires_at=config['material_expires_at'],observed_at=1001)
    monkeypatch.setattr('urllib.request.build_opener',lambda *args:SimpleNamespace(open=lambda *args,**kwargs:io.BytesIO(canonical(observations))))
    return runtime,fault,processes,observations


def test_local_health_never_asserts_external_pass(healthy):
    runtime,fault,processes,observations=healthy
    result=runtime.accept(runtime.manifest['bundle_id'])
    assert result['scope']=='LOCAL_NODE_HEALTH_ONLY' and result['external_acceptance']=='NOT_ASSERTED_BY_NODE'
    assert b'join_url' not in canonical(result) and b'offline-fixture' not in canonical(result)


@pytest.mark.parametrize('failure',['restarts','listener','peer','server-key','binary','argv','expired-monitor','expired-material'])
def test_each_local_health_drift_rejects(healthy,failure):
    runtime,fault,processes,observations=healthy
    fault['kind']=failure
    if failure=='binary':
        (runtime.root/'proc'/str(processes['mesh'])/'exe').write_bytes(b'wrong native')
    if failure=='argv':
        (runtime.root/'proc'/str(processes['tcp'])/'cmdline').write_bytes(b'wrong argv')
    if failure=='expired-monitor':
        observations['observed_at']=900
    if failure=='expired-material':
        runtime.clock=lambda:15400
    with pytest.raises(FleetError):
        runtime.accept(runtime.manifest['bundle_id'])
