"""Generation-bound pseudonyms at ingress; historical storage handles never change."""
from copy import deepcopy
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid


ENVIRONMENT = 'FC_PSEUDONYM_ALIASES'
MAX_BYTES = 32 * 1024 * 1024
DOMAINS = ('device', 'panel_event')
CHANNELS = ('inventory', 'subscriptions', 'technical_metadata', 'support', 'notifications')


def require(condition):
    if not condition:
        raise ValueError('pseudonym_generation_unavailable')


def hexadecimal(value, length=64):
    return type(value) is str and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pseudonym(key, domain, canonical):
    require(type(key) is bytes and len(key) == 32 and domain in DOMAINS)
    require(type(canonical) is str and 0 < len(canonical) <= 128)
    if domain == 'device':
        require(hexadecimal(canonical, 32))
    return hmac.new(key, (('event:' if domain == 'panel_event' else '') + canonical).encode(), hashlib.sha256).hexdigest()


def key_check(key, generation):
    require(type(key) is bytes and len(key) == 32)
    return hmac.new(key, ('fc-pseudonym-generation:' + str(generation)).encode(), hashlib.sha256).hexdigest()


class Aliases:
    def __init__(self, document):
        require(type(document) is dict and set(document) == {'schema', 'generation', 'key_check', 'entities'})
        require(document['schema'] == 'fc-pseudonym-aliases-v1')
        generation = document['generation']
        require(type(generation) is int and 2 <= generation <= 2**31 - 1 and hexadecimal(document['key_check']))
        require(type(document['entities']) is dict and set(document['entities']) == set(DOMAINS))
        self.document = deepcopy(document)
        self.generation = generation
        self.index = {domain: {} for domain in DOMAINS}
        self.handles = {domain: set() for domain in DOMAINS}
        all_entities = set()
        for domain in DOMAINS:
            rows = document['entities'][domain]
            require(type(rows) is list and len(rows) <= 100000)
            for row in rows:
                require(type(row) is dict and set(row) == {'entity', 'handle', 'aliases'})
                require(hexadecimal(row['entity'], 32) and row['entity'] not in all_entities)
                all_entities.add(row['entity'])
                require(hexadecimal(row['handle']) and row['handle'] not in self.handles[domain])
                self.handles[domain].add(row['handle'])
                require(type(row['aliases']) is dict and str(generation) in row['aliases'])
                require(1 <= len(row['aliases']) <= 16)
                for epoch, value in row['aliases'].items():
                    require(type(epoch) is str and epoch.isascii() and epoch.isdecimal()
                            and str(int(epoch)) == epoch and 1 <= int(epoch) <= generation and hexadecimal(value))
                    require(value not in self.index[domain])
                    self.index[domain][value] = row
            for handle in self.handles[domain]:
                require(handle in self.index[domain] and self.index[domain][handle]['handle'] == handle)

    def resolve(self, domain, value, *, current=False):
        require(domain in DOMAINS and hexadecimal(value))
        row = self.index[domain].get(value)
        require(row is not None and (not current or row['aliases'][str(self.generation)] == value))
        return row['handle']

    def check_key(self, key):
        require(hmac.compare_digest(self.document['key_check'], key_check(key, self.generation)))

    def coverage(self, domain, stored):
        values = list(stored)
        mapped = sum(value in self.index[domain] for value in values)
        return dict(stored=len(values), mapped=mapped, missing=len(values)-mapped, conflicts=0)


def prepare(canonical, new_key, *, legacy_key=None, existing=None, generation=2):
    require(type(canonical) is dict and set(canonical) == set(DOMAINS))
    require(existing is not None or legacy_key is not None)
    if existing is None:
        document = dict(schema='fc-pseudonym-aliases-v1', generation=generation,
                        key_check=key_check(new_key, generation), entities={domain: [] for domain in DOMAINS})
    else:
        existing.check_key(new_key)
        require(existing.generation == generation)
        document = deepcopy(existing.document)
    for domain in DOMAINS:
        known = {row['aliases'][str(generation)] for row in document['entities'][domain]}
        for value in sorted(set(canonical[domain])):
            current = pseudonym(new_key, domain, value)
            if current in known:
                continue
            aliases = {str(generation): current}
            handle = current
            if legacy_key is not None:
                handle = pseudonym(legacy_key, domain, value)
                require(handle != current)
                aliases['1'] = handle
            document['entities'][domain].append(dict(entity=uuid.uuid4().hex, handle=handle, aliases=aliases))
            known.add(current)
    return Aliases(document)


