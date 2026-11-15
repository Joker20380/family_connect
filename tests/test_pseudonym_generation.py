from copy import deepcopy
import json
import pytest

from control.friends.pseudonyms import Aliases, digest, load, prepare, pseudonym, save, seal, unseal


@pytest.fixture
def aliases():
    return prepare(dict(device=['a'*32], panel_event=['event-001']), b'n'*32, legacy_key=b'o'*32)


def test_separate_domains_preserve_history_and_no_old_key_after_preparation(aliases, tmp_path):
    path = tmp_path/'aliases.json'
    save(path, aliases)
    current = load(path)
    assert path.stat().st_mode & 0o777 == 0o600
    for domain, canonical in [('device', 'a'*32), ('panel_event', 'event-001')]:
        assert current.resolve(domain, pseudonym(b'n'*32, domain, canonical), current=True) == pseudonym(b'o'*32, domain, canonical)
    assert prepare(dict(device=['a'*32], panel_event=['event-001']), b'n'*32, existing=current).document == current.document
    assert b'o'*32 not in path.read_bytes() and b'n'*32 not in path.read_bytes()


def test_interruption_and_delta_require_complete_matching_manifest(aliases, tmp_path):
    payload = dict(devices=[dict(pseudonym=pseudonym(b'n'*32, 'device', 'a'*32))])
    wrapped = seal(payload, 'inventory', b'n'*32, aliases)
    with pytest.raises(ValueError):
        unseal(wrapped, 'inventory')
    before = digest(aliases.document)
    changed = prepare(dict(device=['a'*32, 'b'*32], panel_event=['event-001','event-002']), b'n'*32,
                      existing=aliases, legacy_key=b'o'*32)
    assert digest(aliases.document) == before
    with pytest.raises(ValueError):
        unseal(wrapped, 'inventory', changed)
    assert unseal(seal(payload, 'inventory', b'n'*32, changed), 'inventory', changed)['devices'][0]['pseudonym'] == pseudonym(b'o'*32,'device','a'*32)
    future = prepare(dict(device=['c'*32], panel_event=[]), b'n'*32, existing=changed)
    assert future.resolve('device', pseudonym(b'n'*32,'device','c'*32)) == pseudonym(b'n'*32,'device','c'*32)


@pytest.mark.parametrize('field,value', [('generation',1),('generation',True),('generation',3),('channel','notifications'),('aliases_sha256','0'*64)])
def test_unknown_or_inconsistent_generation_rejected(aliases, field, value):
    envelope = seal(dict(devices=[]), 'inventory', b'n'*32, aliases)
    envelope[field] = value
    with pytest.raises(ValueError):
        unseal(envelope,'inventory',aliases)
    with pytest.raises(ValueError):
        seal(dict(devices=[]),'inventory',b'o'*32,aliases)


def test_collision_unknown_and_legacy_input_are_rejected(aliases):
    document = deepcopy(aliases.document)
    document['entities']['device'].append(deepcopy(document['entities']['device'][0]))
    with pytest.raises(ValueError):
        Aliases(document)
    with pytest.raises(ValueError):
        unseal(dict(schema=1,devices=[]),'inventory',aliases)
    fresh=seal(dict(devices=[dict(pseudonym='f'*64)]),'inventory',b'n'*32,aliases)
    assert unseal(fresh,'inventory',aliases)['devices'][0]['pseudonym']=='f'*64
    fresh['new_entities']['device']=[]
    with pytest.raises(ValueError):
        unseal(fresh,'inventory',aliases)
    assert aliases.coverage('device', ['f'*64, pseudonym(b'o'*32,'device','a'*32)]) == dict(stored=2,mapped=1,missing=1,conflicts=0)


def test_canonical_notification_ids_never_rewritten(aliases):
    payload = dict(subscriptions=[dict(pseudonym=pseudonym(b'n'*32,'device','a'*32))],
                   events=[dict(event_id='event-001',prior=dict(event_id='event-previous'))],
                   position=44,highwater=45,position_hash='b'*64)
    restored = unseal(seal(payload,'notifications',b'n'*32,aliases),'notifications',aliases)
    assert restored['events'] == payload['events']
    assert restored['position_hash'] == payload['position_hash']
    assert restored['subscriptions'][0]['pseudonym'] == pseudonym(b'o'*32,'device','a'*32)


def test_metadata_revocation_and_sample_times_untouched(aliases):
    payload = dict(devices=[dict(pseudonym=pseudonym(b'n'*32,'device','a'*32),consent_epoch=4,
        sequence=88,consent='revoked',received_at=123,observations={},geoip=None)])
    restored = unseal(seal(payload,'technical_metadata',b'n'*32,aliases),'technical_metadata',aliases)
    assert {name:value for name,value in restored['devices'][0].items() if name!='pseudonym'} == {
        name:value for name,value in payload['devices'][0].items() if name!='pseudonym'}


def test_private_file_duplicate_keys_symlink_and_permissions_rejected(aliases,tmp_path):
    path=tmp_path/'aliases.json';save(path,aliases)
    link=tmp_path/'link';link.symlink_to(path)
    with pytest.raises(OSError):load(link)
    path.chmod(0o644)
    with pytest.raises(ValueError):load(path)
    path.chmod(0o600)
    path.write_text('{"schema":1,"schema":2}')
    with pytest.raises(ValueError):load(path)


def test_preparation_reads_all_canonical_events_and_blocks_active_missing(tmp_path):
    import sqlite3
    from scripts.prepare_pseudonym_migration import build
    database=tmp_path/'registry.sqlite'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE devices(device TEXT)')
        connection.execute('INSERT INTO devices VALUES (?)',('a'*32,))
        connection.execute('CREATE TABLE paid_beta_events(event_id TEXT)')
        connection.executemany('INSERT INTO paid_beta_events VALUES (?)',[(f'event-{number:05d}',) for number in range(1503)])
    old=tmp_path/'old.key';new=tmp_path/'new.key'
    old.write_bytes(b'o'*32);old.chmod(0o600);new.write_bytes(b'n'*32);new.chmod(0o600)
    refs=tmp_path/'refs.json'
    refs.write_text(json.dumps({'pending':dict(domain='device',counts={'f'*64:1},critical=True),
        'events':dict(domain='panel_event',counts={pseudonym(b'o'*32,'panel_event','event-01502'):1},critical=False)}));refs.chmod(0o600)
    output=tmp_path/'aliases.json';report=build(database,old,new,refs,output)
    assert report['canonical']['panel_event']==1503 and report['coverage']['events']['mapped']==1
    assert report['cutover']=='BLOCKED' and not report['activation_performed']
    assert build(database,old,new,refs,output)==report
    with sqlite3.connect(database) as connection:
        connection.execute('INSERT INTO devices VALUES (?)',('b'*32,))
    refs.write_text(json.dumps({'pending':dict(domain='device',counts={pseudonym(b'o'*32,'device','b'*32):1},critical=True)}))
    extended=build(database,old,new,refs,output)
    assert extended['canonical']['device']==2 and extended['coverage']['pending']['missing']==0
    assert extended['aliases_sha256']!=report['aliases_sha256']
    assert load(output).resolve('device',pseudonym(b'n'*32,'device','a'*32))==pseudonym(b'o'*32,'device','a'*32)
