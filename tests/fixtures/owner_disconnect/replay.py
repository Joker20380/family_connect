"""Policy-only red/green regression; not a physical replay of the RS losses."""
import json
import os
import subprocess
from prepare import BASE,WORK,SOURCE,JAVA,ROOT,add,digest

def main():
    tools=ROOT/'state-client-build/field65-export16/diag-source-freeze-1/resume-tools'
    original=BASE/'android-source'/JAVA/'AutomaticConnection.java'
    assert 'else if(++unhealthy>=3)orchestrator.lost(ConnectivityOrchestrator.Failure.NETWORK);' in original.read_text()
    root=WORK/'policy-replay';root.mkdir(exist_ok=False)
    current=(SOURCE/JAVA/'RestrictedHealthPolicy.java').read_text()
    baseline=current.replace('failures=probe||progress?0:Math.min(3,failures+1);','failures=probe?0:Math.min(3,failures+1);')
    assert current!=baseline
    source=root/'RestrictedHealthPolicy.java';add(source,baseline)
    modules=tools/'gradle-home/caches/modules-2/files-2.1'
    jars=[next(modules.glob(pattern)) for pattern in ('com.google.code.gson/gson/2.13.2/*/*.jar','junit/junit/4.13.2/*/*.jar','org.hamcrest/hamcrest-core/1.3/*/*.jar')]
    classes=WORK/'build/android/app/intermediates/javac'
    common=[classes/'privateBeta/compilePrivateBetaJavaWithJavac/classes',classes/'privateBetaUnitTest/compilePrivateBetaUnitTestJavaWithJavac/classes',*jars]
    subprocess.run([tools/'jdk/bin/javac','-cp',os.pathsep.join(map(str,common)),'-d',root,source],check=True)
    outcomes={}
    for label,classpath in [('baseline-rule',[root,*common]),('candidate',common)]:
        result=subprocess.run([tools/'jdk/bin/java','-cp',os.pathsep.join(map(str,classpath)),'org.junit.runner.JUnitCore','com.familyconnect.app.RestrictedHealthPolicyTest'],capture_output=True)
        (root/(label+'.log')).write_bytes(result.stdout+result.stderr);outcomes[label]=result.returncode
    assert outcomes=={'baseline-rule':1,'candidate':0},outcomes
    assert 'failedProbeMustNotTearDownFreshBidirectionalApplicationProgress' in (root/'baseline-rule.log').read_text()
    receipt=dict(scope='exact beta101 three-failure decision rule extracted into deterministic policy harness; not complete Android/native replay',baseline_android_source_sha256=digest(original),result=outcomes)
    (root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()
