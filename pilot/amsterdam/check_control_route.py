"""Root-only broker lifecycle checks, entirely inside a disposable net namespace."""
import importlib.util
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile


def main():
    assert os.geteuid() == 0
    if sys.argv[1:] != ['--isolated']:
        subprocess.run(['unshare','--net','--',sys.executable,str(Path(__file__).resolve()),'--isolated'],check=True)
        return
    helper=Path(__file__).resolve().parents[2]/'clients/linux/control-route-helper.py'
    def ip(*args,check=True):return subprocess.run(['/usr/sbin/ip',*args],text=True,capture_output=True,check=check)
    def rules():return json.loads(ip('-j','-4','rule').stdout)
    before=rules()
    pin=dict(schema=1,provider='a'*64,uid=1000,address='186.246.45.246',port=4242,priority=10590)
    with tempfile.TemporaryDirectory(prefix='fc-route-root-') as folder:
        root=Path(folder);config=root/'config';config.write_text(json.dumps(pin));config.chmod(0o600)
        wrapper=root/'wrapper.py';wrapper.write_text(f"import importlib.util\nfrom pathlib import Path\ns=importlib.util.spec_from_file_location('h',{str(helper)!r});h=importlib.util.module_from_spec(s);s.loader.exec_module(h)\nh.CONFIG=Path({str(config)!r});h.RUN=Path({str(root/'run')!r});h.main()\n")
        def start():
            return subprocess.Popen([sys.executable,'-I',str(wrapper),'a'*64],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'PKEXEC_UID':'1000'})
        def ready(p):
            with selectors.DefaultSelector() as selector:
                selector.register(p.stdout,selectors.EVENT_READ)
                assert selector.select(5),'broker readiness timeout'
                assert p.stdout.readline()==b'READY\n',p.stderr.read().decode()
        def close(p):
            p.stdin.close();assert p.wait(timeout=5)==0,p.stderr.read().decode()
        p=start();ready(p)
        duplicate=start();assert duplicate.wait(timeout=5)!=0
        for name,address in [('uplink0','192.0.2.1/24'),('uplink1','198.51.100.1/24')]:
            ip('link','add',name,'type','dummy');ip('addr','add',address,'dev',name);ip('link','set',name,'up')
        def get():return ip('-j','route','get',pin['address'],'uid','1000','ipproto','tcp','dport','4242',check=False)
        ip('route','add','default','dev','uplink0');assert json.loads(get().stdout)[0]['dev']=='uplink0'
        ip('route','replace','default','dev','uplink1');assert json.loads(get().stdout)[0]['dev']=='uplink1'
        ip('route','del','default');assert get().returncode!=0
        close(p);assert rules()==before
        p=start();ready(p);p.kill();p.wait(timeout=5)
        assert (root/'run/intent.json').exists() and rules()!=before
        p=start();ready(p);close(p);assert rules()==before and not (root/'run/intent.json').exists()
        ip('-4','rule','add','priority','10590','lookup','main');foreign=rules()
        p=start();assert p.wait(timeout=5)!=0;assert rules()==foreign
        ip('-4','rule','del','priority','10590','lookup','main');assert rules()==before
    print(json.dumps(dict(passed=True,checks=['pipe EOF cleanup','exclusive broker','main route replacement','no-main-route refusal','SIGKILL durable recovery','foreign priority preserved','original rules restored'])))

if __name__=='__main__':main()
