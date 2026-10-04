package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedCacheTest {
    @Test public void validLongLivedCacheStillRefreshesOnPersistentCadence()throws Exception{
        Memory storage=new Memory();RestrictedCache original=cache(storage,1000);
        assertTrue(original.attempt(1000));
        byte[] saved=response(1000,15400,5,7,2,"retired-seed");original.accept(saved);
        RestrictedCache restarted=cache(storage,1200);
        assertFalse(restarted.attempt(1299));assertTrue(restarted.attempt(1300));
        assertArrayEquals(saved,restarted.usable());
        assertFalse(cache(storage,1301).attempt(1301));
        assertFalse(cache(storage,1599).attempt(1599));
        assertTrue(cache(storage,1600).attempt(1600));
    }
    @Test public void earlyRefreshFailurePreservesCacheAndAllReplayFloors()throws Exception{
        Memory storage=new Memory();RestrictedCache original=cache(storage,1000);
        byte[] saved=response(1000,15400,5,7,2,"retired-seed");original.accept(saved);
        assertTrue(original.attempt(1300));
        RestrictedCache restarted=cache(storage,1400);
        assertArrayEquals(saved,restarted.usable());assertFalse(restarted.attempt(1400));
        rejected(restarted,response(1300,15700,4,7,2,"revision-rollback"));
        rejected(restarted,response(1300,15700,5,6,2,"crl-rollback"));
        rejected(restarted,response(1300,15700,5,7,1,"issuer-rollback"));
        rejected(restarted,response(999,15700,5,7,2,"time-rollback"));
        rejected(restarted,response(1000,15400,5,7,2,"same-time-conflict"));
        assertArrayEquals(saved,restarted.usable());assertTrue(restarted.attempt(1600));
    }
    @Test public void earlyRefreshCannotResurrectDeniedCache()throws Exception{
        Memory storage=new Memory();RestrictedCache original=cache(storage,1000);
        byte[] saved=response(1000,15400,5,7,2,"seed");original.accept(saved);
        assertTrue(original.attempt(1300));original.denied();
        RestrictedCache restarted=cache(storage,1400);
        assertNull(restarted.usable());assertFalse(restarted.attempt(1400));
        assertTrue(restarted.attempt(1600));rejected(restarted,saved);
        assertNull(cache(storage,1600).usable());
    }
    @Test public void failedCooldownWriteCannotAuthorizeAnAttempt()throws Exception{
        Memory storage=new Memory();RestrictedCache original=cache(storage,1000);
        byte[] saved=response(1000,15400,5,7,2,"seed");original.accept(saved);
        storage.fail=true;
        try{original.attempt(1300);fail("attempt without durable cooldown");}
        catch(java.io.IOException expected){}
        assertArrayEquals(saved,cache(storage,1300).usable());
    }
    @Test public void invalidCacheRefreshDoesNotBypassValidationOrCooldown()throws Exception{
        Memory storage=new Memory();byte[] saved=response(1000,15400,5,7,2,"seed");
        cache(storage,1000).accept(saved);
        RestrictedCache invalid=new RestrictedCache(storage,raw->false);
        assertTrue(invalid.attempt(1300));assertNull(invalid.usable());
        assertFalse(invalid.attempt(1301));rejected(invalid,saved);assertNull(invalid.usable());
    }
    @Test public void renewedAuthorityFloorsAndConflictingContent()throws Exception{
        Memory storage=new Memory();RestrictedCache cache=cache(storage,1000);
        cache.accept(response(1000,2000,1,1,1,"initial"));
        byte[] renewed=response(1001,2000,2,19,2,"renewed");cache.accept(renewed);
        assertArrayEquals(renewed,cache(storage,1000).usable());
        rejected(cache,response(1002,2000,1,19,2,"revision-rollback"));
        rejected(cache,response(1002,2000,2,18,2,"crl-rollback"));
        rejected(cache,response(1002,2000,2,19,1,"delegation-rollback"));
        rejected(cache,response(1001,2000,2,19,2,"conflicting-seed"));
        byte[] future=response(1003,2000,37,43,37,"future");cache.accept(future);
        assertArrayEquals(future,cache(storage,1000).usable());
    }
    @Test public void sharedTimestampInstantsAndReplay()throws Exception{
        JsonObject contract;
        try(var input=getClass().getClassLoader().getResourceAsStream("bootstrap-timestamps.json")){
            assertNotNull(input);contract=ControlJson.parse(input.readAllBytes()).getAsJsonObject();
        }
        for(JsonElement entry:contract.getAsJsonArray("valid")){
            JsonObject value=entry.getAsJsonObject();java.time.Instant instant=java.time.Instant.parse(value.get("value").getAsString());
            assertEquals(value.get("seconds").getAsLong(),instant.getEpochSecond());assertEquals(value.get("nanos").getAsInt(),instant.getNano());
            assertEquals(value.get("canonical").getAsString(),instant.toString());
            assertTrue(instant.minusNanos(1).isBefore(instant));assertFalse(instant.isBefore(instant));
        }
        Memory storage=new Memory();RestrictedCache cache=cache(storage,1000);
        JsonObject first=ControlJson.parse(response(1000,2000,1,1,1,"seed")).getAsJsonObject();
        first.getAsJsonObject("directory").addProperty("issued_at","2026-10-01T14:54:06+03:00");
        cache.accept(first.toString().getBytes(StandardCharsets.UTF_8));
        JsonObject newer=first.deepCopy();newer.getAsJsonObject("directory").addProperty("issued_at","2026-10-01T06:24:07-05:30");
        byte[] accepted=newer.toString().getBytes(StandardCharsets.UTF_8);cache.accept(accepted);
        rejected(cache,first.toString().getBytes(StandardCharsets.UTF_8));
        JsonObject conflict=newer.deepCopy();conflict.getAsJsonObject("directory").addProperty("issued_at","2026-10-01T11:54:07Z");
        rejected(cache,conflict.toString().getBytes(StandardCharsets.UTF_8));
        assertArrayEquals(accepted,cache(storage,1000).usable());
    }
    static class Memory implements RestrictedCache.Storage {
        byte[] raw;boolean fail;
        public byte[] read(){return raw==null?null:raw.clone();}
        public void write(byte[] next)throws Exception{if(fail)throw new java.io.IOException();raw=next.clone();}
    }
    private static byte[] response(long issued,long expiry,long revision,long crl,long sequence,String seed){
        JsonObject value=new JsonObject();value.addProperty("issued_at",issued);value.addProperty("expires_at",expiry);
        value.addProperty("challenge","test-nonce-"+issued);
        value.addProperty("revision",revision);value.addProperty("minimum_crl",crl);
        JsonObject issuer=new JsonObject();issuer.addProperty("payload",Base64.getEncoder().encodeToString(("{\"sequence\":"+sequence+"}").getBytes(StandardCharsets.UTF_8)));value.add("issuer",issuer);
        JsonObject directory=new JsonObject();directory.addProperty("issued_at",java.time.Instant.ofEpochSecond(issued).toString());directory.addProperty("join_url",seed);value.add("directory",directory);
        return value.toString().getBytes(StandardCharsets.UTF_8);
    }
    private static RestrictedCache cache(Memory memory,long now){return new RestrictedCache(memory,raw->{
        try {JsonObject value=ControlJson.parse(raw).getAsJsonObject();return ControlJson.integer(value.get("expires_at"),1)>now;}
        catch(Exception failure){return false;}
    });}
    private static void rejected(RestrictedCache cache,byte[] raw)throws Exception{try{cache.accept(raw);fail("accepted");}catch(IllegalArgumentException expected){}}
    @Test public void missingImportRestartAndRedaction()throws Exception{
        Memory storage=new Memory();RestrictedCache cache=cache(storage,1000);
        assertNull(cache.usable());assertTrue(cache.summary().contains("missing"));
        byte[] response=response(1000,4600,1,1,1,"https://seed-private.invalid");cache.accept(response);
        assertArrayEquals(response,cache(storage,1000).usable());assertTrue(cache.summary().startsWith("READY"));
        assertFalse(cache.summary().contains("https"));assertFalse(cache.summary().contains("seed-private"));
        assertTrue(cache.attempt(1000));assertFalse(cache(storage,1001).attempt(1001));
    }
    @Test public void expiredAndCooldownSurviveRestart()throws Exception{
        Memory storage=new Memory();RestrictedCache cache=cache(storage,1000);
        cache.accept(response(900,1100,1,1,1,"seed"));assertTrue(cache.attempt(1000));
        assertFalse(cache(storage,1000).attempt(1001));assertNull(cache(storage,1100).usable());
        assertTrue(cache(storage,1400).attempt(1400));
    }
    @Test public void staleMalformedAndFailedRefreshPreserveOldState()throws Exception{
        Memory storage=new Memory();RestrictedCache cache=cache(storage,1000);byte[] original=response(1000,2000,2,2,2,"seed");cache.accept(original);
        rejected(cache,"{}".getBytes(StandardCharsets.UTF_8));
        rejected(cache,response(999,2000,2,2,2,"seed"));
        rejected(cache,response(1001,2000,1,2,2,"seed"));
        rejected(cache,response(1001,2000,2,1,2,"seed"));
        rejected(cache,response(1001,2000,2,2,1,"seed"));
        rejected(cache,response(1000,2000,2,2,2,"changed seed"));
        assertArrayEquals(original,cache.usable());storage.fail=true;
        try{cache.accept(response(1001,2000,2,3,2,"new seed"));fail();}catch(java.io.IOException expected){}
        assertArrayEquals(original,cache(storage,1000).usable());
    }
    @Test public void expiredStateRetainsReplayFloors()throws Exception{
        Memory storage=new Memory();cache(storage,1000).accept(response(1000,1500,5,5,5,"seed"));
        RestrictedCache restarted=cache(storage,1600);
        rejected(restarted,response(1600,2600,4,5,5,"seed"));assertNull(restarted.usable());
    }
    @Test public void denialPersistsAndIdempotentImport()throws Exception{
        Memory storage=new Memory();RestrictedCache cache=cache(storage,1000);byte[] response=response(1000,2000,1,1,1,"seed");
        cache.accept(response);cache.accept(response);cache.denied();assertNull(cache(storage,1000).usable());
        assertTrue(cache.summary().contains("authorization rejected"));rejected(cache,response);
        cache.accept(response(1001,2000,2,2,1,"seed"));assertNotNull(cache.usable());
    }
}
