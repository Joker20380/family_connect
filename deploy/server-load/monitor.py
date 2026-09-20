"""Read-only host resource samples; no profiles, peer identifiers or traffic history."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import time


def sample(interface):
    cpu = [int(x) for x in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
    net = Path('/sys/class/net') / interface / 'statistics'
    return dict(clock=time.monotonic(), total=sum(cpu), idle=cpu[3]+cpu[4],
                rx=int((net/'rx_bytes').read_text()), tx=int((net/'tx_bytes').read_text()))


def utilization(before, after, country, capacity_mbps, now):
    elapsed=after['clock']-before['clock'];total=after['total']-before['total']
    idle=after['idle']-before['idle'];rx=after['rx']-before['rx'];tx=after['tx']-before['tx']
    if not (0<elapsed<=60 and total>0 and 0<=idle<=total and min(rx,tx)>=0):
        raise ValueError('Invalid sampling interval or counters')
    cpu=100*(1-idle/total);rx_mbps=rx*8/elapsed/1_000_000;tx_mbps=tx*8/elapsed/1_000_000
    known=type(capacity_mbps) in (int,float) and math.isfinite(capacity_mbps) and capacity_mbps>0
    # Full-duplex link: compare the busiest direction, not RX+TX (VPN counts twice).
    channel=min(100,100*max(rx_mbps,tx_mbps)/capacity_mbps) if known else None
    return dict(country=country,observed_at=int(now),cpu_percent=round(cpu,1),
                rx_mbps=round(rx_mbps,3),tx_mbps=round(tx_mbps,3),
                capacity_mbps=capacity_mbps if known else None,
                channel_percent=round(channel,1) if known else None,
                load_percent=round(max(cpu,channel),1) if known else None,
                reason=None if known else 'capacity-unknown')


def atomic(path, value):
    path=Path(path);temporary=path.with_suffix('.pending')
    temporary.write_text(json.dumps(value,separators=(',',':'))+'\n');temporary.chmod(0o644)
    os.replace(temporary,path)


def remote(config):
    result=subprocess.run(['/usr/bin/ssh','-T','-i',config['key'],
        '-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=4',
        '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+config['known_hosts'],
        'root@186.246.45.246','load'],capture_output=True,timeout=6,check=True)
    if len(result.stdout)>4096:raise ValueError('Oversized sample')
    value=json.loads(result.stdout)
    if value['country']!='nl' or not -15<=time.time()-value['observed_at']<=45:
        raise ValueError('Stale sample')
    return value


def main():
    parser=argparse.ArgumentParser();parser.add_argument('config');args=parser.parse_args()
    path=Path(args.config);config=json.loads(path.read_text());before=sample(config['interface'])
    while True:
        time.sleep(15)
        config=json.loads(path.read_text());after=sample(config['interface'])
        try:value=utilization(before,after,config['country'],config['capacity_mbps'],time.time())
        except ValueError:
            before=after;continue
        before=after;atomic(config['snapshot'],value)
        if config.get('public'):
            values={'ru':value}
            try:values['nl']=remote(config)
            except (OSError,ValueError,KeyError,subprocess.SubprocessError):pass
            atomic(config['public'],dict(schema=1,gateways=values))

if __name__=='__main__':main()
