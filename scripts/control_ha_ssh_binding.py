"""Read-only on-disk SSH dispatch bindings, never a live writer fence or approval."""
import argparse
import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import pwd
import re
import resource
import shlex
import signal
import subprocess
import sys
import time

from scripts import control_ha_writer_preflight as writers

require = writers.census.require
FIELDS = frozenset(('forcecommand', 'authorizedkeysfile', 'authorizedkeyscommand',
    'authorizedkeyscommanduser', 'authorizedprincipalsfile', 'authorizedprincipalscommand',
    'trustedusercakeys', 'permitrootlogin', 'pubkeyauthentication', 'passwordauthentication',
    'kbdinteractiveauthentication', 'authenticationmethods', 'usepam', 'usedns'))
HOSTS = {'RU': '185.251.89.19', 'NL1': '185.10.158.212', 'NL2': '185.10.158.196'}
KEY = re.compile(r'(?:ssh-(?:rsa|ed25519)|ecdsa-sha2-nistp(?:256|384|521)|'
                 r'sk-(?:ssh-ed25519|ecdsa-sha2-nistp256)@openssh.com)\Z')
LIMIT = 128 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def command_record(command):
    require(type(command) is str and 0 < len(command) <= 4096, 'COMMAND_BOUNDS')
    tokens = shlex.split(command)
    require(bool(tokens), 'EMPTY_COMMAND')
    return dict(sha256=digest(command.encode()), argc=len(tokens),
                capture_reference_mentioned=any('capture_receiver' in token or 'capture_launch' in token or
                    'FC_CONTROL_CAPTURE_GATE' in token for token in tokens), admission_proved=False)


def split_quoted(value, delimiter, limit=None):
    parts, start, quoted, escaped = [], 0, False, False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
        elif character == '\\':
            escaped = True
        elif character == '"':
            quoted = not quoted
        elif not quoted and character in delimiter:
            if value[start:index]:
                parts.append(value[start:index])
                if limit is not None and len(parts) == limit:
                    return parts + [value[index + 1:].lstrip()]
            start = index + 1
    require(not quoted and not escaped, 'KEY_QUOTING')
    parts.append(value[start:])
    return [part for part in parts if part]


def keys(raw):
    require(type(raw) is bytes and len(raw) <= LIMIT, 'KEY_FILE_BOUNDS')
    records = []
    for line in raw.decode('utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        require(len(line) <= 16384 and len(records) < 256, 'KEY_LINE_BOUNDS')
        fields = split_quoted(line.strip(), ' \t', 1)
        require(len(fields) == 2, 'KEY_LINE')
        options = []
        if not KEY.fullmatch(fields[0]):
            options = split_quoted(fields[0], ',')
            fields = split_quoted(fields[1], ' \t', 1)
        require(len(fields) == 2 and KEY.fullmatch(fields[0]), 'KEY_TYPE')
        payload_fields = split_quoted(fields[1], ' \t', 1)
        require(bool(payload_fields), 'KEY_PAYLOAD')
        payload = payload_fields[0]
        try:
            require(bool(base64.b64decode(payload, validate=True)), 'KEY_PAYLOAD')
        except ValueError:
            raise ValueError('KEY_PAYLOAD') from None
        forced = [option for option in options if option.startswith('command=')]
        require(len(forced) <= 1, 'DUPLICATE_KEY_COMMAND')
        command = None
        if forced:
            value = forced[0][len('command='):]
            require(value.startswith('"') and value.endswith('"'), 'KEY_COMMAND_QUOTES')
            decoded = shlex.split(value)
            require(len(decoded) == 1, 'KEY_COMMAND_SHAPE')
            command = command_record(decoded[0])
        records.append(dict(line_sha256=digest(line.encode()), command=command,
                            restricted='restrict' in options, certificate_authority='cert-authority' in options,
                            admission_proved=False))
    return dict(sha256=digest(raw), entries=records, key_count=len(records),
                no_per_key_command=sum(record['command'] is None for record in records))


def policy(raw):
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT, 'POLICY_BOUNDS')
    result = {}
    for line in raw.decode('utf-8').splitlines():
        parts = line.split(' ', 1)
        require(len(parts) == 2, 'POLICY_LINE')
        name, value = parts
        if name in FIELDS:
            require(name not in result, 'DUPLICATE_POLICY_FIELD')
            result[name] = value
    require(set(result) == FIELDS, 'MISSING_POLICY_FIELD')
    require(result['usedns'] == 'no', 'DNS_MATCH_CONTEXT_UNRESOLVED')
    for field in ('pubkeyauthentication', 'passwordauthentication', 'kbdinteractiveauthentication', 'usepam'):
        require(result[field] in ('yes', 'no'), 'AUTH_POLICY_VALUE')
    require(result['permitrootlogin'] in ('yes', 'no', 'prohibit-password', 'without-password',
                                        'forced-commands-only'), 'ROOT_POLICY_VALUE')
    return result


