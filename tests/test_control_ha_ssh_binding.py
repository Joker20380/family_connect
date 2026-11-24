import json
from types import SimpleNamespace

import pytest

from scripts import control_ha_ssh_binding as ssh


def policy_values():
    result = {name: 'none' for name in ssh.FIELDS}
    result.update(usedns='no', usepam='yes', forcecommand='none', pubkeyauthentication='yes',
                  passwordauthentication='no', kbdinteractiveauthentication='no',
                  permitrootlogin='prohibit-password', authorizedkeysfile='.ssh/authorized_keys .ssh/authorized_keys2')
    return result


def policy_bytes(values=None):
    return ''.join(name + ' ' + value + '\n' for name, value in (values or policy_values()).items()).encode()


def test_keys_parse_quoted_commas_escapes_and_arbitrary_comments_without_export():
    raw = (b'# comment\nrestrict,from="1.2.3.4,5.6.7.8",command="/private/receiver --value \\\"a,b\\\"" '
           b'ssh-ed25519 YWJj owner private-comment " not parsed\n'
           b'ssh-rsa YWJj another-comment\ncert-authority ssh-ed25519 YWJj\n')
    result = ssh.keys(raw)
    assert result['key_count'] == 3 and result['no_per_key_command'] == 2
    assert result['entries'][0]['command']['sha256'] == ssh.digest(b'/private/receiver --value "a,b"')
    assert result['entries'][0]['restricted'] and result['entries'][2]['certificate_authority']
    assert all(not record['admission_proved'] for record in result['entries'])
    output = json.dumps(result)
    for private in ('/private/receiver', '1.2.3.4', 'YWJj', 'private-comment'):
        assert private not in output


@pytest.mark.parametrize('raw', [b'command="unterminated ssh-ed25519 YWJj', b'ssh-unknown YWJj',
    b'command="one",command="two" ssh-ed25519 YWJj', b'command=unquoted ssh-ed25519 YWJj',
    b'command="" ssh-ed25519 YWJj', b'ssh-ed25519 %%%', b'ssh-ed25519', b'ssh-ed25519 ', b'ssh-ed25519 \xff',
    b'x' * (ssh.LIMIT + 1), (b'ssh-ed25519 YWJj\n') * 257])
def test_bad_keys_refuse_instead_of_empty_success(raw):
    with pytest.raises((ValueError, UnicodeError)):
        ssh.keys(raw)


def test_restrict_is_not_a_forced_command_or_capture_admission():
    result = ssh.keys(b'restrict ssh-ed25519 YWJj')
    assert result['no_per_key_command'] == 1 and result['entries'][0]['restricted']
    assert not result['entries'][0]['admission_proved']
    command = ssh.command_record('python -m control.capture_receiver')
    assert command['capture_reference_mentioned'] and not command['admission_proved']


def test_policy_is_complete_with_ignored_non_projected_fields():
    assert ssh.policy(policy_bytes() + b'port 22\n') == policy_values()


@pytest.mark.parametrize('field', ['pubkeyauthentication', 'passwordauthentication',
                                 'kbdinteractiveauthentication', 'usepam', 'permitrootlogin'])
def test_auth_policy_values_are_not_arbitrary_exported_strings(field):
    values = policy_values()
    values[field] = 'private-value'
    with pytest.raises(ValueError, match='POLICY_VALUE'):
        ssh.policy(policy_bytes(values))


@pytest.mark.parametrize('change', ['empty', 'oversized', 'missing', 'duplicate', 'dns', 'malformed'])
def test_unsafe_or_incomplete_policy_refuses(change):
    raw = policy_bytes()
    if change == 'empty':
        raw = b''
    elif change == 'oversized':
        raw += b'x' * ssh.LIMIT
    elif change == 'missing':
        raw = raw.replace(b'forcecommand none\n', b'')
    elif change == 'duplicate':
        raw += b'forcecommand other\n'
    elif change == 'dns':
        raw = raw.replace(b'usedns no', b'usedns yes')
    else:
        raw += b'invalid\n'
    with pytest.raises(ValueError):
        ssh.policy(raw)


def test_query_only_uses_test_mode_with_scoped_context(monkeypatch):
    calls = []

    def run(arguments, **options):
        calls.append((arguments, options))
        return SimpleNamespace(returncode=0, stdout=policy_bytes())

    monkeypatch.setattr(ssh.subprocess, 'run', run)
    assert ssh.query('root', '192.0.2.1', ssh.HOSTS['RU'], 22) == policy_values()
    assert calls[0][0] == ['/usr/sbin/sshd', '-T', '-C',
                          'user=root,host=192.0.2.1,addr=192.0.2.1,laddr=185.251.89.19,lport=22']
    assert calls[0][1]['timeout'] == 5 and 'shell' not in calls[0][1]


@pytest.mark.parametrize('account,address,port', [('other', '192.0.2.1', 22),
    ('root,host=other', '192.0.2.1', 22), ('root', '192.0.2.1,foo=bar', 22), ('root', 'localhost', 22),
    ('root', '192.0.2.1', 0), ('root', '192.0.2.1', True), ('root', '192.0.2.1', 65536)])
def test_query_refuses_unscoped_or_injected_context(monkeypatch, account, address, port):
    monkeypatch.setattr(ssh.subprocess, 'run', lambda *args, **kwargs: pytest.fail('Unexpected execution'))
    with pytest.raises(ValueError):
        ssh.query(account, address, ssh.HOSTS['RU'], port)


def test_query_failure_never_becomes_empty_policy(monkeypatch):
    monkeypatch.setattr(ssh.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout=b''))
    with pytest.raises(ValueError, match='SSHD_QUERY_FAILED'):
        ssh.query('root', '192.0.2.1', ssh.HOSTS['RU'], 22)


