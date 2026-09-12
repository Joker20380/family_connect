"""Two synthetic Linux peers; tests run on a disposable emulator only."""
import json,os,subprocess,threading,queue,sys,traceback
from pathlib import Path
assert os.environ.get('GITHUB_ACTIONS')=='true'
r=Path(__file__).resolve().parents[2];processes=[]
sys.path.insert(0,str(r/'pilot/android-tcp'))
from fixture import peers
try:
 for awg,port in [(False,51820),(True,51821)]:
  params='jc=3\njmin=40\njmax=80\ns1=17\ns2=29\ns3=3\ns4=9\nh1=1001-1010\nh2=2001-2010\nh3=3001-3010\nh4=4001-4010\ni1=<b 0x11223344><r 16>\n' if awg else ''
  address='10.78.0.4/32\nallowed_ip=fd78:92::4/128' if awg else '10.77.0.4/32\nallowed_ip=fd77:92::4/128'
  config='private_key='+'02'*32+'\nlisten_port='+str(port)+'\n'+params+'public_key=a4e09292b651c278b9772c569f5fa9bb13d906b46ab68c9df9dc2b4409f8a209\nallowed_ip='+address+'\n\n'
  peer=subprocess.Popen([str(r/'clients/android/awg-generated'/('peer-fixture' if awg else 'wg-peer-fixture'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True);processes.append(peer)
  peer.stdin.write(json.dumps({'config':config}));peer.stdin.close();q=queue.Queue();threading.Thread(target=lambda:q.put(peer.stdout.readline().strip()),daemon=True).start();assert q.get(timeout=20)=='ready'
 with peers(r) as counts,(r/'android-awg-runtime.log').open('w') as log:
  result=subprocess.run(['gradle','--no-daemon',':app:connectedDebugAndroidTest'],cwd=r/'clients/android',stdout=log,stderr=subprocess.STDOUT)
 print((r/'android-awg-runtime.log').read_text(),flush=True)
 result.check_returncode()
 assert counts["http"]>=18 and counts["dns"]>=3
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
