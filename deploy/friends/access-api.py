"""Loopback invite/identity API. Public access only through the existing TLS ingress."""
import base64,ipaddress,json,logging,subprocess,threading,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
ROOT=Path('/opt/apps/family_connect/friends-access')
if __name__=='__main__':sys.path.insert(0,str(ROOT/'app'))
from control.friends.access import Access,Rejected
from control.friends.chat import ChatAccess
from control.friends.chat_sync import synchronize
from control.friends.referrals import Referrals,Exhausted,RateLimited
access=Access(ROOT/'access.db');slots=threading.BoundedSemaphore(4)
chat_access=ChatAccess(access)

def unique(pairs):
 result={}
 for key,value in pairs:
  if key in result:raise ValueError()
  result[key]=value
 return result

def configuration_catalog(country):
 raw=(ROOT/'catalog.json').read_bytes()
 if len(raw)>16384:raise ValueError('Oversized catalog')
 catalog=json.loads(raw,object_pairs_hook=unique)
 payload=json.loads(base64.b64decode(catalog['payload'],validate=True),object_pairs_hook=unique)
 gateways=[gateway for gateway in payload['gateways'] if gateway['country']==country]
 if len(gateways)!=1:raise ValueError('Ambiguous gateway')
 host=gateways[0]['tcp']['server']
 address=ipaddress.IPv4Address(host)
 if str(address)!=host or address.is_loopback or address.packed[0]==0 or address.packed[0]>=224:
  raise ValueError('Invalid gateway address')
 return catalog,host

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,status,value):
  raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  self.connection.settimeout(5)
  if self.path not in ('/friends/challenge','/friends/activate','/friends/restricted-readiness','/friends/restricted-readiness/challenge','/friends/restricted-readiness/ack-challenge','/friends/restricted-readiness/ack','/friends/configuration/ru','/friends/configuration/nl','/friends/chat/challenge','/friends/chat/register','/friends/referral/issue','/friends/referral/claim','/friends/device/status','/friends/device/support','/friends/device/diagnostics','/friends/notices/publish','/friends/notices/device/role','/friends/notices/device/publish','/friends/notices/device/list','/friends/notices/device/edit'):self.reply(404,{'error':'not-found'});return
  if not slots.acquire(blocking=False):self.reply(429,{'error':'busy'});return
  phase='http_parse'
  try:
   size=int(self.headers.get('Content-Length','0'));assert 0<size<=(32768 if self.path in ('/friends/notices/publish','/friends/notices/device/publish','/friends/notices/device/list','/friends/notices/device/edit') else 8192) and self.headers.get('Content-Type','').split(';')[0]=='application/json'
   value=json.loads(self.rfile.read(size),object_pairs_hook=unique)
   if self.path.startswith('/friends/restricted-readiness'):
    phase='handler_import'
    from control.friends.restricted import request
    phase='dispatch'
    action='fetch' if self.path=='/friends/restricted-readiness' else self.path.rsplit('/',1)[1]
    result=request(access,action,value,request_id=self.headers.get('X-FC-Probe-ID'))
   elif self.path.startswith('/friends/notices/device/'):
    from control.friends.notices import device_request,NoticeDenied,NoticeConflict
    try:result=device_request(access,ROOT/'notices.sqlite',Path('/opt/apps/family_connect/state-product-https/config/downloads/family-connect-events-v1.json'),self.path.rsplit('/',1)[1],value)
    except NoticeDenied:raise Rejected()
    except NoticeConflict:self.reply(409,{'error':'notice-changed'});return
   elif self.path=='/friends/notices/publish':
    from control.friends.notices import publish,NoticeDenied
    try:result=publish(ROOT/'notices.sqlite',Path('/opt/apps/family_connect/state-product-https/config/downloads/family-connect-events-v1.json'),self.headers.get('Authorization',''),value)
    except NoticeDenied:raise Rejected()
   elif self.path=='/friends/referral/issue':
    result=Referrals(access,(ROOT/'referral.key').read_bytes()).issue(value)
   elif self.path=='/friends/referral/claim':
    assert set(value)=={'token','request_id'}
    result=Referrals(access,(ROOT/'referral.key').read_bytes()).claim(**value)
   elif self.path=='/friends/chat/challenge':
    assert set(value)=={'public_identity','wireguard_public_key','chat_public'}
    result=chat_access.challenge(**value)
   elif self.path=='/friends/chat/register':
    assert set(value)=={'proof','chat_public','chat_signature'}
    result=chat_access.register(**value)
    if (ROOT/'chat-node.json').exists():
     snapshot,node=synchronize(chat_access)
     if value['chat_public'] not in snapshot['public_keys']:raise Rejected()
     result.update(status='active',node=node)
     from control.friends.chat_publishers import configured
     publisher_config=configured(ROOT/'chat-publishers.json',result['device'],value['chat_public'],node['expires_at'],int(access.clock()))
     if publisher_config is not None:result['publisher_configuration']=publisher_config
   elif self.path=='/friends/challenge':
    assert set(value)=={'public_identity','wireguard_public_key','purpose','invitation'}
    result=access.challenge(**value)
   elif self.path=='/friends/activate':
    record=access.complete(value,'activate');result={'device':record['device'],'status':'active'}
   elif self.path=='/friends/device/status':
    result=access.status(value)
   elif self.path=='/friends/device/diagnostics':
    from control.friends.diagnostics import request
    result=request(access,ROOT/'diagnostics.sqlite',value)
   elif self.path=='/friends/device/support':
    from control.friends.support_ids import request
    result=request(access,value)
   else:
    country=self.path.rsplit('/',1)[1];record=access.complete(value,country)
    catalog,host=configuration_catalog(country)
    if country=='ru':command=['/usr/bin/python3','/opt/apps/family_connect/friends-awg/awg-gateway.py','register']
    else:command=['/usr/bin/ssh','-i','/opt/apps/family_connect/friends-awg/registration-key','-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile=/opt/apps/family_connect/friends-awg/known_hosts','root@'+host,'register']
    reply=subprocess.run(command,input=json.dumps(record).encode(),capture_output=True,timeout=15)
    if reply.returncode:raise RuntimeError('Gateway unavailable')
    assigned=json.loads(reply.stdout);assert assigned['public_key']==record['public_key'] and assigned['transport']=='amneziawg-3.1'
    result={'device':record['device'],'country':country,'address':assigned['address'],'tcp_id':record['tcp_id'],'catalog':catalog}
   self.reply(200,result)
  except Exhausted:self.reply(410,{'error':'referral-pool-exhausted'})
  except RateLimited:self.reply(429,{'error':'referral-rate-limited'})
  except Rejected:self.reply(403,{'error':'access-rejected'})
  except (ValueError,AssertionError,KeyError,TypeError):self.reply(400,{'error':'invalid-request'})
  except Exception as error:
   if self.path=='/friends/restricted-readiness/challenge' and type(error).__name__!='ChallengeUnavailable':
    logging.getLogger(__name__).warning('restricted_challenge stage=%s reason=%s',phase,'INTERNAL_DEPENDENCY_FAILURE' if phase=='handler_import' else 'INTERNAL_ERROR')
   self.reply(503,{'error':'unavailable'})
  finally:slots.release()
def main():
 import argparse
 global ROOT,access,chat_access
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root',type=Path,default=ROOT)
 parser.add_argument('--port',type=int,default=18084)
 parser.add_argument('--readiness-ack',metavar='CORRELATION_ID')
 parser.add_argument('--material',type=Path)
 args=parser.parse_args()
 ROOT=args.root.resolve();access=Access(ROOT/'access.db');chat_access=ChatAccess(access)
 if args.readiness_ack is not None:
  from scripts.read_readiness_ack import inspect
  if args.material is None:parser.error('--material required for ACK readback')
  try:print(json.dumps(inspect(ROOT/'access.db',args.material,args.readiness_ack)))
  except Exception:print(json.dumps(dict(version=1,status='UNKNOWN',reason='READBACK_UNAVAILABLE')));raise SystemExit(1) from None
  return
 from control.friends.diagnostics import start_retention
 retention=start_retention(ROOT/'diagnostics.sqlite')
 try:ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
 finally:retention.set()

if __name__=='__main__':main()
