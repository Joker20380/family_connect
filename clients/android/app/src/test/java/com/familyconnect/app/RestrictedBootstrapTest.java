package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedBootstrapTest {
    private final AtomicLong clock=new AtomicLong(1500);
    private final ReadinessProductTest.Memory vault=new ReadinessProductTest.Memory();
    private final RestrictedCache cache=RestrictedCache.detailed(vault,raw->
        ControlJson.parse(raw).getAsJsonObject().has("invalid")?ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED:ReadinessImportResult.Code.READY);
    private final ReadinessProduct product=new ReadinessProduct(cache,new ReadinessProductTest.Memory(),"test",82,clock::get);
    private final Object lock=new Object();
    private int requestCount;
    private RestrictedBootstrap.Selection run(RestrictedBootstrap.Fetch fetch)throws Exception{
        OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
        return RestrictedBootstrap.refresh(cache,product,receipt,()->{
            byte[] response=fetch.run();receipt.challengeIssued();receipt.fetchAuthorized();return response;
        },lock,clock::get);
    }
    private byte[] response(long issued,long expiry)throws Exception{
        JsonObject value=ControlJson.parse(ReadinessProductTest.response(issued,expiry)).getAsJsonObject();
        value.addProperty("challenge","fixture-"+issued);return value.toString().getBytes(StandardCharsets.UTF_8);
    }
    private void provision(byte[] response)throws Exception{
        assertEquals("SUCCESS",run(()->http(response)).status);
    }
    private byte[] http(byte[] response)throws Exception{
        try(ServerSocket listener=new ServerSocket(0,1,InetAddress.getLoopbackAddress())){
            Thread server=new Thread(()->{
                try(Socket accepted=listener.accept()){
                    accepted.setSoTimeout(2000);
                    java.io.BufferedReader input=new java.io.BufferedReader(new java.io.InputStreamReader(accepted.getInputStream(),StandardCharsets.US_ASCII));
                    String line;while((line=input.readLine())!=null&&!line.isEmpty()){}
                    byte[] header=("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "+response.length+"\r\nConnection: close\r\n\r\n").getBytes(StandardCharsets.US_ASCII);
                    accepted.getOutputStream().write(header);accepted.getOutputStream().write(response);requestCount++;
                }catch(IOException failure){throw new AssertionError(failure);}
            },"provisioning-fixture");
            server.start();
            java.net.HttpURLConnection connection=(java.net.HttpURLConnection)new java.net.URL("http://127.0.0.1:"+listener.getLocalPort()+"/").openConnection();
            connection.setConnectTimeout(1000);connection.setReadTimeout(1000);
            try{return connection.getInputStream().readAllBytes();}
            finally{connection.disconnect();server.join(3000);assertFalse(server.isAlive());}
        }
    }
    private byte[] refused()throws Exception{
        int port;
        try(ServerSocket listener=new ServerSocket(0,1,InetAddress.getLoopbackAddress())){port=listener.getLocalPort();}
        try(Socket connection=new Socket()){
            connection.connect(new java.net.InetSocketAddress("127.0.0.1",port),1000);
            throw new AssertionError("controlled provisioning port unexpectedly reachable");
        }
    }
    @Test public void availableRefreshUsesBNotAAndLaterRecoveryUpgrades()throws Exception{
        byte[] first=response(1000,2000),second=response(1200,2200),third=response(1400,2400);
        provision(first);
        assertArrayEquals(second,run(()->http(second)).response);
        assertArrayEquals(second,run(this::refused).response);
        assertArrayEquals(third,run(()->http(third)).response);
        assertEquals(3,requestCount);
    }
    @Test public void unavailableRefreshSelectsExactValidatedCache()throws Exception{
        byte[] first=response(1000,2000);provision(first);
        RestrictedBootstrap.Selection selected=run(this::refused);
        assertEquals("CACHED_VALID_REFRESH_UNAVAILABLE",selected.status);
        assertArrayEquals(first,selected.response);
        assertEquals(ReadinessImportResult.Code.FETCH_FAILED,selected.result.code());
        assertEquals(1,requestCount);
    }
    @Test public void expiredEmptyRevokedAndInvalidCacheFailClosed()throws Exception{
        assertNull(run(this::refused).response);
        provision(response(1000,2000));clock.set(2000);
        assertNull(run(this::refused).response);clock.set(1500);
        cache.denied();assertNull(run(this::refused).response);
        provision(response(1100,2100));
        JsonObject state=ControlJson.parse(vault.read()).getAsJsonObject();state.getAsJsonObject("response").addProperty("invalid",true);
        vault.write(state.toString().getBytes(StandardCharsets.UTF_8));
        assertNull(run(this::refused).response);
    }
    @Test public void unavailableApiWithoutUsableCacheRemainsTemporaryButCannotUseExpiredBytes()throws Exception{
        RestrictedBootstrap.Selection empty=run(this::refused);
        assertNull(empty.response);assertTrue(empty.availabilityFailure);
        try{RestrictedBootstrap.select(empty.response,empty.availabilityFailure,true);fail();}
        catch(ConnectivityOrchestrator.Rejected expected){assertTrue(expected.temporaryBootstrap);}
        provision(response(1000,2000));clock.set(2000);
        RestrictedBootstrap.Selection expired=run(this::refused);assertNull(expired.response);assertTrue(expired.availabilityFailure);
        assertNotNull(run(()->http(response(2000,3000))).response);
    }
    @Test public void authTrustProtocolAndImportFailuresNeverFallBack()throws Exception{
        provision(response(1000,2000));
        for(Exception failure:Arrays.asList(new javax.net.ssl.SSLHandshakeException("trust"),new IOException("invalid body"),new IllegalArgumentException("binding"),
            new FriendsReadinessProtocol.ChallengeFailure(FriendsReadinessProtocol.ChallengeCode.CHALLENGE_INCOMPATIBLE_RESPONSE))){
            assertNull(run(()->{throw failure;}).response);
        }
        byte[] bad=response(1200,2200);JsonObject invalid=ControlJson.parse(bad).getAsJsonObject();invalid.addProperty("invalid",true);
        assertNull(run(()->http(invalid.toString().getBytes(StandardCharsets.UTF_8))).response);
        RestrictedBootstrap.Selection rejected=run(()->{throw new FriendsReadinessProtocol.AuthorizationFailure();});
        assertTrue(rejected.authorizationRejected);assertNull(rejected.response);assertNull(run(this::refused).response);
    }
    @Test public void lateARejectedAndTimeoutCannotResurrectExpiredPermission()throws Exception{
        byte[] second=response(1200,2200);provision(second);
        RestrictedBootstrap.Selection stale=run(()->http(response(1000,2000)));
        assertEquals(ReadinessImportResult.Code.STALE_STATE,stale.result.code());assertNull(stale.response);
        assertArrayEquals(second,cache.usable());
        assertNull(run(()->{clock.set(2200);throw new SocketTimeoutException();}).response);
    }
    @Test public void challengeTlsFailureNotAvailability()throws Exception{
        try(ControlIdentity identity=ControlIdentity.restore(new byte[96])){
            try{FriendsReadinessProtocol.fetch((path,body,id)->{throw new javax.net.ssl.SSLHandshakeException("trust");},identity,new OwnerPrewarmReceipt());fail();}
            catch(FriendsReadinessProtocol.ChallengeFailure failure){assertFalse(RestrictedBootstrap.unavailable(failure));}
        }
    }
}
