package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.util.*;
import javax.crypto.KeyGenerator;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlEnrollmentTest {
    static final String SERVER="https://enroll.example",TOKEN="a".repeat(64);
    static class Local implements ControlEnrollment.Local,AutoCloseable {
        JsonObject record;byte[] material;int creates,prepares,saves;boolean other,failPrepare,failFinal;final ControlTransactionTest.Harness h;
        Local()throws Exception{h=new ControlTransactionTest.Harness();material=h.identity.material();}
        public boolean present(){return record!=null;}
        public boolean otherState(){return other;}
        public JsonObject read(){return record.deepCopy();}
        public void create(JsonObject r){creates++;record=r.deepCopy();}
        public void save(JsonObject r)throws Exception{if(failFinal&&r.get("phase").getAsString().equals("ENROLLED"))throw new IOException("disk");saves++;record=r.deepCopy();}
        public ControlIdentity prepare(boolean init)throws Exception {prepares++;if(failPrepare)throw new IOException("orphan key");return ControlIdentity.restore(material);}
        public void close(){Arrays.fill(material,(byte)0);h.close();}
    }
    static class Remote implements ControlEnrollment.Remote {
        final Local local;int challenges,completions,checks;boolean registered,loseReply,cancelled,badAudience,wrongDevice,denyStatus;
        Remote(Local local){this.local=local;}
        public boolean cancelled(){return cancelled;}
        public JsonObject post(String origin,String path,JsonObject body)throws Exception {
            assertEquals(SERVER,origin);
            // Enrollment holds an operation lease but never the monitor across network waits.
            assertFalse(Thread.holdsLock(ControlJournal.OWNER));
            assertThrows(IOException.class,()->ControlOperations.APP.edit(()->{},()->fail("Concurrent import")));
            if(path.equals("/v2/registration/complete")){
                completions++;if(registered)throw new IOException("proof already consumed");try(var identity=ControlIdentity.restore(local.material)){
                    assertEquals(identity.proveTransportKey(body.get("challenge").getAsString()),body);
                    registered=true;if(loseReply)throw new IOException("reply lost");
                    JsonObject result=new JsonObject();result.addProperty("device_identity",wrongDevice?"0".repeat(32):identity.reference());
                    result.addProperty("entitlement_id","b".repeat(32));result.addProperty("entitlement_revision",1);result.addProperty("status","enrolled");return result;
                }
            }
            boolean status=path.equals("/v2/provisioning/challenge");
            if(status){checks++;if(!registered||denyStatus)throw new IOException("unconfirmed");assertFalse(body.has("invitation_token"));}
            else {challenges++;assertEquals(TOKEN,body.get("invitation_token").getAsString());}
            JsonObject result=new JsonObject();result.addProperty("challenge",Base64.getEncoder().encodeToString(new byte[32]));result.addProperty("expires_at",1120);
            result.addProperty("audience",badAudience?"wrong":status?"family-connect/provisioning-fetch/v1":"family-connect/enrollment/v1");return result;
        }
    }
    static ControlEnrollment core(Local l,Remote r){return new ControlEnrollment(l,r,()->1000);}
    @Test public void explicitRegistrationBindsIdentityAndKeepsInvitationOutOfState()throws Exception{
        try(Local l=new Local()){
            Remote r=new Remote(l);String device=core(l,r).enroll(SERVER,TOKEN);
            assertEquals(l.h.identity.reference(),device);assertEquals("ENROLLED",l.record.get("phase").getAsString());
            assertFalse(l.record.toString().contains(TOKEN));assertTrue(l.record.get("proof").isJsonNull());assertEquals(1,l.creates);assertEquals(1,r.completions);
            assertEquals(device,core(l,r).enroll(SERVER,null));assertEquals(1,r.completions);
            ControlOperations.APP.requireIdle();
        }
    }
    @Test public void lostReplyReconcilesSameIdentityWithoutSecondEnrollment()throws Exception{
        try(Local l=new Local()){
            Remote r=new Remote(l);r.loseReply=true;
            assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));assertEquals("COMPLETING",l.record.get("phase").getAsString());
            String device=core(l,r).enroll(SERVER,null);assertEquals(l.h.identity.reference(),device);
            assertEquals(1,r.challenges);assertEquals(2,r.completions);assertEquals(1,r.checks);assertEquals(1,l.creates);
        }
    }
    @Test public void unconfirmedCompletionNeverConsumesAnotherInvitation()throws Exception{
        try(Local l=new Local()){
            Remote r=new Remote(l);r.loseReply=true;assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));r.denyStatus=true;
            assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));assertEquals(2,r.completions);assertEquals(1,r.challenges);
            assertEquals("COMPLETING",l.record.get("phase").getAsString());
        }
    }
    @Test public void crashBeforeSendingCompleteRetriesExactProof()throws Exception {
        try(Local l=new Local()){
            Remote r=new Remote(l);r.loseReply=true;assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));
            // Model durable intent followed by process death before server received it.
            r.registered=false;r.loseReply=false;JsonObject proof=l.record.getAsJsonObject("proof").deepCopy();
            assertEquals(l.h.identity.reference(),core(l,r).enroll(SERVER,null));
            assertEquals(1,r.challenges);assertEquals(2,r.completions);assertEquals(0,r.checks);
            assertEquals(l.h.identity.proveTransportKey(proof.get("challenge").getAsString()),proof);
        }
    }
    @Test public void finalPersistenceFailureCanReconcile()throws Exception{
        try(Local l=new Local()){
            Remote r=new Remote(l);l.failFinal=true;assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));
            l.failFinal=false;assertEquals(l.h.identity.reference(),core(l,r).enroll(SERVER,null));assertEquals(2,r.completions);
        }
    }
    @Test public void interruptedPreparationKeepsIdentityAndOrigin()throws Exception{
        try(Local l=new Local()){
            Remote r=new Remote(l);l.failPrepare=true;assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));
            assertEquals("INITIALIZING",l.record.get("phase").getAsString());assertEquals(0,r.challenges);
            assertThrows(IllegalArgumentException.class,()->core(l,r).enroll("https://other.example",TOKEN));
            l.failPrepare=false;core(l,r).enroll(SERVER,TOKEN);assertEquals(1,l.creates);
        }
    }
    @Test public void legacyManagedStateCannotBeAdoptedOrReset()throws Exception{
        try(Local l=new Local()){
            l.other=true;Remote r=new Remote(l);assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));assertNull(l.record);assertEquals(0,l.prepares);
        }
    }
    @Test public void invalidInputCannotCreateIdentity()throws Exception{
        for(String url:new String[]{"http://enroll.example","https://user@enroll.example","https://enroll.example/path","https://enroll.example?token=x","https://enroll.example#x"})
            try(Local l=new Local()){Remote r=new Remote(l);assertThrows(Exception.class,()->core(l,r).enroll(url,TOKEN));assertEquals(0,l.creates);}
        try(Local l=new Local()){Remote r=new Remote(l);assertThrows(IllegalArgumentException.class,()->core(l,r).enroll(SERVER,"bad"));assertEquals(0,l.creates);}
        assertEquals(SERVER,ControlEnrollment.origin("https://ENROLL.example:443/"));
    }
    @Test public void badChallengeDoesNotSendProofAndCanRetry()throws Exception{
        try(Local l=new Local()){
            Remote r=new Remote(l);r.badAudience=true;assertThrows(IllegalArgumentException.class,()->core(l,r).enroll(SERVER,TOKEN));
            assertEquals(0,r.completions);assertEquals("READY",l.record.get("phase").getAsString());r.badAudience=false;core(l,r).enroll(SERVER,TOKEN);assertEquals(1,l.creates);
        }
    }
    @Test public void wrongReceiptCannotConfirmAnotherIdentity()throws Exception{
        try(Local l=new Local()){
            Remote r=new Remote(l);r.wrongDevice=true;assertThrows(IllegalArgumentException.class,()->core(l,r).enroll(SERVER,TOKEN));assertEquals("COMPLETING",l.record.get("phase").getAsString());
        }
    }
    @Test public void cancellationAndActiveVpnBlockRegistration()throws Exception{
        try(Local l=new Local()){
            Remote r=new Remote(l);r.cancelled=true;assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));assertEquals(0,l.creates);
            r.cancelled=false;Object owner=new Object();ControlOperations.APP.claim(owner);
            try{assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));assertEquals(0,l.creates);}finally{ControlOperations.APP.release(owner);}
        }
    }
    @Test public void corruptPendingProofCannotQueryOrRegenerate()throws Exception{
        try(Local l=new Local()){
            Remote r=new Remote(l);r.loseReply=true;assertThrows(IOException.class,()->core(l,r).enroll(SERVER,TOKEN));
            l.record.getAsJsonObject("proof").addProperty("wireguard_public_key",Base64.getEncoder().encodeToString(new byte[32]));
            assertThrows(IllegalArgumentException.class,()->core(l,r).enroll(SERVER,TOKEN));assertEquals(0,r.checks);assertEquals(1,l.creates);
        }
    }
    @Test public void enrollmentEnvelopeHasIndependentDomainAndBounds()throws Exception{
        var generator=KeyGenerator.getInstance("AES");generator.init(256);var key=generator.generateKey();byte[] raw="{\"public\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        byte[] encrypted=ControlEnrollmentEnvelope.seal(key,raw);assertArrayEquals(raw,ControlEnrollmentEnvelope.open(key,encrypted));
        assertThrows(Exception.class,()->ControlJournalEnvelope.open(key,encrypted));encrypted[15]^=1;assertThrows(Exception.class,()->ControlEnrollmentEnvelope.open(key,encrypted));
        assertThrows(Exception.class,()->ControlEnrollmentEnvelope.seal(key,new byte[16385]));
    }
    @Test public void enrollmentMarkersAndOrphanAliasBlockLegacy()throws Exception{
        var dir=java.nio.file.Files.createTempDirectory("enrollment-presence-");
        try{
            for(String suffix:new String[]{"",".bak",".new"}){
                var marker=dir.resolve("control-enrollment.enc"+suffix);java.nio.file.Files.write(marker,new byte[0]);
                try{assertThrows(IOException.class,()->ControlStatePresence.requireUnmanaged(dir.toFile(),alias->false));}finally{java.nio.file.Files.delete(marker);}
            }
            assertThrows(IOException.class,()->ControlStatePresence.requireUnmanaged(dir.toFile(),"family-connect-control-enrollment-v1"::equals));
        }finally{java.nio.file.Files.delete(dir);}
    }
}
