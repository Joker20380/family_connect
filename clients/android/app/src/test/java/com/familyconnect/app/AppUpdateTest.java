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
    @Test public void checksSignedSdkBeforeOfferingDownload()throws Exception{
        AppUpdate legacy=parse(manifest());assertEquals(31,legacy.minSdk);assertFalse(legacy.supportsSdk(27));assertTrue(legacy.supportsSdk(31));
        AppUpdate compatible=parse(manifest().replace("\"schema\":1","\"schema\":1,\"min_sdk\":27"));
        assertFalse(compatible.supportsSdk(26));assertTrue(compatible.supportsSdk(27));assertTrue(compatible.supportsSdk(35));
        for(String invalid:new String[]{"null","true","\"27\"","27.0","25","-1","10001"})rejects(manifest().replace("\"schema\":1","\"schema\":1,\"min_sdk\":"+invalid));
    }
    @Test public void corruptOrTrailingDownloadsNeverReportComplete()throws Exception{
        for(byte[] bytes:new byte[][]{new byte[2048],new byte[2049]}){
            bytes[0]=1;int[] highest={0};
            try{parse(manifest()).receive(new ByteArrayInputStream(bytes),new ByteArrayOutputStream(),percent->highest[0]=Math.max(highest[0],percent));fail("Invalid download accepted");}catch(IOException expected){}
            assertTrue(highest[0]<100);
        }
    }
    @Test public void failureAfterExpectedBytesNeverReportsComplete()throws Exception{
        InputStream failing=new ByteArrayInputStream(apk){
            @Override public synchronized int read(byte[] buffer,int offset,int length){if(available()==0)throw new java.io.UncheckedIOException(new IOException("Synthetic disconnect"));return super.read(buffer,offset,length);}
        };
        int[] highest={0};
        try{parse(manifest()).receive(failing,new ByteArrayOutputStream(),percent->highest[0]=percent);fail("Failed transfer accepted");}catch(java.io.UncheckedIOException expected){}
        assertTrue(highest[0]<100);
    }
}
