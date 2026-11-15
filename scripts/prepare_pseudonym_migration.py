"""Prepare private generation aliases from consistent copies, never activate consumers."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import stat

from control.friends.pseudonyms import DOMAINS, load, prepare, require, save, hexadecimal, digest


def private_bytes(path, maximum):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_mode & 0o077 == 0
                and 0 < info.st_size <= maximum)
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum)
    return raw


def build(registry, old_key_path, new_key_path, references_path, output):
    old_key = private_bytes(old_key_path, 32)
    new_key = private_bytes(new_key_path, 32)
    require(len(old_key) == len(new_key) == 32 and old_key != new_key)
    require(not registry.is_symlink() and registry.is_file())
    database = sqlite3.connect(registry.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        database.execute('PRAGMA query_only=ON')
        database.execute('BEGIN')
        require(database.execute('PRAGMA integrity_check').fetchone()[0] == 'ok')
        canonical = dict(device=[row[0] for row in database.execute('SELECT device FROM devices')],
                         panel_event=[row[0] for row in database.execute('SELECT event_id FROM paid_beta_events')])
        require(all(len(values) <= 100000 for values in canonical.values()))
    finally:
        database.close()
    aliases = prepare(canonical, new_key, legacy_key=old_key, existing=load(output) if output.exists() else None)
    references = json.loads(private_bytes(references_path, 16 * 1024 * 1024))
    require(type(references) is dict and len(references) <= 100)
    coverage = {}
    for category, group in references.items():
        require(type(category) is str and 0 < len(category) <= 100)
        require(type(group) is dict and set(group) == {'domain','counts','critical'})
        require(group['domain'] in DOMAINS and type(group['counts']) is dict and type(group['critical']) is bool)
        require(all(hexadecimal(value) and type(count) is int and count > 0 for value,count in group['counts'].items()))
        stored = sum(group['counts'].values())
        mapped = sum(count for value,count in group['counts'].items() if value in aliases.index[group['domain']])
        coverage[category] = dict(stored=stored,mapped=mapped,missing=stored-mapped,conflicts=0,
                                 state='mapped' if stored == mapped else 'legacy_unresolved',critical=group['critical'])
    blocked = any(row['critical'] and row['missing'] for row in coverage.values())
    save(output, aliases)
    return dict(schema=1, generation=aliases.generation, aliases_sha256=digest(aliases.document),
                canonical={domain:len(values) for domain,values in canonical.items()}, coverage=coverage,
                cutover='BLOCKED' if blocked else 'COVERAGE_ONLY_NOT_AUTHORIZATION',
                activation_performed=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('registry','old-key','new-key','references','output','report'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    try:
        report=build(args.registry,args.old_key,args.new_key,args.references,args.output)
        descriptor=os.open(args.report,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(descriptor,'w') as stream:
            json.dump(report,stream,sort_keys=True,indent=2)
            stream.write('\n')
        print(json.dumps(dict(cutover=report['cutover'],activation_performed=False)))
    except (OSError,ValueError,KeyError,TypeError,sqlite3.Error):
        parser.exit(1,'Preparation failed; private inputs withheld; no consumer activated.\n')


if __name__ == '__main__':
    main()
