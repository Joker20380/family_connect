"""Fresh disposable materials, invoked only by the authorized operator workflow."""

import base64
import datetime
import os
from pathlib import Path
import secrets
import time
import uuid

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from .contracts import canonical, digest, exact, fail, load
from .materials import seal
from .operator_harness import PROBE_IDENTITY_SHA256
from .permit import validate
from .private_files import checked, read_private, write_private
from .rehearsal_materials import verify_enrollment
from .role_config import SNI


def raw_private(key):
    return key.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())


def raw_public(key):
    return key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)


def generate(instance_id, probe_public, probe_private, publisher, *, issued_at, expires_at):
    if len(probe_public)!=64 or raw_public(probe_private)!=probe_public[32:] or not 0<expires_at-issued_at<=14400:
        fail('material_factory_binding')
    server=X25519PrivateKey.generate()
    peer=X25519PrivateKey.generate()
    reality=X25519PrivateKey.generate()
    issuer_key=Ed25519PrivateKey.generate()
    gateway_key=Ed25519PrivateKey.generate()
    gateway_public=raw_public(X25519PrivateKey.generate())+raw_public(gateway_key)
    gateway=digest(gateway_public)[:32]
    family=uuid.uuid4().hex
    beginning=datetime.datetime.fromtimestamp(issued_at,datetime.timezone.utc)
    deadline=datetime.datetime.fromtimestamp(expires_at,datetime.timezone.utc)
    issuer=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Disposable rehearsal '+instance_id)])
    authority=(x509.CertificateBuilder().subject_name(issuer).issuer_name(issuer).public_key(issuer_key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(beginning).not_valid_after(deadline)
        .add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
        .add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),critical=True).sign(issuer_key,None))
    crl=(x509.CertificateRevocationListBuilder().issuer_name(issuer).last_update(beginning).next_update(deadline)
         .add_extension(x509.CRLNumber(1),critical=False).sign(issuer_key,None))
    def profile(public, private, role):
        subject=x509.Name([x509.NameAttribute(NameOID.SERIAL_NUMBER,digest(public)[:32]),
            *[x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME,claim) for claim in
              ('protocol=family-connect-5n3-test-v1','family='+family,'role='+role,'revision=1')]])
        leaf=(x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(private.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(beginning).not_valid_after(deadline)
            .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH if role=='gateway' else ExtendedKeyUsageOID.CLIENT_AUTH]),critical=False)
            .add_extension(x509.SubjectAlternativeName([x509.UniformResourceIdentifier('urn:family-connect:identity:'+public.hex()),
                x509.DNSName('gateway.family-connect.test')]),critical=False).sign(issuer_key,None))
        return dict(certificate=leaf.public_bytes(serialization.Encoding.PEM).decode(),
            private_key=private.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode(),
            authority=authority.public_bytes(serialization.Encoding.PEM).decode(),revocations=crl.public_bytes(serialization.Encoding.PEM).decode(),
            family=family,gateway=gateway,minimum_revision=1,minimum_crl=1)
    scope='DISPOSABLE_FLEET_REHEARSAL'
    server_material=dict(scope=scope,server_private_key=base64.b64encode(raw_private(server)).decode(),
                         peer_public_key=base64.b64encode(raw_public(peer)).decode())
    peer_material=dict(scope=scope,server_public_key=base64.b64encode(raw_public(server)).decode(),
                       peer_private_key=base64.b64encode(raw_private(peer)).decode())
    tcp=dict(scope=scope,private_key=base64.urlsafe_b64encode(raw_private(reality)).decode().rstrip('='),
             public_key=base64.urlsafe_b64encode(raw_public(reality)).decode().rstrip('='),uuid=str(uuid.uuid4()),
             short_id=secrets.token_hex(8),sni=SNI,destination=SNI+':443')
    slots={'awg-material':canonical(server_material),'tcp-material':canonical(tcp),
           'mesh-material':canonical(dict(scope=scope,instance_id=instance_id,credentials=profile(gateway_public,gateway_key,'gateway'))),
           'publisher-material':publisher}
    clients={'awg-peer.json':canonical(peer_material),'tcp-client.json':canonical({name:tcp[name] for name in ('scope','uuid','public_key','short_id','sni')}),
             'mesh-profile.json':canonical(profile(probe_public,probe_private,'device'))}
    return slots,clients


def prepare(permit, material_enrollment, authority, request, output, *, now=None):
    from device_identity.friends import load_friends_identity
    current=int(time.time()) if now is None else now
    body=validate(permit['body'],current)
    exact(request,('probe_identity','publisher_material'))
    binding=material_enrollment['body']['binding']
    verify_enrollment(material_enrollment,binding,authority.public_key())
    if any(binding[name]!=body[name] for name in ('instance_id','logical_gateway','ipv4','bundle_a','bundle_b')):
        fail('material_factory_permit')
    destination=checked(Path(output).absolute(),directory=True,owner=os.geteuid())
    if destination.stat().st_mode & 0o077:
        fail('material_factory_custody')
    identity=load_friends_identity(request['probe_identity'],create=False)
    public=base64.b64decode(identity.public_identity,validate=True)
    if digest(public)!=PROBE_IDENTITY_SHA256:
        fail('material_factory_probe_identity')
    private=Ed25519PrivateKey.from_private_bytes(identity._identity.get_private_key()[32:])
    publisher=read_private(request['publisher_material'],owner=os.geteuid())
    from .role_config import publisher_config
    publisher_config(publisher)
    slots,clients=generate(body['instance_id'],public,private,publisher,issued_at=current,expires_at=body['expires_at'])
    envelope=seal(binding,slots,authority,issued_at=current,expires_at=body['expires_at'])
    prefix=body['instance_id']+'-'
    for name,content in clients.items():
        write_private(destination/(prefix+name),content)
    write_private(destination/(prefix+'materials.json'),canonical(envelope))
    return envelope
