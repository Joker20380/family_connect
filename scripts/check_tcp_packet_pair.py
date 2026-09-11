import json,subprocess,time
from pathlib import Path
base=Path('/tmp/fc-tcp-packets');base.mkdir(mode=0o700,exist_ok=True);base.chmod(0o700)
root=Path(__file__).resolve().parents[1]
start=time.time()
server=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','root@185.251.89.19','python3 -u -'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
server.stdin.write((root/'scripts/tcp_packet_capture.py').read_text());server.stdin.close()
ready=server.stdout.readline()
if not ready:raise RuntimeError('Server capture did not start')
ready=json.loads(ready);print(json.dumps({'server_ready':ready,'local_received':time.time(),'request_start':start}),flush=True)
cmd=['docker','run','--rm','--user','0','--cap-add','NET_ADMIN','--device','/dev/net/tun']
for src,dst,mode in [(str(root/'clients/linux'),'/fix','ro'),(str(root/'clients/desktop'),'/desktop','ro'),(str(root/'scripts'),'/checks','ro'),('/tmp/fc-tcp-private','/keys','ro'),('/tmp/fc-tcp-packets/results','/results','rw')]:cmd+=['-v',f'{src}:{dst}:{mode}']
(base/'results').mkdir(exist_ok=True)
try:
    client=subprocess.run(cmd+['--entrypoint','python3','family-connect-xray:26.3.27-pilot1','/checks/check_tcp_packet_client.py'],capture_output=True,text=True,timeout=115)
    print(json.dumps({'client_exit':client.returncode,'client_error':client.stderr[-300:]}),flush=True)
    result=server.stdout.read();rc=server.wait(timeout=15)
    if rc:raise RuntimeError('Server capture failed')
    (base/'results/server.json').write_text(json.dumps(json.loads(result)))
    print(json.dumps({'complete':True,'seconds':round(time.time()-start,2)}),flush=True)
finally:
    if server.poll() is None:server.terminate()
