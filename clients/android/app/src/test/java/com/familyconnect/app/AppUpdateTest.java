package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public class AppUpdateTest {
    private final byte[] apk=new byte[2048];
    private String manifest()throws Exception{return "{\"schema\":1,\"package\":\"com.familyconnect.app.friends\",\"abi\":\"arm64-v8a\",\"version_code\":27,\"version\":\"0.1.18-beta27\",\"size\":2048,\"sha256\":\""+AppUpdate.hex(MessageDigest.getInstance("SHA-256").digest(apk))+"\",\"url\":\""+AppUpdate.BASE+"/downloads/FamilyConnect-Test-0.1.18-beta27.apk\"}";}
    private AppUpdate parse(String s){return AppUpdate.parse(s.getBytes(StandardCharsets.UTF_8));}
    private void rejects(String s){try{parse(s);fail("Accepted invalid metadata");}catch(RuntimeException expected){}}
    @Test public void acceptsVersionAndExactVerifiedBytes()throws Exception{AppUpdate u=parse(manifest());assertEquals(27,u.code);ByteArrayOutputStream out=new ByteArrayOutputStream();int[] progress={0};u.receive(new ByteArrayInputStream(apk),out,p->progress[0]=p);assertArrayEquals(apk,out.toByteArray());assertEquals(100,progress[0]);}
    @Test public void rejectsForeignOriginsPackagesAndUnsafeSizes()throws Exception{String m=manifest();rejects(m.replace(AppUpdate.BASE,"https://example.com"));rejects(m.replace("https:","http:"));rejects(m.replace("app.friends","app.foreign"));rejects(m.replace("2048","150000001"));rejects(m.replace("2048","2048.0"));rejects(m.replace("arm64-v8a","x86"));rejects(m.replace("beta27.apk","beta28.apk"));rejects(m.replace("\"version_code\":27","\"version_code\":\"27\""));}
    @Test public void rejectsTruncatedOversizedAndCorruptDownloads()throws Exception{AppUpdate u=parse(manifest());for(byte[] bad:new byte[][]{new byte[2047],new byte[2049],apk.clone()}){if(bad.length==2048)bad[0]=1;try{u.receive(new ByteArrayInputStream(bad),new ByteArrayOutputStream(),p->{});fail("Bad APK accepted");}catch(IOException expected){}}}
    @Test public void cancellationStopsDownload()throws Exception{try{parse(manifest()).receive(new ByteArrayInputStream(apk),new ByteArrayOutputStream(),p->{throw new InterruptedIOException();});fail();}catch(InterruptedIOException expected){}}
}
