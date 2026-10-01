package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedCacheTest {
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
        assertFalse(cache.attempt(1000));
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
