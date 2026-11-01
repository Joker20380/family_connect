import subprocess
import sys
import time


def main():
    config = sys.argv[1]
    if not config.startswith('/etc/family-connect/rehearsal/gw-') or not config.endswith('/awg.conf'):
        raise SystemExit(1)
    for attempt in range(50):
        result = subprocess.run(['ip','link','show','dev','fcrh0'],capture_output=True)
        if result.returncode == 0:
            break
        time.sleep(0.1)
    else:
        raise SystemExit(1)
    for argv in (['/opt/family-connect/current/bin/awg','setconf','fcrh0',config],
                 ['ip','address','replace','10.203.217.1/30','dev','fcrh0'],
                 ['ip','link','set','dev','fcrh0','mtu','1280','up']):
        if subprocess.run(argv,capture_output=True).returncode:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
