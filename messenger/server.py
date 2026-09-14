"""Standalone closed relay daemon; deployment owns config, identity and volume."""
import argparse
import json
import os
from pathlib import Path
import signal
import stat
import threading

import RNS
from .relay import ClosedRelay,Spool


def read_owned(path, limit, *, private=False):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_nlink!=1 or info.st_mode&0o022:
            raise ValueError('Unsafe operator-owned file')
        if private and info.st_mode&0o007:raise ValueError('Identity is accessible to other users')
        data=os.read(fd,limit+1)
        if len(data)>limit:raise ValueError('Operator file too large')
        return data
    finally:os.close(fd)


def validate_volume(root, marker):
    root=Path(root)
    info=root.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_dev==root.parent.stat().st_dev
            or not os.path.ismount(root)):
        raise ValueError('Required isolated runtime volume is not mounted')
    if read_owned(root/'.volume-id',128).decode().strip()!=marker:
        raise ValueError('Unexpected runtime volume')


def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate setting')
        result[key]=value
    return result


def preflight(settings):
    settings=Path(settings)
    config=json.loads(read_owned(settings,16384),object_pairs_hook=unique)
    if set(config)!={'volume_id','public_key','allowed_public'}:raise ValueError('Invalid settings')
    if (type(config['volume_id']) is not str or len(config['volume_id'])!=32
            or any(c not in '0123456789abcdef' for c in config['volume_id'])):
        raise ValueError('Invalid volume ID')
    if type(config['allowed_public']) is not list or not 1<=len(config['allowed_public'])<=100:
        raise ValueError('Invalid closed pilot list')
    allowed=[bytes.fromhex(value) for value in config['allowed_public']]
    if any(len(value)!=64 for value in allowed) or len(set(allowed))!=len(allowed):
        raise ValueError('Invalid pilot identities')
    base=settings.parent
    root=base/'state'
    validate_volume(root,config['volume_id'])
    node=RNS.Identity.from_bytes(read_owned(base/'node.identity',128,private=True))
    if node is None or node.get_public_key().hex()!=config['public_key']:
        raise ValueError('Node identity does not match pinned bootstrap')
    # No auto-generation of an RNS config outside the bounded volume.
    read_owned(root/'rns/config',4096)
    return root,node,allowed


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--settings',required=True)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    root,node,allowed=preflight(args.settings)
    if args.check:
        print('Mailbox preflight passed',flush=True)
        return
    rns=RNS.Reticulum(configdir=str(root/'rns'),loglevel=0)
    spool=Spool(root/'spool')
    relay=ClosedRelay(node,spool,allowed_public=allowed)
    stop=threading.Event()
    signal.signal(signal.SIGTERM,lambda *_:stop.set())
    signal.signal(signal.SIGINT,lambda *_:stop.set())
    try:
        print(json.dumps(dict(event='ready',public_key=node.get_public_key().hex(),allowed=len(allowed))),flush=True)
        while not stop.is_set():
            spool.expire()
            relay.destination.announce()
            stop.wait(60)
    finally:
        # Stop the listener before SQLite; service cgroup kills any remaining
        # daemon workers. RNS also runs its registered exit handler on exit.
        RNS.Reticulum.exit_handler()
        spool.close()


if __name__=='__main__':main()
