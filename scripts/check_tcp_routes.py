"""Destructive only inside the disposable --network none test container."""
import importlib.util,json,sys,subprocess,argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--helper',default='/fix/tcp-helper.py')
parser.add_argument('--desktop',default='/desktop')
args=parser.parse_args()
sys.path.insert(0,args.desktop)
spec=importlib.util.spec_from_file_location('helper',args.helper)
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
real_command=h.command
def isolated_command(*args,**kwargs):
    # No resolved/DBus in this network-none fixture. Only DNS teardown is stubbed;
    # every iproute2 operation and route assertion runs against the real kernel.
    if args[0]=='resolvectl':
        assert args==('resolvectl','revert','fctcp12345678')
        return subprocess.CompletedProcess(args,0,'','')
    return real_command(*args,**kwargs)
h.command=isolated_command
GATEWAY='203.0.113.19';IDENT='fctcp12345678'
def cmd(*args):return h.command(*args).stdout
def route(address,mark=None):
    args=['ip','-j','route','get',address]
    if mark is not None:args+=['mark',mark]
    return json.loads(cmd(*args))[0]['dev']
def snapshot():
    return {family:json.loads(cmd('ip','-j',family,'rule','show')) for family in ['-4','-6']}
def main():
    assert not Path('/sys/class/net/wlp0s20f3').exists(),'Host namespace is forbidden'
    assert set(p.name for p in Path('/sys/class/net').iterdir())=={'lo'},'Requires --network none'
    h.RUN=Path('/run/fc-route-test');h.RUN.mkdir(mode=0o700)
    for name in ['uplink','lan','dock',IDENT]:
        cmd('ip','link','add',name,'type','dummy');cmd('ip','link','set',name,'up')
    for name,addresses in [('uplink',['192.0.2.2/24','2001:db8:1::2/64']),('lan',['10.20.0.1/24','fd20::1/64']),('dock',['172.20.0.1/16']), (IDENT,['10.79.0.2/32','fd79:92::2/128'])]:
        for address in addresses:cmd('ip','address','add',address,'dev',name,*(['nodad'] if ':' in address else []))
    cmd('ip','route','add','default','via','192.0.2.1','dev','uplink')
    cmd('ip','-6','route','add','default','via','2001:db8:1::1','dev','uplink')
    before=snapshot();h.check_routing_available()
    h.write(h.RUN/'active',json.dumps(dict(id=IDENT,endpoint=GATEWAY)),0o600)
    h.install_routes(IDENT,GATEWAY)
    expected={'1.1.1.1':IDENT,'2606:4700:4700::1111':IDENT,'10.20.0.42':'lan',
        'fd20::42':'lan','172.20.0.42':'dock',GATEWAY:'uplink','127.0.0.1':'lo'}
    for address,device in expected.items():assert route(address)==device,(address,route(address))
    assert route('1.1.1.1',h.TABLE)=='uplink'
    assert route(GATEWAY,h.TABLE)=='uplink'
    # Kernel control packets without SO_MARK still bypass TUN. Uplink loss must not loop.
    cmd('ip','route','del','default','via','192.0.2.1','dev','uplink')
    assert h.command('ip','route','get',GATEWAY,check=False).returncode!=0
    assert route('1.1.1.1')==IDENT
    cmd('ip','route','add','default','via','192.0.2.1','dev','uplink')
    # Wrong owner cannot delete a running profile's routes.
    installed=snapshot();h.cleanup('fctcp87654321');assert snapshot()==installed
    h.cleanup(IDENT);assert snapshot()==before;h.cleanup(IDENT)
    # Reserved priority collision is rejected without touching the foreign rule.
    cmd('ip','rule','add','priority','10629','to','198.51.100.7/32','lookup','main')
    collision=snapshot()
    try:h.check_routing_available()
    except ValueError:pass
    else:raise AssertionError('Priority collision was accepted')
    h.cleanup(IDENT);assert snapshot()==collision
    cmd('ip','rule','del','priority','10629','to','198.51.100.7/32','lookup','main')
    # A failed delete must keep the marker so service cleanup can be retried.
    h.write(h.RUN/'active',json.dumps(dict(id=IDENT,endpoint=GATEWAY)),0o600)
    h.install_routes(IDENT,GATEWAY)
    def fail_delete(*args,**kwargs):
        if args[:5]==('ip','-4','rule','del','priority') and '10630' in args:
            return subprocess.CompletedProcess(args,1,'','simulated failure')
        return isolated_command(*args,**kwargs)
    h.command=fail_delete
    try:h.cleanup(IDENT)
    except RuntimeError:pass
    else:raise AssertionError('Cleanup failure was ignored')
    assert (h.RUN/'active').exists()
    h.command=isolated_command;h.cleanup(IDENT);assert snapshot()==before
    # Abort halfway through setup; ExecStopPost cleanup must remove the partial state.
    h.write(h.RUN/'active',json.dumps(dict(id=IDENT,endpoint=GATEWAY)),0o600)
    cmd('ip','route','add','default','dev',IDENT,'table',h.TABLE)
    family,rule=h.routing_rules(GATEWAY)[0];cmd('ip',family,'rule','add',*rule)
    h.cleanup(IDENT);assert snapshot()==before
    # Legacy marker from the installed old helper is still cleanable.
    h.write(h.RUN/'active',IDENT,0o600)
    for family in ['-4','-6']:
        cmd('ip',family,'route','add','default','dev',IDENT,'table',h.TABLE)
        cmd('ip',family,'rule','add','priority',h.PRIORITY,'not','fwmark',h.TABLE,'lookup',h.TABLE)
    h.cleanup(IDENT);assert snapshot()==before
    print(json.dumps(dict(passed=True,ipv4_ipv6_public_tunnel=True,lan_docker_routes_preserved=True,
        gateway_marked_unmarked_bypass=True,gateway_loss_no_loop=True,foreign_rules_preserved=True,
        partial_setup_cleanup=True,legacy_cleanup=True,cleanup_idempotent=True,failed_cleanup_retry=True)))
if __name__=='__main__':main()
