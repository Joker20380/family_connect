import json,runpy,threading,time
from pathlib import Path
from tcp_packet_capture import capture
if not Path('/.dockerenv').exists():raise RuntimeError('Container required')
p=json.loads(Path('/keys/linux.conf').read_text())
stop=threading.Event();rows=[]
def worker():rows.extend(capture('eth0',p['server'],443,115,stop))
th=threading.Thread(target=worker);th.start()
try:runpy.run_path('/checks/check_tcp_matched.py',run_name='__main__')
finally:
    stop.set();th.join();Path('/results/client-headers.json').write_text(json.dumps(rows))
