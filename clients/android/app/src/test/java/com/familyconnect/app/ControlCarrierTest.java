package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.Assert.*;

public class ControlCarrierTest {
    static class Wire implements ControlCarrier.Wire {
        List<String> paths=new ArrayList<>();List<byte[]> acknowledgements=new ArrayList<>();boolean cancel,offline,badAck,badAudience;long expires=1120;
        public boolean cancelled(){return cancel;}
        public byte[] request(String path,byte[] raw)throws Exception {
            assertFalse(Thread.holdsLock(ControlJournal.OWNER));paths.add(path);if(offline)throw new IOException("offline");
            if(path.endsWith("challenge")){
                var r=new JsonObject();r.addProperty("challenge",Base64.getEncoder().encodeToString(new byte[32]));r.addProperty("expires_at",expires);
                r.addProperty("audience",badAudience?"family-connect/enrollment/v1":"family-connect/provisioning-fetch/v1");return ControlJson.canonical(r,false);
            }
            if(path.endsWith("fetch")){
                var proof=ControlJson.parse(raw).getAsJsonObject();assertFalse(proof.has("transport"));assertEquals("family-connect/provisioning-fetch/v1",proof.get("audience").getAsString());
                return ControlTransactionTest.resource("valid-wg.envelope");
            }
            acknowledgements.add(raw.clone());return (badAck?"OK":"ACK_STORED").getBytes(StandardCharsets.US_ASCII);
        }
    }
    @Test public void fetchProofMatchesIndependentPythonReference()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            var proof=h.identity.proveFetch(Base64.getEncoder().encodeToString(new byte[32]));
            assertEquals("08a5451782d64cf5b7f4fbc67dab6d97259561e09989e7faccd63ea8d6a23f9b",ControlProtocol.hash(ControlJson.canonical(proof,false)));
            assertNotEquals(h.identity.proveTransportKey(Base64.getEncoder().encodeToString(new byte[32])),proof);
            assertThrows(IllegalArgumentException.class,()->h.identity.proveFetch("bad"));
        }
    }
    @Test public void challengeFetchAndApplicationThenSignedAck()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Wire wire=new Wire();var carrier=new ControlCarrier(wire,h.identity,()->1000);
            var host=new ControlApplicationTest.Host();host.stop();var core=ControlApplicationTest.core(h,host);
            assertEquals("COMMITTED",ControlIntake.apply(core,h.identity,ControlIntakeTest.enrollment(h.identity),carrier.receive(),()->host.active!=null));
            assertTrue(core.flush(carrier));assertEquals(3,wire.acknowledgements.size());assertTrue(h.state().getAsJsonArray("outbox").isEmpty());
            assertEquals(List.of("/control/v1/challenge","/control/v1/fetch","/control/v1/ack","/control/v1/ack","/control/v1/ack"),wire.paths);
        }
    }
    @Test public void badChallengeDoesNotSendSignature()throws Exception {
        for(int mode=0;mode<3;mode++)try(var h=new ControlTransactionTest.Harness()){
            Wire wire=new Wire();if(mode==0)wire.badAudience=true;if(mode==1)wire.expires=1000;if(mode==2)wire.expires=1121;
            assertThrows(Exception.class,()->new ControlCarrier(wire,h.identity,()->1000).receive());assertEquals(1,wire.paths.size());
        }
    }
    @Test public void ackFailureKeepsExactBytesAndWorkingVpn()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Wire wire=new Wire();var carrier=new ControlCarrier(wire,h.identity,()->1000);var host=new ControlApplicationTest.Host();host.stop();var core=ControlApplicationTest.core(h,host);
            assertEquals("COMMITTED",core.receive(carrier.receive()));var before=h.state().get("outbox").deepCopy();String active=host.active;
            wire.badAck=true;assertFalse(core.flush(carrier));assertEquals(before,h.state().get("outbox"));assertEquals(active,host.active);
            wire.badAck=false;assertTrue(core.flush(carrier));assertArrayEquals(wire.acknowledgements.get(0),wire.acknowledgements.get(1));assertEquals(1,host.starts);
        }
    }
    @Test public void carrierOutageCannotTouchJournalOrEngine()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Wire wire=new Wire();var carrier=new ControlCarrier(wire,h.identity,()->1000);assertEquals("COMMITTED",h.core.receive(carrier.receive()));var before=h.state();
            wire.offline=true;assertThrows(IOException.class,carrier::receive);assertFalse(h.core.flush(carrier));assertEquals(before,h.state());assertEquals(1,h.app.applies);
        }
    }
    @Test public void cancelledCarrierSendsNothing()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Wire wire=new Wire();wire.cancel=true;assertThrows(IOException.class,()->new ControlCarrier(wire,h.identity,()->1000).receive());assertTrue(wire.paths.isEmpty());
        }
    }
    @Test public void oversizedReplyAndMalformedAckRefused()throws Exception {
        try(var h=new ControlTransactionTest.Harness()){
            Wire wire=new Wire(){public byte[] request(String path,byte[] raw){return new byte[65537];}};var carrier=new ControlCarrier(wire,h.identity,()->1000);
            assertThrows(IOException.class,carrier::receive);assertThrows(Exception.class,()->carrier.send("{}".getBytes(StandardCharsets.UTF_8)));
        }
    }
}
