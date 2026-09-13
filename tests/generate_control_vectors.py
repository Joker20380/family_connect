"""TEST ONLY: build a new immutable vector set, never read deployment keys.

The only keys are derived from conspicuous public test labels below. They MUST
NOT be used for registration or deployment. Encryption is randomized; generate
into a NEW directory, review and commit its bytes, never regenerate during tests.
"""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import RNS
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from device_identity.device import DeviceIdentity
from provisioning import ack
from provisioning.configuration import DOMAIN, AUDIENCE, LOCAL_KEY


def b64(raw): return base64.b64encode(raw).decode()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def encode(value): return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
def seed(label): return hashlib.sha256(('PUBLIC TEST ONLY family-connect vectors v1 '+label).encode()).digest()


def generate(output):
    output.mkdir(parents=True, exist_ok=False)
    private = seed('rns-x25519') + seed('rns-ed25519')
    device = DeviceIdentity(RNS.Identity.from_bytes(private), X25519PrivateKey.from_private_bytes(seed('wg')))
    signer = Ed25519PrivateKey.from_private_bytes(seed('issuer'))
    anchor = signer.public_key().public_bytes_raw()
    peer = X25519PrivateKey.from_private_bytes(seed('gateway')).public_key().public_bytes_raw()
    manifest = dict(schema_version=1, test_only=True, suite='family-connect-control-v1',
        reference_version='0.2.9', fixture_identity='TEST-ONLY-identity.json',
        domains_b64=dict(configuration=b64(DOMAIN),acknowledgement=b64(ack.DOMAIN)), files={}, configurations=[], acknowledgements=[], transcripts=[])
    def put(name, raw):
        (output/name).write_bytes(raw)
        manifest['files'][name] = dict(sha256=digest(raw), size=len(raw))
        return name
    put('TEST-ONLY-identity.json', encode(dict(test_only=True, warning='PUBLIC TEST KEYS: NEVER DEPLOY',
        rns_private_b64=b64(private), wg_private_b64=b64(seed('wg')), issuer_private_b64=b64(seed('issuer')),
        public_identity_b64=device.public_identity, wireguard_public_key=device.wireguard_public_key,
        device_reference=device.reference, anchor_b64=b64(anchor))))
    profile = dict(profile_id='wg1', gateway_id='gw1', transport='wireguard', transport_version='1',
        config=f'[Interface]\nPrivateKey = {LOCAL_KEY}\nAddress = 10.77.0.4/32\nDNS = 1.1.1.1\nMTU = 1280\n'
        f'[Peer]\nPublicKey = {b64(peer)}\nEndpoint = 198.51.100.1:51820\nAllowedIPs = 0.0.0.0/0, ::/0\n')
    payload = dict(schema_version=2,config_id='fixture-1',revision=1,issued_at=1000,expires_at=4600,
        recipient=device.reference,audience=AUDIENCE,wireguard_public_key=device.wireguard_public_key,
        min_client_version='0.2.9',previous_config_hash=None,signer_key_id=digest(anchor),
        gateways=[dict(gateway_id='gw1',endpoint='198.51.100.1',port=51820)],transport_profiles=[profile])
    def signed(value=None, *, plain=None, domain=DOMAIN, key=signer):
        ciphertext=device._identity.encrypt(encode(value) if plain is None else plain)
        return encode(dict(ciphertext=b64(ciphertext),signature=b64(key.sign(domain+ciphertext))))
    records={}
    def config(name, *, value=None, raw=None, error=None, now=1000, version='0.2.9'):
        value=copy.deepcopy(payload if value is None else value)
        raw=signed(value) if raw is None else raw
        case=dict(id=name,input=put(name+'.envelope',raw),now=now,client_version=version,
            expected=dict(category=error or 'ACCEPT'))
        if error is None:
            case['expected'].update(payload=value,envelope_sha256=digest(raw))
        manifest['configurations'].append(case);records[name]=raw
        return raw
    first=config('valid-wg')
    config('valid-awg2',value={**payload,'transport_profiles':[{**profile,'transport':'amneziawg','transport_version':'2.0',
        'config':profile['config'].replace('[Peer]', 'Jc = 4\nJmin = 40\nJmax = 70\nS1 = 16\nS2 = 32\nS3 = 16\nS4 = 16\nH1 = 100\nH2 = 200\nH3 = 300\nH4 = 400\n[Peer]')}]})
    config('valid-tcp',value={**payload,'transport_profiles':[{**profile,'transport':'vless-reality','config':json.dumps(dict(
        type='vless-reality-v1',server='198.51.100.1',port=51820,id='11111111-2222-4333-8444-555555555555',
        public_key=base64.urlsafe_b64encode(peer).decode().rstrip('='),server_name='example.com',short_id='abcd'))}]})
    second_payload={**payload,'revision':2,'config_id':'fixture-2','previous_config_hash':digest(first)}
    second=config('valid-next',value=second_payload)
    config('same-revision-other-bytes')
    config('wrong-previous',value={**second_payload,'previous_config_hash':None})
    for name,changes,error in [
        ('wrong-target',{'recipient':'0'*32},'TARGET'),('wrong-audience',{'audience':'wrong'},'TARGET'),
        ('wrong-wg',{'wireguard_public_key':b64(peer)},'TARGET'),('wrong-signer-id',{'signer_key_id':'0'*64},'SIGNER'),
        ('schema-unknown',{'schema_version':3},'SCHEMA'),('schema-bool',{'schema_version':True},'SCHEMA'),
        ('invalid-timestamps',{'expires_at':999},'STRUCTURE'),('future',{'issued_at':1001},'LEASE'),
        ('unknown-field',{'extra':'reject'},'STRUCTURE'),
        ('bad-profile',{'transport_profiles':[{**profile,'config':'PostUp = forbidden'}]},'STRUCTURE'),
        ('awg31',{'transport_profiles':[{**profile,'transport':'amneziawg','transport_version':'3.1'}]},'UNSUPPORTED_TRANSPORT_VERSION')]:
        config(name,value={**payload,**changes},error=error)
    config('lease-last-second',raw=first,now=4599)
    config('lease-expired',raw=first,now=4600,error='LEASE')
    config('older-client',raw=first,version='0.2.8',error='CLIENT_VERSION')
    config('negative-clock',raw=first,now=-1,error='CLOCK')
    config('wrong-purpose',raw=signed(payload,domain=b'family-connect/device-activation/v1\x00'),error='SIGNATURE')
    config('untrusted-issuer',raw=signed(payload,key=Ed25519PrivateKey.from_private_bytes(seed('other-issuer'))),error='SIGNATURE')
    config('bad-high-sequence',raw=signed({**payload,'revision':999},key=Ed25519PrivateKey.from_private_bytes(seed('other-issuer'))),error='SIGNATURE')
    outer=json.loads(first);bad=bytearray(base64.b64decode(outer['ciphertext']));bad[-1]^=1
    config('tampered-ciphertext',raw=encode({**outer,'ciphertext':b64(bad)}),error='SIGNATURE')
    config('duplicate-outer',raw=first[:-1]+b',"ciphertext":"duplicate"}',error='MALFORMED')
    config('duplicate-plaintext',raw=signed(plain=encode(payload)[:-1]+b',"revision":1}'),error='STRUCTURE')
    config('malformed-json',raw=b'{',error='MALFORMED')
    config('limit-65536',raw=first+b' '*(65536-len(first)))
    config('oversize-65537',raw=first+b' '*(65537-len(first)),error='SIZE')

    def receipt(name, raw, valid=True, body=None):
        manifest['acknowledgements'].append(dict(id=name,input=put(name+'.ack',raw),
            expected=dict(category='ACCEPT' if valid else 'REJECT', **({'body':body} if valid else {}))))
    valid_ack=None
    for status in sorted(ack.STATUSES):
        raw=ack.create(device,digest=digest(first),config_id=None if status=='REJECTED' else 'fixture-1',
            sequence=0 if status=='REJECTED' else 1,status=status,error='SIGNATURE' if status=='REJECTED' else 'NONE',now=1000)
        receipt('ack-'+status.lower(),raw,body=json.loads(raw)['body'])
        if status=='COMMITTED':valid_ack=raw
    body=json.loads(valid_ack)['body']
    receipt('ack-limit-4096',valid_ack+b' '*(4096-len(valid_ack)),body=body)
    receipt('ack-oversize-4097',valid_ack+b' '*(4097-len(valid_ack)),False)
    receipt('ack-duplicate',valid_ack[:-1]+b',"body":{}}',False)
    changed={**body,'status':'FAILED'}
    receipt('ack-tampered',encode(dict(body=changed,signature=json.loads(valid_ack)['signature'])),False)
    for name,changed in [('ack-wrong-id',{**body,'ack_id':'0'*64}),('ack-bool-sequence',{**body,'sequence':True}),
            ('ack-unknown-field',{**body,'extra':'reject'}),('ack-noncanonical-public',{**body,'public_identity':body['public_identity']+'='})]:
        receipt(name,encode(dict(body=changed,signature=b64(device._identity.sign(ack.DOMAIN+encode(changed))))),False)
    receipt('ack-wrong-purpose',encode(dict(body=body,signature=b64(device._identity.sign(DOMAIN+encode(body))))),False)
    def step(op, expected, **options):return dict(operation=op,**options,expected=expected)
    def expected(result,floor,committed,applies,rollbacks,phase='IDLE',active=None):
        return dict(result=result,floor=floor,committed_sha256=digest(records[committed]) if committed else None,
            applies=applies,rollbacks=rollbacks,phase=phase,
            active=(digest(records[active or committed]) if (active or committed) else 'baseline'))
    def receive(name,result,floor,committed,applies,rollbacks,**opts):
        return step('receive',expected(result,floor,committed,applies,rollbacks),input=name,**opts)
    manifest['transcripts']=[dict(id='replay-and-chain',steps=[
        receive('valid-wg','COMMITTED',1,'valid-wg',1,0),receive('valid-wg','COMMITTED',1,'valid-wg',1,0),
        receive('same-revision-other-bytes','REJECTED',1,'valid-wg',1,0,error='REPLAY'),
        receive('bad-high-sequence','REJECTED',1,'valid-wg',1,0,error='SIGNATURE'),
        receive('wrong-previous','REJECTED',1,'valid-wg',1,0,error='PREVIOUS_HASH'),
        receive('valid-next','COMMITTED',2,'valid-next',2,0),receive('valid-wg','REJECTED',2,'valid-next',2,0,error='REPLAY')]),
        dict(id='failed-health-and-replay',steps=[receive('valid-wg','COMMITTED',1,'valid-wg',1,0),
            receive('valid-next','ROLLED_BACK',2,'valid-wg',2,1,health=False,error='HEALTH'),
            receive('valid-next','ROLLED_BACK',2,'valid-wg',2,1,health=True,error='HEALTH')]),
        dict(id='crash-recover-outbox',steps=[
            step('crash',expected('CRASH',1,None,1,0,phase='APPLIED_PENDING',active='valid-wg'),input='valid-wg',at_phase='APPLIED_PENDING'),
            step('restart-recover',expected('ROLLED_BACK',1,None,1,1)),
            step('restart-recover',expected('IDLE',1,None,1,1)),
            receive('valid-wg','ROLLED_BACK',1,None,1,1,error='RECOVERY'),
            step('flush',expected(False,1,None,1,1),available=False,outbox_empty=False),
            step('flush',expected(True,1,None,1,1),available=True,outbox_empty=True)])]
    for transcript in manifest['transcripts']:
        transcript['initial'] = dict(now=1000,client_version='0.2.9',floor=0,committed_sha256=None,active='baseline')
    put('README.txt', b'PUBLIC TEST ONLY. Fixture keys are intentionally public, never deploy them.\nImmutable wire inputs; manifest lists expected results for Python and future native runners.\nRegenerate only as a new reviewed corpus, never during conformance checks.\n')
    (output/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='NEW directory; existing directories are refused')
    args=parser.parse_args();m=generate(args.output)
    print(f'TEST ONLY: {len(m["configurations"])} configurations, {len(m["acknowledgements"])} ACKs, {len(m["transcripts"])} transcripts')
