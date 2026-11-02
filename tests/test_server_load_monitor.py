import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('monitor',Path(__file__).parents[1]/'deploy/server-load/monitor.py')
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)

def counters():
    return dict(clock=0,total=100,idle=50,rx=0,tx=0),dict(clock=10,total=200,idle=120,rx=100_000_000,tx=100_000_000)

def test_full_duplex_and_bottleneck():
    before,after=counters();value=monitor.utilization(before,after,'nl',100,1000)
    assert value['cpu_percent']==30 and value['channel_percent']==80 and value['load_percent']==80
    assert monitor.utilization(before,after,'nl',1000,1000)['load_percent']==30

def test_capacity_unknown_never_claims_cpu_is_total_load():
    for capacity in (None,0,-1,True,float('nan')):
        value=monitor.utilization(*counters(),'ru',capacity,1000)
        assert value['load_percent'] is None and value['cpu_percent']==30

def test_counter_reset_and_long_gap():
    before,after=counters();after['rx']=-1
    with pytest.raises(ValueError):monitor.utilization(before,after,'ru',100,1000)
    before,after=counters();after['clock']=100
    with pytest.raises(ValueError):monitor.utilization(before,after,'ru',100,1000)


def test_egress_only_capacity():
    before,after=counters();after['tx']=10_000_000
    value=monitor.utilization(before,after,'nl',100,1000,'egress','provider-default-estimate')
    assert value['channel_percent']==8 and value['load_percent']==30
    assert value['capacity_basis']=='provider-default-estimate'


def test_independent_node_collection_and_legacy_alias(monkeypatch):
    config=dict(nodes={'nl-amsterdam-1':'185.10.158.212','nl-amsterdam-2':'185.10.158.196'})
    def remote(configuration, gateway_id=None):
        return dict(country='nl',gateway_id=gateway_id,observed_at=1000,
                    cpu_percent=23 if gateway_id=='nl-amsterdam-1' else 7,capacity_mbps=5000)
    monkeypatch.setattr(monitor,'remote',remote)
    result=monitor.public_samples(config,dict(country='ru'))
    assert result['nodes']['nl-amsterdam-1']['cpu_percent']==23
    assert result['nodes']['nl-amsterdam-2']['cpu_percent']==7
    assert result['gateways']['nl']==result['nodes']['nl-amsterdam-1']


def test_missing_first_node_never_uses_second_for_legacy_nl(monkeypatch):
    def remote(configuration, gateway_id=None):
        if gateway_id=='nl-amsterdam-1':raise OSError('offline')
        return dict(country='nl',gateway_id=gateway_id,observed_at=1000)
    monkeypatch.setattr(monitor,'remote',remote)
    result=monitor.public_samples(dict(nodes={'nl-amsterdam-1':'185.10.158.212','nl-amsterdam-2':'185.10.158.196'}),dict(country='ru'))
    assert 'nl' not in result['gateways']
    assert set(result['nodes'])=={'nl-amsterdam-2'}


@pytest.mark.parametrize('nodes',[{'nl-amsterdam-3':'185.10.158.196'},
    {'nl-amsterdam-1':'185.10.158.212','nl-amsterdam-2':'185.10.158.212'}])
def test_invalid_node_inventory_rejected(nodes):
    with pytest.raises(ValueError):monitor.public_samples(dict(nodes=nodes),dict(country='ru'))


@pytest.mark.parametrize('changes',[dict(gateway_id='nl-amsterdam-2'),dict(observed_at=900),dict(country='ru')])
def test_remote_rejects_wrong_node_or_stale_sample(monkeypatch,changes):
    import json
    from types import SimpleNamespace
    sample=dict(country='nl',gateway_id='nl-amsterdam-1',observed_at=1000)
    sample.update(changes)
    monkeypatch.setattr(monitor.time,'time',lambda:1010)
    monkeypatch.setattr(monitor.subprocess,'run',lambda *args,**kwargs:SimpleNamespace(stdout=json.dumps(sample).encode()))
    with pytest.raises(ValueError):
        monitor.remote(dict(remote_host='185.10.158.212',key='fixture',known_hosts='fixture'),'nl-amsterdam-1')
