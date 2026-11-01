import json
from pathlib import Path
import sys
import time


def main():
    path=Path(sys.argv[1])
    if not str(path).startswith('/run/family-connect-rehearsal/fleet-rehearsal-') or path.name!='ready.json':
        raise SystemExit(1)
    deadline=time.monotonic()+40
    while time.monotonic()<deadline:
        if path.is_file() and not path.is_symlink() and 0<path.stat().st_size<=8192:
            try:
                value=json.loads(path.read_bytes())
                if value.get('version')==1 and value.get('seeds'):
                    return
            except (ValueError,OSError):
                pass
        time.sleep(0.25)
    raise SystemExit(1)


if __name__=='__main__':
    main()
