import base64
import copy
import json
import os
from pathlib import Path
import subprocess
import time

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

from test_multi_gateway_renewal import make_fleet, profiles
from test_activated_maintenance import atomic, canonical, proof
from control.friends.restricted import utc
from credential_renewal import VALIDITY
from online_reader import RuntimeReader


@pytest.mark.skipif(os.environ.get('FC_ONLINE_STAND_RUN') != '1', reason='explicit isolated 17-minute native stand')
def test_real_online_publication_two_nodes(tmp_path, monkeypatch):
    fleet = make_fleet(tmp_path, now=int(time.time()))
    old_bound = int(time.time())+500
    issuer = x509.load_pem_x509_certificate(profiles(fleet)['NL']['authority'].encode())
    crl = (x509.CertificateRevocationListBuilder().issuer_name(issuer.subject)
        .last_update(utc(int(time.time())-5)).next_update(utc(old_bound))
        .add_extension(x509.CRLNumber(1),False).sign(fleet.service.signing_key,None).public_bytes(Encoding.PEM))
    atomic(fleet.nodes['RU'].live/'revocations.pem',crl)
    for slot in ('NL','NL2'):
        profile = profiles(fleet)[slot]
        leaf = x509.load_pem_x509_certificate(profile['certificate'].encode())
        builder = (x509.CertificateBuilder().subject_name(leaf.subject).issuer_name(leaf.issuer)
            .public_key(leaf.public_key()).serial_number(leaf.serial_number).not_valid_before(leaf.not_valid_before_utc)
            .not_valid_after(utc(old_bound)))
        for extension in leaf.extensions:
            value = extension.value
            if isinstance(value,x509.SubjectAlternativeName):
                value = x509.SubjectAlternativeName([item for item in value if not isinstance(item,x509.DNSName)] +
                                                   [x509.DNSName('gateway.family-connect.test')])
            builder = builder.add_extension(value,extension.critical)
        profile.update(certificate=builder.sign(fleet.service.signing_key,None).public_bytes(Encoding.PEM).decode(),revocations=crl.decode())
        atomic(fleet.nodes[slot].live/'gateway.json',canonical(profile))
        fleet.nodes[slot].online_reader = RuntimeReader(tmp_path/(slot+'.sock'))
    for node in fleet.nodes.values():
        node.clock = time.time
        node.online_qualification = True
    fleet.controller.clock = time.time
    fleet.service.access.clock = time.time
    for node in fleet.controller.nodes.values():
        node.timeout_seconds = 1
    monkeypatch.setitem(VALIDITY,'leaf',1000)
    monkeypatch.setitem(VALIDITY,'crl',1000)
    services = {'NL':fleet.service,'NL2':copy.copy(fleet.service)}
    secondary = fleet.nodes['RU'].live/'gateways'/'nl-amsterdam-2'
    services['NL2'].manifest = json.loads((secondary/'issuer.json').read_bytes())
    services['NL2'].seed_source = lambda: (secondary/'directory.json').read_bytes()
    def publish_delivery():
        for slot, service in services.items():
            response = service.fetch(proof(service,fleet.device))
            atomic(tmp_path/(slot+'-delivery.json'),canonical(dict(response=response,
                identity=base64.b64encode(fleet.device._identity.get_private_key()).decode(),
                anchor=base64.b64encode(fleet.service.anchor).decode())))
    publish_delivery()
    for service in services.values():
        service.publication_source = lambda: ((fleet.nodes['RU'].live/'online-delivery.json').read_bytes()
            if (fleet.nodes['RU'].live/'online-delivery.json').exists() else None)
    environment = dict(os.environ, FC_ONLINE_STAND=str(tmp_path))
    log = tmp_path/'native.log'
    with log.open('w') as output:
        command = [os.environ['FC_NATIVE_TEST'], '-test.run=^TestOnlinePublicationStand$', '-test.timeout=23m', '-test.v']
        process = subprocess.Popen(command,cwd=Path(__file__).resolve().parents[1]/'carrier',env=environment,stdout=output,stderr=subprocess.STDOUT)
        def wait(suffix, seconds):
            deadline = time.monotonic()+seconds
            while not all((tmp_path/(slot+'-'+suffix+'.json')).exists() for slot in ('NL','NL2')):
                assert process.poll() is None, log.read_text()
                assert time.monotonic()<deadline, 'stand timeout '+suffix
                time.sleep(.1)
        try:
            wait('started',60)
            for generation in (1,2):
                result = fleet.controller.run_online('test-native-online-generation-'+str(generation),schedule_seconds=0)
                assert result['result']=='COMMITTED',result
                atomic(tmp_path/('controller-'+str(generation)+'.json'),canonical(result))
                publish_delivery()
                wait('generation-'+str(generation),30)
                if generation==1:
                    wait('crossed',510)
            wait('finished',1010)
            assert process.wait(timeout=30)==0,log.read_text()
            assert all(not node.barrier.stopped() and node.barrier.starts==0 for node in fleet.nodes.values())
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
