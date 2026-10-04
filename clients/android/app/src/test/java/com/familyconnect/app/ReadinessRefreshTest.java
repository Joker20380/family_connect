package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import org.junit.Test;
import static org.junit.Assert.*;

public class ReadinessRefreshTest {
    @Test public void failedEarlyFetchKeepsUsableCacheAndPersistentBackoff()throws Exception{
        long now=System.currentTimeMillis()/1000;
        ReadinessProductTest.Memory vault=new ReadinessProductTest.Memory();
        RestrictedCache cache=ReadinessProductTest.cache(vault);
        byte[] saved=ReadinessProductTest.response(now-600,now+14400);cache.accept(saved);
        assertTrue(cache.attempt(now));
        int[] requests={0};OwnerPrewarmReceipt attempt=new OwnerPrewarmReceipt();
        try(ControlIdentity identity=ControlIdentity.restore(new byte[96])){
            try{
                FriendsReadinessProtocol.fetch((path,body,id)->{requests[0]++;throw new java.net.SocketTimeoutException();},identity,attempt);
                fail("fetch should fail");
            }catch(FriendsReadinessProtocol.ChallengeFailure expected){
                assertEquals(FriendsReadinessProtocol.ChallengeCode.CHALLENGE_TIMEOUT,expected.code);
            }
        }
        assertEquals(1,requests[0]);assertArrayEquals(saved,ReadinessProductTest.cache(vault).usable());
        assertFalse(ReadinessProductTest.cache(vault).attempt(now+299));
        assertTrue(ReadinessProductTest.cache(vault).attempt(now+300));
    }
    @Test public void rejectedEarlyImportKeepsOldBundleAndCannotAckReady()throws Exception{
        long now=System.currentTimeMillis()/1000;
        for(ReadinessImportResult.Code failure:new ReadinessImportResult.Code[]{ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED,ReadinessImportResult.Code.BOOTSTRAP_VALIDATION_FAILED}){
            ReadinessProductTest.Memory vault=new ReadinessProductTest.Memory(),receipts=new ReadinessProductTest.Memory();
            byte[] saved=ReadinessProductTest.response(now-600,now+14400);ReadinessProductTest.cache(vault).accept(saved);
            RestrictedCache cache=RestrictedCache.detailed(vault,raw->Arrays.equals(raw,saved)?ReadinessImportResult.Code.READY:failure);
            assertTrue(cache.attempt(now));
            ReadinessProduct product=ReadinessProductTest.product(cache,receipts);
            ReadinessImportResult result=product.imported(ReadinessProductTest.response(now,now+14400),new OwnerPrewarmReceipt(),now);
            assertEquals(failure,result.code());
            product.publish(result,payload->{assertEquals(failure.name(),payload.get("result").getAsString());assertFalse(payload.get("orchestrator_usable").getAsBoolean());});
            assertArrayEquals(saved,cache.usable());assertFalse(cache.attempt(now+1));
        }
    }
    @Test public void savedLongCacheUsesScheduledAuthenticatedFetchImportAndAck()throws Exception{
        long now=System.currentTimeMillis()/1000;
        ReadinessProductTest.Memory vault=new ReadinessProductTest.Memory(),receipts=new ReadinessProductTest.Memory();
        RestrictedCache oldCache=ReadinessProductTest.cache(vault);
        assertTrue(oldCache.attempt(now-600));
        OwnerPrewarmReceipt previous=new OwnerPrewarmReceipt();
        byte[] old=ReadinessProductTest.response(now-600,now+14400);
        assertEquals(ReadinessImportResult.Code.READY,ReadinessProductTest.product(oldCache,receipts).imported(old,previous,now-600).code());
        byte[] persisted=vault.read();
        ReadinessProductTest.Memory upgradedVault=new ReadinessProductTest.Memory();upgradedVault.write(persisted);
        int[] validations={0};
        RestrictedCache upgraded=RestrictedCache.detailed(upgradedVault,raw->{
            if(new String(raw,StandardCharsets.UTF_8).contains("new-seed.invalid"))validations[0]++;
            return ReadinessImportResult.Code.READY;
        });
        ReadinessProduct product=ReadinessProductTest.product(upgraded,receipts);
        assertEquals("restart",product.restart(now).json().get("phase").getAsString());
        assertEquals(previous.challengeId,upgraded.context().challengeId);
        assertTrue("Unexpired old seed must not suppress the production refresh gate",upgraded.attempt(now));
        assertArrayEquals(old,upgraded.usable());
        OwnerPrewarmReceipt fresh=new OwnerPrewarmReceipt();ArrayList<String> paths=new ArrayList<>();
        String nonce=Base64.getEncoder().encodeToString(new byte[32]);
        try(ControlIdentity identity=ControlIdentity.restore(new byte[96])){
            byte[] publicIdentity=identity.publicIdentity();
            FriendsReadinessProtocol.Transport server=(path,body,id)->{
                paths.add(path);assertTrue(id.matches("[a-f0-9]{32}"));
                JsonObject result=new JsonObject();
                if(path.endsWith("/challenge")||path.endsWith("/ack-challenge")){
                    assertEquals(Base64.getEncoder().encodeToString(publicIdentity),body.get("public_identity").getAsString());
                    result.addProperty("challenge",nonce);result.addProperty("expires_at",System.currentTimeMillis()/1000+120);
                    result.addProperty("audience","family-connect/enrollment/v1");
                }else if(path.equals("/friends/restricted-readiness")){
                    assertEquals(identity.proveTransportKey(nonce),body);
                    result=ControlJson.parse(ReadinessProductTest.response(now,now+14400)).getAsJsonObject();
                    result.addProperty("challenge",nonce);result.addProperty("device",identity.reference());
                    result.getAsJsonObject("directory").addProperty("join_url","https://new-seed.invalid");
                }else{
                    assertEquals("/friends/restricted-readiness/ack",path);
                    assertEquals(identity.proveTransportKey(nonce),body.getAsJsonObject("proof"));
                    JsonObject payload=body.getAsJsonObject("receipt");
                    assertEquals("import",payload.get("phase").getAsString());
                    assertEquals("READY",payload.get("result").getAsString());
                    assertEquals(fresh.challengeId,payload.get("correlation_id").getAsString());
                    assertEquals(fresh.fetchId,upgraded.context().fetchId);assertTrue(validations[0]>0);
                    assertTrue(new String(upgraded.usable(),StandardCharsets.UTF_8).contains("new-seed.invalid"));
                    result.addProperty("version",1);result.addProperty("correlation_id",fresh.challengeId);result.addProperty("status","ACK_RECEIVED");
                }
                return result;
            };
            byte[] response=FriendsReadinessProtocol.fetch(server,identity,fresh);
            try{
                ReadinessImportResult result=product.imported(response,fresh,now);
                assertEquals(ReadinessImportResult.Code.READY,result.code());
                product.publish(result,payload->FriendsReadinessProtocol.acknowledge(server,identity,payload));
                assertEquals("ACK_RECEIVED",product.delivery);assertTrue(product.durable);
                assertArrayEquals(response,upgraded.usable());assertArrayEquals(publicIdentity,identity.publicIdentity());
            }finally{Arrays.fill(response,(byte)0);}
        }
        assertEquals(Arrays.asList("/friends/restricted-readiness/challenge","/friends/restricted-readiness","/friends/restricted-readiness/ack-challenge","/friends/restricted-readiness/ack"),paths);
        assertNotEquals(previous.challengeId,upgraded.context().challengeId);
        assertFalse(ReadinessProductTest.cache(upgradedVault).attempt(now+299));
        assertTrue(ReadinessProductTest.cache(upgradedVault).attempt(now+300));
    }
}
