"""RU/EN: register a public device key on the controlled pilot gateway.

Run as operator on the gateway host; no private client key is accepted.
Existing peers are preserved. Requires gateway.sh with peers/*.conf startup loading
for persistence across gateway replacement. Does not restart the gateway.
"""
import argparse
import base64
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import subprocess

def register(peer, keys, container):
    if set(peer) != {'version','public_key','address','ipv6'} or peer['version'] != 1:
        raise ValueError('invalid peer record')
    raw = base64.b64decode(peer['public_key'],validate=True)
    if len(raw)!=32 or not any(raw) or base64.b64encode(raw).decode()!=peer['public_key']:
        raise ValueError('invalid public key')
    address=ipaddress.IPv4Address(peer['address'])
    n=int(address)-int(ipaddress.IPv4Address('10.77.0.0'))
    if not 4<=n<=254 or peer['ipv6']!=f'fd77:92::{n:x}':
        raise ValueError('invalid allocation')
    allowed=f'{address}/32,{peer["ipv6"]}/128'
    keys=Path(keys).resolve(strict=True)
    peers=keys/'peers';peers.mkdir(mode=0o700,exist_ok=True)
    # Enforce that restart persistence is supported before adding a peer.
    result=subprocess.run(['docker','exec',container,'cat','/usr/local/bin/family-connect-wg'],capture_output=True,text=True,check=True)
    if '# family-connect-dynamic-peers-v1' not in result.stdout:
        raise RuntimeError('Gateway image must be upgraded to dynamic peers support before enrollment; no changes made')
    with (keys/'.enrollment.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        current=subprocess.run(['docker','exec',container,'wg','show','wg0','allowed-ips'],capture_output=True,text=True,check=True).stdout
        for line in current.splitlines():
            public, routes=line.split('\t',1)
            networks=[ipaddress.ip_network(x.strip()) for x in routes.replace(',',' ').split() if x!='(none)']
            if public==peer['public_key'] and {str(x) for x in networks}!={f'{address}/32',f'{peer["ipv6"]}/128'}:
                raise ValueError('device key already assigned another address')
            if public!=peer['public_key'] and any((net.version==4 and address in net) or (net.version==6 and ipaddress.IPv6Address(peer['ipv6']) in net) for net in networks):
                raise ValueError('address already assigned')
        config=f'[Peer]\nPublicKey = {peer["public_key"]}\nAllowedIPs = {allowed}\n'
        destination=peers/f'{n}.conf'
        for saved in peers.glob('*.conf'):
            content=saved.read_text()
            if saved==destination and content!=config:raise ValueError('address already reserved')
            if saved!=destination and peer['public_key'] in content:raise ValueError('key already reserved')
        # Persist before applying; on an apply failure the address remains reserved for a safe retry.
        if not destination.exists():
            with destination.open('x') as file:file.write(config)
        subprocess.run(['docker','exec',container,'wg','set','wg0','peer',peer['public_key'],'allowed-ips',allowed],check=True)
    print('Public peer registered and persisted; existing peers were preserved.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--peer',type=Path,required=True)
    parser.add_argument('--keys',type=Path,required=True);parser.add_argument('--container',required=True)
    args=parser.parse_args();os.umask(0o077)
    register(json.loads(args.peer.read_text()),args.keys,args.container)
