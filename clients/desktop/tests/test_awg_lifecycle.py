import copy
import json
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'linux'))
import awg_lifecycle as lifecycle


class System:
    def __init__(self):
        self.commands = []
        self.rules = {family: [dict(priority=32766, src='all', table='main'),
                              dict(priority=10617, src='all', table='main', suppress_prefixlength=0)]
                      for family in ('-4', '-6')}
        self.routes = {family: [] for family in self.rules}
        self.tables, self.links, self.dns, self.markers = [], [], set(), {}
        self.mark, self.fail = '0', None

    def command(self, *args, **kwargs):
        self.commands.append(args)
        if args == self.fail:
            raise RuntimeError('synthetic command failure')
        if args[:2] == ('ip', '-j'):
            if args[2:] == ('-d', 'link', 'show'):
                return json.dumps(self.links)
            return json.dumps(self.rules[args[2]] if args[3] == 'rule' else self.routes[args[2]])
        if args[:4] == ('nft', '-j', 'list', 'tables'):
            return json.dumps(dict(nftables=[dict(table=entry) for entry in self.tables]))
        if args[:4] == ('nft', '-j', 'list', 'table'):
            items = [dict(table=entry) for entry in self.tables if (entry['family'], entry['name']) == args[4:]]
            items.extend(dict(chain=dict(name=name)) for name in self.markers.get(args[4:], []))
            return json.dumps(dict(nftables=items))
        if args[:3] == ('nft', 'delete', 'table'):
            self.tables = [entry for entry in self.tables if (entry['family'], entry['name']) != args[3:]]
            return ''
        if args[:2] == ('sysctl', '-n'):
            return self.mark
        if args[:2] == ('sysctl', '-q'):
            self.mark = args[-1].split('=')[1]
            return ''
        if args[:3] == ('ip', 'link', 'delete'):
            self.links = []
            for family in self.routes:
                self.routes[family] = [entry for entry in self.routes[family] if entry.get('dev') != args[-1]]
            return ''
        if args[:2] == ('resolvconf', '-d'):
            self.dns.discard(args[2])
            return ''
        if args[0] == 'ip' and args[2] == 'route':
            entry = dict(type='unreachable', dst='default', metric=32760, table=lifecycle.TABLE)
            if args[3] == 'add':
                self.routes[args[1]].append(entry)
            else:
                self.routes[args[1]].remove(entry)
            return ''
        if args[0] == 'ip' and args[2] == 'rule':
            entry = dict(priority=int(args[5]), src='all')
            if entry['priority'] == 10619:
                entry.update(table='main', suppress_prefixlength=0)
            else:
                entry.update(table=lifecycle.TABLE, fwmark=hex(lifecycle.TABLE), **{'not': True})
            if args[3] == 'add':
                self.rules[args[1]].append(entry)
            else:
                self.rules[args[1]].remove(entry)
            return ''
        raise AssertionError(args)


