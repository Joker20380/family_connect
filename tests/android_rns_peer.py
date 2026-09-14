"""Isolated real RNS test of the Python code packaged in Android; PUBLIC TEST identities only."""
import base64, hashlib, json, os, pathlib, select, socket, subprocess, sys
root=pathlib.Path(os.environ.get('FC_TEST_REPO',pathlib.Path(__file__).resolve().parents[1]))
source=pathlib.Path(os.environ.get('FC_ANDROID_RNS_SOURCE',root/'clients/android/app/src/main/python'))
sys.path[:0]=[str(root),str(source)]
if sys.argv[2]=='internal':sys.modules['cryptography']=None
import RNS
from fc_rns_transport import Channel

def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def b64(raw):return base64.b64encode(raw).decode()
d=pathlib.Path(sys.argv[1]);d.mkdir(exist_ok=True)
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
server=subprocess.Popen([sys.executable,str(root/'tests/reticulum_control_peer.py'),'server',str(d),str(port)],cwd=root,env={**os.environ,'PYTHONPATH':str(root)},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
channel=None
try:
    assert select.select([server.stdout],[],[],15)[0], 'server startup timeout'
    assert server.stdout.readline().strip()=='ready','server startup failed'
    fixture=json.loads((d/'fixture.json').read_text());identity=RNS.Identity.from_bytes(bytes.fromhex(fixture['identity']))
    wg=RNS.Cryptography.X25519PrivateKey.from_private_bytes(bytes.fromhex(fixture['wg'])).public_key().public_bytes()
    keys=dict(public_identity=b64(identity.get_public_key()),wireguard_public_key=b64(wg))
    class Callbacks:
        stop=False;binds=0
        def bindSocket(self,fd):self.binds+=1;return fd>=0
        def cancelled(self):return self.stop
    callbacks=Callbacks()
    def open_channel():return Channel(str(d/'android'),'127.0.0.1',port,b64(bytes.fromhex(fixture['provider'])),callbacks)
    def request(path,body):return base64.b64decode(channel.request(path,b64(encode(body))))
    def fetch():
        challenge=json.loads(request('/control/v1/challenge',keys))
        proof=dict(schema_version=1,audience='family-connect/provisioning-fetch/v1',**keys,challenge=challenge['challenge'])
        proof['signature']=b64(identity.sign(b'family-connect/provisioning-fetch/v1\0'+encode(proof)))
        return request('/control/v1/fetch',proof)
    channel=open_channel();envelope=fetch();assert 0<len(envelope)<=65536
    body=dict(schema_version=1,device=identity.hash.hex(),public_identity=keys['public_identity'],envelope_hash=hashlib.sha256(envelope).hexdigest(),config_id='config-1',sequence=1,status='COMMITTED',error='NONE',timestamp=1000)
    body['ack_id']=hashlib.sha256(encode(body)).hexdigest()
    receipt=dict(body=body,signature=b64(identity.sign(b'family-connect/control-ack/v1\0'+encode(body))))
    assert request('/control/v1/ack',receipt)==b'ACK_STORED'
    assert request('/control/v1/ack',receipt)==b'ACK_STORED'
    callbacks.stop=True
    try:request('/control/v1/challenge',keys);raise AssertionError('not cancelled')
    except OSError:pass
    channel.close();callbacks.stop=False;channel=open_channel();second=fetch();assert second!=envelope
    # Parent verifies opaque wire bytes using the reference config verifier in its separate process.
    (d/'envelope1').write_bytes(envelope);(d/'envelope2').write_bytes(second)
    assert callbacks.binds==2
    if sys.argv[2]=='internal':assert RNS.Cryptography.Provider.backend()=='internal'
    print('REAL_RNS_PASS '+sys.argv[2],flush=True)
finally:
    if channel is not None:channel.close()
    server.terminate()
    try:server.wait(timeout=5)
    except subprocess.TimeoutExpired:server.kill();server.wait()
