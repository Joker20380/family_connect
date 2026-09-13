"""Conformance of immutable, PUBLIC TEST ONLY inputs against Python reference.

This runner never starts a carrier or invokes a platform VPN backend. Native
runners should consume the same manifest and bytes without regeneration.
"""
import base64
import hashlib
import json
from pathlib import Path

import pytest
import RNS
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from device_identity.device import DeviceIdentity
from provisioning import ack
from provisioning.configuration import ConfigError, ConfigVerifier
from provisioning.envelope import ProvisioningRejected
from provisioning.transaction import ControlJournal, ProvisioningCore

ROOT=Path(__file__).parent/'vectors/control-v1'
MANIFEST=json.loads((ROOT/'manifest.json').read_text())


def device(root=ROOT):
    keys=json.loads((root/'TEST-ONLY-identity.json').read_text())
    assert keys['test_only'] is True
    d=DeviceIdentity(RNS.Identity.from_bytes(base64.b64decode(keys['rns_private_b64'],validate=True)),
        X25519PrivateKey.from_private_bytes(base64.b64decode(keys['wg_private_b64'],validate=True)))
    assert d.public_identity==keys['public_identity_b64']
    assert d.wireguard_public_key==keys['wireguard_public_key'] and d.reference==keys['device_reference']
    return d,base64.b64decode(keys['anchor_b64'],validate=True)


def verify_config(case,root=ROOT):
    d,anchor=device(root)
    verifier=ConfigVerifier(anchor=anchor,device=d,client_version=case['client_version'])
    raw=(root/case['input']).read_bytes()
    if case['expected']['category']!='ACCEPT':
        with pytest.raises(ConfigError) as error:verifier.verify(raw,now=case['now'])
        assert error.value.category==case['expected']['category']
    else:
        verified=verifier.verify(raw,now=case['now'])
        assert verified.digest==case['expected']['envelope_sha256']
        assert verified.state.model_dump(mode='json')==case['expected']['payload']


def verify_ack(case,root=ROOT):
    raw=(root/case['input']).read_bytes()
    if case['expected']['category']=='ACCEPT':assert ack.verify(raw)==case['expected']['body']
    else:
        with pytest.raises(ProvisioningRejected):ack.verify(raw)


def test_corpus_integrity_and_test_key_separation():
    assert MANIFEST['schema_version']==1 and MANIFEST['test_only'] is True
    files=MANIFEST['files']
    assert set(p.name for p in ROOT.iterdir())==set(files)|{'manifest.json'}
    ids=[c['id'] for kind in ('configurations','acknowledgements','transcripts') for c in MANIFEST[kind]]
    assert len(ids)==len(set(ids))
    for name,expected in files.items():
        assert Path(name).name==name and not (ROOT/name).is_symlink()
        raw=(ROOT/name).read_bytes()
        assert len(raw)==expected['size'] and hashlib.sha256(raw).hexdigest()==expected['sha256']
    _,anchor=device()
    production_anchor=base64.b64decode((ROOT.parents[2]/'clients/desktop/update.pub').read_text().strip())
    assert anchor!=production_anchor
    from scripts.package_control import FILES
    assert not any('vectors' in p or 'generate_control_vectors' in p for p in FILES)


@pytest.mark.parametrize('case',MANIFEST['configurations'],ids=lambda c:c['id'])
def test_configuration_vector(case):verify_config(case)


@pytest.mark.parametrize('case',MANIFEST['acknowledgements'],ids=lambda c:c['id'])
def test_ack_vector(case):verify_ack(case)


class Application:
    def __init__(self):self.active='baseline';self.applies=0;self.rollbacks=0;self.health=True
    def snapshot(self,previous=None):return dict(known=[self.active],active=[self.active])
    def apply(self,verified,baseline):self.applies+=1;self.active=verified.digest
    def healthy(self,verified):return self.health
    def rollback(self,staged,previous,baseline):self.rollbacks+=1;self.active=baseline['active'][0]


@pytest.mark.parametrize('transcript',MANIFEST['transcripts'],ids=lambda t:t['id'])
def test_journal_transcript(transcript,tmp_path):
    initial=transcript['initial']
    assert initial['floor']==0 and initial['committed_sha256'] is None and initial['active']=='baseline'
    d,anchor=device();v=ConfigVerifier(anchor=anchor,device=d,client_version=initial['client_version'])
    j=ControlJournal(tmp_path/'journal',v);j.initialize();app=Application()
    core=ProvisioningCore(journal=j,application=app,device=d,clock=lambda:initial['now'])
    by_id={c['id']:c for c in MANIFEST['configurations']}
    def record():
        with j._locked() as directory:return j.read(directory)
    failed_delivery=None
    for step in transcript['steps']:
        op=step['operation'];app.health=step.get('health',True)
        if op in ('receive','crash'):
            raw=(ROOT/by_id[step['input']]['input']).read_bytes()
            if op=='crash':
                original=j._write
                def crash(directory,data):
                    original(directory,data)
                    if data['phase']==step['at_phase']:raise SystemExit('TEST ONLY process death')
                j._write=crash
                try:
                    with pytest.raises(SystemExit):core.receive(raw)
                finally:j._write=original
                result='CRASH'
            else:result=core.receive(raw)
        elif op=='restart-recover':
            j=ControlJournal(tmp_path/'journal',v)
            core=ProvisioningCore(journal=j,application=app,device=d,clock=lambda:initial['now'])
            result=core.recover()
        elif op=='flush':
            before=record()['outbox'];seen=[]
            class Carrier:
                def send_ack(self,raw):seen.append(raw);return step['available']
            result=core.flush_acks(Carrier())
            if result is False:
                assert record()['outbox']==before
                failed_delivery=seen[0]
            elif failed_delivery is not None:assert seen[0]==failed_delivery
            assert (not record()['outbox'])==step['outbox_empty']
        else:raise AssertionError('unknown transcript operation')
        state=record()
        actual=dict(result=result,floor=state['floor'],phase=state['phase'],
            committed_sha256=state['committed']['digest'] if state['committed'] else None,
            applies=app.applies,rollbacks=app.rollbacks,active=app.active)
        assert actual==step['expected']
        if 'error' in step:
            assert ack.verify(base64.b64decode(state['outbox'][-1]))['error']==step['error']


def test_generator_new_directory_only_without_key_file_reads(tmp_path,monkeypatch):
    from generate_control_vectors import generate
    target=tmp_path/'fresh'
    # The generator may write test inputs, but cannot load any key/profile file.
    with monkeypatch.context() as patch:
        def forbidden(*_,**__):raise AssertionError('generator attempted file input')
        patch.setattr(Path,'read_bytes',forbidden);patch.setattr(Path,'read_text',forbidden)
        manifest=generate(target)
        with pytest.raises(FileExistsError):generate(target)
    assert manifest['test_only'] and len(manifest['configurations'])==30
    for case in manifest['configurations']:verify_config(case,target)
    for case in manifest['acknowledgements']:verify_ack(case,target)
