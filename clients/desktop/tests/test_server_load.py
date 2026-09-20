import json
import pytest
from backend import verified_server_load

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