@pytest.fixture
def owner(tmp_path, monkeypatch):
    directory = tmp_path/'run'
    original = Path.lstat
    def metadata(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        if path == directory:
            fields = list(info)
            fields[4] = 0
            return os.stat_result(fields)
        return info
    def read(path, *, private):
        assert private and stat.S_IMODE(path.stat().st_mode) == 0o600
        return path.read_text()
    monkeypatch.setattr(lifecycle, 'RUN', directory)
    monkeypatch.setattr(Path, 'lstat', metadata)
    system = System()
    result = lifecycle.Owner(SimpleNamespace(command=system.command, read=read), 'fcawg12345678')
    result.system = system
    return result


def activate(owner):
    owner.prepare()
    system = owner.system
    record = owner.record
    system.links = [dict(ifname=owner.identifier, ifindex=7, ifalias='fc-awg-v1:'+record['generation'],
                         linkinfo=dict(info_kind='tun'))]
    for family, nft_family in (('-4', 'ip'), ('-6', 'ip6')):
        system.routes[family].append(dict(dst='default', table=lifecycle.TABLE, dev=owner.identifier))
        system.tables.append(dict(name='wg-quick-'+owner.identifier, family=nft_family, comment='fc-awg-v1:'+record['generation']))
        system.markers[(nft_family, 'wg-quick-'+owner.identifier)] = ['fc_awg_v1_'+record['generation']]
    system.mark = '1'
    system.dns.add(record['dns_entry'])
    record.update(ready=True, index=7)
    owner.persist()
    owner.verify()


@pytest.mark.parametrize('crash', [False, True])
def test_cleanup_restores_owned_resources_and_preserves_foreign_rules(owner, crash):
    initial = copy.deepcopy(owner.system.rules)
    activate(owner)
    if crash:
        owner.system.command('ip', 'link', 'delete', 'dev', owner.identifier)
    owner.cleanup()
    owner.cleanup()
    assert owner.system.rules == initial
    assert not owner.system.links and not owner.system.tables and not owner.system.dns
    assert all(not entries for entries in owner.system.routes.values())
    assert not owner.path.exists() and owner.system.mark == '0'


@pytest.mark.parametrize('field', ['alias', 'index', 'kind', 'nft', 'marker', 'rule', 'route', 'baseline'])
def test_uncertain_ownership_leaves_journal_and_does_not_delete_anything(owner, field):
    activate(owner)
    system = owner.system
    if field == 'alias':
        system.links[0]['ifalias'] = 'foreign'
    elif field == 'index':
        system.links[0]['ifindex'] = 8
    elif field == 'kind':
        system.links[0]['linkinfo']['info_kind'] = 'dummy'
    elif field == 'nft':
        system.tables[0]['comment'] = 'foreign'
    elif field == 'marker':
        system.markers[('ip', 'wg-quick-'+owner.identifier)] = ['fc_awg_v1_'+'a'*32]
    elif field == 'rule':
        system.rules['-4'][-1]['suppress_prefixlength'] = 1
    elif field == 'route':
        system.routes['-4'].append(dict(table=lifecycle.TABLE, dst='192.0.2.0/24', dev='foreign'))
    else:
        system.rules['-4'].append(dict(priority=11000, src='all', table=500))
    system.commands.clear()
    with pytest.raises(ValueError):
        owner.cleanup()
    assert owner.path.exists() and owner.system.mark == '1'
    assert not any('delete' in command or 'del' in command or '-d' in command[:2] for command in system.commands)


@pytest.mark.parametrize('collision', ['priority', 'table', 'link', 'nft', 'journal'])
def test_preflight_cannot_adopt_existing_resources(owner, collision):
    if collision == 'priority':
        owner.system.rules['-4'].append(dict(priority=10619, src='all', table=500))
    elif collision == 'table':
        owner.system.routes['-6'].append(dict(table=lifecycle.TABLE, dst='default', dev='other'))
    elif collision == 'link':
        owner.system.links.append(dict(ifname=owner.identifier))
    elif collision == 'nft':
        owner.system.tables.append(dict(name='wg-quick-'+owner.identifier, family='ip'))
    else:
        owner.path.symlink_to('/nonexistent')
    with pytest.raises(ValueError):
        owner.prepare()
    assert not any('add' in command for command in owner.system.commands)


def test_partial_prepare_is_recoverable_without_a_tun(owner):
    owner.system.fail = lifecycle.rules('-4')[1]
    with pytest.raises(RuntimeError):
        owner.prepare()
    assert owner.path.exists()
    owner.system.fail = None
    owner.cleanup()
    assert not owner.path.exists() and all(not entries for entries in owner.system.routes.values())


def test_partial_cleanup_retries_remaining_resources(owner):
    activate(owner)
    owner.system.fail = ('nft', 'delete', 'table', 'ip6', 'wg-quick-'+owner.identifier)
    with pytest.raises(RuntimeError):
        owner.cleanup()
    assert owner.path.exists() and not owner.system.links and len(owner.system.tables) == 1
    owner.system.fail = None
    owner.cleanup()
    assert not owner.path.exists() and not owner.system.tables


@pytest.mark.parametrize('field,value', [('schema', True), ('id', 'fcawg87654321'), ('index', True),
    ('generation', 'x'*32), ('dns_entry', '../../resolv.conf'), ('baseline_rules', 'invalid'), ('ready', 1), ('src_valid_mark', '2')])
def test_invalid_journal_rejected_before_network_commands(owner, field, value):
    activate(owner)
    record = dict(owner.record, **{field: value})
    owner.path.write_text(json.dumps(record))
    owner.system.commands.clear()
    with pytest.raises(ValueError):
        owner.cleanup()
    assert not owner.system.commands and owner.path.exists()


def test_preexisting_sysctl_one_is_not_reset(owner):
    owner.system.mark = '1'
    activate(owner)
    owner.system.rules['-4'].append(dict(priority=11000, src='all', table=500))
    owner.cleanup()
    assert owner.system.mark == '1' and owner.system.rules['-4'][-1]['table'] == 500


def test_missing_journal_cannot_claim_cleanup_of_existing_network_resources(owner):
    activate(owner)
    owner.system.command('ip', 'link', 'delete', 'dev', owner.identifier)
    owner.path.unlink()
    owner.system.commands.clear()
    with pytest.raises(ValueError):
        owner.cleanup()
    assert owner.system.tables and owner.system.dns
    assert not any('delete' in command or 'del' in command for command in owner.system.commands)


@pytest.mark.parametrize('mode', [0o755, 0o777])
def test_nonprivate_journal_directory_is_rejected(owner, mode):
    lifecycle.RUN.chmod(mode)
    with pytest.raises(ValueError):
        lifecycle.Owner(owner.helper, owner.identifier)


@pytest.mark.parametrize('extra', [dict(dst='192.0.2.1'), dict(fwmark='0x1'), dict(fwmask='0xff'),
                                 dict(protocol='static'), dict(suppress_prefixlength=0), {'not': False}])
def test_altered_priority_rule_is_not_owned(extra):
    rule = dict(priority=10620, src='all', table=lifecycle.TABLE, fwmark=hex(lifecycle.TABLE), **{'not': True})
    assert lifecycle.rule_owned(rule)
    rule.update(extra)
    assert not lifecycle.rule_owned(rule)


def test_unknown_quick_source_fails_closed():
    with pytest.raises(ValueError):
        lifecycle.managed_source('unreviewed source')


def test_bookworm_iproute_and_nft_json_are_accepted_with_ownership_marker(owner):
    activate(owner)
    for entries in owner.system.rules.values():
        for entry in entries:
            if 'suppress_prefixlength' in entry:
                entry['suppress_prefixlen'] = entry.pop('suppress_prefixlength')
            if entry.get('priority') == 10620:
                entry['not'] = None
                entry['table'] = str(entry['table'])
            if entry.get('priority') in lifecycle.PRIORITIES:
                assert lifecycle.rule_owned(entry)
    for table in owner.system.tables:
        table.pop('comment')
    owner.verify()


def test_missing_not_is_not_the_inverted_rule():
    assert not lifecycle.rule_owned(dict(priority=10620, src='all', table='64620', fwmark='0xfc6c'))


def test_ambiguous_suppress_fields_are_not_owned():
    assert not lifecycle.rule_owned(dict(priority=10619, src='all', table='main', suppress_prefixlength=0, suppress_prefixlen=0))