def test_only_declared_standard_public_key_files_are_read(tmp_path):
    account = SimpleNamespace(pw_dir=str(tmp_path), pw_uid=1000)
    assert ssh.key_paths('none', account) == []
    assert ssh.key_paths('%h/.ssh/authorized_keys', account) == [tmp_path / '.ssh/authorized_keys']
    result = ssh.key_files('.ssh/authorized_keys', account)
    assert result[0]['status'] == 'ABSENT'
    (tmp_path / '.ssh').mkdir()
    (tmp_path / '.ssh/authorized_keys').write_bytes(b'ssh-ed25519 YWJj')
    result = ssh.key_files('.ssh/authorized_keys', account)
    assert result[0]['key_count'] == 1
    (tmp_path / '.ssh/authorized_keys').unlink()
    (tmp_path / '.ssh/authorized_keys').symlink_to(tmp_path / 'missing')
    with pytest.raises(ValueError, match='KEY_PATH_SYMLINK'):
        ssh.key_files('.ssh/authorized_keys', account)


@pytest.mark.parametrize('value', ['/etc/other', '../../private', '%u', '.ssh/id_ed25519',
                                 '.ssh/authorized_keys .ssh/authorized_keys'])
def test_custom_or_private_paths_require_separate_qualification(value):
    with pytest.raises(ValueError):
        ssh.key_paths(value, SimpleNamespace(pw_dir='/home/fixture'))


@pytest.fixture
def installed(monkeypatch):
    monkeypatch.setenv('SSH_CONNECTION', '192.0.2.1 43210 185.251.89.19 22')
    monkeypatch.setattr(ssh.pwd, 'getpwnam', lambda name: SimpleNamespace(pw_uid=0, pw_dir='/root'))
    monkeypatch.setattr(ssh, 'key_files', lambda value, account: [dict(status='OBSERVED', **ssh.keys(b'ssh-ed25519 YWJj'))])
    calls = []

    def query(*arguments):
        calls.append(arguments)
        return policy_values()

    monkeypatch.setattr(ssh, 'query', query)
    return calls


def test_double_observation_never_closes_root_manual_dispatch(installed):
    result = ssh.collect('RU')
    assert len(installed) == 2 * 4 * len(ssh.writers.ACCOUNTS['RU'])
    assert result['observations_equal']
    for field in ('services_changed', 'ssh_policy_changed', 'commands_dispatched', 'all_writers_qualified', 'capture_permitted'):
        assert result[field] is False
    assert 'ROOT_AND_MANUAL_DISPATCH_NOT_CLOSED' in result['unresolved']
    assert '192.0.2.1' not in json.dumps(result) and '/root' not in json.dumps(result)


def test_forced_and_dynamic_dispatch_remain_unqualified_and_redacted(monkeypatch, installed):
    values = policy_values()
    values.update(forcecommand='/private/forced --secret private-token',
                  authorizedkeyscommand='/private/keys', trustedusercakeys='/private/ca',
                  authorizedprincipalscommand='/private/principals')
    monkeypatch.setattr(ssh, 'query', lambda *args: values)
    result = ssh.collect('RU')
    sample = result['accounts']['root']['contexts']['current_connection']
    assert sample['force_command']['sha256'] == ssh.digest(values['forcecommand'].encode())
    assert sample['dynamic_keys'] and sample['certificate_authority'] and sample['dynamic_principals']
    assert not sample['admission_proved'] and not result['capture_permitted']
    serialized = json.dumps(result)
    assert '/private/' not in serialized and 'private-token' not in serialized


def test_changed_authorized_keys_refuses(monkeypatch, installed):
    calls = []

    def changing_keys(*arguments):
        calls.append(True)
        raw = b'ssh-ed25519 YWJj' if len(calls) <= 4 * len(ssh.writers.ACCOUNTS['RU']) else b'ssh-rsa YWJj'
        return [dict(status='OBSERVED', **ssh.keys(raw))]

    monkeypatch.setattr(ssh, 'key_files', changing_keys)
    with pytest.raises(ValueError, match='SSH_BINDINGS_CHANGED'):
        ssh.collect('RU')


def test_changed_policy_refuses(monkeypatch, installed):
    snapshot = ssh.snapshot
    calls = []

    def changed(*arguments):
        result = snapshot(*arguments)
        calls.append(True)
        if len(calls) == 2:
            result['root']['contexts']['current_connection']['policy_sha256'] = 'changed'
        return result

    monkeypatch.setattr(ssh, 'snapshot', changed)
    with pytest.raises(ValueError, match='SSH_BINDINGS_CHANGED'):
        ssh.collect('RU')


@pytest.mark.parametrize('connection', ['', '192.0.2.1 1 186.246.51.201 22',
                                      '192.0.2.1 x 185.251.89.19 22', 'private 1 185.251.89.19 22'])
def test_wrong_or_missing_live_connection_refuses(monkeypatch, installed, connection):
    monkeypatch.setenv('SSH_CONNECTION', connection)
    with pytest.raises(ValueError):
        ssh.collect('RU')
    assert not installed


def test_refused_key_read_is_not_mistaken_for_account_absence(monkeypatch, installed):
    monkeypatch.setattr(ssh, 'key_files', lambda *args: (_ for _ in ()).throw(PermissionError()))
    with pytest.raises(PermissionError):
        ssh.collect('RU')


def test_absent_accounts_are_explicit(monkeypatch, installed):
    monkeypatch.setattr(ssh.pwd, 'getpwnam', lambda name: (_ for _ in ()).throw(KeyError(name)))
    result = ssh.collect('RU')
    assert all(record['status'] == 'ACCOUNT_ABSENT' for record in result['accounts'].values())
    assert not result['capture_permitted']
