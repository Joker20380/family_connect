"""Native safety checks in memory/private scratch, never an engine dispatcher."""
import ast
from contextlib import closing
from copy import deepcopy
import importlib.util
import io
import ipaddress
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import uuid
import zipfile

from control.friends import transport_policy as policy
from scripts.control_ha_live_sqlite import require
from scripts.control_ha_node_restore import document, validate

SOURCE = Path(__file__).resolve().parents[1]


def definition(raw, name, parent=None):
    tree = ast.parse(raw)
    if parent:
        tree = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == parent)
    return next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)


def same(raw, expected, names, parent=None):
    for name in names:
        require(ast.dump(definition(raw, name, parent)) == ast.dump(definition(expected, name, parent)),
                'NATIVE_SAFETY_IMPLEMENTATION_CHANGED')


def qualify(files, manifest, scratch):
    summary = validate(files, manifest)
    gateway_source = (SOURCE / 'control/friends/transport_gateway.py').read_bytes()
    allocator_source = (SOURCE / 'deploy/friends/awg-gateway.py').read_bytes()
    with zipfile.ZipFile(io.BytesIO(files['transport.pyz'])) as archive:
        require(len(archive.infolist()) <= 256, 'NATIVE_ARCHIVE_BOUNDS')
        for name, expected, methods, parent in (
                ('transport_gateway.py', gateway_source, ('load', 'allowed', 'accept'), 'Gateway'),
                ('transport_policy.py', (SOURCE / 'control/friends/transport_policy.py').read_bytes(),
                 ('validate', 'successor'), None)):
            path = 'control/friends/' + name
            require(archive.getinfo(path).file_size <= 1024 * 1024 and
                    sum(entry.filename == path for entry in archive.infolist()) == 1, 'NATIVE_ARCHIVE_ENTRY')
            same(archive.read(path), expected, methods, parent)
    same(files['gateway.py'], allocator_source, ('address',))
    scratch = Path(scratch)
    require(scratch.is_absolute() and '..' not in scratch.parts and
            all(not parent.is_symlink() for parent in (scratch, *scratch.parents)) and
            scratch.parent.stat().st_mode & 0o777 == 0o700 and scratch.parent.stat().st_uid == os.geteuid(),
            'PRIVATE_SCRATCH_PARENT')
    scratch.mkdir(mode=0o700)
    for name, body in (('transport-state.json', files['state.json']), ('transport-enforcement.json', files['enforcement.json'])):
        descriptor = os.open(scratch / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(body)
    spec = importlib.util.spec_from_file_location('control.friends._ha_node_safety', SOURCE / 'control/friends/transport_gateway.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    point = dict(boot=manifest['boot'], monotonic=manifest['monotonic'], wall=manifest['captured_at_ns'] / 1e9)
    module.boot_id = lambda: point['boot']
    module.emit = lambda value: None
    def forbidden(*args, **kwargs):
        raise RuntimeError('NODE_RUNTIME_COMMAND_FORBIDDEN')
    engine = module.Gateway(SimpleNamespace(ROOT=scratch, add_peer=forbidden),
                            clock=lambda: point['wall'], monotonic=lambda: point['monotonic'], run=forbidden)
    original = document(files['state.json'])
    require(engine.load() == original, 'NATIVE_LOAD_CHANGED')
    counts = dict(duplicate_preserved=0, stale_envelope_refused=0, terminal_denial_preserved=0,
                  paid_clock_checks=0, pending_denied=0)
    for cached in original['records'].values():
        decision = cached['decision']
        envelope = dict(schema=1, profile=policy.PROFILE, node=manifest['node'],
                        observed_at=decision['observed_at'], decisions=[decision])
        with engine.operation():
            if point['wall'] - policy.LEASE_SECONDS < decision['observed_at']:
                engine.accept(envelope)
                counts['duplicate_preserved'] += 1
            else:
                try:
                    engine.accept(envelope)
                except ValueError as error:
                    require(str(error) == 'INVALID_TRANSPORT_ENVELOPE', 'UNEXPECTED_STALE_REFUSAL')
                else:
                    raise ValueError('STALE_ENVELOPE_ACCEPTED')
                counts['stale_envelope_refused'] += 1
        require(engine.load()['records'] == original['records'], 'DUPLICATE_RENEWED_LEASE')
        if not decision['identity_allowed'] or decision['state'] == 'revoked':
            attack = dict(decision, identity_allowed=True, allowed=True,
                          state='active' if decision['state'] == 'revoked' else decision['state'])
            try:
                policy.successor(decision, attack)
            except ValueError as error:
                require(str(error) == 'TERMINAL_DECISION', 'UNEXPECTED_TERMINAL_REFUSAL')
            else:
                raise ValueError('TERMINAL_DECISION_LOST')
            counts['terminal_denial_preserved'] += 1
        if cached['prepared'] and not decision['cohort']:
            require(not engine.allowed(cached), 'PREPARATION_LOST')
            counts['pending_denied'] += 1
        if decision['cohort']:
            saved = deepcopy(point)
            point['boot'] = str(uuid.uuid4())
            require(not engine.allowed(cached), 'REBOOT_RENEWED_LEASE')
            point.update(boot=cached['boot'], monotonic=cached['deadline'])
            require(not engine.allowed(cached), 'MONOTONIC_RENEWED_LEASE')
            point.update(monotonic=manifest['monotonic'], wall=decision['valid_until'])
            require(not engine.allowed(cached), 'WALLCLOCK_RENEWED_LEASE')
            point.update(saved)
            counts['paid_clock_checks'] += 1
    with closing(sqlite3.connect(':memory:')) as database:
        database.deserialize(files['peers.sqlite'])
        database.execute('PRAGMA trusted_schema=OFF')
        database.execute('BEGIN IMMEDIATE')
        next_id = database.execute('INSERT INTO peers(public) VALUES (?)', ('offline-allocation-probe',)).lastrowid
        require(next_id == summary['sequence_floor'] + 1, 'ALLOCATOR_SEQUENCE_REUSED')
        database.rollback()
    settings = document(files['settings.json'])
    namespace = dict(ipaddress=ipaddress, settings=lambda: settings)
    function = definition(allocator_source, 'address')
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<reviewed-native-address>', 'exec'), namespace)
    require(namespace['address'](next_id) == str(ipaddress.ip_network(settings['network'])[next_id + 1]) + '/32',
            'NATIVE_ALLOCATION_CHANGED')
    return dict(summary, native_safety=counts, next_allocation_id=next_id, installed_safety_ast_match=True,
                native_commands_executed=0, original_capsule_unchanged=True)
