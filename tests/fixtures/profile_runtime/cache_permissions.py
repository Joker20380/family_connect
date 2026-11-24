import hashlib
import importlib.util
import json
import marshal
import os
from pathlib import Path
import pwd
import struct
import subprocess
import sys


def main():
    directory = Path(sys.argv[1])
    assert os.geteuid() == 0 and sys.version_info[:3] == (3, 14, 4)
    assert directory.parent == Path('/run') and directory.name.startswith('fc-ha-cache-')
    assert directory.resolve(strict=True) == directory and directory.stat().st_uid == 0
    assert not list(directory.iterdir())
    account = pwd.getpwnam('family-restricted')
    assert account.pw_uid == 979
    directory.chmod(0o755)
    source = directory / 'fc_ha_cache_fixture.py'
    source.write_text('VALUE = "READABLE_SOURCE"\n')
    source.chmod(0o644)
    cache = Path(importlib.util.cache_from_source(str(source)))
    cache.parent.mkdir(mode=0o700)
    header = importlib.util.MAGIC_NUMBER + struct.pack('<III', 0, int(source.stat().st_mtime), source.stat().st_size)
    cache.write_bytes(header + marshal.dumps(compile('raise RuntimeError("SYNTHETIC_CACHE_USED")', str(source), 'exec')))
    cache.chmod(0o600)
    before = hashlib.sha256(cache.read_bytes()).hexdigest()
    child = '''import importlib,json,os,sys
sys.path.insert(0,sys.argv[1])
assert sys.flags.isolated==sys.flags.no_site==sys.flags.no_user_site==1 and sys.dont_write_bytecode
try:
    module=importlib.import_module('fc_ha_cache_fixture')
    result=module.VALUE
except RuntimeError as error:
    assert str(error)=='SYNTHETIC_CACHE_USED'
    result='SYNTHETIC_CACHE_USED'
print(json.dumps(dict(uid=os.getuid(),result=result)))
'''

    def enter():
        os.setgroups(os.getgrouplist(account.pw_name, account.pw_gid))
        os.setgid(account.pw_gid)
        os.setuid(account.pw_uid)

    results = []
    for selected in (enter, None):
        result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', child, str(directory)],
            env={'PATH': '/usr/bin:/bin', 'LANG': 'C'}, cwd='/', capture_output=True, timeout=4, preexec_fn=selected)
        assert result.returncode == 0 and not result.stderr
        results.append(json.loads(result.stdout))
    assert results == [dict(uid=979, result='READABLE_SOURCE'), dict(uid=0, result='SYNTHETIC_CACHE_USED')]
    assert hashlib.sha256(cache.read_bytes()).hexdigest() == before
    assert {member.name for member in directory.iterdir()} == {source.name, '__pycache__'}
    assert list(cache.parent.iterdir()) == [cache]
    print(json.dumps(dict(classification='NATIVE_CACHE_PERMISSION_STAND_PASS', python=list(sys.version_info[:3]),
        unprivileged_source_fallback=True, root_cache_read=True, cache_unchanged=True,
        application_imports=False, capture_permitted=False), sort_keys=True))


if __name__ == '__main__':
    main()
