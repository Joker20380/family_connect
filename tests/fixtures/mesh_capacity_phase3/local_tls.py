"""Observation-only local copy, never the live A/B binary."""
import json
import shutil
import subprocess
from prepare import SOURCE, WORK, FIX, TOOLS, environment, patch_file, digest

target=WORK/'local-tls-source'
if not target.exists():
    shutil.copytree(SOURCE,target)
    path=target/'familysession/session.go'
    text=path.read_text()
    old='count, err := peer.Read(buffer)\n\t\t\tif err != nil'
    assert text.count(old)==1
    text=text.replace(old,'count, err := peer.Read(buffer)\nif count>0 {labTLSObserve("bridge_read",connection,buffer[:count])}\n\t\t\tif err != nil')
    old='if _, err := session.connection.Write(message); err != nil {'
    assert text.count(old)==1
    text=text.replace(old,'labTLSObserve("app_plaintext",session.stream,message)\n'+old)
    patch_file(path,text)
patch_file(target/'familysession/lab_short_test.go',(FIX/'short_data_test.go').read_text())
patch_file(target/'familysession/lab_observe.go','package familysession\nvar labTLSObserve = func(string,*stream,[]byte){}\n')
attempt=len(list(WORK.glob('short-data-*.log')))+1
with (WORK/f'short-data-{attempt}.log').open('x') as log:
    subprocess.run([TOOLS/'go/bin/go','test','-p=1','-race','-tags=fc_perf_diagnostic','-v','-run','TestLabTLSShortOrigin','-count=1','-timeout=45s','./familysession'],cwd=target,env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
patch_file(WORK/'short-data-inventory.json',json.dumps({str(path.relative_to(target)):digest(path) for path in target.rglob('*') if path.is_file()},indent=2))
