"""Managed AWG 3.1: real issuer/encryption/verifier, no live keys or VPN changes."""
import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from clients.desktop.profile_config import AWG31_FIELDS, parse
from control.fleet_publish import FleetPublisher
from control.fleet_store import FleetStore
from device_identity.device import DeviceIdentity
from provisioning.configuration import ConfigError, ConfigVerifier, TransportProfile
from test_fleet import inventory, load
from test_fleet_store import grant, reserve
from test_fleet_publish import profile


@pytest.fixture
def issued(tmp_path, inventory):
    # IDs are intentionally unrelated to the historical pilot names.
    for index, gateway in enumerate(inventory['gateways']):
        gateway['gateway_id'] = f'new-region-node-{index}'
    from test_fleet import observations
    samples = [sample.model_copy(update={'gateway_id': f'new-region-node-{index}'})
               for index, sample in enumerate(observations())]
    store = FleetStore(tmp_path/'fleet', clock=lambda: 1000)
    store.initialize(load(inventory))
    device = DeviceIdentity.generate()
    grant(store, device)
    lease = reserve(store, device, observations=samples)
    store.mark_ready(lease.lease_id, generation=1)
    signer = Ed25519PrivateKey.generate()
    anchor = signer.public_key().public_bytes_raw()
    store.pin_publication_authority(base64.b64encode(anchor).decode())
    binding = profile('3.1')
    publisher = FleetPublisher(store, signer=signer,
        bindings={(lease.gateway_id, lease.transport, lease.version): binding})
    def publish():
        return publisher.publish(lease.lease_id, device=device.reference,
            previous_config_hash=None, min_client_version='0.2.13')
    raw = publish()
    return device, anchor, raw, publish, binding, lease


def verifier(issued, **kwargs):
    device, anchor, *_ = issued
    return ConfigVerifier(anchor=anchor, device=device, client_version='0.2.13', **kwargs)


def test_awg31_signed_delivery_preserves_every_parameter_and_dynamic_gateway(issued):
    device, _, raw, publish, binding, lease = issued
    state = verifier(issued, supports_awg31=True).verify(raw, now=1000).state
    p, = state.transport_profiles
    assert p.transport_version == '3.1' and p.gateway_id == lease.gateway_id
    assert state.gateways[0].gateway_id.startswith('new-region-node-')
    assert all(p.parsed()['Interface'][key] == value for key, value in binding.parameters.items())
    local = p.config.replace('LOCAL_DEVICE_KEY', base64.b64encode(device._wireguard_key.private_bytes_raw()).decode())
    assert parse(local, allow_awg=True, allow_awg31=True)['Interface']['Address'] == lease.address
    assert publish() == raw
    assert binding.parameters['HeaderProtectionKey'].encode() not in raw


@pytest.mark.parametrize('capability', [False, True])
def test_capability_is_explicit_not_inferred_from_version(issued, capability):
    v = verifier(issued, supports_awg31=capability)
    if capability:
        v.verify(issued[2], now=1000)
    else:
        with pytest.raises(ConfigError, match='UNSUPPORTED_TRANSPORT_VERSION'):
            v.verify(issued[2], now=1000)
        with pytest.raises(ConfigError, match='UNSUPPORTED_TRANSPORT_VERSION'):
            verifier(issued).verify(issued[2], now=1000)


@pytest.mark.parametrize('field', sorted(AWG31_FIELDS))
def test_partial_awg31_is_rejected(issued, field):
    state = verifier(issued, supports_awg31=True).verify(issued[2], now=1000).state
    value = state.transport_profiles[0].model_dump()
    value['config'] = '\n'.join(line for line in value['config'].splitlines()
                                 if not line.startswith(field+' = '))
    with pytest.raises(ValueError):
        TransportProfile.model_validate(value)


@pytest.mark.parametrize('field,value', [
    ('HeaderProtectionKey', base64.b64encode(bytes(32)).decode()),
    ('ContentPaddingAddition', '256-0'), ('RandomTrailers', '1'),
    ('DisableCookies', 'yes'), ('H1', '100'), ('S1', '1'),
    ('S1', '48'), ('PostUp', 'arbitrary'),
])
def test_invalid_protection_parameters_are_rejected(issued, field, value):
    state = verifier(issued, supports_awg31=True).verify(issued[2], now=1000).state
    data = state.transport_profiles[0].model_dump()
    lines = [line for line in data['config'].splitlines() if not line.startswith(field+' = ')]
    data['config'] = '\n'.join(lines).replace('[Peer]', field+' = '+value+'\n[Peer]')
    with pytest.raises(ValueError):
        TransportProfile.model_validate(data)


def test_downgrade_label_cannot_discard_protection(issued):
    state = verifier(issued, supports_awg31=True).verify(issued[2], now=1000).state
    data = state.transport_profiles[0].model_dump()
    data['transport_version'] = '2.0'
    with pytest.raises(ValueError):
        TransportProfile.model_validate(data)


def test_awg31_capability_does_not_bypass_expiry_or_minimum_version(issued):
    with pytest.raises(ConfigError, match='LEASE'):
        verifier(issued, supports_awg31=True).verify(issued[2], now=1100)
    device, anchor, raw, *_ = issued
    old = ConfigVerifier(anchor=anchor, device=device, client_version='0.2.10', supports_awg31=True)
    with pytest.raises(ConfigError, match='CLIENT_VERSION'):
        old.verify(raw, now=1000)


@pytest.mark.parametrize('healthy', [False, True])
def test_awg31_journal_retry_and_health_rollback(issued, tmp_path, healthy):
    from provisioning.transaction import ControlJournal, ProvisioningCore
    from test_control_channel import Application
    journal = ControlJournal(tmp_path/'journal', verifier(issued, supports_awg31=True))
    journal.initialize()
    application = Application()
    application.health = healthy
    core = ProvisioningCore(journal=journal, application=application,
                            device=issued[0], clock=lambda: 1000)
    expected = 'COMMITTED' if healthy else 'ROLLED_BACK'
    assert core.receive(issued[2]) == expected
    # Reopen durable state: an identical delivery must not trigger another apply.
    journal = ControlJournal(tmp_path/'journal', verifier(issued, supports_awg31=True))
    core = ProvisioningCore(journal=journal, application=application,
                            device=issued[0], clock=lambda: 1000)
    assert core.receive(issued[2]) == expected
    assert len(application.applied) == 1
    if not healthy:
        assert application.active == 'baseline' and len(application.restored) == 1
