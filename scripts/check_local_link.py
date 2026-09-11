import concurrent.futures,json,re,subprocess,time,statistics
from pathlib import Path
OUT=Path('/tmp/fc-local-link-result.json')
def run(args,timeout=8):return subprocess.run(args,capture_output=True,text=True,timeout=timeout)
route=json.loads(run(['ip','-j','route','get','185.251.89.19']).stdout)[0]
dev=route['dev'];gateway=route.get('gateway')
if not gateway or not (Path('/sys/class/net')/dev/'wireless').exists():raise RuntimeError('Expected Wi-Fi gateway unavailable')
def wifi():
 p=run(['iw','dev',dev,'station','dump']);d={'available':p.returncode==0}
 for label in ('signal','signal avg','tx retries','tx failed','tx packets','rx packets','tx bitrate','rx bitrate'):
  m=re.search(r'^\s*'+re.escape(label)+r':\s*(-?[\d.]+)',p.stdout,re.M)
  if m:d[label]=float(m.group(1))
 for label in ('tx_errors','rx_errors','tx_dropped','rx_dropped'):
  d[label]=int((Path('/sys/class/net')/dev/'statistics'/label).read_text())
 return d
def probe(kind):
 start=time.monotonic()
 if kind=='https':
  p=run(['curl','--disable','--noproxy','*','--interface',dev,'-sS','--fail','--connect-timeout','3','--max-time','5','-o','/dev/null','-w','%{http_code} %{time_connect} %{time_appconnect} %{time_starttransfer} %{time_total}','https://1.1.1.1/cdn-cgi/trace'])
  return {'kind':kind,'ok':p.returncode==0 and p.stdout.startswith('200 '),'code':p.returncode,'timing':p.stdout.split(),'error':p.stderr.strip()[:200]}
 target={'gateway':gateway,'vps':'185.251.89.19','control':'1.1.1.1'}[kind]
 p=run(['ping','-n','-I',dev,'-c','1','-W','1',target],timeout=3)
 m=re.search(r'time[=<]([\d.]+)',p.stdout)
 return {'kind':kind,'ok':p.returncode==0,'ms':float(m.group(1)) if m else None}
rows=[];start=time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for i in range(30):
  stamp=time.time()-start;before=wifi();results=list(pool.map(probe,['gateway','vps','control','https']));after=wifi()
  rows.append({'t':round(stamp,3),'before':before,'after':after,'results':results})
  if any(not x['ok'] or (x.get('ms') or 0)>100 for x in results):print(json.dumps({'round':i+1,'results':results}),flush=True)
  time.sleep(1)
summary={}
for kind in ('gateway','vps','control','https'):
 v=[x for r in rows for x in r['results'] if x['kind']==kind];times=[x['ms'] for x in v if x.get('ms') is not None]
 summary[kind]={'passed':sum(x['ok'] for x in v),'total':len(v)}
 if times:summary[kind].update(median_ms=statistics.median(times),max_ms=max(times))
summary['wifi_available']=all(r['before']['available'] and r['after']['available'] for r in rows)
summary['seconds']=round(time.time()-start,3)
OUT.write_text(json.dumps({'summary':summary,'rows':rows},indent=2)+'\n');OUT.chmod(0o600)
print(json.dumps(summary),flush=True)
