"""Qualify retained bytecode and selected loaded service settings without executing either."""
import argparse
import base64
import configparser
import hashlib
import importlib.util
import io
import json
import marshal
from pathlib import Path
import re
import resource
import shlex
import struct
import sys
import types


def require(condition):
    if not condition:
        raise ValueError('RUNTIME_QUALIFICATION_REFUSED')


def require_code_match(cached, compiled):
    require(type(cached) is types.CodeType and type(compiled) is types.CodeType and cached == compiled)
    for field in ('co_argcount', 'co_posonlyargcount', 'co_kwonlyargcount', 'co_nlocals', 'co_stacksize',
                  'co_flags', 'co_code', 'co_names', 'co_varnames', 'co_filename', 'co_name', 'co_qualname',
                  'co_firstlineno', 'co_linetable', 'co_exceptiontable', 'co_freevars', 'co_cellvars'):
        require(getattr(cached, field) == getattr(compiled, field))
    for cached_value, compiled_value in zip(cached.co_consts, compiled.co_consts, strict=True):
        if type(compiled_value) is types.CodeType:
            require_code_match(cached_value, compiled_value)


def qualify_bytecode(source, bytecode, filename, mtime_ns, optimize=0):
    require(type(source) is bytes and 0 < len(source) <= 1048576)
    require(type(bytecode) is bytes and 16 < len(bytecode) <= 1048576)
    require(type(filename) is str and filename.startswith('/') and '\x00' not in filename)
    require(type(mtime_ns) is int and mtime_ns >= 0 and type(optimize) is int and optimize in (0, 1, 2))
    require(bytecode[:4] == importlib.util.MAGIC_NUMBER)
    flags = struct.unpack('<I', bytecode[4:8])[0]
    require(flags in (0, 1, 3))
    if flags == 0:
        stamp, size = struct.unpack('<II', bytecode[8:16])
        require(stamp == ((mtime_ns // 1000000000) & 0xffffffff) and size == len(source))
    else:
        require(bytecode[8:16] == importlib.util.source_hash(source))
    stream = io.BytesIO(bytecode[16:])
    cached = marshal.load(stream)
    require(stream.tell() == len(bytecode) - 16 and type(cached) is types.CodeType)
    compiled = compile(source, filename, 'exec', dont_inherit=True, optimize=optimize)
    require_code_match(cached, compiled)
    return dict(classification='BYTECODE_SOURCE_MATCH', source_sha256=hashlib.sha256(source).hexdigest(),
        bytecode_sha256=hashlib.sha256(bytecode).hexdigest(), flags=flags, optimize=optimize,
        python=list(sys.version_info[:3]), code_executed=False, capture_permitted=False)


def qualify_cache_receipt(receipt):
    require(type(receipt) is dict and type(receipt.get('files')) is dict and 0 < len(receipt['files']) <= 64)
    results = {}
    for name, item in receipt['files'].items():
        match = re.fullmatch(r'([A-Za-z_][A-Za-z0-9_]*)\.cpython-([0-9]{2,3})(?:\.opt-([12]))?\.pyc', name)
        require(match is not None and match[2] == str(sys.version_info.major) + str(sys.version_info.minor))
        require(item['optimize'] == int(match[3] or 0))
        source, bytecode = (item[key] for key in ('source', 'bytecode'))
        source_path, cache_path = (Path(entry['path']) for entry in (source, bytecode))
        require(source_path.name == match[1] + '.py' and cache_path.name == name and
                cache_path.parent == source_path.parent / '__pycache__')
        decoded = []
        for entry in (source, bytecode):
            require(type(entry['raw']) is str and len(entry['raw']) <= 1398104)
            raw = base64.b64decode(entry['raw'], validate=True)
            require(len(raw) == entry['metadata']['size'] and hashlib.sha256(raw).hexdigest() == entry['sha256'])
            decoded.append(raw)
        results[name] = qualify_bytecode(*decoded, str(source_path), source['metadata']['mtime_ns'], item['optimize'])
    return dict(classification='RETAINED_CACHE_SOURCE_MATCH', files=results,
                code_executed=False, capture_permitted=False, independent_approval=False)


SERVICE_PROPERTIES = {'Type': 's', 'User': 's', 'Group': 's', 'WorkingDirectory': 's', 'Restart': 's',
    'ProtectSystem': 's', 'NoNewPrivileges': 'b', 'PrivateTmp': 'b', 'RestartUSec': 't',
    'TimeoutStopUSec': 't', 'UMask': 'u', 'ReadWritePaths': 'as', 'EnvironmentFiles': 'a(sb)',
    'ExecStart': 'a(sasbttttuii)', 'ExecStartPre': 'a(sasbttttuii)', 'ExecStartPost': 'a(sasbttttuii)',
    'ExecStop': 'a(sasbttttuii)', 'ExecStopPost': 'a(sasbttttuii)', 'ExecReload': 'a(sasbttttuii)',
    'NeedDaemonReload': 'b', 'DropInPaths': 'as'}
SERVICE_SETTINGS = {'Type', 'User', 'Group', 'WorkingDirectory', 'Restart', 'ProtectSystem', 'NoNewPrivileges',
    'PrivateTmp', 'RestartSec', 'TimeoutStopSec', 'UMask', 'ReadWritePaths', 'EnvironmentFile', 'ExecStart'}


def words(value):
    require(type(value) is str and value and not any(char in value for char in ('\\', '%', '$', '\n', '\r', '\x00')))
    result = shlex.split(value)
    require(result)
    return result


def qualify_service_projection(raw, properties):
    require(type(raw) is bytes and 0 < len(raw) <= 65536 and b'\x00' not in raw)
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.optionxform = str
    parser.read_string(raw.decode('utf-8'))
    require(set(parser.sections()) <= {'Unit', 'Service', 'Install'} and not parser.defaults() and 'Service' in parser)
    service = parser['Service']
    require(set(service) == SERVICE_SETTINGS)
    values = {}
    for key, signature in SERVICE_PROPERTIES.items():
        item = properties[key]
        require(type(item) is dict and set(item) == {'type', 'data'} and item['type'] == signature)
        value = item['data']
        expected = str if signature == 's' else bool if signature == 'b' else int if signature in ('t', 'u') else list
        require(type(value) is expected)
        values[key] = value
    require(not values['DropInPaths'])
    compared = {key: service[key] == values[key] for key in
                ('Type', 'User', 'Group', 'WorkingDirectory', 'Restart', 'ProtectSystem')}
    for key in ('NoNewPrivileges', 'PrivateTmp'):
        require(service[key] in ('yes', 'true', '1', 'no', 'false', '0'))
        compared[key] = (service[key] in ('yes', 'true', '1')) == values[key]
    for key, setting in [('RestartSec', 'RestartUSec'), ('TimeoutStopSec', 'TimeoutStopUSec')]:
        require(re.fullmatch(r'[0-9]{1,10}', service[key]))
        compared[key] = int(service[key]) * 1000000 == values[setting]
    require(re.fullmatch(r'0?[0-7]{3}', service['UMask']))
    compared['UMask'] = int(service['UMask'], 8) == values['UMask']
    compared['ReadWritePaths'] = words(service['ReadWritePaths']) == values['ReadWritePaths']
    environment = words(service['EnvironmentFile'])
    require(len(environment) == 1 and environment[0].removeprefix('-').startswith('/'))
    compared['EnvironmentFile'] = [[environment[0].removeprefix('-'), environment[0].startswith('-')]] == values['EnvironmentFiles']
    command = words(service['ExecStart'])
    require(command[0].startswith('/'))
    loaded = values['ExecStart']
    require(len(loaded) == 1 and type(loaded[0]) is list and len(loaded[0]) == 10)
    require(type(loaded[0][0]) is str and type(loaded[0][1]) is list and
            all(type(token) is str for token in loaded[0][1]) and type(loaded[0][2]) is bool)
    compared['ExecStart'] = loaded[0][:3] == [command[0], command, False]
    extra_hooks = [key for key in ('ExecStartPre', 'ExecStartPost', 'ExecStop', 'ExecStopPost', 'ExecReload') if values[key]]
    mismatched = sorted(key for key, equal in compared.items() if not equal)
    return dict(classification='SELECTED_SERVICE_SETTINGS_MATCH' if not mismatched and not extra_hooks else
        'SELECTED_SERVICE_SETTINGS_DIFFER', compared_settings=sorted(compared), mismatched_settings=mismatched,
        extra_loaded_hooks=extra_hooks, need_daemon_reload=values['NeedDaemonReload'],
        full_unit_equivalence=False, environment_contents_checked=False, capture_permitted=False,
        independent_approval=False, source_sha256=hashlib.sha256(raw).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--cache-receipt', type=Path)
    source.add_argument('--unit-receipt', type=Path)
    args = parser.parse_args()
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        target = args.cache_receipt or args.unit_receipt
        require(target.stat().st_size <= 12 * 1024 * 1024)
        receipt = json.loads(target.read_bytes())
        result = qualify_cache_receipt(receipt) if args.cache_receipt else qualify_service_projection(
            base64.b64decode(receipt['fragment']['raw'], validate=True), receipt['properties'])
        print(json.dumps(result, sort_keys=True))
        return 0 if result['classification'].endswith('_MATCH') else 1
    except Exception:
        print(json.dumps(dict(classification='RUNTIME_QUALIFICATION_REFUSED', capture_permitted=False)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
