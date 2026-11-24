import io
import json
import os
import sqlite3
import tarfile
from copy import deepcopy
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from control.friends import pseudonyms
from scripts import control_ha_owner_joint as joint
from scripts.control_ha_owner_joint_lab import OwnerLab, LABEL
from scripts import control_ha_owner_runtime as owner
from scripts import control_ha_worker_custody as worker
from scripts.control_ha_import import encoded,digest,import_snapshot
from scripts.referral_postgres_rehearsal import NOW
from tests.test_control_ha_import import repository
from tests.test_control_ha_installed_composite import source,prepared


def sealed_archive(*, mutate=None, extra=False):
    backup=b'PGDMP-fixture-never-restored'
    manifest=dict(purpose=joint.PURPOSE,image=owner.IMAGES['postgres'],excluded_row_tables=joint.EXCLUDED,
        application_dispatch=False,full_recovery=False,metadata_projection='consent-epoch-sequence-status-only',
        dump_sha256=digest(backup),fingerprints={f'table_{number}':dict(rows=0,sha256=digest(b'')) for number in range(37)},
        metadata_floor_rows=1)
    floors=[dict(pseudonym='a'*64,consent_epoch=1,sequence=2,consent='revoked',received_at=3)]
    if mutate:mutate(manifest,floors)
    files={'database.dump':backup,'manifest.json':encoded(manifest),'floors.json':encoded(floors)}
    if extra:files['unexpected']=b'x'
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:') as archive:
        for name,raw in files.items():
            info=tarfile.TarInfo(name);info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
    raw=stream.getvalue();key=os.urandom(32);nonce=os.urandom(12)
    capsule=joint.MAGIC+nonce+AESGCM(key).encrypt(nonce,raw,joint.PURPOSE.encode())
    return capsule,key,dict(ciphertext_sha256=digest(capsule),archive_sha256=digest(raw),source_image=owner.IMAGES['postgres'])


def test_owner_archive_closed_privacy_profile():
    backup,manifest,floors=joint.owner_archive(*sealed_archive())
    assert len(manifest['fingerprints'])==37 and len(floors)==1 and backup.startswith(b'PGDMP')


@pytest.mark.parametrize('field',('image','label','network'))
def test_panel_lab_refuses_wrong_container_boundary(field):
    lab=OwnerLab.__new__(OwnerLab);lab.container='owned-id';lab.token='expected'
    info=dict(Image=owner.IMAGES['postgres'],Config=dict(Labels={LABEL:'expected'}),HostConfig=dict(NetworkMode='none'))
    if field=='image':info['Image']='unexpected'
    elif field=='label':info['Config']['Labels'][LABEL]='unexpected'
    else:info['HostConfig']['NetworkMode']='host'
    lab.docker=lambda *args:encoded([info])
    with pytest.raises(ValueError,match='OWNER_LAB_OWNERSHIP'):lab.owned()


@pytest.mark.parametrize('label',('../escape','/absolute','x,y',''))
def test_probe_never_mounts_outside_private_scope(label):
    lab=OwnerLab.__new__(OwnerLab);lab.owned=lambda:None
    with pytest.raises(ValueError,match='PROBE_SCOPE'):lab.probe(dict(mode='baseline'),b'{}',{},label)


def test_readiness_ignores_entrypoint_temporary_unix_only_server(tmp_path,monkeypatch):
    lab=OwnerLab(tmp_path/'lab')
    lab.docker=lambda *args,**kwargs:b'owned-id' if args[0]=='run' else b''
    lab.owned=lambda:None
    probes=[]
    def readiness(arguments,**kwargs):
        probes.append(arguments)
        assert arguments[arguments.index('-h')+1]=='127.0.0.1'
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr('scripts.control_ha_owner_joint_lab.subprocess.run',readiness)
    with lab:assert lab.container=='owned-id'
    assert len(probes)==1


