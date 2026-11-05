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
    profile_snapshot.CONFIGURATION_PATH = configuration
    raise SystemExit(profile_snapshot.main([]))


if __name__ == '__main__':
    main()
