"""Installed AWG lifecycle acceptance inside the isolated test container only."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


def command(*arguments, check=True):
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=15)
    if check and result.returncode:
        raise RuntimeError('Isolated lifecycle command failed: '+Path(arguments[0]).name)
    return result.stdout.strip() if check else result


def query(*arguments):
    return json.loads(command(*arguments))


def snapshot():
    dns = command('resolvconf', '-l', check=False)
    assert dns.returncode == 0 or (dns.returncode == 1 and not dns.stdout.strip() and
                                  not list(Path('/run/resolvconf/interfaces').glob('*')))
    return dict(rules={family: query('ip', '-j', family, 'rule', 'show') for family in ('-4', '-6')},
        routes={family: query('ip', '-j', family, 'route', 'show', 'table', 'all') for family in ('-4', '-6')},
        nft=query('nft', '-j', 'list', 'ruleset'), dns=dns.stdout.strip(), resolver=Path('/etc/resolv.conf').read_bytes(),
        mark=command('sysctl', '-n', 'net.ipv4.conf.all.src_valid_mark'))


def main():
    identifier, host_netns, expected_address = sys.argv[1:]
    assert Path('/.dockerenv').exists() and str(os.stat('/proc/self/ns/net').st_ino) != host_netns
    assert os.geteuid() == 0 and re.fullmatch('fcawg[a-f0-9]{8}', identifier)
    helper = '/usr/local/lib/family-connect-awg/helper'
    loader = importlib.machinery.SourceFileLoader('fc_checked_awg', helper)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    def healthy(interface, expected):
        assert command('curl', '--noproxy', '*', '--interface', 'if!'+interface, '--silent', '--fail',
                       '--max-time', '10', 'http://10.78.0.1:8080/') == 'family-connect-awg-test'
        stamps = module.command(module.BIN+'/awg', 'show', interface, 'latest-handshakes')
        assert any(0 <= time.time()-int(line.split()[1]) < 30 for line in stamps.splitlines())
    module.healthy = healthy
    for family in ('-4', '-6'):
        command('ip', family, 'rule', 'add', 'priority', '10617', 'table', 'main', 'suppress_prefixlength', '0')
    command('nft', 'add', 'table', 'inet', 'fc_accept_foreign')
    baseline = snapshot()
    generations = set()
    for mode in ('disconnect', 'process-crash', 'restart'):
        sys.argv = ['helper', 'up', identifier]
        try:
            module.main()
        except Exception:
            print(json.dumps(dict(rules={family: query('ip', '-j', family, 'rule', 'show') for family in ('-4', '-6')},
                tables=query('nft', '-j', 'list', 'tables'))), flush=True)
            for family in ('ip', 'ip6'):
                result = command('nft', 'list', 'table', family, 'wg-quick-'+identifier, check=False)
                print('\n'.join(result.stdout.splitlines()[:5]), flush=True)
            raise
        assigned = query('ip', '-j', 'address', 'show', 'dev', identifier)
        assert any(address['local'] == expected_address for address in assigned[0]['addr_info'])
        journal = Path('/run/family-connect-awg/active.json')
        record = json.loads(journal.read_text())
        assert record['ready'] and record['generation'] not in generations
        generations.add(record['generation'])
        assert command('sh', '/source/clients/linux/install-awg.sh', '/source', '/opt/awg31', check=False).returncode != 0
        if mode == 'process-crash':
            matches = []
            for process in Path('/proc').iterdir():
                if not process.name.isdigit():
                    continue
                try:
                    arguments = (process/'cmdline').read_bytes().split(b'\x00')
                    if len(arguments) == 3 and arguments[:2] == [os.fsencode(module.BIN+'/amneziawg-go'), identifier.encode()]:
                        matches.append(int(process.name))
                except (FileNotFoundError, ProcessLookupError):
                    pass
            assert len(matches) == 1
            os.kill(matches[0], signal.SIGKILL)
            deadline = time.monotonic()+3
            while Path('/sys/class/net', identifier).exists() and time.monotonic() < deadline:
                time.sleep(.05)
            assert not Path('/sys/class/net', identifier).exists() and journal.exists()
            for family, address in (('-4', '1.1.1.1'), ('-6', '2606:4700:4700::1111')):
                result = command('ip', family, 'route', 'get', address, check=False)
                assert result.returncode != 0 and any(message in result.stderr.lower() for message in ('unreachable', 'no route to host'))
            assert command('sh', '/source/clients/linux/install-awg.sh', '/source', '/opt/awg31', check=False).returncode != 0
        command(helper, 'down', identifier)
        command(helper, 'down', identifier)
        assert not journal.exists() and snapshot() == baseline
        print('PASS: '+mode+' restores routes/rules/DNS/firewall; foreign resources preserved.', flush=True)
    for family in ('-4', '-6'):
        command('ip', family, 'rule', 'del', 'priority', '10617', 'table', 'main', 'suppress_prefixlength', '0')
    command('nft', 'delete', 'table', 'inet', 'fc_accept_foreign')


if __name__ == '__main__':
    main()
