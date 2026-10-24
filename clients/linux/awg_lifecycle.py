"""Journal only owned AWG quick resources, including after userspace TUN death."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat

RUN = Path('/run/family-connect-awg')
TABLE = 64620
PRIORITIES = (10619, 10620)


def require(condition):
    if not condition:
        raise ValueError('AWG resource ownership cannot be verified')


def managed_source(source):
    replacements = {
        'SELF="$(readlink -f "${BASH_SOURCE[0]}")"': 'SELF="/usr/local/lib/family-connect-awg/awg-quick"',
        'table=51820\n\t\twhile [[ -n $(ip -4 route show table $table 2>/dev/null) || -n $(ip -6 route show table $table 2>/dev/null) ]]; do\n\t\t\t((table++))\n\t\tdone': 'table=64620',
        '\tcmd ip $proto rule add not fwmark $table table $table\n\tcmd ip $proto rule add table main suppress_prefixlength 0\n': '',
        '\tprintf -v nftcmd \'%sadd table %s %s\\n\' "$nftcmd" "$pf" "$nftable"':
            '\tprintf -v nftcmd \'%sadd table %s %s { comment "fc-awg-v1:%s"; }\\nadd chain %s %s fc_awg_v1_%s\\n\' "$nftcmd" "$pf" "$nftable" "$FC_AWG_GENERATION" "$pf" "$nftable" "$FC_AWG_GENERATION"',
        '\tcmd "${WG_QUICK_USERSPACE_IMPLEMENTATION:-amneziawg-go}" "$INTERFACE"':
            '\tcmd "${WG_QUICK_USERSPACE_IMPLEMENTATION:-amneziawg-go}" "$INTERFACE"\n\tcmd ip link set dev "$INTERFACE" alias "fc-awg-v1:$FC_AWG_GENERATION"',
    }
    for old, new in replacements.items():
        require(source.count(old) == 1)
        source = source.replace(old, new)
    require(source.count('$(resolvconf_iface_prefix)$INTERFACE') == 4)
    source = source.replace('$(resolvconf_iface_prefix)$INTERFACE', '${FC_AWG_DNS_ENTRY}')
    begin, end = source.index('\ndel_if() {'), source.index('\nadd_addr() {')
    source = source[:begin] + '\ndel_if() {\n\tif ip link show dev "$INTERFACE" >/dev/null 2>&1; then cmd ip link delete dev "$INTERFACE"; fi\n}\n' + source[end:]
    return source


def rules(family):
    return [('ip', family, 'rule', 'add', 'priority', '10620', 'not', 'fwmark', str(TABLE), 'table', str(TABLE)),
            ('ip', family, 'rule', 'add', 'priority', '10619', 'table', 'main', 'suppress_prefixlength', '0')]


def rule_owned(value):
    if set(value) - {'priority', 'src', 'table', 'not', 'fwmark', 'fwmask', 'suppress_prefixlength', 'suppress_prefixlen', 'protocol'}:
        return False
    if value.get('src') != 'all' or value.get('protocol', 'boot') != 'boot':
        return False
    suppress = [value[key] for key in ('suppress_prefixlength', 'suppress_prefixlen') if key in value]
    if value.get('priority') == 10619:
        return (value.get('table') in ('main', 254, '254') and len(suppress) == 1 and type(suppress[0]) is int and suppress[0] == 0 and
                not set(value) & {'not', 'fwmark', 'fwmask'})
    try:
        mark = int(str(value.get('fwmark', '')), 0)
        mask = int(str(value.get('fwmask', '0xffffffff')), 0)
    except ValueError:
        return False
    return (value.get('priority') == 10620 and value.get('table') in (TABLE, str(TABLE)) and 'not' in value and
            (value['not'] is None or value['not'] is True) and mark == TABLE and mask == 0xffffffff and not suppress)


class Owner:
    def __init__(self, helper, identifier):
        require(re.fullmatch(r'fcawg[0-9a-f]{8}', identifier) is not None)
        self.helper, self.identifier = helper, identifier
        self.path = RUN/'active.json'
        self.record = None
        try:
            RUN.mkdir(mode=0o700)
            RUN.chmod(0o700)
        except FileExistsError:
            pass
        info = RUN.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o700)

    def command(self, *args, **kwargs):
        return self.helper.command(*args, **kwargs)

    def json(self, *args):
        return json.loads(self.command(*args))

    def persist(self):
        temporary = RUN/('.'+secrets.token_hex(16))
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(descriptor, 'w') as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump(self.record, stream, separators=(',', ':'))
                stream.flush();os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            self.sync()
        finally:
            temporary.unlink(missing_ok=True)
        require(json.loads(self.helper.read(self.path, private=True)) == self.record)

    def sync(self):
        descriptor = os.open(RUN, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)

    def load(self):
        if not os.path.lexists(self.path):
            return False
        value = json.loads(self.helper.read(self.path, private=True))
        require(set(value) == {'schema', 'id', 'generation', 'index', 'ready', 'dns_entry', 'src_valid_mark', 'baseline_rules'})
        require(type(value['schema']) is int and value['schema'] == 1 and value['id'] == self.identifier)
        require(isinstance(value['generation'], str) and re.fullmatch('[a-f0-9]{32}', value['generation']) is not None)
        require(type(value['index']) is int and 0 <= value['index'] < 2**31 and type(value['ready']) is bool)
        require(isinstance(value['dns_entry'], str) and re.fullmatch(r'(?:[A-Za-z0-9-]+\.)?'+self.identifier, value['dns_entry']) is not None)
        require(value['src_valid_mark'] in ('0', '1') and isinstance(value['baseline_rules'], str) and re.fullmatch('[a-f0-9]{64}', value['baseline_rules']) is not None)
        self.record = value
        return True

    def inspect(self):
        return {family: self.json('ip', '-j', family, 'rule', 'show') for family in ('-4', '-6')}

    def rule_hash(self, observed):
        other = {family: [rule for rule in entries if rule.get('priority') not in PRIORITIES] for family, entries in observed.items()}
        return hashlib.sha256(json.dumps(other, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def firewall(self):
        found = [item['table'] for item in self.json('nft', '-j', 'list', 'tables')['nftables'] if 'table' in item and item['table'].get('name') == 'wg-quick-'+self.identifier]
        result = []
        for table in found:
            require(table['family'] in ('ip', 'ip6'))
            items = self.json('nft', '-j', 'list', 'table', table['family'], table['name'])['nftables']
            metadata = [item['table'] for item in items if 'table' in item]
            require(len(metadata) == 1 and metadata[0]['family'] == table['family'] and metadata[0]['name'] == table['name'])
            markers = [item['chain']['name'] for item in items if 'chain' in item and item['chain']['name'].startswith('fc_awg_v1_')]
            result.append(dict(metadata[0], ownership_markers=markers))
        return result

    def table_owned(self, table):
        return (table['family'] in ('ip', 'ip6') and
                table.get('comment', 'fc-awg-v1:'+self.record['generation']) == 'fc-awg-v1:'+self.record['generation'] and
                table['ownership_markers'] == ['fc_awg_v1_'+self.record['generation']])

    def route_entries(self, family):
        return [item for item in self.json('ip', '-j', family, 'route', 'show', 'table', 'all') if str(item.get('table')) == str(TABLE)]

    def link(self):
        found = [item for item in self.json('ip', '-j', '-d', 'link', 'show') if item.get('ifname') == self.identifier]
        require(len(found) <= 1)
        return found[0] if found else None

    def owned_link(self):
        link = self.link()
        if link is not None:
            require(link.get('ifalias') == 'fc-awg-v1:'+self.record['generation'])
            require(self.record['index'] in (0, link['ifindex']))
            require(link.get('linkinfo', {}).get('info_kind') in ('tun', 'amneziawg', 'wireguard'))
        return link

    def prepare(self):
        require(not os.path.lexists(self.path) and self.link() is None and not self.firewall())
        observed = self.inspect()
        for family, entries in observed.items():
            require(not any(entry.get('priority') in PRIORITIES for entry in entries) and not self.route_entries(family))
        prefix = ''
        order = Path('/etc/resolvconf/interface-order')
        if order.exists():
            for line in order.read_text().splitlines():
                if re.fullmatch('[A-Za-z0-9-]+\\*', line.strip()):
                    prefix = line.strip()[:-1]+'.';break
        self.record = dict(schema=1, id=self.identifier, generation=secrets.token_hex(16), index=0, ready=False,
            dns_entry=prefix+self.identifier, src_valid_mark=self.command('sysctl', '-n', 'net.ipv4.conf.all.src_valid_mark'),
            baseline_rules=self.rule_hash(observed))
        require(self.record['src_valid_mark'] in ('0', '1'))
        self.persist()
        for family in ('-4', '-6'):
            self.command('ip', family, 'route', 'add', 'unreachable', 'default', 'metric', '32760', 'table', str(TABLE))
            for arguments in rules(family):self.command(*arguments)

    def quick(self, config):
        path = Path(self.helper.BIN)/'awg-quick'
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'r') as source:
            info = os.fstat(source.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o755)
            text = source.read(65537);require(len(text) <= 65536)
        environment = dict(self.helper.ENV, FC_AWG_GENERATION=self.record['generation'], FC_AWG_DNS_ENTRY=self.record['dns_entry'])
        self.helper.command('/bin/bash', '-c', managed_source(text), 'fc-awg-quick', 'up', str(config), environment=environment)
        link = self.owned_link();require(link is not None)
        self.record.update(index=link['ifindex'], ready=True);self.persist()
        self.verify()

    def verify(self):
        require(self.record is not None and self.record['ready'] and self.owned_link() is not None)
        tables = self.firewall()
        require(len(tables) == 2 and {table['family'] for table in tables} == {'ip', 'ip6'} and all(self.table_owned(table) for table in tables))
        observed = self.inspect()
        for family, entries in observed.items():
            owned = [entry for entry in entries if entry.get('priority') in PRIORITIES]
            require(len(owned) == 2 and all(rule_owned(entry) for entry in owned))
            routes = self.route_entries(family)
            require(any(entry.get('type') == 'unreachable' and entry.get('dst') == 'default' and entry.get('metric') == 32760 for entry in routes))
            require(any(entry.get('dev') == self.identifier and entry.get('dst') == 'default' for entry in routes))

    def cleanup(self):
        if not self.load():
            require(self.link() is None and not self.firewall())
            for family, entries in self.inspect().items():
                require(not any(entry.get('priority') in PRIORITIES for entry in entries) and not self.route_entries(family))
            return
        observed = self.inspect()
        tables = self.firewall()
        for table in tables:
            require(self.table_owned(table))
        for family, entries in observed.items():
            require(all(rule_owned(entry) for entry in entries if entry.get('priority') in PRIORITIES))
            for entry in self.route_entries(family):
                require(entry.get('dst') == 'default' and (entry.get('dev') == self.identifier or
                    entry.get('type') == 'unreachable' and entry.get('metric') == 32760))
        if self.record['src_valid_mark'] == '0':
            require(self.rule_hash(observed) == self.record['baseline_rules'])
        if self.owned_link() is not None:
            self.command('ip', 'link', 'delete', 'dev', self.identifier)
        require(self.link() is None)
        self.command('resolvconf', '-d', self.record['dns_entry'], '-f')
        for table in tables:self.command('nft', 'delete', 'table', table['family'], table['name'])
        for family, entries in observed.items():
            for arguments in reversed(rules(family)):
                priority = int(arguments[arguments.index('priority')+1])
                if any(entry.get('priority') == priority for entry in entries):
                    self.command(*tuple('del' if item == 'add' else item for item in arguments))
            for entry in self.route_entries(family):
                require(entry.get('type') == 'unreachable' and entry.get('metric') == 32760)
                self.command('ip', family, 'route', 'del', 'unreachable', 'default', 'metric', '32760', 'table', str(TABLE))
        require(not self.firewall() and self.link() is None)
        for family, entries in self.inspect().items():
            require(not any(entry.get('priority') in PRIORITIES for entry in entries) and not self.route_entries(family))
        if self.record['src_valid_mark'] == '0':
            current = self.command('sysctl', '-n', 'net.ipv4.conf.all.src_valid_mark');require(current in ('0', '1'))
            if current == '1':self.command('sysctl', '-q', 'net.ipv4.conf.all.src_valid_mark=0')
        self.path.unlink();self.sync();self.record = None
