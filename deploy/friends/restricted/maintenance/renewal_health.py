import json
from pathlib import Path
import re
import subprocess
import time

from credential_renewal import Rejected, canonical, parse, read_private, require

CONFIGURATION_PATH = Path('/etc/fc-credential-renewal-health.json')


def evaluate_health(timer, service, now_usec):
    require(type(now_usec) is int and now_usec >= 0, 'CLOCK_INVALID')
    require(set(timer) == {'ActiveState','LastTriggerUSecMonotonic'}, 'HEALTH_SCHEMA')
    require(set(service) == {'Result','ExecMainStatus'}, 'HEALTH_SCHEMA')
    last = int(timer['LastTriggerUSecMonotonic'])
    alerts = []
    if timer['ActiveState'] != 'active':
        alerts.append('CONTROLLER_DISABLED_CRITICAL')
    if last > now_usec or (last == 0 and now_usec > 15*60*1000000) or now_usec-last > 20*60*1000000:
        alerts.append('CONTROLLER_STALE_CRITICAL')
    if service['Result'] != 'success' or service['ExecMainStatus'] != '0':
        alerts.append('CONTROLLER_FAILURE_OR_MAINTENANCE_REQUIRED')
    return dict(schema=1,result='HEALTHY' if not alerts else 'CRITICAL',alerts=alerts,
                remote_alert_delivery='UNAVAILABLE',credential_mutations=0)


def read(unit, fields):
    require(type(unit) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}\.(?:timer|service)',unit), 'HEALTH_UNIT')
    process = subprocess.run(['/usr/bin/systemctl','show',unit,'--property='+','.join(fields)],
                             capture_output=True,timeout=10,check=False)
    require(process.returncode == 0 and len(process.stdout) < 8192, 'HEALTH_READ_FAILED')
    value = dict(line.split('=',1) for line in process.stdout.decode().splitlines())
    if 'LastTriggerUSecMonotonic' in fields:
        require(unit.endswith('.timer'), 'HEALTH_UNIT')
        escaped = ''.join(chr(value) if chr(value).isascii() and chr(value).isalnum() else '_'+format(value,'02x')
                          for value in unit.encode())
        raw = subprocess.run(['/usr/bin/busctl','--system','get-property','org.freedesktop.systemd1',
            '/org/freedesktop/systemd1/unit/'+escaped,
            'org.freedesktop.systemd1.Timer','LastTriggerUSecMonotonic'],
            capture_output=True,timeout=10,check=False)
        require(raw.returncode == 0 and len(raw.stdout) < 128, 'HEALTH_CLOCK_READ_FAILED')
        parts = raw.stdout.decode().split()
        require(len(parts) == 2 and parts[0] == 't' and parts[1].isdigit(), 'HEALTH_CLOCK_SCHEMA')
        value['LastTriggerUSecMonotonic'] = parts[1]
    return value


def main():
    try:
        config = parse(read_private(CONFIGURATION_PATH))
        require(type(config) is dict and set(config) == {'schema','timer','service'} and type(config['schema']) is int and
                config['schema'] == 1 and type(config['timer']) is str and type(config['service']) is str and
                config['timer'].endswith('.timer') and config['service'] == config['timer'][:-6]+'.service', 'HEALTH_SCHEMA')
        timer = read(config['timer'],('ActiveState','LastTriggerUSecMonotonic'))
        service = read(config['service'],('Result','ExecMainStatus'))
        result = evaluate_health(timer,service,time.monotonic_ns()//1000)
    except Exception as error:
        result = dict(schema=1,result='CRITICAL',cause=str(error) if isinstance(error,Rejected) else 'HEALTH_UNAVAILABLE',
                      remote_alert_delivery='UNAVAILABLE',credential_mutations=0)
    print(canonical(result).decode())
    if result['result'] != 'HEALTHY':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
