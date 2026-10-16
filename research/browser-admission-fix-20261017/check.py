import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
state = root.parent
tools = state / 'field65-export16/diag-source-freeze-1/resume-tools'
source = root / 'source'
output = root / sys.argv[1]
output.mkdir(mode=0o700)
sensor = next(zone/'temp' for zone in Path('/sys/class/thermal').glob('thermal_zone*') if (zone/'type').read_text().strip() == 'x86_pkg_temp')
environment = os.environ | dict(GOMAXPROCS='1', GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off', GOFLAGS='-mod=readonly', GOCACHE=str(tools/'go-cache'), GOPATH=str(tools/'gopath'), GOMODCACHE=str(tools/'gopath/pkg/mod'))
receipts = []
batch_start = time.monotonic()
retained = state / 'reliable-full-stack-1/run.py'
definitions = [node for node in ast.parse(retained.read_text()).body if isinstance(node,ast.FunctionDef) and node.name in ('temperature','interrupt','run')]
exec(compile(ast.Module(body=definitions,type_ignores=[]),str(retained),'exec'))
signal.signal(signal.SIGTERM,interrupt)
signal.signal(signal.SIGINT,interrupt)
go = str(tools/'go/bin/go')
overlay = output/'overlay.json'
overlay.write_text(json.dumps({'Replace': {str(source/'carrier/tcpforward'/name): str(root/'fixtures'/name) for name in ('admission_export_test.go','browser_admission_test.go')}}))
selection = '^Test(Admission|BrowserAdmission|FlowLimit|ConcurrentTCPIsolation|FamilyDNS|UnsupportedTraffic|Service|ReasonTyped|SessionTag|Report|Capture|MuxLimitAndIndependentReset|MuxSlowConsumerAndInteractive|MuxHalfCloseAndOpenErrors|MuxSessionCancellationManyStreams|MuxSchedulerRoundRobinAndPriority|MuxDNSCancellationAndShutdown|MuxOpenCloseCancellationStress|MuxGlobalBlockedWriterShutdown)'
lease_selection = '^TestLease(FullDataCapacityStillRenews|RealFamilyMuxPersistentTCP|LegacyClientAndServer|ControlRevalidatesAdmission|ControlRevocationBeforeConfirmation|ControlStopsAtSecurityLimit|SecurityAndReplay)$'
for mode, count in [('normal',2),('race',1)]:
    flags = ['-race'] if mode == 'race' else []
    run('carrier-'+mode,[go,'test','-p=1','-overlay='+str(overlay),*flags,'./tcpforward','./wholedevice','./sessiondiag','-run',selection,'-count='+str(count),'-timeout=100s','-failfast','-v'],source/'carrier')
    run('lease-'+mode,[go,'test','-p=1',*flags,'./roombroker','-run',lease_selection,'-count='+str(count),'-timeout=90s','-failfast','-v'],source/'carrier')
    run('gateway-'+mode,[go,'test','-p=1',*flags,'./tcpforward','./sessiondiag','-run','^Test(Admission|MuxLimitAndIndependentReset|MuxHalfCloseAndOpenErrors|MuxSessionCancellationManyStreams|ReasonTyped)','-count=1','-timeout=50s','-failfast','-v'],root/'gateway-source/carrier')
module = output/'native.mod'
shutil.copyfile(source/'pilot/android-restricted/go.mod',module)
shutil.copyfile(source/'pilot/android-restricted/go.sum',output/'native.sum')
run('packet-module',[go,'mod','edit','-modfile='+str(module),'-replace=github.com/Joker20380/family_connect/carrier='+str(source/'carrier'),'-replace=github.com/xtls/xray-core='+str(root/'xray')],source/'pilot/android-restricted')
for mode in ('normal','race'):
    run('packet-'+mode,[go,'test','-p=1','-modfile='+str(module),'-ldflags=-checklinkname=0',*(['-race'] if mode=='race' else []),'./packet','-run','^TestExistingPacketEngineTCPDNSAndFailClosed$','-count=1','-timeout=40s','-v'],source/'pilot/android-restricted')
classes = output/'classes'
classes.mkdir()
previous = state/'transport-speed-cutover-1/build/android/app/intermediates'
main_classes = previous/'javac/researchProvisioning/compileResearchProvisioningJavaWithJavac/classes'
resource_jar = previous/'compile_and_runtime_not_namespaced_r_class_jar/researchProvisioning/processResearchProvisioningResources/R.jar'
dependencies = tools/'gradle-home/caches/modules-2/files-2.1'
jars = [next(dependencies.glob(pattern)) for pattern in ('com.google.code.gson/gson/2.13.2/*/*.jar','junit/junit/4.13.2/*/*.jar','org.hamcrest/hamcrest-core/1.3/*/*.jar')]
classpath = os.pathsep.join(map(str,[classes,main_classes,resource_jar,tools/'android/platforms/android-35/android.jar',*jars,source/'clients/android/app/src/test/resources']))
java_root = source/'clients/android/app/src'
files = [java_root/'main/java/com/familyconnect/app'/name for name in ('Diagnostics.java','DiagnosticRing.java')]
tests = ['AdmissionDiagnosticsTest','DiagnosticRingTest','BootstrapCorrelationTest','StartupFidelityTest']
files += [java_root/'test/java/com/familyconnect/app'/(name+'.java') for name in tests]
run('jvm-compile',[str(tools/'jdk/bin/javac'),'-source','17','-target','17','-implicit:none','-cp',classpath,'-d',str(classes),*map(str,files)],source)
run('jvm-export',[str(tools/'jdk/bin/java'),'-Xmx256m','-cp',classpath,'org.junit.runner.JUnitCore',*['com.familyconnect.app.'+name for name in tests]],source)
