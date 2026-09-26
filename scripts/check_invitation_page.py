"""Local Firefox acceptance of the invitation page; synthetic tokens, no live claims."""
from pathlib import Path
import base64,hashlib,json,re,subprocess,tempfile,threading
from http.server import BaseHTTPRequestHandler,HTTPServer
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'artifacts/invitation';OUTPUT.mkdir(parents=True,exist_ok=True)
source=(ROOT/'deploy/friends/invite/index.html').read_text()
check=r'''
addEventListener('load',async()=>{
 try{
  document.documentElement.classList.add('no-motion');
  const expected=/^[a-f0-9]{64}$/.test(location.hash.slice(1)),fragment=location.hash;
  function check(v,message){if(!v)throw Error(message)}
  const installed=byId('installed'),circle=byId('open');
  check(!installed.checked,'initially off');
  check(getComputedStyle(installed).borderTopColor==='rgb(255, 173, 70)','off orange');
  circle.click();check(!byId('downloads-view').hidden,'download navigation');check(location.hash===fragment,'invitation fragment preserved');
  for(const platform of ['windows','linux','android']){
   document.querySelector('[data-platform="'+platform+'"]').click();
   check(byId('download').getAttribute('href').startsWith('/downloads/FamilyConnect-'),'download link');
  }
  check(byId('download').getAttribute('href').includes('beta51.apk'),'APK version');
  byId('connect-tab').click();installed.checked=true;installed.dispatchEvent(new Event('change'));

  check(getComputedStyle(installed).borderTopColor==='rgb(112, 244, 198)','on turquoise');
  check(circle.dataset.ready===String(expected),'invitation readiness');
  if(expected)check(circle.getAttribute('href')==='familyconnect://invite/'+location.hash.slice(1),'exact URI');
  else {check(circle.getAttribute('aria-disabled')==='true','invalid disabled');circle.click();check(byId('message').textContent.includes('полную ссылку'),'invalid message');}
  byId('help-tab').click();byId('motion').checked=false;byId('motion').dispatchEvent(new Event('change'));check(document.documentElement.classList.contains('no-motion'),'motion off');
  byId('connect-tab').click();check(location.hash===fragment,'fragment survives all tabs');
  if(location.search.includes('off')){installed.checked=false;installed.dispatchEvent(new Event('change'));}
  check(document.documentElement.scrollWidth<=innerWidth,'horizontal overflow');
  await fetch('/result',{method:'POST',body:JSON.stringify({passed:true,invitation:expected,checks:13})});
 }catch(e){await fetch('/result',{method:'POST',body:JSON.stringify({passed:false,error:String(e)})});}
});
'''

page=source.replace('</script>',check+'</script>')
def digest(tag):return base64.b64encode(hashlib.sha256(re.search('<'+tag+'>(.*?)</'+tag+'>',page,re.S).group(1).encode()).digest()).decode()
csp="default-src 'none'; script-src 'sha256-"+digest('script')+"'; style-src 'sha256-"+digest('style')+"'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
result={};done=threading.Event()
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  raw=page.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Security-Policy',csp);self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  assert self.path=='/result';result.update(json.loads(self.rfile.read(int(self.headers['Content-Length']))));self.send_response(204);self.end_headers();done.set()
s=HTTPServer(('127.0.0.1',0),H);threading.Thread(target=s.serve_forever,daemon=True).start()
try:
 for name,fragment in [('valid-on','a'*64),('valid-off','a'*64),('missing',''),('invalid','BAD')]:
  done.clear();result.clear()
  profile=tempfile.mkdtemp(prefix='fc-invite-page-')
  command=['firefox','--headless','--no-remote','--profile',profile,'--window-size','390,1100','--screenshot',str(OUTPUT/f'page-{name}.png'),f'http://127.0.0.1:{s.server_port}/?render={name}#'+fragment]
  p=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  try:
   assert done.wait(35),'Browser timeout';assert result.get('passed'),result
   p.wait(timeout=20);print(name,result,flush=True)
  finally:
   if p.poll() is None:p.terminate();p.wait(timeout=10)
finally:s.shutdown()
