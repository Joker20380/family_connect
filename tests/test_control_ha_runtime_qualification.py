import base64
import copy
import hashlib
import importlib.util
import json
import marshal
import struct
import subprocess
import sys

import pytest

from scripts import control_ha_runtime_qualification as qualification


SOURCE = b'"""Synthetic module."""\ndef value():\n    assert True\n    return "source"\n'
FILENAME = '/synthetic/package/module.py'
MTIME = 1700000000000000000


def bytecode(source=SOURCE, filename=FILENAME, flags=0, optimize=0):
    header = importlib.util.MAGIC_NUMBER + struct.pack('<I', flags)
    header += struct.pack('<II', MTIME // 1000000000, len(source)) if flags == 0 else importlib.util.source_hash(source)
    return header + marshal.dumps(compile(source, filename, 'exec', dont_inherit=True, optimize=optimize))


@pytest.mark.parametrize('flags', [0, 1, 3])
@pytest.mark.parametrize('optimize', [0, 1, 2])
def test_matching_bytecode_is_checked_without_execution(flags, optimize):
    result = qualification.qualify_bytecode(SOURCE, bytecode(flags=flags, optimize=optimize), FILENAME, MTIME, optimize)
    assert result['classification'] == 'BYTECODE_SOURCE_MATCH'
    assert result['flags'] == flags and result['optimize'] == optimize
    assert result['code_executed'] is result['capture_permitted'] is False


@pytest.mark.parametrize('change', ['magic', 'flags', 'timestamp', 'size', 'source_hash', 'forged_code',
    'filename', 'nested_filename', 'trailing', 'not_code'])
def test_bytecode_corruption_and_forgery_refused(change):
    raw = bytecode()
    if change == 'magic':
        raw = b'nope' + raw[4:]
    elif change == 'flags':
        raw = raw[:4] + struct.pack('<I', 2) + raw[8:]
    elif change == 'timestamp':
        raw = raw[:8] + b'\x00' * 4 + raw[12:]
    elif change == 'size':
        raw = raw[:12] + b'\x00' * 4 + raw[16:]
    elif change == 'source_hash':
        raw = bytecode(flags=3)
        raw = raw[:8] + b'\x00' * 8 + raw[16:]
    elif change == 'forged_code':
        raw = raw[:16] + marshal.dumps(compile('raise RuntimeError("Do not execute")', FILENAME, 'exec'))
    elif change == 'filename':
        raw = bytecode(filename='/other/module.py')
    elif change == 'nested_filename':
        code = marshal.loads(raw[16:])
        constants = tuple(value.replace(co_filename='/other/module.py') if hasattr(value, 'co_filename') else value for value in code.co_consts)
        raw = raw[:16] + marshal.dumps(code.replace(co_consts=constants))
    elif change == 'trailing':
        raw += b'extra'
    else:
        raw = raw[:16] + marshal.dumps(['not code'])
    with pytest.raises(ValueError, match='QUALIFICATION_REFUSED'):
        qualification.qualify_bytecode(SOURCE, raw, FILENAME, MTIME)


def test_matching_code_never_executes_side_effects(tmp_path):
    marker = tmp_path / 'executed'
    source = f'from pathlib import Path\nPath({str(marker)!r}).write_text("bad")\n'.encode()
    result = qualification.qualify_bytecode(source, bytecode(source), FILENAME, MTIME)
    assert result['code_executed'] is False and not marker.exists()


@pytest.mark.parametrize('nested', [False, True])
@pytest.mark.parametrize('field', ['co_stacksize', 'co_qualname'])
def test_code_metadata_ignored_by_python_equality_still_refuses(field, nested):
    raw = bytecode()
    original = marshal.loads(raw[16:])

    def changed(code):
        value = code.co_stacksize + 1 if field == 'co_stacksize' else 'forged_name'
        return code.replace(**{field: value})

    modified = original.replace(co_consts=tuple(changed(value) if hasattr(value, 'co_code') else value
        for value in original.co_consts)) if nested else changed(original)
    assert original == modified
    with pytest.raises(ValueError, match='QUALIFICATION_REFUSED'):
        qualification.qualify_bytecode(SOURCE, raw[:16] + marshal.dumps(modified), FILENAME, MTIME)


def receipt():
    name = f'module.cpython-{sys.version_info.major}{sys.version_info.minor}.pyc'
    def entry(raw, path):
        return dict(raw=base64.b64encode(raw).decode(), path=path, sha256=hashlib.sha256(raw).hexdigest(),
                    metadata=dict(size=len(raw), mtime_ns=MTIME))
    return dict(files={name: dict(source=entry(SOURCE, FILENAME),
        bytecode=entry(bytecode(), '/synthetic/package/__pycache__/' + name), optimize=0)})


def test_receipt_and_cli_preserve_false_approval(tmp_path):
    value = receipt()
    assert qualification.qualify_cache_receipt(value)['independent_approval'] is False
    target = tmp_path / 'cache.json'
    target.write_text(json.dumps(value))
    process = subprocess.run([sys.executable, '-m', 'scripts.control_ha_runtime_qualification',
        '--cache-receipt', str(target)], capture_output=True, timeout=15, check=True)
    result = json.loads(process.stdout)
    assert result['classification'] == 'RETAINED_CACHE_SOURCE_MATCH' and not result['capture_permitted']


@pytest.mark.parametrize('change', ['hash', 'size', 'path', 'optimization', 'tag'])
def test_receipt_binding_refuses_inconsistency(change):
    value = receipt()
    name, item = next(iter(value['files'].items()))
    if change == 'hash':
        item['source']['sha256'] = '0' * 64
    elif change == 'size':
        item['source']['metadata']['size'] += 1
    elif change == 'path':
        item['bytecode']['path'] = '/elsewhere/' + name
    elif change == 'optimization':
        item['optimize'] = 1
    else:
        value['files']['module.cpython-999.pyc'] = value['files'].pop(name)
    with pytest.raises(ValueError, match='QUALIFICATION_REFUSED'):
        qualification.qualify_cache_receipt(value)


UNIT = b'''[Unit]
Description=Synthetic fixture
[Service]
Type=simple
User=fixture
Group=fixture
WorkingDirectory=/synthetic
EnvironmentFile=/synthetic/runtime.env
ExecStart=/synthetic/python -B /synthetic/bootstrap.py
Restart=on-failure
RestartSec=5
TimeoutStopSec=15
UMask=0077
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/synthetic/state /synthetic/run
PrivateTmp=yes
[Install]
WantedBy=multi-user.target
'''


def properties():
    values = dict(Type='simple', User='fixture', Group='fixture', WorkingDirectory='/synthetic',
        EnvironmentFiles=[['/synthetic/runtime.env', False]], ExecStart=[['/synthetic/python',
        ['/synthetic/python', '-B', '/synthetic/bootstrap.py'], False, 1, 2, 0, 0, 1234, 0, 0]],
        ExecStartPre=[], ExecStartPost=[], ExecStop=[], ExecStopPost=[], ExecReload=[], Restart='on-failure',
        RestartUSec=5000000, TimeoutStopUSec=15000000, UMask=0o077, NoNewPrivileges=True,
        PrivateTmp=True, ProtectSystem='strict', ReadWritePaths=['/synthetic/state', '/synthetic/run'],
        NeedDaemonReload=True, DropInPaths=[])
    return {key: dict(type=signature, data=values[key]) for key, signature in qualification.SERVICE_PROPERTIES.items()}


def test_reload_flag_is_not_a_service_command_difference():
    result = qualification.qualify_service_projection(UNIT, properties())
    assert result['classification'] == 'SELECTED_SERVICE_SETTINGS_MATCH'
    assert len(result['compared_settings']) == 14 and result['need_daemon_reload'] is True
    assert result['full_unit_equivalence'] is result['environment_contents_checked'] is False
    assert result['capture_permitted'] is result['independent_approval'] is False


@pytest.mark.parametrize(('setting', 'new'), [('Type', 'notify'), ('User', 'other'), ('Group', 'other'),
    ('WorkingDirectory', '/other'), ('Restart', 'always'), ('ProtectSystem', 'full'), ('NoNewPrivileges', False),
    ('PrivateTmp', False), ('RestartUSec', 10), ('TimeoutStopUSec', 10), ('UMask', 0),
    ('ReadWritePaths', ['/other']), ('EnvironmentFiles', [['/other/env', False]]),
    ('ExecStart', [['/other/python', ['/other/python'], False, 0, 0, 0, 0, 0, 0, 0]])])
def test_selected_setting_difference_is_reported(setting, new):
    value = properties()
    value[setting]['data'] = copy.deepcopy(new)
    result = qualification.qualify_service_projection(UNIT, value)
    assert result['classification'] == 'SELECTED_SERVICE_SETTINGS_DIFFER'
    assert len(result['mismatched_settings']) == 1 and not result['capture_permitted']


def test_extra_loaded_hook_is_not_ignored():
    value = properties()
    value['ExecStopPost']['data'] = copy.deepcopy(value['ExecStart']['data'])
    result = qualification.qualify_service_projection(UNIT, value)
    assert result['extra_loaded_hooks'] == ['ExecStopPost']
    assert result['classification'] == 'SELECTED_SERVICE_SETTINGS_DIFFER'


@pytest.mark.parametrize('change', ['type', 'bool', 'dropin', 'unknown', 'duplicate', 'escape', 'duration', 'environment', 'mask'])
def test_unqualified_unit_syntax_and_bindings_refuse(change):
    raw, value = UNIT, properties()
    if change == 'type':
        value['User']['type'] = 'as'
    elif change == 'bool':
        value['NeedDaemonReload']['data'] = 1
    elif change == 'dropin':
        value['DropInPaths']['data'] = ['/synthetic/override.conf']
    elif change == 'unknown':
        raw = raw.replace(b'Type=simple', b'Type=simple\nExecCondition=/synthetic/condition')
    elif change == 'duplicate':
        raw = raw.replace(b'Type=simple', b'Type=simple\nType=notify')
    elif change == 'escape':
        raw = raw.replace(b'/synthetic/bootstrap.py', b'/synthetic/%n.py')
    elif change == 'duration':
        raw = raw.replace(b'RestartSec=5', b'RestartSec=5min')
    elif change == 'environment':
        raw = raw.replace(b'EnvironmentFile=/', b'EnvironmentFile=--/')
    else:
        raw = raw.replace(b'UMask=0077', b'UMask=9999')
    with pytest.raises((ValueError, qualification.configparser.Error)):
        qualification.qualify_service_projection(raw, value)