def query(account, source, local, port):
    require(account in {name for values in writers.ACCOUNTS.values() for name in values}, 'ACCOUNT_SCOPE')
    for address in (source, local):
        require(str(ipaddress.ip_address(address)) == address, 'ADDRESS_SHAPE')
    require(type(port) is int and 1 <= port <= 65535, 'PORT_SHAPE')
    context = f'user={account},host={source},addr={source},laddr={local},lport={port}'
    result = subprocess.run(['/usr/sbin/sshd', '-T', '-C', context], capture_output=True, timeout=5,
                            env={'PATH': os.defpath, 'LC_ALL': 'C'})
    require(result.returncode == 0, 'SSHD_QUERY_FAILED')
    return policy(result.stdout)


def key_paths(value, account):
    if value == 'none':
        return []
    result = []
    for entry in value.split():
        require(entry in ('.ssh/authorized_keys', '.ssh/authorized_keys2',
                          '%h/.ssh/authorized_keys', '%h/.ssh/authorized_keys2'), 'KEY_PATH_NOT_QUALIFIED')
        relative = entry.removeprefix('%h/')
        result.append(Path(account.pw_dir) / relative)
    require(0 < len(result) <= 2 and len(result) == len(set(result)), 'KEY_PATHS')
    return result


def key_files(value, account):
    result = []
    for candidate in key_paths(value, account):
        try:
            require(all(not item.is_symlink() for item in (candidate, *candidate.parents)), 'KEY_PATH_SYMLINK')
            record = dict(status='OBSERVED', **keys(writers.bounded(candidate)))
        except FileNotFoundError:
            record = dict(status='ABSENT')
        result.append(dict(path_sha256=digest(str(candidate).encode()), **record))
    return result


def snapshot(node, contexts, local, port):
    result = {}
    for name in writers.ACCOUNTS[node]:
        try:
            account = pwd.getpwnam(name)
        except KeyError:
            result[name] = dict(status='ACCOUNT_ABSENT')
            continue
        samples = {}
        for label, address in contexts.items():
            effective = query(name, address, local, port)
            forced = effective['forcecommand']
            samples[label] = dict(policy_sha256=writers.census.digest(writers.census.canonical(effective)),
                force_command=None if forced == 'none' else command_record(forced),
                key_files=key_files(effective['authorizedkeysfile'], account),
                dynamic_keys=effective['authorizedkeyscommand'] != 'none',
                certificate_authority=effective['trustedusercakeys'] != 'none',
                dynamic_principals=effective['authorizedprincipalscommand'] != 'none',
                password_authentication=effective['passwordauthentication'],
                pubkey_authentication=effective['pubkeyauthentication'],
                permit_root_login=effective['permitrootlogin'],
                admission_proved=False)
        result[name] = dict(status='OBSERVED', uid=account.pw_uid, contexts=samples)
    return result


def collect(node):
    require(node in HOSTS, 'NODE_SCOPE')
    connection = os.environ.get('SSH_CONNECTION', '').split()
    require(len(connection) == 4, 'SSH_CONNECTION_REQUIRED')
    source, remote_port, local, local_port = connection
    require(str(ipaddress.ip_address(source)) == source and local == HOSTS[node] and
            remote_port.isdecimal() and local_port.isdecimal(), 'SSH_CONNECTION_BINDING')
    contexts = {'current_connection': source, **HOSTS}
    started = time.time_ns()
    before = snapshot(node, contexts, local, int(local_port))
    after = snapshot(node, contexts, local, int(local_port))
    require(before == after, 'SSH_BINDINGS_CHANGED')
    return dict(schema=1, node=node, started_at_ns=started, finished_at_ns=time.time_ns(),
        contexts_sha256=writers.census.digest(writers.census.canonical(contexts)), accounts=before,
        observations_equal=True, source='ON_DISK_DEFAULT_SSHD_CONFIGURATION',
        unresolved=['LIVE_DAEMON_CONFIG_NOT_ATTESTED', 'OTHER_SOURCE_ADDRESSES_AND_NAT_NOT_COVERED',
                    'COMMAND_SOURCE_AND_GATE_NOT_ATTESTED', 'ROOT_AND_MANUAL_DISPATCH_NOT_CLOSED',
                    'EXTERNAL_OPERATIONS_NOT_SETTLED', 'INDEPENDENT_APPROVAL_REQUIRED'],
        services_changed=False, ssh_policy_changed=False, commands_dispatched=False,
        all_writers_qualified=False, capture_permitted=False)


def deadline(*arguments):
    raise TimeoutError('OBSERVATION_DEADLINE')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--node', choices=HOSTS, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(90)
    try:
        print(json.dumps(collect(args.node), sort_keys=True))
    except Exception:
        print('SSH_BINDING_REFUSED', file=sys.stderr)
        return 1
    finally:
        signal.alarm(0)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
