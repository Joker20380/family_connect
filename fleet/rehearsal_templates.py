"""Non-shell argv and namespace-local network policy for disposable rehearsals."""

import re
import datetime

from .contracts import fail

CURRENT = '/opt/family-connect/current'
UNIT_NAMES = ('prepare','awg','tcp','mesh','snapshot','monitoring')
SYSCTL = b'net.ipv4.ip_forward = 1\n'
TABLE = 'family_connect_rehearsal'


def nftables(interface):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,14}', interface) or interface in ('lo','fcrh0'):
        fail('rehearsal_uplink')
    return ('''table inet family_connect_rehearsal {
 chain input {
  type filter hook input priority 0; policy accept;
  iifname "lo" accept
  ct state established,related accept
  udp dport 51827 accept
  tcp dport { 4443, 18444 } accept
  tcp dport 19727 drop
 }
 chain forward {
  type filter hook forward priority 0; policy accept;
  iifname "fcrh0" ip saddr != 10.203.217.2 drop
  iifname "fcrh0" ip daddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16 } drop
  iifname "fcrh0" oifname "UPLINK" accept
  iifname "fcrh0" drop
  oifname "fcrh0" ct state established,related accept
  oifname "fcrh0" drop
 }
 chain postrouting {
  type nat hook postrouting priority srcnat; policy accept;
  ip saddr 10.203.217.0/30 oifname "UPLINK" masquerade
 }
}
''').replace('UPLINK',interface).encode()


def units(bundle_id, instance_id, lifetime, expires_at=None):
    if (not re.fullmatch(r'gw-[0-9a-f]{32}', bundle_id)
            or not re.fullmatch(r'fleet-rehearsal-[a-z0-9-]+', instance_id)
            or type(lifetime) is not int or not 1 <= lifetime <= 14400):
        fail('rehearsal_template_binding')
    config = '/etc/family-connect/rehearsal/'+bundle_id
    state = '/run/family-connect-rehearsal/'+instance_id
    commands = {
        'prepare': '/usr/bin/test -r '+config+'/metadata.json',
        'awg': CURRENT+'/bin/amneziawg-go -f fcrh0',
        'tcp': CURRENT+'/bin/xray run -config '+config+'/tcp.json',
        'mesh': CURRENT+'/bin/gateway -family-config '+config+'/profile/gateway.json -listen 0.0.0.0:18444'
                +' -duration '+str(lifetime)+'s -directory-export '+state+'/ready.json',
        'snapshot': '/usr/bin/python3 -I -B '+CURRENT+'/runtime/ready_wait.py '+state+'/ready.json',
        'monitoring': '/usr/bin/python3 -I -B '+CURRENT+'/runtime/monitoring.py --metadata '+config+'/metadata.json',
    }
    result = {}
    for index, name in enumerate(UNIT_NAMES):
        predecessor = ('network-online.target' if index == 0 else 'fc-rehearsal-'+UNIT_NAMES[index-1]+'.service')
        privileged = name in ('prepare','awg')
        oneshot = name in ('prepare','snapshot')
        unit = ('[Unit]\nDescription=Disposable Family Connect rehearsal '+name+'\nAfter='+predecessor+'\n'
                'Requires='+predecessor+'\nStartLimitIntervalSec=60\nStartLimitBurst=3\n\n[Service]\n'
                'Type='+('oneshot' if oneshot else 'simple')+'\nUser='+('root' if privileged else 'fc-rehearsal')+'\n'
                'Group='+('root' if privileged else 'fc-rehearsal')+'\nWorkingDirectory='+CURRENT+'\n'
                'ExecStartPre=/usr/bin/python3 -I -B '+CURRENT+'/runtime/expiry_guard.py '+config+'/metadata.json\n'
                'ExecStart='+commands[name]+'\nRestart='+('no' if oneshot else 'on-failure')+'\nRestartSec=3\n'
                'TimeoutStartSec=45\nTimeoutStopSec=30\nKillMode=control-group\nUMask=0077\n'
                'NoNewPrivileges=yes\nProtectSystem=strict\nProtectHome=yes\nPrivateTmp=yes\n'
                'ProtectKernelTunables=yes\nProtectKernelModules=yes\nProtectControlGroups=yes\n'
                'LockPersonality=yes\nRestrictSUIDSGID=yes\nRestrictRealtime=yes\n'
                'CapabilityBoundingSet='+('CAP_NET_ADMIN' if name=='awg' else '')+'\n'
                'RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6'+(' AF_NETLINK' if name=='awg' else '')+'\n'
                'StandardOutput=null\nStandardError=null\n')
        if oneshot:
            unit += 'RemainAfterExit=yes\n'
        else:
            unit += 'RuntimeMaxSec='+str(lifetime)+'\n'
        if name == 'awg':
            unit += ('ReadWritePaths=/run/family-connect-rehearsal\nRuntimeDirectory=wireguard\n'
                     'ReadWritePaths=/run/wireguard\nDevicePolicy=closed\nDeviceAllow=/dev/net/tun rw\n'
                     'ExecStartPost=/usr/bin/python3 -I -B '+CURRENT+'/runtime/awg_setup.py '+config+'/awg.conf\n')
        if name == 'mesh':
            unit += ('EnvironmentFile='+config+'/publisher.env\nReadWritePaths='+state+'\n'
                     'RuntimeDirectory=family-connect-rehearsal/'+instance_id+'\nRuntimeDirectoryMode=0700\n'
                     'RuntimeDirectoryPreserve=yes\n')
        if name == 'monitoring':
            unit += 'IPAddressDeny=any\nIPAddressAllow=localhost\n'
        unit += '\n[Install]\nWantedBy=multi-user.target\n'
        result['fc-rehearsal-'+name+'.service'] = unit.encode()
    if expires_at is not None:
        deadline=datetime.datetime.fromtimestamp(expires_at,datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        result['fc-rehearsal-expiry.timer']=('[Unit]\nDescription=Absolute disposable rehearsal deadline\n'
            '[Timer]\nOnCalendar='+deadline+'\nAccuracySec=1s\nPersistent=true\n'
            'Unit=fc-rehearsal-expiry.service\n[Install]\nWantedBy=timers.target\n').encode()
        result['fc-rehearsal-expiry.service']=('[Unit]\nDescription=Stop expired disposable rehearsal\n'
            '[Service]\nType=oneshot\nUser=root\nGroup=root\nExecStart=/usr/bin/systemctl stop '
            +' '.join('fc-rehearsal-'+name+'.service' for name in reversed(UNIT_NAMES))+'\n'
            'NoNewPrivileges=yes\nProtectSystem=strict\nProtectHome=yes\nCapabilityBoundingSet=\n'
            'RestrictAddressFamilies=AF_UNIX\n').encode()
    return result
