package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.net.ConnectException;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.Test;
import static org.junit.Assert.*;

public class MobileBootstrapTest {
    private final AtomicLong clock=new AtomicLong(1500);
    private final ReadinessProductTest.Memory storage=new ReadinessProductTest.Memory();
    private final RestrictedCache cache=RestrictedCache.detailed(storage,raw->ReadinessImportResult.Code.READY);
    private final ReadinessProduct product=new ReadinessProduct(cache,new ReadinessProductTest.Memory(),"test",96,clock::get);
    private byte[] saved()throws Exception{
        byte[] response=ReadinessProductTest.response(1000,2000);
        cache.importProduct(response,new OwnerPrewarmReceipt(),clock.get());return response;
    }
    private RestrictedBootstrap.Selection exchange(Exception relay)throws Exception{
        try(ControlIdentity identity=ControlIdentity.restore(new byte[96])){
            OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
            ReadinessBootstrapRoute route=new ReadinessBootstrapRoute((path,body,id)->{throw new ConnectException();},(path,body,id)->{throw relay;});
            return RestrictedBootstrap.refresh(cache,product,receipt,()->FriendsReadinessProtocol.fetch(route::post,identity,receipt),this,clock::get);
        }
    }
    @Test public void oldPythonExceptionLostAvailabilityButTypedBridgeKeepsValidCache()throws Exception{
        byte[] response=saved();
        assertNull(exchange(new RuntimeException("synthetic Python socket refusal")).response);
        RestrictedBootstrap.Selection fixed=exchange(new FriendsReadinessProtocol.Unavailable());
        assertEquals("CACHED_VALID_REFRESH_UNAVAILABLE",fixed.status);
        assertArrayEquals(response,RestrictedBootstrap.select(fixed.response,fixed.availabilityFailure,false));
        assertArrayEquals(response,cache.usable(clock.get()));
    }
    @Test public void typedAvailabilityNeverRevivesMissingExpiredOrDenied()throws Exception{
        assertNull(exchange(new FriendsReadinessProtocol.Unavailable()).response);
        saved();clock.set(2000);assertNull(exchange(new FriendsReadinessProtocol.Unavailable()).response);
        clock.set(1500);cache.denied();assertNull(exchange(new FriendsReadinessProtocol.Unavailable()).response);
    }
    @Test public void trustProtocolAndAuthorizationDoNotBecomeAvailability()throws Exception{
        saved();
        for(Exception failure:new Exception[]{new javax.net.ssl.SSLHandshakeException("secret"),new IllegalArgumentException("secret"),new FriendsReadinessProtocol.ChallengeFailure(FriendsReadinessProtocol.ChallengeCode.CHALLENGE_UNAUTHORIZED)})
            assertNull(exchange(failure).response);
        assertNull(exchange(new FriendsReadinessProtocol.Unavailable()).response);
    }
    @Test public void restartAndApiRecoveryRetainFloorAndReplaceOnlyValidSnapshot()throws Exception{
        byte[] response=saved();
        assertArrayEquals(response,exchange(new FriendsReadinessProtocol.Unavailable()).response);
        RestrictedCache restarted=RestrictedCache.detailed(storage,raw->ReadinessImportResult.Code.READY);
        assertArrayEquals(response,restarted.usable(clock.get()));
        assertEquals(ReadinessImportResult.Code.READY,product.restart(clock.get()).code());
        byte[] next=ReadinessProductTest.response(1200,2400);
        assertEquals(ReadinessImportResult.Code.READY,product.imported(next,new OwnerPrewarmReceipt(),clock.get()).code());
        assertArrayEquals(next,restarted.usable(clock.get()));
        assertEquals(ReadinessImportResult.Code.STALE_STATE,product.imported(response,new OwnerPrewarmReceipt(),clock.get()).code());
        assertArrayEquals(next,restarted.usable(clock.get()));
    }
    @Test public void exportPreservesStagesCacheAndOriginalConnectionWithoutSecrets()throws Exception{
        saved();DiagnosticRing ring=new DiagnosticRing("FC-ZMVK-MM7C","test",96,34);
        ReadinessFetchTrace trace=new ReadinessFetchTrace(new OwnerPrewarmReceipt(),"older-connection",1000);
        trace.request("/friends/restricted-readiness/challenge",ReadinessFetchTrace.Route.HTTPS_UNDERLAY);
        trace.network("CELLULAR",42);trace.stage(ReadinessFetchTrace.Stage.CONNECT_TLS_WRITE);
        trace.failed(new ConnectException("SECRET_TOKEN https://ROOM.invalid PROOF"));
        trace.request("/friends/restricted-readiness/challenge",ReadinessFetchTrace.Route.RNS);
        trace.stage(ReadinessFetchTrace.Stage.RELAY_OPEN);trace.failed(new FriendsReadinessProtocol.Unavailable());
        trace.cache(cache.diagnostic(clock.get()));trace.complete(ReadinessImportResult.Code.FETCH_FAILED,true,false,1400);
        ring.readinessFetch(trace);
        JsonObject bundle=new JsonObject();
        DiagnosticRing.exportRecord(bundle,"incident",ring.snapshot().toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),"FC-ZMVK-MM7C");
        String encoded=new String(DiagnosticRing.exportBytes(bundle),java.nio.charset.StandardCharsets.UTF_8);
        assertFalse(encoded.contains("SECRET_TOKEN"));assertFalse(encoded.contains("ROOM.invalid"));assertFalse(encoded.contains("PROOF"));
        JsonObject evidence=bundle.getAsJsonObject("incident").getAsJsonObject("readiness_fetch");
        assertTrue(evidence.get("connection_changed").getAsBoolean());
        assertEquals("CACHE",evidence.get("selected_source").getAsString());
        assertEquals("READY",evidence.getAsJsonObject("cache").get("validation").getAsString());
        assertEquals(2,evidence.getAsJsonArray("failures").size());
        assertEquals(42,evidence.get("network_generation").getAsInt());
    }
    @Test public void traceBoundAndClassifierFailClosed(){
        ReadinessFetchTrace trace=new ReadinessFetchTrace(new OwnerPrewarmReceipt(),"",0);
        for(int count=0;count<100;count++)trace.failed(new java.io.IOException("secret"));
        assertEquals(4,trace.json().getAsJsonArray("failures").size());
        assertEquals(ReadinessFetchTrace.Error.TLS,ReadinessFetchTrace.classify(new javax.net.ssl.SSLException("synthetic")));
        assertEquals(ReadinessFetchTrace.Error.DNS,ReadinessFetchTrace.classify(new java.net.UnknownHostException()));
    }
}
