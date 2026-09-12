"""Build one pinned WG-compatible/AWG JNI runtime. No root tools or public UAPI."""
import hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'clients/android/awg-generated'
ANDROID='5420011143f9dd42831cc95fcdb0d6ac9bde868f';ENGINE='1cc94272ca8e9e223a5fe76382f5880f09d3c12d'
def run(*args,**kw):subprocess.run(args,check=True,**kw)
def checkout(url,rev,path):
 run('git','clone','--quiet',url,str(path));run('git','-C',str(path),'checkout','--quiet','--detach',rev)
 assert subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()==rev
assert subprocess.check_output(['go','version'],text=True).strip()=='go version go1.26.1 linux/amd64'
assert not OUT.exists(),'Use a clean generated output directory'
OUT.mkdir(parents=True)
with tempfile.TemporaryDirectory(prefix='fc-android-awg-') as temporary:
 temp=Path(temporary);android=temp/'android';engine=temp/'engine'
 checkout('https://github.com/amnezia-vpn/amneziawg-android',ANDROID,android)
 checkout('https://github.com/amnezia-vpn/amneziawg-go',ENGINE,engine)
 xray=temp/'xray'
 checkout('https://github.com/XTLS/Xray-core','d2758a023cd7f4174a5a5fa4ff66e487d4342ba0',xray)
 tun=xray/'proxy/tun/tun_android.go';code=tun.read_text().replace('\terr = unix.SetNonblock(fd, true)','\tif err != nil || fd < 3 { return nil, errors.New("invalid Android TUN descriptor") }\n\terr = unix.SetNonblock(fd, true)').replace('\t\t_ = unix.Close(fd)\n','');tun.write_text(code)
 source=android/'tunnel/src/main/java';dest=OUT/'java'
 for file in source.rglob('*.java'):
  if file.name in ('AwgQuickBackend.java','RootShell.java','ToolsInstaller.java'):continue
  target=dest/file.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(file.read_bytes())
 backend=dest/'org/amnezia/awg/backend/GoBackend.java';text=backend.read_text().replace('"wg-go"','"fc-awg"')
 text=text.replace('            currentTunnel = tunnel;\n            currentConfig = config;', '''            int socket4=awgGetSocketV4(currentTunnelHandle),socket6=awgGetSocketV6(currentTunnelHandle);
            if(socket4<0||!service.protect(socket4)||(socket6>=0&&!service.protect(socket6))){
                awgTurnOff(currentTunnelHandle);currentTunnelHandle=-1;
                throw new BackendException(Reason.UNABLE_TO_START_VPN);
            }
            currentTunnel = tunnel;
            currentConfig = config;''')
 text=text.replace('            service.protect(awgGetSocketV4(currentTunnelHandle));','').replace('            service.protect(awgGetSocketV6(currentTunnelHandle));','')
 # Await Android service destruction before another backend can reuse its ready future.
 text=text.replace('                vpnService.get(0, TimeUnit.NANOSECONDS).stopSelf();', '                final VpnService stoppingService=vpnService.get(0, TimeUnit.NANOSECONDS);\n                stoppingService.stopSelf();\n                try { stoppingService.destroyed.get(3, TimeUnit.SECONDS); }\n                catch (final TimeoutException e) { throw new IllegalStateException("VPN service shutdown timed out"); }')
 text=text.replace('public static class VpnService extends android.net.VpnService {', 'public static class VpnService extends android.net.VpnService {\n        public final java.util.concurrent.CompletableFuture<Void> destroyed=new java.util.concurrent.CompletableFuture<>();')
 text=text.replace('            super.onDestroy();', '            super.onDestroy();\n            destroyed.complete(null);')
 backend.write_text(text)
 native=android/'tunnel/tools/libwg-go';api=native/'api-android.go';text=api.read_text()
 for imp in ('net','os','os/signal','runtime','runtime/debug','strings'):text=text.replace('\n\t"'+imp+'"','')
 text=text.replace('\n\t"unsafe"','\n\t"unsafe"\n\t"sync"').replace('\n\t"github.com/amnezia-vpn/amneziawg-go/ipc"','')
 start=text.index('func init()');end=text.index('//export awgTurnOn',start)
 text=text[:start]+'var handlesMu sync.RWMutex\nfunc init(){tunnelHandles=make(map[int32]TunnelHandle)}\n\n'+text[end:]
 start=text.index('\ttag := cstring');end=text.index('\n\ttun, name, err',start)
 text=text[:start]+'\tlogger := device.NewLogger(device.LogLevelSilent, "")\n'+text[end:]
 text=text.replace('\n\tuapi   net.Listener','')
 start=text.index('\tvar uapi net.Listener');end=text.index('\n\terr = device.Up()',start);text=text[:start]+text[end:]
 text=text.replace('\n\t\tuapiFile.Close()','').replace('TunnelHandle{device: device, uapi: uapi}','TunnelHandle{device: device}')
 text=text.replace('\n\tif handle.uapi != nil {\n\t\thandle.uapi.Close()\n\t}','')
 text=text.replace('err = device.IpcSet(settings)\n\tif err != nil {\n\t\tunix.Close(int(tunFd))', 'err = device.IpcSet(settings)\n\tif err != nil {\n\t\tdevice.Close()')
 for name in ('awgTurnOn','awgTurnOff','awgGetSocketV4','awgGetSocketV6','awgGetConfig'):
  start=text.index('func '+name+'(');brace=text.index('{',start);lock='Lock' if name in ('awgTurnOn','awgTurnOff') else 'RLock';unlock='Unlock' if lock=='Lock' else 'RUnlock'
  text=text[:brace+1]+'\n handlesMu.'+lock+'();defer handlesMu.'+unlock+'()'+text[brace+1:]
 start=text.index('func awgVersion()');end=text.index('\nfunc main()',start);text=text[:start]+'func awgVersion() *C.char {return C.CString("FamilyConnect/'+ENGINE+'") }\n'+text[end:];api.write_text(text)
 text=api.read_text().replace(' handlesMu.Lock();defer handlesMu.Unlock()',' handlesMu.Lock();defer handlesMu.Unlock()\n if tcpRunning.Load(){unix.Close(int(tunFd));return -1}',1)
 api.write_text(text)
 for name in ('tcp-android.go','tcp-jni.c'):shutil.copy2(ROOT/'pilot/android-tcp'/name,native/name)
 run('go','mod','edit','-replace','github.com/xtls/xray-core='+str(xray),cwd=native)
 run('go','mod','edit','-require','github.com/xtls/xray-core@v0.0.0',cwd=native)
 run('go','mod','edit','-replace','github.com/amnezia-vpn/amneziawg-go='+str(engine),cwd=native)
 env=os.environ.copy();env['GOTOOLCHAIN']='local';run('go','mod','tidy',cwd=native,env=env)
 run('go','build','-trimpath','-buildvcs=false','-o',str(OUT/'xray-peer'),'./main',cwd=xray,env=env)
 # Same in-memory encrypted UDP echo peer used for isolated Windows acceptance, portable source.
 peer=engine/'cmd/fc-android-peer';peer.mkdir(parents=True);shutil.copy2(ROOT/'pilot/android-awg/peer.go',peer/'main.go')
 run('go','build','-trimpath','-buildvcs=false','-o',str(OUT/'peer-fixture'),'./cmd/fc-android-peer',cwd=engine,env=env)
 wg=temp/'wireguard'
 checkout('https://github.com/WireGuard/wireguard-go','ecfc5a8d54462e18e13c72173e2623d16d8e25a0',wg)
 wgpeer=wg/'cmd/fc-android-peer';wgpeer.mkdir(parents=True)
 (wgpeer/'main.go').write_text((ROOT/'pilot/android-awg/peer.go').read_text().replace('github.com/amnezia-vpn/amneziawg-go','golang.zx2c4.com/wireguard'))
 run('go','build','-trimpath','-buildvcs=false','-o',str(OUT/'wg-peer-fixture'),'./cmd/fc-android-peer',cwd=wg,env=env)
 ndk=Path(os.environ['ANDROID_NDK_HOME'])/'toolchains/llvm/prebuilt/linux-x86_64/bin'
 hashes={};abis={'arm64-v8a':('arm64','aarch64-linux-android26-clang'),'armeabi-v7a':('arm','armv7a-linux-androideabi26-clang'),'x86':('386','i686-linux-android26-clang'),'x86_64':('amd64','x86_64-linux-android26-clang')}
 for abi,(arch,cc) in abis.items():
  output=OUT/'jniLibs'/abi/'libfc-awg.so';output.parent.mkdir(parents=True)
  cross=env|{'GOOS':'android','GOARCH':arch,'CGO_ENABLED':'1','CC':str(ndk/cc),'CGO_LDFLAGS':'-Wl,-soname=libfc-awg.so -Wl,-z,max-page-size=16384'}
  if arch=='arm':cross['GOARM']='7'
  run('go','build','-trimpath','-buildvcs=false','-ldflags=-buildid=','-buildmode=c-shared','-o',str(output),cwd=native,env=cross)
  hashes[abi]=hashlib.sha256(output.read_bytes()).hexdigest()
 licenses=OUT/'assets/awg-licenses';licenses.mkdir(parents=True)
 shutil.copy2(xray/'LICENSE',licenses/'Xray.txt')
 gvisor=Path(subprocess.check_output(['go','list','-m','-f','{{.Dir}}','gvisor.dev/gvisor'],cwd=native,env=env,text=True).strip());shutil.copy2(gvisor/'LICENSE',licenses/'gVisor.txt')
 shutil.copy2(android/'COPYING',licenses/'Android.txt');shutil.copy2(engine/'LICENSE',licenses/'Engine.txt')
 manifest={'android_revision':ANDROID,'engine_revision':ENGINE,'go':'1.26.1','ndk':'28.2.13676358','abis':hashes,'jni_source_sha256':hashlib.sha256(api.read_bytes()).hexdigest(),'public_uapi':False,'root_backend':False,'single_runtime':True,'xray_revision':'d2758a023cd7f4174a5a5fa4ff66e487d4342ba0','tcp_source_sha256':hashlib.sha256((native/'tcp-android.go').read_bytes()).hexdigest(),'tcp_jni_sha256':hashlib.sha256((native/'tcp-jni.c').read_bytes()).hexdigest(),'go_sum_sha256':hashlib.sha256((native/'go.sum').read_bytes()).hexdigest(),'wg_peer_revision':'ecfc5a8d54462e18e13c72173e2623d16d8e25a0'}
 (OUT/'assets/awg-build.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest))
