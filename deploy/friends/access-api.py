"""Loopback invite/identity API. Public access only through the existing TLS ingress."""
import json,subprocess,threading,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
ROOT=Path('/opt/apps/family_connect/friends-access')
sys.path.insert(0,str(ROOT/'app'))
from control.friends.access import Access,Rejected
access=Access(ROOT/'access.db');slots=threading.BoundedSemaphore(4)

def unique(pairs):
 result={}
 for key,value in pairs:
  if key in result:raise ValueError()
  result[key]=value
 return result
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,status,value):
  raw=json.dumps(value,separators=(',',':')).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  self.connection.settimeout(5)
  if self.path not in ('/friends/challenge','/friends/activate','/friends/configuration/ru','/friends/configuration/nl'):self.reply(404,{'error':'not-found'});return
  if not slots.acquire(blocking=False):self.reply(429,{'error':'busy'});return
  try:
   size=int(self.headers.get('Content-Length','0'));assert 0<size<=8192 and self.headers.get('Content-Type','').split(';')[0]=='application/json'
   value=json.loads(self.rfile.read(size),object_pairs_hook=unique)
   if self.path=='/friends/challenge':
    assert set(value)=={'public_identity','wireguard_public_key','purpose','invitation'}
    result=access.challenge(**value)
   elif self.path=='/friends/activate':
    record=access.complete(value,'activate');result={'device':record['device'],'status':'active'}
   else:
    country=self.path.rsplit('/',1)[1];record=access.complete(value,country)
    if country=='ru':command=['/usr/bin/python3','/opt/apps/family_connect/friends-awg/awg-gateway.py','register']
    else:command=['/usr/bin/ssh','-i','/opt/apps/family_connect/friends-awg/registration-key','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile=/opt/apps/family_connect/friends-awg/known_hosts','root@186.246.45.246','register']
    reply=subprocess.run(command,input=json.dumps(record).encode(),capture_output=True,timeout=15)
    if reply.returncode:raise RuntimeError('Gateway unavailable')
    assigned=json.loads(reply.stdout);assert assigned['public_key']==record['public_key'] and assigned['transport']=='amneziawg-3.1'
    result={'device':record['device'],'country':country,'address':assigned['address'],'tcp_id':record['tcp_id'],'catalog':json.loads((ROOT/'catalog.json').read_bytes())}
   self.reply(200,result)
  except Rejected:self.reply(403,{'error':'access-rejected'})
  except (ValueError,AssertionError,KeyError,TypeError):self.reply(400,{'error':'invalid-request'})
  except Exception:self.reply(503,{'error':'unavailable'})
  finally:slots.release()
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',18084),Handler).serve_forever()
