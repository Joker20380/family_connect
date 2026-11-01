import copy
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from fleet.acceptance import STEPS, verify
from fleet.contracts import FleetError, canonical
from fleet.material_factory import generate, raw_public
from fleet.operator_harness import mesh_result, run
from fleet.rehearsal_cli import COMMANDS, parser
from fleet.role_config import awg_config, mesh_config, publisher_config, tcp_config


@pytest.mark.parametrize('action',[action for action in COMMANDS if action!='prepare'])
def test_operator_commands_require_explicit_permit_and_pin(action):
    with pytest.raises(SystemExit):
        parser().parse_args([action])


@pytest.mark.parametrize('flag',['--force','--skip-health','--insecure','--live','--shell'])
def test_no_generic_live_bypass(flag):
    with pytest.raises(SystemExit):
        parser().parse_args(['stage',flag])


def test_fresh_material_factory_and_role_contracts():
    private=Ed25519PrivateKey.generate()
    public=raw_public(X25519PrivateKey.generate())+raw_public(private)
    publisher=canonical(dict(scope='DISPOSABLE_FLEET_REHEARSAL',token='synthetic-token-not-a-provider-credential'))
    slots,clients=generate('fleet-rehearsal-test',public,private,publisher,issued_at=1000,expires_at=1300)
    assert awg_config(slots['awg-material'])[1]['port']==51827
    assert b'4443' in tcp_config(slots['tcp-material'])
    assert publisher_config(slots['publisher-material']).startswith(b'YANDEX_')
    profile,binding=mesh_config(slots['mesh-material'],instance_id='fleet-rehearsal-test',now=1001,permit_expires_at=1300)
    assert binding['expires_at']==1300
    other,unused=generate('fleet-rehearsal-test',public,private,publisher,issued_at=1000,expires_at=1300)
    assert other['awg-material']!=slots['awg-material'] and other['tcp-material']!=slots['tcp-material']
    assert clients['mesh-profile.json'] not in slots.values()


def test_mesh_safe_result_requires_all_native_evidence():
    events=[dict(event='family_auth',accepted=True),dict(event='mux_result',status='PASS'),
            dict(event='fleet_probe_egress',passed=True,expected_rehearsal_egress=True)]
    events += [dict(event='mux_https',passed=True) for index in range(4)]
    events += [dict(event='mux_dns',passed=True) for index in range(3)]
    raw=b'\n'.join(canonical(event) for event in events)
    assert all(value=='PASS' for value in mesh_result(raw).values())
    for index in range(len(events)):
        with pytest.raises(FleetError):
            mesh_result(b'\n'.join(canonical(event) for position,event in enumerate(events) if position!=index))


def test_synthetic_operator_harness_signs_only_after_probes_and_cleanup():
    key=Ed25519PrivateKey.generate()
    challenge=dict(instance_id='fleet-rehearsal-test',bundle_id='gw-'+'a'*32,operation_id='verification-one',
        verification_nonce='b'*64,ipv4='8.8.8.8',local_health_sha256='c'*64,started_at=1000,expires_at=1300)
    calls=[]
    harness=SimpleNamespace(challenge=challenge)
    for role,steps in STEPS.items():
        def probe(directory,role=role,steps=steps):
            calls.append(role)
            return {step:'PASS' for step in steps}
        setattr(harness,role,probe)
    receipt=run(harness,key,now=lambda:1001)
    assert calls==['awg','tcp','mesh']
    assert verify(receipt,key.public_key(),challenge,now=1002)
    harness.tcp=lambda directory:(_ for unused in ()).throw(FleetError('fixture_failure'))
    failed=run(harness,key,now=lambda:1001)
    assert failed['body']['cleanup']=='FAIL'
    with pytest.raises(FleetError):
        verify(failed,key.public_key(),challenge,now=1002)
