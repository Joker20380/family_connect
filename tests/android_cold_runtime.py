import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.request
import android_emulator_guard as emulator_guard

ROOT=Path(__file__).resolve().parents[1]
WORK=None
AUTH=None
monitor=None
owned_processes=[]
TOOLS=Path('/mnt/data/PycharmProjects/family_connect/state-client-build/field65-export16/diag-source-freeze-1/resume-tools')
AVD=Path('/mnt/data/PycharmProjects/family_connect/state-client-build/cold-native-diagnostic-20261106/offline-avd')
CONTAINER='fc-cold-provision-authority-native-diag'
sys.path.insert(0,str(ROOT/'tests'))
from android_core_emulators import require_nvidia_renderer,observe_wall_clock

record={'source':'6eb61a9faa659b6b07ac16bf9f4bac46a41cd2a7','result':'STARTING','connect_attempted':False,'android_jni_gate':'RETAINED_PASS_NOT_REPEATED','phase':'BASELINE','process_roots':{str(os.getpid()):'runner'}}
capture_lock=threading.Lock()
previous={}
previous_at=time.monotonic()
last_cpu={}
ticks=os.sysconf('SC_CLK_TCK')

def observe_resources():
    global previous,previous_at,last_cpu
    with capture_lock:
        now=time.monotonic()
        processes={}
        for path in Path('/proc').glob('[0-9]*/stat'):
            try:
                raw=path.read_text();end=raw.rindex(')');fields=raw[end+2:].split()
                processes[int(path.parent.name)]={'pid':int(path.parent.name),'ppid':int(fields[1]),'name':re.sub(r'[^\w .-]','?',raw[raw.index('(')+1:end])[:64],'ticks':int(fields[11])+int(fields[12]),'start':int(fields[19])}
            except (FileNotFoundError,PermissionError,ProcessLookupError):pass
        interval=now-previous_at
        roots=dict(record['process_roots'])
        totals={}
        entries=[]
        for pid,entry in processes.items():
            old=previous.get(pid)
            cpu=100*(entry['ticks']-old['ticks'])/ticks/interval if interval>=0.2 and old and old['start']==entry['start'] else last_cpu.get(pid,0)
            last_cpu[pid]=cpu
            parent=pid;seen=set();role='other'
            while parent and parent not in seen:
                seen.add(parent)
                if str(parent) in roots:role=roots[str(parent)];break
                parent=processes.get(parent,{}).get('ppid',0)
            if role=='secret_input' and entry['name']=='stand':role='telemost_workers'
            if role=='other' and entry['name'] in ('java','go','compile','link','clang','ninja'):
                try:
                    if str(Path('/proc',str(pid),'cwd').resolve()).startswith(str(ROOT)):role='own_worktree_build'
                except (FileNotFoundError,PermissionError,ProcessLookupError):pass
            totals[role]=round(totals.get(role,0)+cpu,2)
            entries.append(dict(pid=pid,name=entry['name'],cpu_percent=round(cpu,2),role=role))
        previous=processes;previous_at=now
        memory={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:','SwapFree:'))}
        hottest=sorted(entries,key=lambda entry:entry['cpu_percent'],reverse=True)[:20]
        selected={entry['pid']:entry for entry in hottest}
        selected.update({entry['pid']:entry for entry in entries if entry['role']!='other'})
        return dict(stage=record['phase'],unix_time=time.time(),sample_interval_seconds=round(interval,3),memory_kib=memory,cpu_percent_one_core_100=totals,processes=sorted(selected.values(),key=lambda entry:entry['cpu_percent'],reverse=True))


def save_guard(payload):
    if 'stop' in payload:
        event=payload['stop']
        name='guard-stop-'+event['reason']+'-'+event.get('limit','sensor')+'.json'
        (WORK/name).write_text(json.dumps(payload,indent=2)+'\n')
        return
    if 'frame' in payload:
        record['last_resources']=observe_resources()
        payload['resources']=record['last_resources']
    with capture_lock:
        with (WORK/'resources.jsonl').open('a') as output:
            output.write(json.dumps(payload)+'\n')


def audit(stage):
    record['phase']=stage
    with monitor.read_lock:
        frame=monitor.audit(stage)
        assert record['last_resources']['memory_kib']['MemAvailable']>=4*1024*1024,'MEMORY_PREFLIGHT'
    print('RESOURCE_STAGE',stage,flush=True)
    return frame


def own_start(create):
    if record.get('guard_stop'):raise emulator_guard.GuardStopped(record['guard_stop']['reason'])
    process=create()
    owned_processes.append(process)
    if record.get('guard_stop'):
        emulator_guard.stop(process)
        raise emulator_guard.GuardStopped(record['guard_stop']['reason'])
    return process


def aborted(event):
    record['abort_stage']=record['phase']
    try:(AUTH/'stop').touch()
    except OSError as failure:record['stop_marker_error']=type(failure).__name__
    for process in list(owned_processes):
        try:emulator_guard.stop(process)
        except OSError as failure:record['owned_stop_error']=type(failure).__name__
    if event.get('limit') in ('cleanup','overall'):
        for process in list(owned_processes):
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except OSError as failure:record['owned_kill_error']=type(failure).__name__
        if record.get('owns_stand'):
            try:subprocess.run(['docker','stop','--time','1',CONTAINER],capture_output=True,timeout=emulator_guard.FORCED_CLEANUP_SECONDS)
            except Exception:record['forced_authority_cleanup']='UNKNOWN'
        record['result']='FAIL_FORCED_TEST_LIFETIME'
        receipt=monitor.snapshot()|{'source':record.get('source'),'result':record['result'],
                                   'forced_authority_cleanup':record.get('forced_authority_cleanup','NOT_VERIFIED')}
        try:(WORK/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        finally:os._exit(124)


def cellular_only(connectivity):
    networks=[line for line in connectivity.splitlines() if 'NetworkAgentInfo{' in line]
    return len(networks)==1 and all(token in networks[0] for token in
        ('Transports: CELLULAR ', 'CONNECTED/CONNECTED', 'INTERNET', 'NOT_RESTRICTED', 'NOT_VPN', 'FOREGROUND'))


def direct_rules(action):
    assert action in ('REJECT','DROP')
    return [['shell','iptables','-I','OUTPUT','-d',address,'-p','tcp','--dport',port,'-j',action]
            for address,port in (('185.251.89.19','8443'),('186.246.45.246','4242'))]


def main(work, *, observe_cpu_temperature=False, base_apks=None, api_level=27,
         avd_home=AVD, avd_name='fc-cold-one', require_cellular=False, direct_block='REJECT'):
    global WORK,AUTH,monitor
    WORK=Path(work).resolve();AUTH=WORK/'local-auth'
    avd_home=Path(avd_home).resolve()
    assert api_level in (27,28) and re.fullmatch('[a-zA-Z0-9_-]+',avd_name)
    rules_to_install=direct_rules(direct_block)
    record['qualification']={'api_level':api_level,'cellular_only':require_cellular,'direct_block':direct_block,
                             'cellular_scope':'EMULATOR_NOT_FIELD_MOBILE_NETWORK'}
    record['imported_guard']={'path':str(Path(emulator_guard.__file__).resolve()),
                             'sha256':hashlib.sha256(Path(emulator_guard.__file__).read_bytes()).hexdigest()}
    assert AUTH.is_dir(),'EXISTING_ISOLATED_WORK_DIRECTORY_REQUIRED'
    for name in ('runtime.started','receipt.json','resources.jsonl','emulator.log','instrumentation.log'):
        assert not (WORK/name).exists(),'UNUSED_RUNTIME_OUTPUT_DIRECTORY_REQUIRED'
    if base_apks:
        base_apks=Path(base_apks).resolve()
        record['native_source']=record['source']
        record['source']=(base_apks/'managed-source.txt').read_text().strip()
        assert re.fullmatch('[0-9a-f]{40}',record['source']),'MANAGED_SOURCE_REQUIRED'
    monitor=emulator_guard.Monitor(record,save_guard,aborted,cpu_temperature_stop=not observe_cpu_temperature)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
    emulator=None;vault=None;package=None;lock=None;logs=[];owns_stand=False
    sdk=TOOLS/'android'
    adb=[str(sdk/'platform-tools/adb'),'-s','emulator-5582']
    def live():
        assert not record.get('guard_stop'),'HOST_GUARD_STOP'
        assert emulator is not None and emulator.poll() is None,'OWNED_EMULATOR_EXITED'
    def call(arguments,timeout=15):
        live()
        return subprocess.run(adb+arguments,check=True,capture_output=True,text=True,timeout=timeout).stdout
    try:
        assert not (WORK/'runtime.started').exists(),'SINGLE_RUNTIME_ALREADY_STARTED'
        (WORK/'runtime.started').touch()
        monitor.start()
        audit('IMMUTABLE_COMPONENTS_READY')
        lock=open('/mnt/data/PycharmProjects/family_connect/state-client-build/mesh-core-runtime-20261105/android-emulator.lock','a')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        record['shared_lock_acquired']=True
        for path in Path('/proc').glob('[0-9]*/comm'):
            try:assert 'qemu-system' not in path.read_text(),'OTHER_EMULATOR_PRESENT'
            except FileNotFoundError:pass
        assert os.access('/dev/kvm',os.R_OK|os.W_OK),'KVM_UNAVAILABLE'
        assert shutil.disk_usage(avd_home).free>=7372*1024*1024,'AVD_DISK_PREFLIGHT'
        assert (avd_home/(avd_name+'.avd/config.ini')).is_file(),'OWN_AVD_MISSING'
        assert not subprocess.check_output(['docker','ps','-aq','--filter','name=^'+CONTAINER+'$'],text=True).strip(),'AUTHORITY_NAME_ALREADY_OWNED'
        log=(WORK/'emulator.log').open('xb');logs.append(log)
        environment=os.environ|dict(JAVA_HOME=str(TOOLS/'jdk'),ANDROID_HOME=str(sdk),ANDROID_SDK_ROOT=str(sdk),ANDROID_AVD_HOME=str(avd_home),__NV_PRIME_RENDER_OFFLOAD='1',__GLX_VENDOR_LIBRARY_NAME='nvidia')
        record['phase']='ANDROID_BOOT'
        emulator=own_start(lambda: emulator_guard.start([str(sdk/'emulator/emulator'),'-avd',avd_name,'-port','5582','-no-window','-no-audio','-no-snapshot','-no-boot-anim','-gpu','host','-accel','on','-memory','2048','-cores','2'],environment,log))
        record['process_roots'][str(emulator.pid)]='emulator'
        deadline=time.monotonic()+120
        while True:
            live()
            boot=subprocess.run(adb+['shell','getprop','sys.boot_completed'],capture_output=True,text=True,timeout=10)
            if boot.returncode==0 and boot.stdout.strip()=='1':break
            assert time.monotonic()<deadline,'BOOT_TIMEOUT'
            time.sleep(2)
        assert call(['shell','getprop','ro.build.version.sdk']).strip()==str(api_level)
        assert call(['shell','getprop','ro.product.cpu.abi']).strip()=='x86_64'
        record['phase']='ANDROID_POSTBOOT_COLD_RESET'
        surface=call(['shell','dumpsys','SurfaceFlinger'])
        (WORK/'renderer.txt').write_text(surface);record['renderer']=require_nvidia_renderer(surface)
        call(['root']);call(['wait-for-device'],30)
        if require_cellular:
            call(['shell','svc','wifi','disable'])
            call(['shell','svc','data','enable'])
            deadline=time.monotonic()+20
            while True:
                connectivity=call(['shell','dumpsys','connectivity'])
                (WORK/'cellular-selection.txt').write_text(connectivity)
                if cellular_only(connectivity):break
                assert time.monotonic()<deadline,'CELLULAR_ONLY_NETWORK_UNAVAILABLE'
                time.sleep(0.5)
        call(['shell','am','force-stop','com.familyconnect.app.friends'])
        call(['shell','am','force-stop','com.familyconnect.app.friends.test'])
        for name in ('com.familyconnect.app.friends.test','com.familyconnect.app.friends'):
            result=subprocess.run(adb+['uninstall',name],capture_output=True,text=True,timeout=15)
            record.setdefault('owned_package_reset',{})[name]='REMOVED' if 'Success' in result.stdout else 'ABSENT_OR_NOT_INSTALLED'
        remaining=subprocess.run(adb+['shell','pm','path','com.familyconnect.app.friends'],capture_output=True,text=True,timeout=10)
        assert 'package:' not in remaining.stdout,'OWN_PACKAGE_NOT_RESET'
        connectivity=call(['shell','dumpsys','connectivity'])
        (WORK/'connectivity-before-workers.txt').write_text(connectivity)
        if require_cellular:assert cellular_only(connectivity),'CELLULAR_ONLY_NETWORK_UNAVAILABLE'
        assert not re.search(r'(?:NetworkAgentInfo|Transports:)[^\n]*\bVPN\b',connectivity),'VPN_ACTIVE_BEFORE_WORKERS'
        record['no_test_package_no_readiness_before_workers']=True
        record['phase']='ANDROID_PREWORKER_CLOCK_OBSERVATION'
        observe_wall_clock(adb,record)
        audit('ANDROID_READY_NO_VPN_BEFORE_ROOMS')
        live()
        print('ANDROID_READY_PROTECTED_LOCAL_PASSWORD_DIALOG_OPENING',flush=True)
        record['phase']='SECURE_INPUT_AND_WORKER_START'
        log=(AUTH/'stand.log').open('xb');logs.append(log)
        vault=own_start(lambda: subprocess.Popen([sys.executable,str(AUTH/'vault_to_runtime.py')],stdout=log,stderr=subprocess.STDOUT,env=os.environ|{'GDK_BACKEND':'x11'},start_new_session=True))
        record['process_roots'][str(vault.pid)]='secret_input';owns_stand=True;record['owns_stand']=True
        fixture=AUTH/'fixture'
        last_authority_check=0
        while not all((fixture/name).is_file() for name in ('directory.json','locator.json','identity96.private','anchor.pub')):
            live()
            assert vault.poll() is None,'STAND_EXITED_BEFORE_READY'
            if time.monotonic()-last_authority_check>2:
                status=subprocess.run(['docker','inspect','-f','{{.State.Pid}}',CONTAINER],capture_output=True,text=True,timeout=5)
                if status.returncode==0 and status.stdout.strip().isdigit() and int(status.stdout.strip())>0:record['process_roots'][status.stdout.strip()]='authority'
                last_authority_check=time.monotonic()
            time.sleep(0.5)
        authority_pid=int(subprocess.check_output(['docker','inspect','-f','{{.State.Pid}}',CONTAINER],text=True).strip())
        record['process_roots'][str(authority_pid)]='authority'
        audit('AFTER_AUTHORITY_TELEMOST_WORKERS')
        verified=subprocess.run([str(AUTH/'verify_locator'),str(fixture)],check=True,capture_output=True,text=True,timeout=10)
        record['locator_after_workers']=json.loads(verified.stdout)
        subprocess.run(['docker','exec',CONTAINER,'/usr/local/bin/python','/repo/tests/fixtures/mobile_bootstrap/provision_backend.py','verify-cold','/state'],check=True,capture_output=True,timeout=15)
        record['synthetic_identity_registered']=True
        record['phase']='FINAL_ASSET_PACKAGING'
        log=(WORK/'asset-packaging.log').open('xb');logs.append(log)
        packaging=[sys.executable,str(ROOT/'tests/android_cold_pack_assets.py'),str(WORK)]
        if base_apks:packaging+=['--base-apks',str(base_apks)]
        package=own_start(lambda: subprocess.Popen(packaging,stdout=log,stderr=subprocess.STDOUT,start_new_session=True))
        record['process_roots'][str(package.pid)]='asset_packaging'
        while package.poll() is None:live();time.sleep(0.25)
        assert package.returncode==0,'ASSET_PACKAGING_FAILED'
        audit('FINAL_APKS_READY_NO_COMPILER')
        record['phase']='FINAL_INSTALL'
        for name in ('app-friends.apk','app-friends-androidTest.apk'):
            assert 'Success' in call(['install','--no-streaming','-t',str(WORK/'apk-final'/name)],45),'OWNED_INSTALL_FAILED'
        call(['shell','appops','set','com.familyconnect.app.friends','ACTIVATE_VPN','allow'])
        rules=call(['shell','iptables','-S','OUTPUT'])
        assert not re.search(r'--dport (8443|4242).*(REJECT|DROP)',rules),'UNEXPECTED_EXISTING_BLOCKS'
        for rule in rules_to_install:call(rule)
        (WORK/'guest-rules-before.txt').write_text(call(['shell','iptables','-nvxL','OUTPUT']))
        call(['shell','am','start','-n','com.familyconnect.app.friends/com.familyconnect.app.FriendsActivity'])
        observe_wall_clock(adb,record)
        with sqlite3.connect('file:'+str(fixture/'access.db')+'?mode=ro',uri=True) as database:
            assert database.execute('select count(*) from restricted_challenges').fetchone()[0]==0
            assert database.execute('select count(*) from restricted_certificates').fetchone()[0]==0
        verified=subprocess.run([str(AUTH/'verify_locator'),str(fixture)],check=True,capture_output=True,text=True,timeout=10)
        record['locator_before_connect']=json.loads(verified.stdout)
        assert record['locator_before_connect']['remaining_seconds']>=200,'LOCATOR_WINDOW_BELOW_CANDIDATE_CONTRACT'
        audit('COLD_PREREQUISITES_BEFORE_CONNECT')
        record['phase']='SINGLE_AUTOMATIC_CONNECTION'
        monitor.begin_attempt()
        record['connect_attempted']=True
        with (WORK/'instrumentation.log').open('xb') as output:
            result=own_start(lambda: subprocess.Popen(adb+['shell','am','instrument','-w','-e','expected_api',str(api_level),'-e','cellular_only',str(require_cellular).lower(),'-e','class','com.familyconnect.app.ColdProvisionRuntimeTest','com.familyconnect.app.friends.test/androidx.test.runner.AndroidJUnitRunner'],stdout=output,stderr=subprocess.STDOUT,start_new_session=True))
            result.wait(timeout=monitor.remaining())
        record['result']='PASS_POSITIVE_ONLY' if result.returncode==0 and 'OK (1 test)' in (WORK/'instrumentation.log').read_text() else 'FAIL_RUNTIME'
        audit('AFTER_SINGLE_CONNECT')
        (WORK/'guest-rules-after.txt').write_text(call(['shell','iptables','-nvxL','OUTPUT']))
        (WORK/'guest-connectivity-after.txt').write_text(call(['shell','dumpsys','connectivity']))
    except Exception as failure:
        record['result']='FAIL_RUNTIME_CAPTURE' if record['connect_attempted'] else 'FAIL_PRECONNECT'
        record['failure_stage']=record['phase'];record['failure_category']=type(failure).__name__
        if isinstance(failure,AssertionError):record['failure_code']=str(failure)
        try:monitor.sample('FAILURE_CAPTURE')
        except Exception:pass
        print(record['result'],record['failure_stage'],record.get('failure_code',record['failure_category']),flush=True)
    finally:
        monitor.begin_cleanup()
        try:
            (AUTH/'stop').touch()
            if package is not None and package.poll() is None:
                os.killpg(package.pid,signal.SIGTERM);package.wait(timeout=15)
            if emulator is not None:
                if emulator.poll() is None:
                    try:subprocess.run(adb+['shell','am','force-stop','com.familyconnect.app.friends'],capture_output=True,timeout=5)
                    except Exception:pass
                    emulator_guard.stop(emulator)
                try:emulator.wait(timeout=30)
                except subprocess.TimeoutExpired:emulator.kill();emulator.wait(timeout=10)
                record['owned_emulator_stopped']=True
            if vault is not None:
                try:vault.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(vault.pid,signal.SIGTERM)
                    vault.wait(timeout=15)
                record['secret_input_exit']=vault.returncode
            if owns_stand:
                existing=subprocess.check_output(['docker','ps','-q','--filter','name=^'+CONTAINER+'$'],text=True,timeout=5).strip()
                if existing:subprocess.run(['docker','stop','--time','5',CONTAINER],capture_output=True,timeout=15)
        except Exception as failure:
            record['cleanup_error']=type(failure).__name__
            for process in list(owned_processes):emulator_guard.stop(process)
        finally:
            for log in logs:log.close()
            if lock is not None:lock.close()
            if not monitor.close():record['result']='FAIL_MONITOR_JOIN'
            if record.get('guard_stop') and record['result'].startswith('PASS'):
                record['result']='FAIL_GUARD_DURING_CLEANUP'
        record['provider_rooms_created']=len(list(AUTH.glob('own-room-*.private')))
        record['provider_room_deletion']='NOT_VERIFIED'
        (WORK/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Explicit isolated work directory required; no runtime authorization implied')
    parser.add_argument('work')
    parser.add_argument('--base-apks')
    parser.add_argument('--api-level',type=int,choices=(27,28),default=27)
    parser.add_argument('--avd-home',default=str(AVD))
    parser.add_argument('--avd-name',default='fc-cold-one')
    parser.add_argument('--cellular-only',action='store_true')
    parser.add_argument('--direct-block',choices=('REJECT','DROP'),default='REJECT')
    parser.add_argument('--observe-cpu-temperature-only',action='store_true',help='Explicit owner-authorized run: retain CPU readings without CPU thermal stop; all other guards remain')
    arguments=parser.parse_args()
    main(arguments.work,observe_cpu_temperature=arguments.observe_cpu_temperature_only,base_apks=arguments.base_apks,
         api_level=arguments.api_level,avd_home=arguments.avd_home,avd_name=arguments.avd_name,
         require_cellular=arguments.cellular_only,direct_block=arguments.direct_block)
