"""Disposable CI-only REALITY gateway + local TLS camouflage + HTTP and DNS fixtures."""
import contextlib,datetime,hashlib,http.server,ipaddress,json,os,socket,socketserver,ssl,struct,subprocess,tempfile,threading,time
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.asymmetric import rsa
ID='11111111-2222-4333-8444-555555555555'
@contextlib.contextmanager
def peers(root):
 assert os.environ.get('GITHUB_ACTIONS')=='true'
 counts={'http':0,'dns':0};lock=threading.Lock()
 class HTTP(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
   data=self.path.encode();self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   with lock:counts['http']+=1
  def log_message(self,*args):pass
 class DNS(socketserver.BaseRequestHandler):
  def handle(self):
   data,sock=self.request
   try:
    pos=12
    while data[pos]:pos+=1+data[pos]
    pos+=1;qtype,qclass=struct.unpack('!HH',data[pos:pos+4]);end=pos+4
    value=socket.inet_pton(socket.AF_INET,'198.19.1.1') if qtype==1 else socket.inet_pton(socket.AF_INET6,'fd79:fc::1') if qtype==28 else b''
    answer=b'\xc0\x0c'+struct.pack('!HHIH',qtype,1,0,len(value))+value if value else b''
    reply=data[:2]+b'\x81\x80'+struct.pack('!HHHH',1,bool(value),0,0)+data[12:end]+answer;sock.sendto(reply,self.client_address)
    with lock:counts['dns']+=1
   except (IndexError,struct.error):pass
 http=http.server.ThreadingHTTPServer(('127.0.0.1',0),HTTP);dns=socketserver.ThreadingUDPServer(('127.0.0.1',0),DNS)
 for server in (http,dns):threading.Thread(target=server.serve_forever,daemon=True).start()
 with tempfile.TemporaryDirectory(prefix='fc-tcp-fixture-') as directory:
  temp=Path(directory);key=rsa.generate_private_key(public_exponent=65537,key_size=2048);name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'android.test')]);now=datetime.datetime.now(datetime.timezone.utc)
  cert=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(days=1)).not_valid_after(now+datetime.timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName('android.test')]),False).sign(key,hashes.SHA256())
  (temp/'cert.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM));(temp/'key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
  tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version=ssl.TLSVersion.TLSv1_3;tls.maximum_version=ssl.TLSVersion.TLSv1_3;tls.set_alpn_protocols(['h2','http/1.1']);tls.load_cert_chain(temp/'cert.pem',temp/'key.pem')
  camouflage=socket.socket();camouflage.bind(('127.0.0.1',0));camouflage.listen();camouflage.settimeout(.5);stop=threading.Event()
  def handle(conn):
   try:
    with tls.wrap_socket(conn,server_side=True) as secure:secure.settimeout(3);secure.recv(4096)
   except (OSError,ssl.SSLError):conn.close()
  def accept():
   while not stop.is_set():
    try:conn,_=camouflage.accept();threading.Thread(target=handle,args=(conn,),daemon=True).start()
    except socket.timeout:pass
    except OSError:break
  threading.Thread(target=accept,daemon=True).start()
  config={'log':{'loglevel':'warning'},'inbounds':[{'listen':'0.0.0.0','port':51900,'protocol':'vless','settings':{'clients':[{'id':ID,'flow':'xtls-rprx-vision'}],'decryption':'none'},'streamSettings':{'network':'raw','security':'reality','realitySettings':{'show':False,'target':'127.0.0.1:'+str(camouflage.getsockname()[1]),'xver':0,'serverNames':['android.test'],'privateKey':'AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgI','shortIds':['0102030405060708']}}}], 'outbounds':[{'tag':'http','protocol':'freedom','settings':{'redirect':'127.0.0.1:'+str(http.server_port)}},{'tag':'dns','protocol':'freedom','settings':{'redirect':'127.0.0.1:'+str(dns.server_address[1])}}], 'routing':{'rules':[{'type':'field','network':'udp','outboundTag':'dns'}]}}
  log=(root/'android-tcp-peer.log').open('w');process=subprocess.Popen([str(root/'clients/android/awg-generated/xray-peer'),'run','-config','stdin:'],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True);process.stdin.write(json.dumps(config));process.stdin.close()
  try:
   until=time.monotonic()+15
   while True:
    if process.poll() is not None:raise RuntimeError('Synthetic REALITY server failed')
    try:
     with socket.create_connection(('127.0.0.1',51900),timeout=.2):break
    except OSError:
     if time.monotonic()>until:raise
     time.sleep(.1)
   yield counts
  finally:
   if process.poll() is None:process.kill();process.wait(timeout=10)
   log.close();stop.set();camouflage.close();http.shutdown();http.server_close();dns.shutdown();dns.server_close()
   (root/'android-tcp-peer-result.json').write_text(json.dumps(counts,indent=2)+'\n')
