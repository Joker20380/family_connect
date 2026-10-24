"""Ordinary owner USB operations and exact existing next-session server policy."""
import argparse
import json
import re
import runpy
import sys
import subprocess
import time

from observe import ROOT,WORK,remote_observation
from scripts.owner_android_support import command,snapshot,save


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['connect','close'])
    parser.add_argument('label')
    parser.add_argument('--profile',choices=['P0','P1'])
    parser.add_argument('--preserve-profile',action='store_true')
    parser.add_argument('--verify-close',action='store_true')
    args=parser.parse_args();assert re.fullmatch('[a-z0-9-]+',args.label)
    before=snapshot('31ce63ba');save(WORK/(args.label+'-control-before.json'),before)
    began=time.time();record=dict(action=args.action,before_epoch=began,profile=args.profile)
    if args.action=='connect':
        assert args.profile and before['state']=='DISCONNECTED','NORMAL_DISCONNECT_REQUIRED'
        if not args.preserve_profile:
            sys.path.insert(0,str(ROOT/'tests/fixtures/speed_candidate'))
            module=runpy.run_path(str(ROOT/'tests/fixtures/speed_candidate/policy.py'))
            module['main'].__globals__['WORK']=WORK
            target=json.loads((WORK/'p0-observed-gateway.json').read_text())['operator']['speed-target']
            assert re.fullmatch('[0-9a-f]{32}',target)
            sys.argv=['policy.py',args.profile,target,args.label]
            module['main']()
            record['profile_receipt']=command('31ce63ba','profile',args.profile)
            assert record['profile_receipt']=='NEXT_SESSION_'+args.profile
        else:record['profile_receipt']='NO_PROFILE_WRITES_ORDINARY_CONNECT'
        record['command']=command('31ce63ba','connect')
        assert record['command']=='CONNECT_REQUESTED'
        for attempt in range(45):
            current=snapshot('31ce63ba')
            if current['state']=='CONNECTED' and current['restricted_readiness']=='READY':break
            time.sleep(2)
        else:raise RuntimeError('CONNECT_NOT_READY_WITHIN90S')
    else:
        tag=before['restricted_session'].get('session_tag');assert tag
        record['session_tag']=tag
        if args.verify_close:
            gateway_before=remote_observation(tag,12000)
            save(WORK/(args.label+'-gateway-before.json'),gateway_before)
            record['gateway_terminal_before_disconnect']=any(row['event']=='session_terminal' for row in gateway_before['records'])
        resources={}
        for kind,arguments in [('memory',['meminfo','com.familyconnect.app.friends']),('cpu',['cpuinfo'])]:
            result=subprocess.run(['adb','-s','31ce63ba','shell','dumpsys',*arguments],capture_output=True,text=True,timeout=12)
            resources[kind]=dict(exit=result.returncode,output=result.stdout[:262144],truncated=len(result.stdout)>262144)
        save(WORK/(args.label+'-android-resources.json'),dict(epoch=time.time(),resources=resources))
        record['disconnect_epoch']=time.time()
        record['command']=command('31ce63ba','disconnect')
        assert record['command']=='DISCONNECT_REQUESTED'
        for attempt in range(30):
            current=snapshot('31ce63ba')
            if current['state']=='DISCONNECTED':break
            time.sleep(2)
        else:raise RuntimeError('DISCONNECT_NOT_COMPLETE_WITHIN60S')
        record['android_disconnected_epoch']=time.time()
        cleanup=[event for event in current['events'] if event.get('session_tag')==tag and event.get('event') in ('cleanup_completed','cleanup_failed')]
        record['android_cleanup']=cleanup[-1] if cleanup else None
        for attempt in range(8):
            gateway=remote_observation(tag,12000)
            terminal=[row for row in gateway['records'] if row['event']=='session_terminal']
            if terminal:break
            time.sleep(3)
        save(WORK/(args.label+'-gateway-terminal.json'),gateway)
        record['gateway_terminal_observed']=bool(terminal)
        assert terminal,'MISSING_GATEWAY_TERMINAL'
        record['gateway_terminal']=terminal[-1]
        assert cleanup and cleanup[-1]['event']=='cleanup_completed','NATIVE_CLEANUP_NOT_CONFIRMED'
    record['completed_epoch']=time.time();record['seconds']=time.time()-began
    save(WORK/(args.label+'-control-after.json'),current)
    save(WORK/(args.label+'-control-receipt.json'),record)
    print(json.dumps(dict(action=args.action,state=current['state'],seconds=record['seconds'],session=current['restricted_session'].get('session_tag'))))


if __name__=='__main__':main()
