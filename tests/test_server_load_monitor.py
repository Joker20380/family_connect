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
