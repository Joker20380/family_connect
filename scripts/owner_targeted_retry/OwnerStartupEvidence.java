package com.familyconnect.app;

import android.content.Context;
import android.util.AtomicFile;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.File;
import java.io.FileInputStream;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import static org.junit.Assert.*;

final class OwnerStartupEvidence {
    static long handle(RestrictedTunnelEngine engine) throws Exception {
        if (engine == null) return 0;
        Field field=RestrictedTunnelEngine.class.getDeclaredField("handle");
        field.setAccessible(true);
        return field.getLong(engine);
    }

    static String digest(File file) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(FileInputStream stream=new FileInputStream(file)) {
            byte[] buffer=new byte[65536];int count;
            while((count=stream.read(buffer))!=-1)digest.update(buffer,0,count);
        }
        StringBuilder result=new StringBuilder();
        for(byte value:digest.digest())result.append(String.format("%02x",value&255));
        return result.toString();
    }

    static JsonObject capture(Context context,long handle) throws Exception {
        JsonObject result=new JsonObject();
        result.addProperty("observed_utc_ms",System.currentTimeMillis());
        result.addProperty("observed_elapsed_ms",android.os.SystemClock.elapsedRealtime());
        if(handle<=0) {result.addProperty("collection","NO_ACCEPTED_ATTEMPT");return result;}
        JsonObject read=JsonParser.parseString(StartupDiagnostics.read(context)).getAsJsonObject();
        String collection=read.get("collection").getAsString();
        result.addProperty("collection",collection);
        if(!read.has("result"))return result;
        StartupResult value=new StartupResult(read.getAsJsonObject("result").toString());
        assertEquals("Startup attempt mismatch",handle,value.attempt);
        result.add("result",JsonParser.parseString(value.json));
        AtomicFile file=new AtomicFile(new File(context.getNoBackupFilesDir(),"diag-owner-startup.json"));
        try {
            assertTrue("Startup persistence bound",file.getBaseFile().length()<=4096);
            StartupResult persisted=new StartupResult(new String(file.readFully(),StandardCharsets.UTF_8));
            assertEquals(value.attempt,persisted.attempt);
            assertEquals(JsonParser.parseString(value.json),JsonParser.parseString(persisted.json));
            result.addProperty("atomic_file","MATCH");
        } catch(Exception | AssertionError failure) {
            result.addProperty("atomic_file","COLLECTION_ERROR");
        }
        return result;
    }

    static void requireComplete(JsonObject evidence,long previous) {
        assertEquals("AVAILABLE",evidence.get("collection").getAsString());
        assertEquals("MATCH",evidence.get("atomic_file").getAsString());
        JsonObject result=evidence.getAsJsonObject("result");
        assertTrue(result.get("complete").getAsBoolean());
        assertTrue("Stale startup attempt",result.get("attempt").getAsLong()>previous);
    }

    static void attach(Throwable primary,Throwable secondary) {
        if(primary!=secondary)primary.addSuppressed(secondary);
    }
}
