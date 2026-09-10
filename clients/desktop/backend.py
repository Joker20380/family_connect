import ctypes
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid
from profile_config import validate, MAX_PROFILE

def read_profile(path):
    with Path(path).open("rb") as source:
        return validate(source.read(MAX_PROFILE+1).decode("utf-8-sig"))


PREFIX='fc-app-'
class BackendError(Exception): pass


def run(*args,timeout=30):
    result=subprocess.run(args,capture_output=True,text=True,timeout=timeout,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0) if sys.platform=='win32' else 0)
    if result.returncode:
        raise BackendError('System VPN operation failed: '+Path(args[0]).name+'; exit='+str(result.returncode))
    return result.stdout.strip()


class Linux:
    def profiles(self):
        result=[]
        for line in run('nmcli','-t','--escape','no','-f','UUID,NAME,TYPE','connection','show').splitlines():
            parts=line.split(':')
            if len(parts)==3 and parts[2]=='wireguard' and (parts[1].startswith(PREFIX) or parts[1]=='fc-ru-linux'):
                result.append((parts[0],parts[1]))
        return result
    def active(self,ident):
        return ident in run('nmcli','-t','-f','UUID','connection','show','--active',timeout=3).splitlines()
    def connect(self,ident): run('nmcli','connection','up','uuid',ident)
    def disconnect(self,ident): run('nmcli','connection','down','uuid',ident)
    def import_profile(self,path):
        data=read_profile(path)
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
    if sys.platform.startswith('linux'):return Linux()
    raise BackendError('Unsupported operating system')
