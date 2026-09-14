"""Two synthetic Linux peers; tests run on a disposable emulator only."""
import json,os,subprocess,threading,queue,sys,traceback
from pathlib import Path
assert os.environ.get('GITHUB_ACTIONS')=='true'
r=Path(__file__).resolve().parents[2];processes=[]
sys.path.insert(0,str(r/'pilot/android-tcp'))
from fixture import peers
try:
 for awg,port in [(False,51820),(True,51821)]:
  params='jc=3\njmin=40\njmax=80\ns1=16\ns2=16\ns3=16\ns4=16\nh1=1\nh2=2\nh3=3\nh4=4\nheader_protection_key=0303030303030303030303030303030303030303030303030303030303030303\ncontent_padding_addition=0-32\nrandom_trailers=true\ndisable_cookies=false\ni1=<b 0x11223344><r 16>\n' if awg else ''
  address='10.78.0.4/32\nallowed_ip=fd78:92::4/128' if awg else '10.77.0.4/32\nallowed_ip=fd77:92::4/128'
  config='private_key='+'02'*32+'\nlisten_port='+str(port)+'\n'+params+'public_key=a4e09292b651c278b9772c569f5fa9bb13d906b46ab68c9df9dc2b4409f8a209\nallowed_ip='+address+'\n\n'
  peer=subprocess.Popen([str(r/'clients/android/awg-generated'/('peer-fixture' if awg else 'wg-peer-fixture'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,env=os.environ|{"FC_PEER_DROP_FILE":str(r/("android-auto-awg.drop" if awg else "android-auto-wg.drop"))});processes.append(peer)
  peer.stdin.write(json.dumps({'config':config}));peer.stdin.close();q=queue.Queue();threading.Thread(target=lambda:q.put(peer.stdout.readline().strip()),daemon=True).start();assert q.get(timeout=20)=='ready'
 with peers(r) as counts,(r/'android-awg-runtime.log').open('w') as log:
  result=subprocess.run(['gradle','--no-daemon',':app:connectedDebugAndroidTest','-Pandroid.testInstrumentationRunnerArguments.fc_disposable=true'],cwd=r/'clients/android',stdout=log,stderr=subprocess.STDOUT)
 print((r/'android-awg-runtime.log').read_text(),flush=True)
 result.check_returncode()
 from storage_restart import check as storage_restart
 storage_restart(r)
 assert counts["http"]>=24 and counts["dns"]>=4
except BaseException:
 with (r/"android-tcp-runner.log").open("w") as log:traceback.print_exc(file=log)
 raise
finally:
 with (r/'android-awg-crash.log').open('w') as log:
  subprocess.run(['adb','logcat','-d','-b','crash'],stdout=log,stderr=subprocess.STDOUT,timeout=20)
 with (r/'android-awg-app.log').open('w') as log:
  subprocess.run(['adb','logcat','-d'],stdout=log,stderr=subprocess.STDOUT,timeout=20)
 for peer in processes:
  if peer.poll() is None:peer.kill();peer.wait(timeout=10)
