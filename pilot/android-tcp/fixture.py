"""Disposable CI-only REALITY gateway + local TLS camouflage + HTTP and DNS fixtures."""
import contextlib,datetime,http.server,json,os,socket,socketserver,ssl,struct,tempfile,threading
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization,hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from readiness import Receipt, require_ready, reserve_endpoint, running_peer, running_server
ID='11111111-2222-4333-8444-555555555555'

class FixtureCounts(dict):
 def begin_tests(self):
  require_ready(self.process,self.port,self.receipt)
  self.receipt.record('instrumentation_start',pid=self.process.pid,port=self.port)

class BoundedHTTPServer(http.server.ThreadingHTTPServer):
 daemon_threads=False
 def get_request(self):
  connection,address=super().get_request();connection.settimeout(3);return connection,address

@contextlib.contextmanager
def peers(root):
 assert os.environ.get('GITHUB_ACTIONS')=='true'
 receipt=Receipt(root/'android-tcp-lifecycle.json');counts=FixtureCounts(http=0,dns=0)
 try:
  with contextlib.ExitStack() as resources:
   with _peers(root,counts,receipt,resources):yield counts
 except BaseException as error:
  receipt.record('failed',error_type=type(error).__name__)
  raise
 finally:
  receipt.record('cleanup_finished')
  (root/'android-tcp-peer-result.json').write_text(json.dumps(counts,indent=2)+'\n')

@contextlib.contextmanager
def _peers(root,counts,receipt,resources):
 lock=threading.Lock()
 reservation=resources.enter_context(reserve_endpoint(51900,receipt))
 class HTTP(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
   data=self.path.encode();self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   with lock:counts['http']+=1
  def log_message(self,*args):pass
 class DNS(socketserver.BaseRequestHandler):
  def handle(self):
   if (root/"android-auto-tcp.drop").exists():return
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
 class Control(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
   modes={'/up':(),'/wg-down':('wg',),'/udp-down':('wg','awg'),'/all-down':('wg','awg','tcp')}
   if self.path not in modes:self.send_error(404);return
   for name in ('wg','awg','tcp'):
    path=root/('android-auto-'+name+'.drop')
    if name in modes[self.path]:path.touch()
    else:path.unlink(missing_ok=True)
   self.send_response(200);self.end_headers()
  def log_message(self,*args):pass
 def serve(server,label):return resources.enter_context(running_server(server,receipt,label))
 control=serve(BoundedHTTPServer(('0.0.0.0',51902),Control),'control')
 http_server=serve(BoundedHTTPServer(('127.0.0.1',0),HTTP),'http')
 dns=serve(socketserver.ThreadingUDPServer(('127.0.0.1',0),DNS),'dns')
 with tempfile.TemporaryDirectory(prefix='fc-tcp-fixture-') as directory:
  temp=Path(directory);key=rsa.generate_private_key(public_exponent=65537,key_size=2048);name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'android.test')]);now=datetime.datetime.now(datetime.timezone.utc)
  cert=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(days=1)).not_valid_after(now+datetime.timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName('android.test')]),False).sign(key,hashes.SHA256())
  (temp/'cert.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM));(temp/'key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
  tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version=ssl.TLSVersion.TLSv1_3;tls.maximum_version=ssl.TLSVersion.TLSv1_3;tls.set_alpn_protocols(['h2','http/1.1']);tls.load_cert_chain(temp/'cert.pem',temp/'key.pem')
  class TLS(socketserver.BaseRequestHandler):
   def handle(self):
    self.request.settimeout(3)
    try:
     with tls.wrap_socket(self.request,server_side=True) as secure:secure.recv(4096)
    except (OSError,ssl.SSLError):pass
  camouflage=serve(socketserver.ThreadingTCPServer(('127.0.0.1',0),TLS),'camouflage')
  config={'log':{'loglevel':'warning'},'inbounds':[{'listen':'0.0.0.0','port':51900,'protocol':'vless','settings':{'clients':[{'id':ID,'flow':'xtls-rprx-vision'}],'decryption':'none'},'streamSettings':{'network':'raw','security':'reality','realitySettings':{'show':False,'target':'127.0.0.1:'+str(camouflage.server_address[1]),'xver':0,'serverNames':['android.test'],'privateKey':'AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgI','shortIds':['0102030405060708']}}}], 'outbounds':[{'tag':'http','protocol':'freedom','settings':{'redirect':'127.0.0.1:'+str(http_server.server_port)}},{'tag':'dns','protocol':'freedom','settings':{'redirect':'127.0.0.1:'+str(dns.server_address[1])}}], 'routing':{'rules':[{'type':'field','network':'udp','outboundTag':'dns'}]}}
  reservation.close();receipt.record('reservation_released',port=51900)
  with running_peer([str(root/'clients/android/awg-generated/xray-peer'),'run','-config','stdin:'],config,root,51900,receipt) as process:
   counts.process=process;counts.port=51900;counts.receipt=receipt
   yield counts
   require_ready(process,51900,receipt)
