import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description='Provider-free real JVM/JNI/Go diagnostic boundary test')
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    output = args.output.resolve()
    output.relative_to(root / 'state-client-build')
    output.mkdir(parents=True, exist_ok=False)
    tools = args.tools.resolve()
    native = root / 'pilot/android-restricted/native'
    source = (native / 'provision.go').read_text()
    assert source.count('coldprovision.Telemost(network)') == 1
    assert source.count('defer provisioningResult(output, lease.diagnostic)') == 1
    source = source.removeprefix('//go:build android\n\n')
    source = source.replace('coldprovision.Telemost(network)', 'diagnosticConnector(network, resolver)')
    source = source.replace('defer provisioningResult(output, lease.diagnostic)', 'testPostEntered <- struct{}{}\n\tdefer provisioningResult(output, lease.diagnostic)')
    (output / 'provision.go').write_text(source)
    for name in ('provision_lease.go', 'provision_bridge.c'):
        (output / name).write_bytes((native / name).read_bytes())
    bridge = (native / 'bridge.c').read_text().split('struct text{',1)[0]
    bridge = bridge.replace('AttachCurrentThread(vm,&env,NULL)', 'AttachCurrentThread(vm,(void **)&env,NULL)')
    (output / 'bridge.c').write_text(bridge + '''
extern char *fcProvisionFixture(void);
extern void fcProvisionWaitPost(void);
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_NativeRestricted_fixture(JNIEnv *env,jclass cls){char *raw=fcProvisionFixture();jstring result=(*env)->NewStringUTF(env,raw);free(raw);return result;}
JNIEXPORT void JNICALL Java_com_familyconnect_app_NativeRestricted_waitPost(JNIEnv *env,jclass cls){fcProvisionWaitPost();}
''')
    tests = (root / 'carrier/coldprovision/diagnostic_test.go').read_text()
    fixture = tests[tests.index('func diagnosticFixture'):tests.index('func TestDiagnosticBefore')]
    fixture = fixture.replace('*testing.T', '*diagnosticTest')
    fixture = re.sub(r'\b(Envelope|Address|Locator|Protocol|Domain)\b', r'coldprovision.\1', fixture)
    endpoint = tests[tests.index('type diagnosticEndpoint'):tests.index('func TestDiagnosticRealTLS')]
    (output / 'fixture.go').write_text('''package main
// #include <stdlib.h>
import "C"
import (
 "bytes"; "context"; "crypto/ed25519"; "crypto/rand"; "crypto/tls"; "crypto/x509"; "encoding/base64"; "encoding/binary"; "encoding/json"; "encoding/pem"; "io"; "math/big"; "strings"; "time"
 "github.com/Joker20380/family_connect/carrier/bootstrap"
 "github.com/Joker20380/family_connect/carrier/coldprovision"
 "github.com/Joker20380/family_connect/carrier/familysession"
 "github.com/Joker20380/family_connect/carrier/roombroker"
 "github.com/Joker20380/family_connect/carrier/underlay"
)
type diagnosticTest struct{}
func (*diagnosticTest) Helper(){}
func (*diagnosticTest) Fatal(...any){panic("fixture creation failed")}
type delegation struct { Version int `json:"version"`; Sequence int64 `json:"sequence"`; Family string `json:"family"`; Gateway string `json:"gateway"`; Authority string `json:"authority"`; MinimumRevision int `json:"minimum_revision"`; IssuedAt int64 `json:"issued_at"`; ExpiresAt int64 `json:"expires_at"` }
''' + fixture + endpoint + '''
var testPostEntered=make(chan struct{},16)
var fixtureIdentity tls.Certificate
//export fcProvisionWaitPost
func fcProvisionWaitPost(){<-testPostEntered}
//export fcProvisionFixture
func fcProvisionFixture()*C.char{
 locator,anchor,identity:=diagnosticFixture(&diagnosticTest{});fixtureIdentity=identity
 raw,_:=json.Marshal(map[string][]byte{"locator":locator,"anchor":anchor});return C.CString(string(raw))
}
func diagnosticConnector(network *underlay.Network,resolver string)bootstrap.SeedConnector{
 return func(lifetime,ready context.Context,_ roombroker.Room)(familysession.PacketEndpoint,error){
  switch resolver {
  case "127.0.0.2:53": _,err:=network.Dial("udp4","127.0.0.1:53");return nil,err
  case "127.0.0.3:53": return nil,io.EOF
  case "127.0.0.6:53": <-lifetime.Done();return nil,io.EOF
  }
  identity:=fixtureIdentity
  if resolver=="127.0.0.4:53" {_,_,identity=diagnosticFixture(&diagnosticTest{})}
  forward,reverse:=make(chan []byte,64),make(chan []byte,64)
  client,server:=&diagnosticEndpoint{reverse,forward,lifetime},&diagnosticEndpoint{forward,reverse,lifetime}
  go bootstrap.ServeCarrier(lifetime,server,func(ctx context.Context,endpoint familysession.PacketEndpoint){
   connection,err:=familysession.ReliableConnection(ctx,endpoint);if err!=nil{return};defer connection.Close()
   secured:=tls.Server(connection,&tls.Config{Certificates:[]tls.Certificate{identity},MinVersion:tls.VersionTLS13,NextProtos:[]string{coldprovision.Protocol}})
   if secured.HandshakeContext(ctx)!=nil{return}
   var header [4]byte
   if _,err:=io.ReadFull(secured,header[:]);err==nil{body:=make([]byte,binary.BigEndian.Uint32(header[:]));if _,err:=io.ReadFull(secured,body);err==nil{secured.CloseWrite();<-ctx.Done()}}
  })
  return client,nil
 }
}
func main(){}
''')
    (output / 'go.mod').write_text('module provisioningjnitest\n\ngo 1.26.0\nrequire github.com/Joker20380/family_connect/carrier v0.0.0\nreplace github.com/Joker20380/family_connect/carrier => ' + str(root / 'carrier') + '\n')
    (output / 'go.sum').write_bytes((root / 'carrier/go.sum').read_bytes())
    (output / 'NativeRestricted.java').write_bytes(Path(__file__).with_name('native_diagnostic') .joinpath('NativeRestricted.java').read_bytes())
    gson = next((tools / 'gradle-home/caches').rglob('gson-2.13.2.jar'))
    environment = os.environ | {'GOMAXPROCS':'2','GOCACHE':str(tools/'go-cache'),'GOMODCACHE':str(tools/'go-mod'),'GOPROXY':'off','GOTOOLCHAIN':'local','CGO_ENABLED':'1','CGO_CFLAGS':f'-I{tools}/jdk/include -I{tools}/jdk/include/linux'}
    commands = [[str(tools/'go1260/go/bin/go'),'build','-mod=mod','-buildmode=c-shared','-o',str(output/'libprovision_test.so'),'.'],
                [str(tools/'jdk/bin/javac'),'-cp',str(gson),'-d',str(output),str(output/'NativeRestricted.java')],
                [str(tools/'jdk/bin/java'),'-Xcheck:jni','-XX:ActiveProcessorCount=2','-cp',str(output)+os.pathsep+str(gson),'com.familyconnect.app.NativeRestricted',str(output/'libprovision_test.so')]]
    receipt={'provider_requests':0,'platform':'host JVM JNI, not Android','seams':['local connector only','Post-entered synchronization'], 'inputs':{name:hashlib.sha256((native/name).read_bytes()).hexdigest() for name in ('provision.go','provision_bridge.c','provision_lease.go')},'checks':[]}
    for index,command in enumerate(commands):
        log=output/f'check-{index}.log'
        with log.open('xb') as stream:
            result=subprocess.run(command,cwd=output,env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=180)
        receipt['checks'].append({'exit':result.returncode,'log':log.name,'sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
        (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(log.name,result.returncode,flush=True)
        if result.returncode:raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
