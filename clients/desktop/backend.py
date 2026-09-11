import ctypes
import json
import stat
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid
from profile_config import validate, parse, parse_tcp, AWG_FIELDS, MAX_PROFILE

def read_profile(path, *, allow_awg=False):
    with Path(path).open("rb") as source:
        return validate(source.read(MAX_PROFILE+1).decode("utf-8-sig"),allow_awg=allow_awg)


PREFIX='fc-app-'
class BackendError(Exception): pass
class AuthorizationError(BackendError): pass


def run(*args,timeout=30):
    result=subprocess.run(args,capture_output=True,text=True,timeout=timeout,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0) if sys.platform=='win32' else 0)
    if result.returncode:
        raise BackendError('System VPN operation failed: '+Path(args[0]).name+'; exit='+str(result.returncode))
    return result.stdout.strip()


HEALTH_TARGETS=(('https://1.1.1.1/cdn-cgi/trace','trace'),('https://api.ipify.org','plain'))


def probe_interface(interface, expected):
    import ipaddress
    if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,15}',interface):raise BackendError('Invalid VPN interface')
    expected=str(ipaddress.ip_address(expected))
    for url,kind in HEALTH_TARGETS:
        try:
            raw=run('/usr/bin/curl','--disable','--noproxy','*','--interface',interface,'--fail','--silent',
                '--connect-timeout','3','--max-time','5','--max-filesize','4096',url,timeout=7)
            actual=dict(line.split('=',1) for line in raw.splitlines() if '=' in line).get('ip') if kind=='trace' else raw.strip()
            if actual==expected:return
        except (BackendError,subprocess.TimeoutExpired):pass
    raise BackendError('VPN internet checks failed')


class RecoveryPolicy:
    """UI-thread policy; health workers never change connection intent or routing."""
    interval=15
    max_attempts=3
    def __init__(self,clock=time.monotonic):
        self.clock=clock;self.stop()
    def stop(self):
        self.identity=None;self.failures=0;self.attempts=0;self.next_check=0
        self.good_since=None;self.exhausted=False
    def arm(self,identity):
        self.stop();self.identity=identity;self.next_check=self.clock()+self.interval
    def due(self,identity):
        return self.identity is not None and self.identity==identity and not self.exhausted and self.clock()>=self.next_check
    def observe(self,healthy,*,allow_recovery=True):
        if self.identity is None or self.exhausted:return False
        now=self.clock();self.next_check=now+self.interval
        if healthy:
            self.failures=0
            if self.good_since is None:self.good_since=now
            if now-self.good_since>=60:self.attempts=0
            return False
        self.good_since=None;self.failures+=1
        if self.failures<2 or not allow_recovery:return False
        if self.attempts>=self.max_attempts:self.exhausted=True;return False
        self.attempts+=1;return True
    def recovered(self,success):
        self.good_since=None
        if success:self.failures=0
        else:self.failures=2
        self.exhausted=not success and self.attempts>=self.max_attempts
        self.next_check=self.clock()+min(60,15*2**max(0,self.attempts-1))