def load(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_mode & 0o077 == 0
                and 0 < info.st_size <= MAX_BYTES)
        raw = stream.read(MAX_BYTES + 1)
    def unique(pairs):
        result = {}
        for name, value in pairs:
            require(name not in result)
            result[name] = value
        return result
    require(len(raw) <= MAX_BYTES)
    return Aliases(json.loads(raw, object_pairs_hook=unique))


def save(path, aliases):
    path = Path(path)
    raw = json.dumps(aliases.document, sort_keys=True, separators=(',', ':')).encode()
    require(len(raw) <= MAX_BYTES and not path.is_symlink())
    descriptor, temporary = tempfile.mkstemp(prefix='.aliases-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def references(payload, channel):
    require(channel in CHANNELS and type(payload) is dict)
    def devices(rows):
        for row in rows:
            yield row, 'pseudonym', 'device'
    if channel == 'notifications':
        yield from devices(payload.get('subscriptions', []))
    else:
        yield from devices(payload.get('devices', []))
    if channel == 'subscriptions':
        for row in payload.get('devices', []):
            if row.get('event'):
                yield row['event'], 'event_id', 'panel_event'
        for row in (payload.get('history') or {}).get('events', []):
            yield row, 'pseudonym', 'device'
            yield row, 'event_id', 'panel_event'
    if channel == 'inventory':
        for name in ('transport_observation', 'metrics'):
            if payload.get(name):
                yield from devices(payload[name].get('devices', []))
        if payload.get('subscription_observation'):
            yield from references(payload['subscription_observation'], 'subscriptions')


def seal(payload, channel, key, aliases=None):
    path = os.environ.get(ENVIRONMENT)
    if aliases is None and not path:
        return payload
    aliases = aliases or load(path)
    aliases.check_key(key)
    fresh = {domain: set() for domain in DOMAINS}
    for row, field, domain in references(payload, channel):
        require(hexadecimal(row[field]))
        if row[field] in aliases.index[domain]:
            aliases.resolve(domain, row[field], current=True)
        else:
            fresh[domain].add(row[field])
    return dict(schema='fc-pseudonyms-v1', generation=aliases.generation, aliases_sha256=digest(aliases.document),
                channel=channel, payload=payload, new_entities={domain:sorted(values) for domain,values in fresh.items()})


def unseal(document, channel, aliases=None):
    path = os.environ.get(ENVIRONMENT)
    if aliases is None and not path:
        require(type(document) is dict and document.get('schema') != 'fc-pseudonyms-v1')
        return document
    aliases = aliases or load(path)
    require(type(document) is dict and set(document) == {'schema', 'generation', 'aliases_sha256', 'channel', 'payload', 'new_entities'})
    require(document['schema'] == 'fc-pseudonyms-v1' and type(document['generation']) is int
            and document['generation'] == aliases.generation and document['channel'] == channel
            and document['aliases_sha256'] == digest(aliases.document))
    payload = deepcopy(document['payload'])
    fresh = {domain: set() for domain in DOMAINS}
    for row, field, domain in references(payload, channel):
        require(hexadecimal(row[field]))
        if row[field] in aliases.index[domain]:
            row[field] = aliases.resolve(domain, row[field], current=True)
        else:
            fresh[domain].add(row[field])
    require(document['new_entities'] == {domain:sorted(values) for domain,values in fresh.items()})
    return payload


def handle(value):
    path = os.environ.get(ENVIRONMENT)
    if not path:
        return value
    aliases = load(path)
    require(hexadecimal(value))
    return aliases.resolve('device', value) if value in aliases.index['device'] else value
