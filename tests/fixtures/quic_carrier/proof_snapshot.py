import json


def remote_drain(ssh,host,stage):
    source='''import json
from pathlib import Path
path=Path(STAGE)/'peer.jsonl';result=[]
assert path.stat().st_size<=33554432
with path.open('rb') as source:
 for line in source:
  if line.endswith(b'\\n') and b'"event":"p_drained"' in line:
   assert len(line)<=4194304
   record=json.loads(line)
   if record.get('event')=='p_drained':result=[record]
print(json.dumps(result,separators=(',',':')))
'''.replace('STAGE',repr(stage))
    return json.loads(ssh(host,source,timeout=12))
