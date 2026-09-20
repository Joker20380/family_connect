"""Describe checked AWG 3.1 binaries for the privileged Linux installer."""
import hashlib
import json
import sys
from pathlib import Path

root=Path(sys.argv[1])
pins=json.loads(Path(sys.argv[2]).read_text())
record=dict(schema=1, engine=pins['engine_commit'], tools=pins['tools_commit'],
            files={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
                   for name in ('amneziawg-go','awg','awg-quick')})
(root/'awg31.json').write_text(json.dumps(record,sort_keys=True)+'\n')
