import json
import pytest
from backend import verified_server_load, verified_server_loads

def payload(**changes):
    sample=dict(country='nl',observed_at=1000,cpu_percent=30,rx_mbps=80,tx_mbps=75,capacity_mbps=100)
    sample.update(changes);return json.dumps(dict(schema=1,gateways={'nl':sample})).encode()

def test_bottleneck_and_unknown_capacity():
    assert verified_server_load(payload(),'nl',1010)['percent']==80
    sample=verified_server_load(payload(capacity_mbps=None),'nl',1010)
    assert sample['percent'] is None and sample['cpu']==30

@pytest.mark.parametrize('changes', [dict(cpu_percent=True),dict(cpu_percent=float('nan')),dict(capacity_mbps=0),dict(rx_mbps=-1),dict(country='ru'),dict(observed_at=900),dict(observed_at=1050)])
def test_bad_or_stale_metrics_rejected(changes):
    with pytest.raises(ValueError):verified_server_load(payload(**changes),'nl',1010)

def test_unknown_gateway_not_mapped_to_another_server():
    with pytest.raises((ValueError,KeyError)):verified_server_load(payload(),'ru',1010)


def test_provider_egress_estimate():
    value=verified_server_load(payload(rx_mbps=900,tx_mbps=20,capacity_mbps=200,
        capacity_direction='egress',capacity_basis='provider-default-estimate'),'nl',1010)
    assert value['percent']==30 and value['estimated'] and value['capacity']==200


def test_verified_server_loads_returns_both_and_skips_missing():
    both=dict(schema=1,gateways={'nl':dict(country='nl',observed_at=1000,cpu_percent=30,rx_mbps=80,tx_mbps=75,capacity_mbps=100),
                                  'ru':dict(country='ru',observed_at=1000,cpu_percent=10,rx_mbps=1,tx_mbps=2,capacity_mbps=200,capacity_direction='duplex',capacity_basis='configured')})
    values=verified_server_loads(json.dumps(both).encode(),1010)
    assert set(values)=={'nl','ru'} and values['nl']['percent']==80 and values['ru']['percent']==10
    missing=verified_server_loads(json.dumps(dict(schema=1,gateways={'nl':both['gateways']['nl']})).encode(),1010)
    assert set(missing)=={'nl'}


def node_payload(**changes):
    first=dict(country='nl',gateway_id='nl-amsterdam-1',observed_at=1000,cpu_percent=23,
               rx_mbps=2500,tx_mbps=1000,capacity_mbps=5000,capacity_direction='duplex',
               capacity_basis='operator-assumed-capacity')
    first.update(changes)
    second=dict(first,gateway_id='nl-amsterdam-2',cpu_percent=7,rx_mbps=5,tx_mbps=2)
    return json.dumps(dict(schema=1,gateways={},nodes={'nl-amsterdam-1':first,'nl-amsterdam-2':second})).encode()


def test_distinct_node_metrics_and_operator_capacity():
    values=verified_server_loads(node_payload(),1010)
    assert set(values)=={'nl-amsterdam-1','nl-amsterdam-2'}
    assert values['nl-amsterdam-1']['percent']==50
    assert values['nl-amsterdam-2']['percent']==7
    assert values['nl-amsterdam-1']['capacity']==5000
    assert values['nl-amsterdam-1']['estimated']
    assert values['nl-amsterdam-1']['capacity_basis']=='operator-assumed-capacity'


@pytest.mark.parametrize('changes',[dict(gateway_id='nl-amsterdam-2'),dict(country='ru'),dict(observed_at=900)])
def test_node_binding_and_freshness_do_not_fall_back_to_country(changes):
    values=verified_server_loads(node_payload(**changes),1010)
    assert 'nl-amsterdam-1' not in values
    with pytest.raises((ValueError,KeyError)):
        verified_server_load(payload(),'nl-amsterdam-1',1010)
