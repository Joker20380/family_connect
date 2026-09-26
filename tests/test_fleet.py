import base64
import copy
import json

import pytest

from control.fleet import MAX_REGISTRY_BYTES, Observation, load_registry, rank_gateways, validate_update


@pytest.fixture
def inventory():
    def gateway(name, address, pool):
        return dict(gateway_id=name, failure_domain=name, country='nl', state='active',
                    endpoints=[dict(transport='amneziawg', version='3.1', address=address, port=51820)],
                    tunnel_pool=pool, max_devices=100, weight=1.0, egress_budget_mbps=200.0)
    return dict(schema_version=1, revision=7,
                gateways=[gateway('nl-01', '186.246.45.246', '10.83.0.0/24'),
                          gateway('nl-02', '185.251.89.19', '10.84.0.0/24')],
                control_ingresses=[dict(ingress_id='control-01', failure_domain='nl-01',
                    address='186.246.45.246', port=4242,
                    provider_public=base64.b64encode(bytes(range(64))).decode())])


def load(value):
    return load_registry(json.dumps(value).encode())


def observations():
    return [Observation(gateway_id=node, registry_revision=7, observed_at=1000,
                        ready_transports=('amneziawg',), allocated_devices=10,
                        cpu_percent=10.0, memory_percent=25.0, tx_mbps=20.0)
            for node in ('nl-01', 'nl-02')]


def rank(inventory, samples=None, **options):
    args = dict(device='fixture-device', country='nl', transport='amneziawg', version='3.1', now=1000)
    args.update(options)
    return rank_gateways(load(inventory), observations() if samples is None else samples, **args)


def test_multiple_nodes_per_country_and_order_independence(inventory):
    expected = rank(inventory)
    assert set(expected) == {'nl-01', 'nl-02'}
    inventory['gateways'].reverse()
    assert rank(inventory, list(reversed(observations()))) == expected


@pytest.mark.parametrize('mutation', [
    lambda r: r.update(schema_version=True),
    lambda r: r.update(private_key='not-allowed'),
    lambda r: r['gateways'][1].update(gateway_id='nl-01'),
    lambda r: r['gateways'][1].update(tunnel_pool='10.83.0.128/25'),
    lambda r: r['gateways'][0].update(tunnel_pool='8.8.8.0/24'),
    lambda r: r['gateways'][0].update(max_devices=254),
    lambda r: r['gateways'][0].update(egress_budget_mbps=0),
    lambda r: r['gateways'][0].update(egress_budget_mbps=float('nan')),
    lambda r: r['gateways'][0].update(weight=True),
    lambda r: r['gateways'][0]['endpoints'][0].update(address='127.0.0.1'),
    lambda r: r['gateways'][0]['endpoints'][0].update(address='10.0.0.1'),
    lambda r: r['gateways'][0]['endpoints'][0].update(address='2606:4700:4700::1111%eth0'),
    lambda r: r['gateways'][0]['endpoints'][0].update(address='::ffff:808:808'),
    lambda r: r['gateways'][0]['endpoints'][0].update(port=True),
    lambda r: r['gateways'][0]['endpoints'][0].update(transport='wireguard'),
    lambda r: r['gateways'][1].update(endpoints=copy.deepcopy(r['gateways'][0]['endpoints'])),
    lambda r: r['control_ingresses'].append(copy.deepcopy(r['control_ingresses'][0])),
    lambda r: r['control_ingresses'][0].update(provider_public='invalid'),
])
def test_invalid_registry_fails_closed(inventory, mutation):
    mutation(inventory)
    with pytest.raises(ValueError):
        load(inventory)


def test_duplicate_json_and_size(inventory):
    raw = json.dumps(inventory).encode().replace(b'"revision": 7', b'"revision": 7, "revision": 8')
    for invalid in (raw, b'x' * (MAX_REGISTRY_BYTES + 1), b''):
        with pytest.raises(ValueError):
            load_registry(invalid)


@pytest.mark.parametrize('change', [
    dict(observed_at=954), dict(observed_at=1001), dict(registry_revision=6),
    dict(ready_transports=()), dict(allocated_devices=100), dict(cpu_percent=85.0),
    dict(memory_percent=85.0), dict(tx_mbps=170.0),
])
def test_unhealthy_stale_full_nodes_get_no_new_assignments(inventory, change):
    samples = observations()
    samples[0] = Observation.model_validate({**samples[0].model_dump(), **change})
    assert rank(inventory, samples) == ['nl-02']


