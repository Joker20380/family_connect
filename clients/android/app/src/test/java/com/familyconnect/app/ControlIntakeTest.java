package com.familyconnect.app;

import java.io.*;
import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlIntakeTest {
    static JsonObject enrollment(ControlIdentity identity)throws Exception {
        JsonObject r=new JsonObject();r.addProperty("schema",1);r.addProperty("origin","https://enroll.example");r.addProperty("phase","ENROLLED");r.addProperty("device",identity.reference());r.add("proof",JsonNull.INSTANCE);return r;
    }
    static String apply(ControlTransactionTest.Harness h,ControlApplicationTest.Host host,byte[] raw)throws Exception {
        return ControlIntake.apply(ControlApplicationTest.core(h,host),h.identity,enrollment(h.identity),raw,()->host.active!=null);
    }
    @Test public void boundedReadPreservesBytesAndRejectsInvalidSizes()throws Exception {
        byte[] raw=new byte[65536];raw[31]=17;assertArrayEquals(raw,ControlIntake.read(new ByteArrayInputStream(raw)));
        assertThrows(IOException.class,()->ControlIntake.read(new ByteArrayInputStream(new byte[65537])));
        assertThrows(IOException.class,()->ControlIntake.read(new ByteArrayInputStream(new byte[0])));
        assertThrows(IOException.class,()->ControlIntake.read(null));assertThrows(IOException.class,()->ControlIntake.copy(null));
        byte[] copy=ControlIntake.copy(raw);raw[31]=18;assertEquals(17,copy[31]);
    }
    @Test public void unreadableOrNonprogressingProviderCannotReturnPartialEnvelope() {
        assertThrows(IOException.class,()->ControlIntake.read(new InputStream(){public int read()throws IOException{throw new IOException("provider");}}));
        assertThrows(IOException.class,()->ControlIntake.read(new InputStream(){public int read(){return 0;}public int read(byte[] b){return 0;}}));
    }
    @Test public void interruptedReadIsCancelled() {
        Thread.currentThread().interrupt();
        try{assertThrows(InterruptedIOException.class,()->ControlIntake.read(new ByteArrayInputStream(new byte[]{1})));}
        finally{Thread.interrupted();}
    }
    @Test public void validSignedFileReachesTransactionAndCommitsWithAck()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            var host=new ControlApplicationTest.Host();host.stop();
            byte[] raw=ControlIntake.read(new ByteArrayInputStream(ControlTransactionTest.resource("valid-wg.envelope")));
            assertEquals("COMMITTED",apply(h,host,raw));assertEquals(1,host.starts);assertEquals("wg",host.active);
            assertEquals(3,h.state().getAsJsonArray("outbox").size());assertEquals(1,h.state().get("floor").getAsLong());
        }
    }
    @Test public void plaintextAndWrongEnvelopeDoNotChangeProfiles()throws Exception {
        for(byte[] raw:new byte[][]{"[Interface]\nPrivateKey=unsafe".getBytes(java.nio.charset.StandardCharsets.UTF_8),"{\"schema_version\":1}".getBytes(java.nio.charset.StandardCharsets.UTF_8)})
            try(var h=new ControlTransactionTest.Harness()){
                var host=new ControlApplicationTest.Host();host.stop();var before=host.profiles.deepCopy();
                assertEquals("REJECTED",apply(h,host,raw));assertEquals(before,host.profiles);assertEquals(0,host.starts);assertEquals(0,host.saves);
            }
    }
    @Test public void unfinishedOrForeignEnrollmentCannotEnterTransaction()throws Exception {
        for(int scenario=0;scenario<3;scenario++)try(var h=new ControlTransactionTest.Harness()){
            var host=new ControlApplicationTest.Host();host.stop();var r=enrollment(h.identity);
            if(scenario==0)r.addProperty("phase","READY");if(scenario==1)r.addProperty("device","0".repeat(32));if(scenario==2)r.addProperty("origin","http://enroll.example");
            assertThrows(Exception.class,()->ControlIntake.apply(ControlApplicationTest.core(h,host),h.identity,r,ControlTransactionTest.resource("valid-wg.envelope"),()->false));
            assertEquals(0,h.state().get("floor").getAsLong());assertEquals(0,h.state().getAsJsonArray("outbox").size());assertEquals(0,host.saves);
        }
    }
    @Test public void duplicateCommittedFileResumesWithoutRewritingProfiles()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            var host=new ControlApplicationTest.Host();host.stop();byte[] raw=ControlTransactionTest.resource("valid-wg.envelope");
            assertEquals("COMMITTED",apply(h,host,raw));int saves=host.saves;var before=h.state().get("committed").deepCopy();
            host.stop();h.restart();assertEquals("COMMITTED",apply(h,host,raw));assertEquals(2,host.starts);assertEquals(saves,host.saves);
            assertEquals(before,h.state().get("committed"));assertEquals(3,h.state().getAsJsonArray("outbox").size());
            assertEquals("COMMITTED",apply(h,host,raw));assertEquals(2,host.starts);
        }
    }
    @Test public void duplicateResumeStillRequiresHealthyTraffic()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            var host=new ControlApplicationTest.Host();host.stop();byte[] raw=ControlTransactionTest.resource("valid-wg.envelope");
            apply(h,host,raw);host.stop();host.good=false;assertThrows(IOException.class,()->apply(h,host,raw));assertNull(host.active);assertEquals(2,host.starts);
        }
    }
    @Test public void pendingCrashRecoversBeforeAnyNewApplication()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            var host=new ControlApplicationTest.Host();host.stop();var before=host.profiles.deepCopy();h.store.failAt=4;
            byte[] raw=ControlTransactionTest.resource("valid-wg.envelope");
            assertThrows(ControlTransactionTest.Death.class,()->apply(h,host,raw));h.store.failAt=-1;host.stop();h.restart();
            assertEquals("ROLLED_BACK",apply(h,host,raw));assertEquals(before,host.profiles);assertNull(host.active);assertEquals(1,host.starts);
        }
    }
    @Test public void expiryAndCancellationCannotConnect()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            var host=new ControlApplicationTest.Host();host.stop();h.clock[0]=4600;
            assertEquals("REJECTED",apply(h,host,ControlTransactionTest.resource("valid-wg.envelope")));assertEquals(0,host.starts);
        }
        try(var h=new ControlTransactionTest.Harness()){
            var host=new ControlApplicationTest.Host();host.stop();host.cancelled=true;
            assertEquals("ROLLED_BACK",apply(h,host,ControlTransactionTest.resource("valid-wg.envelope")));assertEquals(0,host.starts);
        }
    }
}
