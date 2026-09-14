"""Explicit operator steps on the authorized original gateway; never touches VPN services."""
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

IP = '185.251.89.19'
ROOT = Path('/opt/apps/family_connect/state-product-https')
NGINX = 'nginx@sha256:dc5069ad14f19660b141b21236140b91656bf89bbc3e2417c70ae650cd66104c'
CERTBOT = 'certbot/certbot@sha256:c23159d30afdd9c97960578aa4654f5901de6cae394958f894074dedd55e599d'
NAME = 'family-connect-product-https'


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def nginx(*args):
    return ['docker', 'run', '--rm', '--network', 'host', '--read-only',
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m', '--security-opt', 'no-new-privileges',
            '--memory', '64m', '--pids-limit', '32',
            '-v', str(ROOT/'config')+':/etc/fc:ro',
            '-v', str(ROOT/'certificates')+':/etc/letsencrypt:ro',
            '-v', str(ROOT/'webroot')+':/var/www/acme:ro',
            '--entrypoint', 'nginx', NGINX, '-c', '/etc/fc/nginx.conf', *args]


def certbot(*args, staging=False):
    state = ROOT/('staging' if staging else 'certificates')
    return ['docker', 'run', '--rm', '--network', 'host',
            '-v', str(state)+':/etc/letsencrypt',
            '-v', str(ROOT/'work')+':/var/lib/letsencrypt',
            '-v', str(ROOT/'logs')+':/var/log/letsencrypt',
            '-v', str(ROOT/'webroot')+':/var/www/acme', CERTBOT, *args]


def replace(path, text, mode=0o644):
    pending=path.with_suffix(path.suffix+'.new')
    pending.write_text(text);pending.chmod(mode);os.replace(pending,path)


def main():
    assert os.geteuid() == 0, 'Operator root required'
    addresses=json.loads(subprocess.check_output(['ip','-j','address'],text=True))
    assert any(a.get('local') == IP for iface in addresses for a in iface['addr_info']), 'Wrong gateway'
    step=sys.argv[1]
    if step in ('prepare','resume-prepare'):
        if step=='prepare':assert not ROOT.exists(), 'Existing HTTPS state must be inspected, never replaced'
        else:
            assert ROOT.is_dir() and not (ROOT/'certificates/live').exists(), 'Only pre-certificate preparation can resume'
            names=subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines()
            assert NAME not in names, 'Existing container requires inspection'
        with urllib.request.urlopen('http://127.0.0.1:18082/healthz',timeout=5) as response:
            assert json.load(response)['service']=='family-connect-product'
        # Refuse occupying any existing HTTP/HTTPS pilot listener.
        listeners=subprocess.check_output(['ss','-H','-lnt'],text=True)
        assert not any(line.split()[3].rsplit(':',1)[-1] in ('80','8443') for line in listeners.splitlines())
        ROOT.mkdir(mode=0o700,exist_ok=step=='resume-prepare')
        for name in ('config','webroot','certificates','staging','work','logs'):
            (ROOT/name).mkdir(mode=0o755 if name in ('config','webroot') else 0o700,exist_ok=step=='resume-prepare')
        template=Path(__file__).with_name('nginx.conf.template').read_text().replace('@IP@',IP)
        replace(ROOT/'config/nginx-final.conf',template)
        # Only HTTP challenge server until the certificate has passed issuance.
        http=template[:template.index('    server {\n        listen 8443 ssl;')]+'}\n'
        replace(ROOT/'config/nginx.conf',http)
        run(nginx('-t'))
        command=nginx('-g','daemon off;')
        command.remove('--rm');command[2:2]=['-d','--name',NAME,'--restart','unless-stopped']
        run(command,stdout=subprocess.DEVNULL)
        print('ACME-only listener prepared; product HTTPS still disabled')
    elif step in ('staging','issue'):
        staging=step=='staging'
        args=['certonly','--non-interactive','--agree-tos','--register-unsafely-without-email',
              '--webroot','--webroot-path','/var/www/acme','--preferred-profile','shortlived',
              '--ip-address',IP,'--cert-name','family-connect-product']
        if staging:args.append('--staging')
        # ACME logs remain server-private, including account metadata.
        with (ROOT/'logs'/('issue-'+step+'.log')).open('w') as log:
            run(certbot(*args,staging=staging),stdout=log,stderr=subprocess.STDOUT)
        print(step+' certificate issued')
    elif step == 'activate':
        assert (ROOT/'certificates/live/family-connect-product/fullchain.pem').exists()
        prior=(ROOT/'config/nginx.conf').read_text()
        replace(ROOT/'config/nginx.conf',(ROOT/'config/nginx-final.conf').read_text())
        try:run(nginx('-t'))
        except BaseException:
            replace(ROOT/'config/nginx.conf',prior);raise
        run(['docker','kill','--signal=HUP',NAME],stdout=subprocess.DEVNULL)
        print('HTTPS enabled on TCP8443; existing API and VPN processes retained')
    elif step in ('renew','renew-test'):
        args=['renew','--non-interactive']
        if step=='renew-test':args.append('--dry-run')
        with (ROOT/'logs'/(step+'.log')).open('w') as log:
            run(certbot(*args),stdout=log,stderr=subprocess.STDOUT)
        if step=='renew':
            run(nginx('-t'));run(['docker','kill','--signal=HUP',NAME],stdout=subprocess.DEVNULL)
        print(step+' passed')
    else:raise ValueError('Unknown explicit step')


if __name__ == '__main__':
    main()
