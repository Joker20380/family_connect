"""Compile real old94 client, oldb9 server and new source; loopback-only matrix."""

import json
import os
import shutil
import subprocess
import sys
import time

from prepare import WORK, ROOT, FIXTURE, BASE, ANDROID, TOOLS, environment, digest


def main():
    os.umask(0o077)
    target=WORK/'compatibility'
    resume='--resume' in sys.argv
    if not resume:target.mkdir(mode=0o700,exist_ok=False)
    cases={"old-client":ANDROID/'android-source/carrier',"old-server":BASE/'gateway-source/carrier',"new":WORK/'carrier'}
    for name,original in cases.items():
        if resume:
            assert (target/(name+'.test')).is_file()
            continue
        source=target/name;shutil.copytree(original,source)
        content=(FIXTURE/'cross_process_test.go').read_text()
        if name.startswith('old'):
            content=content.replace('familysession.OpenMux(ctx,&profilePacketConnection{Conn:connection},raw,server,os.Getenv("MUX_PROFILE_ENABLE")=="1")','familysession.Open(ctx,&profilePacketConnection{Conn:connection},raw,server)')
        patch='*** Begin Patch\n*** Add File: '+str(source/'tcpforward/profile_cross_process_test.go')+'\n'+''.join('+'+line+'\n' for line in content.splitlines())+'*** End Patch\n'
        subprocess.run(['apply_patch',patch],check=True,stdout=subprocess.DEVNULL)
        with (target/(name+'-build.log')).open('x') as output:
            subprocess.run([TOOLS/'go/bin/go','test','-c','-race','-o',target/(name+'.test'),'./tcpforward'],cwd=source,env=environment(),stdout=output,stderr=subprocess.STDOUT,check=True)
        print('BUILT',name,flush=True)
    legacy='family-connect-5n3-test-v1';extended='family-connect-mux-credit128-v1';results=[]
    for name,client,server,enabled,expected in [('old-old','old-client','old-server','0',legacy),('old-new','old-client','new','1',legacy),('new-old','new','old-server','1',legacy),('new-new','new','new','1',extended),('forced-legacy','new','new','0',legacy)]:
        suffix='-retry' if resume else ''
        directory=target/(name+suffix);directory.mkdir(mode=0o700)
        env=environment();env.update(MUX_PROFILE_FIXTURE=str(directory),MUX_PROFILE_ROLE='credentials')
        args=['-test.run=^TestProfileCrossProcess$','-test.v','-test.timeout=30s']
        subprocess.run([target/'new.test',*args],env=env,check=True,stdout=subprocess.DEVNULL)
        env.update(MUX_PROFILE_EXPECT=expected,MUX_PROFILE_ENABLE=enabled,MUX_PROFILE_ROLE='server')
        with (directory/'server.log').open('x') as server_log,(directory/'client.log').open('x') as client_log:
            process=subprocess.Popen([target/(server+'.test'),*args],env=env,stdout=server_log,stderr=subprocess.STDOUT)
            try:
                deadline=time.monotonic()+10
                while not (directory/'ready.json').exists():
                    if process.poll() is not None or time.monotonic()>deadline:raise RuntimeError('server fixture not ready')
                    time.sleep(.05)
                env.update(MUX_PROFILE_ROLE='client',MUX_PROFILE_ENABLE='1')
                result=subprocess.run([target/(client+'.test'),*args],env=env,stdout=client_log,stderr=subprocess.STDOUT,timeout=35)
                status=process.wait(timeout=35)
                results.append(dict(case=name,client_exit=result.returncode,server_exit=status,profile=expected))
                (target/('results'+suffix+'.json')).write_text(json.dumps(results,indent=2))
                assert result.returncode==status==0
            finally:
                if process.poll() is None:process.terminate();process.wait(timeout=5)
        print('PASS',name,expected,flush=True)


if __name__=='__main__':main()