@pytest.mark.parametrize('state', ['provisioning', 'draining', 'disabled'])
def test_lifecycle_excludes_new_assignments(inventory, state):
    inventory['gateways'][0]['state'] = state
    assert rank(inventory) == ['nl-02']


def test_draining_or_busy_node_keeps_existing_assignment(inventory):
    inventory['gateways'][0]['state'] = 'draining'
    samples = observations()
    samples[0] = Observation.model_validate({**samples[0].model_dump(), 'allocated_devices': 100,
                                            'cpu_percent': 100.0, 'tx_mbps': 300.0})
    assert rank(inventory, samples, current='nl-01')[0] == 'nl-01'
    inventory['gateways'][0]['state'] = 'disabled'
    assert rank(inventory, samples, current='nl-01') == ['nl-02']


def test_no_hidden_country_or_transport_fallback(inventory):
    assert rank(inventory, country='ru') == []
    assert rank(inventory, version='2.0') == []
    assert rank(inventory, transport='wireguard', version='1') == []
    assert rank(inventory, []) == []
    assert len(rank(inventory, country=None)) == 2


def test_duplicate_telemetry_is_rejected(inventory):
    with pytest.raises(ValueError):
        rank(inventory, observations() + observations())


def test_weighted_distribution_and_sticky_addition(inventory):
    inventory['gateways'][1]['weight'] = 3.0
    registry = load(inventory)
    counts = {'nl-01': 0, 'nl-02': 0}
    for n in range(1000):
        result = rank_gateways(registry, observations(), device=f'device-{n}', country='nl',
                               transport='amneziawg', version='3.1', now=1000)
        counts[result[0]] += 1
    assert 650 < counts['nl-02'] < 850
    # A newly added, less busy gateway does not move established assignments.
    assert rank(inventory, current='nl-01')[0] == 'nl-01'


def test_changed_ip_requires_fresh_registry_revision_observation(inventory):
    inventory['revision'] += 1
    inventory['gateways'][0]['endpoints'][0]['address'] = '1.1.1.1'
    assert rank(inventory) == []


def test_public_ipv6_endpoint_is_inventory_only(inventory):
    inventory['gateways'][0]['endpoints'][0]['address'] = '2606:4700:4700::1111'
    assert load(inventory).gateways[0].endpoints[0].address == '2606:4700:4700::1111'
    assert rank(inventory) == ['nl-02']
    assert set(rank(inventory, address_families=(4, 6))) == {'nl-01', 'nl-02'}


def test_registry_update_retains_identity_pool_and_bootstrap(inventory):
    previous = load(inventory)
    inventory['revision'] += 1
    inventory['gateways'][0]['state'] = 'draining'
    assert validate_update(previous, load(inventory)).revision == 8


@pytest.mark.parametrize('mutation', [
    lambda r: r.update(revision=7),
    lambda r: r['gateways'].pop(),
    lambda r: r['gateways'][0].update(tunnel_pool='10.85.0.0/24'),
    lambda r: r['gateways'][0].update(failure_domain='another-host'),
    lambda r: r['control_ingresses'][0].update(address='1.1.1.1'),
])
def test_unsafe_registry_update_rejected(inventory, mutation):
    previous = load(inventory)
    inventory['revision'] += 1
    mutation(inventory)
    with pytest.raises(ValueError):
        validate_update(previous, load(inventory))


@pytest.mark.parametrize('change', [dict(now=True), dict(max_age=0), dict(device=''), dict(version='4')])
def test_invalid_selection_request(inventory, change):
    with pytest.raises(ValueError):
        rank(inventory, **change)


def test_control_ingress_cannot_claim_data_tcp_socket(inventory):
    inventory['gateways'][0]['endpoints'][0].update(transport='vless-reality', version='1', port=4242)
    with pytest.raises(ValueError):
        load(inventory)


def test_cli_validation_never_echoes_rejected_input(inventory, tmp_path, monkeypatch, capsys):
    from scripts.check_fleet import main
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps(inventory))
    monkeypatch.setattr('sys.argv', ['check-fleet', str(path)])
    main()
    assert json.loads(capsys.readouterr().out)['gateways'] == 2
    inventory['private_key'] = 'TEST-SENSITIVE-INPUT'
    path.write_text(json.dumps(inventory))
    with pytest.raises(SystemExit) as failure:
        main()
    assert failure.value.code == 1
    output = capsys.readouterr()
    assert output.err == 'Invalid fleet registry\n' and not output.out
