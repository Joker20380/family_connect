"""Send a prepared notice through the administrator API, with safe retries.

The JSON request contains a stable id, kind, title, body, platforms and days.
The administrator token is read from a private file and never printed.
"""
import argparse
import json
from pathlib import Path
import urllib.request
import urllib.error
from messenger.service_events import validate_feed
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request-file',required=True)
    parser.add_argument('--token-file',required=True)
    parser.add_argument('--send',action='store_true',help='Without this flag, validate and preview only')
    args=parser.parse_args();value=json.loads(Path(args.request_file).read_text())
    if set(value)!={'id','kind','title','body','platforms','days'} or type(value['days']) is not int or not 1<=value['days']<=365:raise ValueError('Invalid request')
    now=int(time.time());validate_feed(dict(version=1,events=[dict(id=value['id'],kind=value['kind'],title=value['title'],body=value['body'],platforms=value['platforms'],author='Administrator',created=now,expires=now+value['days']*86400)]))
    if not args.send:
        print(json.dumps(value,ensure_ascii=False,indent=2));print('Preview only; nothing sent.');return
    token=Path(args.token_file).read_text().strip()
    request=urllib.request.Request('https://185.251.89.19:8443/friends/notices/publish',data=json.dumps(value,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},method='POST')
    # urllib must not forward administrator credentials through a redirect.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    try:
        with urllib.request.build_opener(NoRedirect).open(request,timeout=25) as response:reply=json.load(response)
    except urllib.error.HTTPError as error:raise SystemExit('Publication failed: HTTP '+str(error.code)) from None
    except urllib.error.URLError:raise SystemExit('Service unavailable; retry the same request file.') from None
    if reply!={'id':value['id'],'status':'published'}:raise SystemExit('Unexpected service reply')
    print('Published notice:',reply['id'])


if __name__=='__main__':main()