@pytest.mark.parametrize('kind',('extra','pin','key','image','dispatch','observations','duplicate','hash','table'))
def test_owner_archive_rejects_untrusted_or_privacy_bearing_inputs(kind):
    def mutate(manifest,floors):
        if kind=='image':manifest['image']='sha256:'+'0'*64
        elif kind=='dispatch':manifest['application_dispatch']=True
        elif kind=='observations':floors[0]['observations']={}
        elif kind=='duplicate':floors.append(deepcopy(floors[0]));manifest['metadata_floor_rows']=2
        elif kind=='hash':manifest['dump_sha256']='0'*64
        elif kind=='table':manifest['fingerprints']['../untrusted']=manifest['fingerprints'].pop('table_0')
    capsule,key,pin=sealed_archive(mutate=mutate,extra=kind=='extra')
    if kind=='pin':pin['archive_sha256']='0'*64
    if kind=='key':key=b'x'*32
    with pytest.raises(Exception):joint.owner_archive(capsule,key,pin)


def test_sqlite_postgres_projection_matches_native_shape(source,repository):
    canonical=prepared(source);files=source[1]
    aliases=pseudonyms.Aliases(json.loads(files['access/pseudonym-aliases.json']))
    key=files['access/support-inventory-hmac.key']
    with sqlite3.connect(':memory:') as database:
        database.deserialize(source[0]['registry']);database.row_factory=sqlite3.Row
        original=database.serialize()
        envelope=joint.projection(database,key,aliases,NOW,'a'*64)
        assert database.serialize()==original
    import_snapshot(repository,canonical.snapshot)
    with repository.transaction() as transaction:
        assert joint.projection(transaction.paid(),key,aliases,NOW,'a'*64)==envelope
    decoded=pseudonyms.unseal(envelope,'subscriptions',aliases)
    assert decoded['history']['events'] and len(decoded['devices'])==len(envelope['payload']['devices'])
    assert all(set(row)=={'pseudonym','cohort','subscription','event'} for row in decoded['devices'])
    changed=deepcopy(envelope);changed['generation']+=1
    with pytest.raises(ValueError):pseudonyms.unseal(changed,'subscriptions',aliases)


@pytest.mark.parametrize('field',('identity','key','intent','aliases'))
def test_separate_namespaces_are_not_silently_merged(source,monkeypatch,field):
    canonical=prepared(source);files=source[1]
    from scripts.control_ha_external_v1 import records
    device=records(canonical.snapshot)['devices'][0]
    owner_files={'panel-aliases.json':files['access/pseudonym-aliases.json'],
                 'inventory-hmac.key':files['access/support-inventory-hmac.key']}
    with sqlite3.connect(':memory:') as database:
        database.execute('CREATE TABLE devices(device,wg)')
        database.execute('INSERT INTO devices VALUES (?,?)',('synthetic','synthetic-key'))
        database.commit();owner_files['synthetic.sqlite']=database.serialize()
    with sqlite3.connect(':memory:') as database:
        database.execute('CREATE TABLE transport_keys(device_identity,public_key)')
        database.execute('CREATE TABLE peer_outbox(public_key)')
        database.execute('INSERT INTO transport_keys VALUES (?,?)',('legacy','legacy-key'))
        database.execute("INSERT INTO peer_outbox VALUES ('legacy-key')")
        if field=='identity':database.execute('UPDATE transport_keys SET device_identity=?',(device['device'],))
        elif field=='key':database.execute('UPDATE transport_keys SET public_key=?',(device['wg'],))
        elif field=='intent':database.execute('UPDATE peer_outbox SET public_key=?',(device['wg'],))
        database.commit();worker_files={'product.sqlite':database.serialize()}
    if field=='aliases':owner_files['panel-aliases.json']+=b' '
    monkeypatch.setattr(owner,'validate',lambda value:None);monkeypatch.setattr(owner,'unpack',lambda value:owner_files)
    monkeypatch.setattr(worker,'validate',lambda value:None);monkeypatch.setattr(worker,'unpack',lambda value:worker_files)
    with pytest.raises(ValueError,match='COLLISION|ALIAS_BINDING'):joint.bindings(canonical,{}, {})
