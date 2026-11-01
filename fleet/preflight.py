"""Fail closed before host writes; only Ubuntu24.04 x86_64 is qualified."""

import ipaddress
from pathlib import Path
import re
import shlex
import subprocess

from .contracts import canonical, exact, fail, load, typed

FIELDS = ('os', 'version', 'architecture', 'kernel', 'cpu', 'ram_mb', 'disk_mb', 'time_sync',
          'tun', 'ipv4', 'ipv6', 'resolver', 'https', 'systemd', 'firewall', 'security',
          'ports_available', 'pending_reboot', 'existing_instance')


def accept(report, instance):
    exact(report, FIELDS)
    if report['os'] != 'ubuntu' or report['version'] != '24.04':
        fail('unsupported_os')
    if report['architecture'] != 'x86_64':
        fail('unsupported_architecture')
    if (not re.fullmatch(r'[0-9]+\.[0-9]+\.[A-Za-z0-9_.+-]+', str(report['kernel']))
            or any(type(report[field]) is not int or report[field] < minimum for field,minimum in
                   [('cpu',1),('ram_mb',1024),('disk_mb',2048)])
            or report['ipv4'] != instance['ipv4'] or report['ipv6'] != instance['ipv6']
            or report['firewall'] not in ('nftables','iptables-nft')
            or report['security'] not in ('apparmor-enforcing','apparmor-supported')
            or report['existing_instance'] not in (None,instance['instance_id'])):
        fail('host_preflight')
    if any(report[name] is not True for name in ('time_sync','tun','resolver','https','systemd','ports_available')):
        fail('host_capability')
    if report['pending_reboot'] is not False:
        fail('pending_reboot')
    return report


class SSH:
    def __init__(self, host, user, known_hosts, fingerprint, runner=subprocess.run):
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            fail('ssh_host')
        if not typed(user,'id') or not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}',user):
            fail('ssh_user')
        path = Path(known_hosts)
        if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o022:
            fail('ssh_known_hosts')
        lines = path.read_text().strip().splitlines()
        if len(lines) != 1 or len(lines[0].split()) != 3 or lines[0].split()[0] != str(address):
            fail('ssh_host_binding')
        result = runner(['ssh-keygen','-lf',str(path),'-E','sha256'],capture_output=True,text=True,timeout=5)
        fields = result.stdout.split()
        if result.returncode or len(fields) < 2 or not fingerprint.startswith('SHA256:') or fields[1] != fingerprint:
            fail('ssh_fingerprint_mismatch')
        self.argv = ['ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
                     '-o','UpdateHostKeys=no','-o','CheckHostIP=yes',
                     '-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no','-o','ForwardAgent=no',
                     '-o','ClearAllForwardings=yes','-o','ControlMaster=no','-o','ConnectTimeout=10',
                     '-o','GlobalKnownHostsFile=/dev/null','-o','UserKnownHostsFile='+str(path),user+'@'+str(address)]
        self.runner = runner

    def probe(self, instance, ports, *, bundle_id=None):
        source = Path(__file__).with_name('probe.py').read_text()
        request = dict(ipv4=instance['ipv4'],ipv6=instance['ipv6'],ports=ports)
        if bundle_id is not None:
            request.update(bundle_id=bundle_id,instance_id=instance['instance_id'])
        result = self.runner(self.argv + ['python3 -I -c ' + shlex.quote(source)],
                             input=canonical(request).decode(),
                             capture_output=True,text=True,timeout=90)
        if result.returncode:
            fail('ssh_probe_failed')
        return load(result.stdout)

    def mutate(self, *arguments):
        fail('live_rehearsal_required')