class Linux:
    awg_root=Path('/etc/family-connect/awg')
    awg_helper='/usr/local/lib/family-connect-awg/helper'
    def _awg_records(self):
        return self._records(self.awg_root,'fcawg')
    def _records(self,root,prefix):
        if not root.exists(): return {}
        info=root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:
            raise BackendError('Unsafe AWG installation')
        records={}
        for path in root.glob(prefix+'*.json'):
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            try:
                info=os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022 or info.st_nlink!=1:
                    raise BackendError('Unsafe AWG metadata')
                record=json.loads(os.read(fd,4097))
            finally:os.close(fd)
            if record['owner']!=os.getuid():continue
            if not re.fullmatch(prefix+r'[0-9a-f]{8}',record['id']) or path.stem!=record['id']:
                raise BackendError('Invalid AWG metadata')
            records[record['id']]=record
        return records
    def _awg(self,action,ident=None,data=None):
        args=['pkexec',self.awg_helper,action]+([ident] if ident else [])
        try:
            p=subprocess.run(args,input=data,capture_output=True,text=True,timeout=120)
        except subprocess.TimeoutExpired:
            raise BackendError('AWG authorization or operation timed out') from None
        if p.returncode in (126,127):raise AuthorizationError('AmneziaWG authorization cancelled or unavailable')
        if p.returncode:raise BackendError('AmneziaWG operation failed')
        return p.stdout.strip()
    def _fallback(self,ident):
        matches=[key for key,value in self._awg_records().items() if value.get('primary')==ident]
        if len(matches)>1:raise BackendError('Ambiguous fallback configuration')
        return matches[0] if matches else None
    def _nm_active(self,ident):
        return ident in run('nmcli','-t','-f','UUID','connection','show','--active',timeout=3).splitlines()
    def _probe(self,ident,expected):
        interface=run('nmcli','-g','GENERAL.DEVICES','connection','show',ident,timeout=3)
        if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,15}',interface): raise BackendError('Missing VPN interface')
        probe_interface(interface,expected)
    def supports_recovery(self,ident):
        return ident in self._awg_records() or self._fallback(ident) is not None
    def healthy(self,ident):
        records=self._awg_records();fallback=self._fallback(ident)
        awg=ident if ident in records else fallback
        if not awg:return self.active(ident)
        primary=records.get(ident,{}).get('primary') or ident
        try:
            if Path('/sys/class/net',awg).exists():probe_interface(awg,records[awg]['endpoint'])
            elif self._nm_active(primary):self._probe(primary,records[awg]['endpoint'])
            else:return False
            return True
        except (BackendError,subprocess.TimeoutExpired):return False
    def recover(self,ident):
        # Called only after UI intent/revision checks; serialized with user operations.
        # A failed AWG may reconnect to a working original WG, then fall back again.
        records=self._awg_records()
        primary=records.get(ident,{}).get('primary') or ident
        fallback=self._fallback(primary)
        failed_wg=bool(fallback and not Path('/sys/class/net',fallback).exists() and self._nm_active(primary))
        self.disconnect(primary)
        if failed_wg:self._awg('up',fallback)
        else:self.connect(primary)
        if not self.healthy(primary):raise BackendError('Connection recovery failed')
    def profiles(self):
        result=[]
        for line in run('nmcli','-t','--escape','no','-f','UUID,NAME,TYPE','connection','show').splitlines():
            parts=line.split(':')
            if len(parts)==3 and parts[2]=='wireguard' and (parts[1].startswith(PREFIX) or parts[1]=='fc-ru-linux'):
                result.append((parts[0],parts[1]))
        result.extend((ident,'AmneziaWG · '+ident) for ident in self._awg_records())
        return result
    def active(self,ident):
        records=self._awg_records()
        if ident in records:
            primary=records[ident].get('primary')
            return Path('/sys/class/net',ident).exists() or bool(primary and self._nm_active(primary))
        fallback=self._fallback(ident)
        if fallback and Path('/sys/class/net',fallback).exists():return True
        return ident in run('nmcli','-t','-f','UUID','connection','show','--active',timeout=3).splitlines()
    def connect(self,ident):
        records=self._awg_records()
        if ident in records:
            primary=records[ident].get('primary')
            was_active=bool(primary and self._nm_active(primary))
            if was_active:run('nmcli','connection','down','uuid',primary)
            try:self._awg('up',ident)
            except Exception:
                if was_active:run('nmcli','connection','up','uuid',primary)
                raise
            return
        fallback=self._fallback(ident)
        if fallback and Path('/sys/class/net',fallback).exists():
            self._awg('up',fallback);return
        if not fallback:
            run('nmcli','connection','up','uuid',ident);return
        # Bounded connection-time failover. No routing changes during status polling.
        try:
            run('nmcli','connection','up','uuid',ident)
            for attempt in range(2):
                try:self._probe(ident,records[fallback]['endpoint']);return
                except BackendError:
                    if attempt:raise
                    time.sleep(1)
        except (BackendError,subprocess.TimeoutExpired):
            if self._nm_active(ident):run('nmcli','connection','down','uuid',ident)
            self._awg('up',fallback)
    def disconnect(self,ident):
        records=self._awg_records()
        if ident in records:
            self._awg('down',ident)
            primary=records[ident].get('primary')
            if primary and self._nm_active(primary):run('nmcli','connection','down','uuid',primary)
            return
        fallback=self._fallback(ident)
        if fallback and Path('/sys/class/net',fallback).exists():self._awg('down',fallback)
        if self._nm_active(ident):run('nmcli','connection','down','uuid',ident)
    def import_profile(self,path):
        data=read_profile(path,allow_awg=True)
        if set(parse(data,allow_awg=True)['Interface'])&AWG_FIELDS:
            return self._awg('import',data=data)
        name=PREFIX+uuid.uuid4().hex[:8]
        with tempfile.TemporaryDirectory(prefix='family-connect-') as folder:
            file=Path(folder)/(name+'.conf')
            fd=os.open(file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as out: out.write(data)
            answer=run('nmcli','connection','import','type','wireguard','file',str(file))
            match=re.search(r'\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b',answer,re.I)
            if not match: raise BackendError('Unable to identify imported connection')
            ident=match.group()
            try:
                run('nmcli','connection','modify',ident,'connection.autoconnect','no',
                    'ipv4.dns-priority','-50','ipv6.dns-priority','-50','ipv4.dns-search','~.')
            except Exception:
                run('nmcli','connection','delete','uuid',ident)
                raise
        return ident


class LinuxTCP(Linux):
    tcp_root=Path('/etc/family-connect/tcp')
    tcp_helper='/usr/local/lib/family-connect-tcp/helper'
    def _tcp_records(self):return self._records(self.tcp_root,'fctcp')
    def _tcp(self,action,ident=None,data=None):
        try:
            p=subprocess.run(['pkexec',self.tcp_helper,action]+([ident] if ident else []),
                input=data,capture_output=True,text=True,timeout=120)
        except subprocess.TimeoutExpired:raise BackendError('TCP operation timed out') from None
        if p.returncode in (126,127):raise AuthorizationError('TCP authorization cancelled or unavailable')
        if p.returncode:raise BackendError('TCP operation failed')
        return p.stdout.strip()
    def _chain(self,ident):
        awg=self._awg_records();tcp=self._tcp_records()
        primary={**awg,**tcp}.get(ident,{}).get('primary') or ident
        matches=[key for key,value in tcp.items() if key==primary or value.get('primary')==primary]
        if len(matches)>1:raise BackendError('Ambiguous TCP fallback')
        if not matches:return None
        end=matches[0]
        fallback=self._fallback(primary)
        expected=awg[fallback]['endpoint'] if fallback else tcp[end]['endpoint']
        chain=[] if primary==end else [('wg',primary,expected)]
        if fallback:chain.append(('awg',fallback,awg[fallback]['endpoint']))
        chain.append(('tcp',end,tcp[end]['endpoint']))
        return chain
    def _live(self,item):
        kind,ident,_=item
        return self._nm_active(ident) if kind=='wg' else Path('/sys/class/net',ident).exists()
    def _stop(self,item):
        kind,ident,_=item
        if kind=='wg':
            if self._nm_active(ident):run('nmcli','connection','down','uuid',ident)
        elif kind=='awg':self._awg('down',ident)
        else:self._tcp('down',ident)
    def _check(self,item):
        kind,ident,expected=item
        if kind=='wg':self._probe(ident,expected)
        else:probe_interface(ident,expected)
    def _attempt(self,chain):
        for index,item in enumerate(chain):
            kind,ident,_=item
            try:
                if kind=='wg':run('nmcli','connection','up','uuid',ident)
                elif kind=='awg':self._awg('up',ident)
                else:self._tcp('up',ident)
                self._check(item);return
            except AuthorizationError:raise
            except (BackendError,subprocess.TimeoutExpired):
                # A cleanup failure stops the chain; never stack conflicting routes.
                # No later transport will start: an inactive final TCP needs no
                # second authorization. Any residual root state remains guarded
                # by the helper on the next explicit start.
                if not (kind=='tcp' and index==len(chain)-1 and not self._live(item)):
                    self._stop(item)
                if index==len(chain)-1:raise BackendError('All VPN transports failed') from None
    def profiles(self):
        return super().profiles()+[(ident,'VLESS + REALITY · '+ident) for ident in self._tcp_records()]
    def supports_recovery(self,ident):return bool(self._chain(ident)) or super().supports_recovery(ident)
    def allows_automatic_recovery(self,ident):
        chain=self._chain(ident)
        return not (chain and len(chain)==1 and chain[0][0]=='tcp')
    def active(self,ident):
        chain=self._chain(ident)
        return any(self._live(item) for item in chain) if chain else super().active(ident)
    def healthy(self,ident):
        chain=self._chain(ident)
        if not chain:return super().healthy(ident)
        live=[item for item in chain if self._live(item)]
        if len(live)!=1:return False
        try:self._check(live[0]);return True
        except (BackendError,subprocess.TimeoutExpired):return False
    def disconnect(self,ident):
        chain=self._chain(ident)
        if not chain:return super().disconnect(ident)
        for item in reversed(chain):
            if self._live(item):self._stop(item)
    def connect(self,ident):
        chain=self._chain(ident)
        if not chain:return super().connect(ident)
        selected=next((item for item in chain if item[1]==ident),chain[0])
        if self.healthy(ident) and (selected==chain[0] or self._live(selected)):return
        self.disconnect(ident)
        start=next((i for i,item in enumerate(chain) if item[1]==ident),0)
        self._attempt(chain[start:])
    def recover(self,ident):
        chain=self._chain(ident)
        if not chain:return super().recover(ident)
        live=[i for i,item in enumerate(chain) if self._live(item)]
        start=(live[0]+1)%len(chain) if len(live)==1 else 0
        self.disconnect(ident)
        self._attempt(chain[start:]+chain[:start])
    def import_profile(self,path):
        with Path(path).open('rb') as source:raw=source.read(MAX_PROFILE+1).decode('utf-8-sig')
        if raw.lstrip().startswith('{'):
            return self._tcp('import',data=json.dumps(parse_tcp(raw)))
        return super().import_profile(path)


class Windows:
    def __init__(self):
        if not ctypes.windll.shell32.IsUserAnAdmin(): raise BackendError('Administrator rights required')
        script=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'verify-wireguard.ps1'
        try:
            answer=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script.read_text(encoding='utf-8')],capture_output=True,text=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except FileNotFoundError:
            raise BackendError('PowerShell unavailable') from None
        errors={20:'WireGuard not installed',21:'WireGuard signature verification failed'}
        if answer.returncode:
            raise BackendError(errors.get(answer.returncode,'WireGuard verification failed; exit='+str(answer.returncode)))
        self.exe=Path(answer.stdout.strip())
        if not self.exe.is_file(): raise BackendError('WireGuard not installed')
        self.directory=self.exe.parent/'Data'/'Configurations'
    def _state(self,name):
        from ctypes import wintypes as w
        class STATUS(ctypes.Structure):
            _fields_=[(n,w.DWORD) for n in ['type','state','controls','win32','specific','checkpoint','hint']]
        api=ctypes.WinDLL('advapi32',use_last_error=True)
        api.OpenSCManagerW.argtypes=[w.LPCWSTR,w.LPCWSTR,w.DWORD];api.OpenSCManagerW.restype=w.HANDLE
        api.OpenServiceW.argtypes=[w.HANDLE,w.LPCWSTR,w.DWORD];api.OpenServiceW.restype=w.HANDLE
        api.CloseServiceHandle.argtypes=[w.HANDLE]
        api.QueryServiceStatus.argtypes=[w.HANDLE,ctypes.POINTER(STATUS)]
        manager=api.OpenSCManagerW(None,None,1)
        if not manager: raise BackendError('Cannot access Windows services')
        try:
            service=api.OpenServiceW(manager,name,4)
            if not service:
                if ctypes.get_last_error()==1060:return 0
                raise BackendError('Cannot query VPN service')
            try:
                status=STATUS()
                if not api.QueryServiceStatus(service,ctypes.byref(status)): raise BackendError('Cannot query VPN service')
                return status.state
            finally:api.CloseServiceHandle(service)
        finally:api.CloseServiceHandle(manager)
    def profiles(self):
        return [(p.name.removesuffix('.conf.dpapi'),p.name.removesuffix('.conf.dpapi'))
                for p in self.directory.glob(PREFIX+'*.conf.dpapi')]
    def active(self,ident): return self._state('WireGuardTunnel$'+ident)==4
    def connect(self,ident):
        if not re.fullmatch(r'fc-app-[0-9a-f]{8}',ident): raise BackendError('Invalid profile identifier')
        service='WireGuardTunnel$'+ident
        if self._state(service): run('sc.exe','start',service)
        else: run(str(self.exe),'/installtunnelservice',str(self.directory/(ident+'.conf.dpapi')))
        run('sc.exe','config',service,'start=','demand')
    def disconnect(self,ident):run(str(self.exe),'/uninstalltunnelservice',ident)
    def import_profile(self,path):
        data=read_profile(path)
        if not self._state('WireGuardManager'): run(str(self.exe),'/installmanagerservice')
        elif self._state('WireGuardManager')!=4: run('sc.exe','start','WireGuardManager')
        for _ in range(30):
            if self.directory.is_dir(): break
            time.sleep(0.1)
        else: raise BackendError('WireGuard secure store unavailable')
        name=PREFIX+uuid.uuid4().hex[:8]
        plain=self.directory/(name+'.conf')
        # Official manager owns ACL and DPAPI conversion. No app-managed plaintext store.
        try:
            with plain.open('x',encoding='utf-8') as out:out.write(data)
            for _ in range(100):
                if not plain.exists() and (self.directory/(name+'.conf.dpapi')).exists():return name
                time.sleep(0.1)
            raise BackendError('WireGuard secure import timed out')
        finally:plain.unlink(missing_ok=True)


def backend():
    if sys.platform=='win32':return Windows()
    if sys.platform.startswith('linux'):return LinuxTCP()
    raise BackendError('Unsupported operating system')


TCP_UPDATER=Path('/usr/local/lib/family-connect-tcp-updater/broker')

def tcp_updater_available():
    try:
        for p in (TCP_UPDATER.parent,*TCP_UPDATER.parent.parents):
            info=p.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:return False
        info=TCP_UPDATER.lstat()
        return stat.S_ISREG(info.st_mode) and info.st_uid==0 and info.st_nlink==1 and not info.st_mode&0o022 and os.access(TCP_UPDATER,os.X_OK)
    except OSError:return False

def install_tcp_component():
    if not tcp_updater_available():raise BackendError('TCP system updater is not installed')
    try:
        result=subprocess.run(['pkexec',str(TCP_UPDATER),'install'],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=900)
    except subprocess.TimeoutExpired as error:raise BackendError('TCP installation timed out; check system state before retrying') from error
    if result.returncode in (126,127):raise AuthorizationError('TCP installation authorization cancelled or unavailable')
    if result.returncode:raise BackendError('TCP installation failed')
    return True
