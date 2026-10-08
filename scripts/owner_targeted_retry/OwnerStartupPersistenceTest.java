package com.familyconnect.app;

import android.util.AtomicFile;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import org.junit.Test;
import static org.junit.Assert.*;

public class OwnerStartupPersistenceTest extends OwnerFieldAcceptanceTest {
    @Test public void syntheticProjectionPersistence() throws Exception {
        guard();
        assertEquals(arguments.getString("expected_apk_sha256"),OwnerStartupEvidence.digest(new File(context.getApplicationInfo().sourceDir)));
        File directory=new File(context.getCacheDir(),"bootstrap-cause-owner-test");
        assertFalse(directory.exists());assertTrue(directory.mkdir());
        AtomicFile file=new AtomicFile(new File(directory,"diag-owner-startup.json"));
        JsonObject evidence=new JsonObject();evidence.addProperty("event","SYNTHETIC_ART_PERSISTENCE");
        Throwable primary=null;
        try {
            String fixture="{\"schema\":1,\"attempt\":17,\"started_unix_ms\":1,\"observed_ms\":2,\"completed_ms\":3,\"complete\":true,\"status\":\"FAILED\",\"stage\":\"HELLO_RECEIVE\",\"cause\":\"DEADLINE\",\"private\":\"SYNTHETIC_SECRET\"}";
            StartupResult expected=new StartupResult(fixture);
            FileOutputStream output=file.startWrite();
            try {output.write(expected.json.getBytes(StandardCharsets.UTF_8));file.finishWrite(output);}
            catch(Exception failure) {file.failWrite(output);throw failure;}
            StartupResult actual=new StartupResult(new String(file.readFully(),StandardCharsets.UTF_8));
            assertEquals(JsonParser.parseString(expected.json),JsonParser.parseString(actual.json));
            assertEquals("HELLO_RECEIVE:DEADLINE",actual.failure().getMessage());
            assertFalse(actual.json.contains("SYNTHETIC_SECRET"));
            evidence.addProperty("result","PASS");
            evidence.addProperty("origin","SYNTHETIC_NOT_LIVE");
        } catch(Exception | Error failure) {primary=failure;throw failure;}
        finally {
            try {file.delete();assertTrue(directory.delete());evidence.addProperty("fixture_cleanup",true);report(evidence);}
            catch(Exception | Error cleanup) {
                if(primary!=null)OwnerStartupEvidence.attach(primary,cleanup);
                else if(cleanup instanceof Exception)throw (Exception)cleanup;
                else throw (Error)cleanup;
            }
        }
    }
}
