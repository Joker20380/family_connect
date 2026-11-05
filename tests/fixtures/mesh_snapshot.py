import os
from pathlib import Path
import sys


def main():
    assert os.geteuid() == 0 and Path('/.dockerenv').exists()
    assert len(sys.argv) == 3 and os.environ.get('SSH_ORIGINAL_COMMAND') == 'restricted-sync'
    capsule, configuration = map(Path, sys.argv[1:])
    assert capsule.is_absolute() and configuration.is_relative_to('/run')
    sys.path.insert(0, str(capsule))
    from control.friends import profile_snapshot
    assert profile_snapshot.__file__.startswith(str(capsule)+'/')
    raw = sys.stdin.buffer.read(20001)
    try:
        request = profile_snapshot.store.parse(raw, 20000)
        if request != profile_snapshot.SNAPSHOT_REQUEST or type(request['schema']) is not int:
            raise ValueError()
    except Exception:
        raise SystemExit('READ_ONLY_SNAPSHOT_REQUIRED') from None
    profile_snapshot.CONFIGURATION_PATH = configuration
    descriptor = os.memfd_create('qualification-snapshot-request', os.MFD_CLOEXEC)
    with os.fdopen(descriptor, 'w+b') as stream:
        stream.write(raw)
        stream.flush()
        stream.seek(0)
        os.dup2(stream.fileno(), 0, inheritable=True)
        raise SystemExit(profile_snapshot.main([]))


if __name__ == '__main__':
    main()
