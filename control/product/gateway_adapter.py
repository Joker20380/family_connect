"""Local Docker pilot adapter; preserves unmanaged peers and restart persistence."""
import configparser
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess

from device_identity.device import _private_directory
from provisioning.models import GatewayCandidate


class DockerGateway:
    def __init__(self, *, container, keys, run=subprocess.run):
        if type(container) is not str or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}',container):
            raise ValueError('invalid container name')
        self.container, self.keys, self.run = container, Path(keys).absolute(), run

    def _command(self, *args):
        return self.run(['docker','exec',self.container,*args],check=True,
                        capture_output=True,text=True,timeout=3).stdout.strip()

    @staticmethod
    def _safe(fd):
        info=os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or
                stat.S_IMODE(info.st_mode)!=0o600 or info.st_nlink!=1):
            raise ValueError('unsafe gateway file')

    @classmethod
    def _read(cls, directory, name):
        fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
        try:
            cls._safe(fd)
            data=os.read(fd,16385)
            if len(data)>16384:raise ValueError('oversized peer record')
            return data.decode('ascii')
        finally:os.close(fd)

    @staticmethod
    def _parse(raw):
        parser=configparser.ConfigParser(interpolation=None)
        parser.read_string(raw)
        if parser.sections()!=['Peer'] or set(parser['Peer'])!={'publickey','allowedips'}:
            raise ValueError('unsupported saved peer')
        return parser['Peer']['publickey'],{str(ipaddress.ip_network(x.strip())) for x in parser['Peer']['allowedips'].split(',')}

    @staticmethod
    def _persist(directory, name, raw):
        temporary='.product-'+secrets.token_hex(16)
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory)
        try:
            with os.fdopen(fd,'w') as stream:
                stream.write(raw);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,name,src_dir_fd=directory,dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:os.unlink(temporary,dir_fd=directory)
            except FileNotFoundError:pass

    def apply(self, identity, public_key, addresses, *, present, gateway):
        if not re.fullmatch('[0-9a-f]{32}',identity):raise ValueError('invalid device')
        GatewayCandidate.valid_key(public_key)
        routes={str(ipaddress.ip_network(a,strict=True)) for a in addresses}
        ipv4=[ipaddress.ip_network(a) for a in routes if ipaddress.ip_network(a).version==4]
        if len(ipv4)!=1 or ipv4[0].prefixlen!=32:raise ValueError('pilot IPv4 host required')
        n=int(ipv4[0].network_address)-int(ipaddress.ip_address('10.77.0.0'))
        if not 4<=n<=254 or not routes<={f'10.77.0.{n}/32',f'fd77:92::{n:x}/128'}:
            raise ValueError('outside pilot allocation')
        # Validate that persistence really belongs to this container's /keys mount.
        mounts=json.loads(self.run(['docker','inspect','--format','{{json .Mounts}}',self.container],
            check=True,capture_output=True,text=True,timeout=3).stdout)
        if not any(m.get('Destination')=='/keys' and Path(m['Source']).resolve()==self.keys.resolve() for m in mounts):
            raise ValueError('gateway persistence mount mismatch')
        if '# family-connect-dynamic-peers-v1' not in self._command('cat','/usr/local/bin/family-connect-wg'):
            raise ValueError('gateway persistence unsupported')
        if '# family-connect-peer-sync-v1' not in self._command('cat','/usr/local/bin/family-connect-peer-sync'):
            raise ValueError('gateway peer synchronization unsupported')
        if (self._command('wg','show','wg0','public-key')!=gateway['public_key'] or
                self._command('wg','show','wg0','listen-port')!=str(gateway['port'])):
            raise ValueError('gateway identity mismatch')
        with _private_directory(self.keys) as keys:
            lock=os.open('.enrollment.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600,dir_fd=keys)
            try:
                self._safe(lock);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                # Original pilot peers never become product-owned implicitly.
                for name in ('android.pub','linux.pub'):
                    try:static=self._read(keys,name).strip()
                    except FileNotFoundError:continue
                    if static==public_key:raise ValueError('unmanaged static peer')
                with _private_directory(self.keys/'peers') as peers:
                    name=f'product-{identity}.conf'
                    owned=False
                    for saved in os.listdir(peers):
                        if not saved.endswith('.conf'):continue
                        key,allowed=self._parse(self._read(peers,saved))
                        if saved==name:
                            if key!=public_key or allowed!=routes:raise ValueError('owned record mismatch')
                            owned=True
                        elif key==public_key or (present and any(ipaddress.ip_network(a).overlaps(ipaddress.ip_network(b))
                            for a in allowed for b in routes if ipaddress.ip_network(a).version==ipaddress.ip_network(b).version)):
                            raise ValueError('unmanaged allocation conflict')
                    current=self._command('wg','show','wg0','allowed-ips')
                    live={}
                    for line in current.splitlines():
                        key,raw=line.split('\t',1)
                        live[key]={str(ipaddress.ip_network(x)) for x in raw.replace(',',' ').split() if x!='(none)'}
                    for key,allowed in live.items():
                        if present and key==public_key and allowed!=routes:raise ValueError('live key allocation conflict')
                        if present and key!=public_key and any(ipaddress.ip_network(a).overlaps(ipaddress.ip_network(b))
                            for a in allowed for b in routes if ipaddress.ip_network(a).version==ipaddress.ip_network(b).version):
                            raise ValueError('live address allocation conflict')
                    if present:
                        if public_key in live and not owned:raise ValueError('unmanaged live peer')
                        self._persist(peers,name,f'[Peer]\nPublicKey = {public_key}\nAllowedIPs = {",".join(sorted(routes))}\n')
                    else:
                        # Persist removal first. A crash before wg remove is retried
                        # from the durable outbox; restart cannot resurrect the file.
                        if owned:os.unlink(name,dir_fd=peers);os.fsync(peers)
                    # The gateway obtains this same lock and reads current intent.
                    # Late Docker commands therefore cannot replay a stale install.
                    fcntl.flock(lock,fcntl.LOCK_UN)
                    self._command('/usr/local/bin/family-connect-peer-sync',identity,public_key)
                    after=self._command('wg','show','wg0','allowed-ips')
                    actual={}
                    for line in after.splitlines():
                        key,raw=line.split('\t',1)
                        actual[key]={str(ipaddress.ip_network(x)) for x in raw.replace(',',' ').split() if x!='(none)'}
                    if (present and actual.get(public_key)!=routes) or (not present and public_key in actual):
                        raise RuntimeError('gateway verification failed')
            finally:os.close(lock)
