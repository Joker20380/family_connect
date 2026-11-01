import json
from pathlib import Path
import re
import sys
import time


def main():
    path=sys.argv[1]
    if not re.fullmatch(r'/etc/family-connect/rehearsal/gw-[0-9a-f]{32}/metadata.json',path):
        raise SystemExit(1)
    metadata=json.loads(Path(path).read_bytes())
    lifetime=metadata.get('runtime_lifetime_seconds')
    if type(lifetime) is not int or not 300<=lifetime<=900 or not time.time()+lifetime+120<metadata['material_expires_at']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
