"""Derive a private health/recovery candidate from the exact installed beta101 capsule."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[3]
FIXTURE=Path(__file__).resolve().parent
BASE=ROOT/'state-client-build/p1-lifecycle-101-20261021'
WORK=ROOT/'state-client-build/owner-disconnections-20261022'
SOURCE=WORK/'android-source'
JAVA=Path('clients/android/app/src/main/java/com/familyconnect/app')

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def replace(path,old,new):
    text=path.read_text();assert text.count(old)==1,(path,old)
    position=text.index(old);start=text.rfind('\n',0,position)+1;end=text.find('\n',position+len(old))
    if end<0:end=len(text)
    original=text[start:end];new=original.replace(old,new);old=original
    subprocess.run(['apply_patch','*** Begin Patch\n*** Update File: '+str(path)+'\n@@\n'+''.join('-'+line+'\n' for line in old.splitlines())+''.join('+'+line+'\n' for line in new.splitlines())+'*** End Patch\n'],check=True)

def add(path,text):
    subprocess.run(['apply_patch','*** Begin Patch\n*** Add File: '+str(path)+'\n'+''.join('+'+line+'\n' for line in text.splitlines())+'*** End Patch\n'],check=True)

def inventory(root):
    return {str(path.relative_to(root)):digest(path) for path in sorted(root.rglob('*')) if path.is_file() and not any(part in ('.git','.gradle','build','__pycache__') for part in path.relative_to(root).parts)}

def main():
    os.umask(0o077)
    assert not SOURCE.exists()
    assert digest(BASE/'delivery/FamilyConnect-0.1.18-beta101-lifecycle.apk')=='3c023e39d95e29fe0561dc462e28f1e643b9e14558cf49700d58df528b2963d9'
    before=inventory(BASE/'android-source');(WORK/'parent-source-inventory.json').write_text(json.dumps(before,indent=2)+'\n')
    shutil.copytree(BASE/'android-source',SOURCE,ignore=shutil.ignore_patterns('.git','.gradle','build','__pycache__'))
    add(SOURCE/JAVA/'RestrictedHealthPolicy.java',(FIXTURE/'RestrictedHealthPolicy.java').read_text())
    add(SOURCE/'clients/android/app/src/test/java/com/familyconnect/app/RestrictedHealthPolicyTest.java',(FIXTURE/'RestrictedHealthPolicyTest.java').read_text())
    path=SOURCE/JAVA/'AutomaticConnection.java'
    replace(path,'    private int unhealthy;','    private int unhealthy;\n    private RestrictedHealthPolicy restrictedHealth=new RestrictedHealthPolicy();')
    replace(path,'        orchestrator.check(deadline);unhealthy=0;nextHealth=0;','        orchestrator.check(deadline);unhealthy=0;nextHealth=0;restrictedHealth=new RestrictedHealthPolicy();')
    replace(path,'''                boolean good=health.check("10.79.0.2");nextHealth=now()+30000;
                Diagnostics.dns(context,good);orchestrator.trafficHealthy(good);
                if(interrupted!=null)orchestrator.lost(interrupted);
                else if(good)unhealthy=0;
                else if(++unhealthy>=3)orchestrator.lost(ConnectivityOrchestrator.Failure.NETWORK);''','''                restrictedHealth.begin(restricted.healthSample());
                boolean good=health.check("10.79.0.2");nextHealth=now()+30000;
                Diagnostics.dns(context,good);
                failure=restricted.connectionFailure();
                if(interrupted!=null){orchestrator.lost(interrupted);return;}
                if(failure!=null){orchestrator.lost(failure);return;}
                RestrictedHealthPolicy.Decision decision=restrictedHealth.observe(good,restricted.healthSample());
                if(!good&&decision.progress)Diagnostics.dnsProgress(context);
                orchestrator.trafficHealthy(good||decision.progress);
                if(decision.recover)orchestrator.lost(ConnectivityOrchestrator.Failure.NETWORK);''')
    path=SOURCE/JAVA/'RestrictedTunnelEngine.java'
    replace(path,'    boolean healthy() {','    private RestrictedHealthPolicy.Sample healthSample;\n    RestrictedHealthPolicy.Sample healthSample(){return healthSample;}\n\n    boolean healthy() {')
    replace(path,'    private void evidence(JSONObject snapshot) throws Exception {','    private void evidence(JSONObject snapshot) throws Exception {\n        healthSample=RestrictedHealthPolicy.sample(snapshot.toString(),SystemClock.elapsedRealtime(),authorizationDenied());')
    path=SOURCE/JAVA/'DiagnosticRing.java'
    replace(path,'        DNS_PROBE_OK, DNS_PROBE_FAILED, SIGNAL_WS_CLOSE, ICE_DISCONNECTED, ICE_FAILED, PEER_CONNECTION_FAILED,','        DNS_PROBE_OK, DNS_PROBE_FAILED, DNS_TRAFFIC_PROGRESS, SIGNAL_WS_CLOSE, ICE_DISCONNECTED, ICE_FAILED, PEER_CONNECTION_FAILED,')
    replace(path,'    synchronized void dns(boolean good,long now){add(Component.DNS,good?Code.DNS_PROBE_OK:Code.DNS_PROBE_FAILED,state,state,"none",0,now);}','    synchronized void dns(boolean good,long now){add(Component.DNS,good?Code.DNS_PROBE_OK:Code.DNS_PROBE_FAILED,state,state,"none",0,now);}\n    synchronized void dnsProgress(long now){add(Component.DNS,Code.DNS_TRAFFIC_PROGRESS,state,state,"restricted",0,now);}')
    path=SOURCE/JAVA/'Diagnostics.java'
    replace(path,'    static void dns(Context context,boolean good){try{Diagnostics store=get(context);synchronized(store){store.ring.dns(good,System.currentTimeMillis());store.save(false);}}catch(Exception ignored){}}','    static void dns(Context context,boolean good){try{Diagnostics store=get(context);synchronized(store){store.ring.dns(good,System.currentTimeMillis());store.save(false);}}catch(Exception ignored){}}\n    static void dnsProgress(Context context){try{Diagnostics store=get(context);synchronized(store){store.ring.dnsProgress(System.currentTimeMillis());store.save(false);}}catch(Exception ignored){}}')
    replace(SOURCE/'clients/android/app/build.gradle',"versionCodeOverride = 101; versionNameOverride = '0.1.18-beta101-lifecycle'","versionCodeOverride = 102; versionNameOverride = '0.1.18-beta102-recovery'")
    after=inventory(SOURCE);changed=[name for name in after if before.get(name)!=after[name]]
    (WORK/'source-delta-manifest.json').write_text(json.dumps(dict(parent=before,source=after,changed=changed,native_unchanged=True,primary_rs_cause='UNRESOLVED',field_ready=False),indent=2)+'\n')
    print('CANDIDATE_SOURCE',SOURCE,'CHANGED',changed)

if __name__=='__main__':main()
