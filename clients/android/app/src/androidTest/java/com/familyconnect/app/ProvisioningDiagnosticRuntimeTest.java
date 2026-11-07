package com.familyconnect.app;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class ProvisioningDiagnosticRuntimeTest {
    public boolean protect(int fd){throw new AssertionError("Provider-free probe must not open sockets");}
    @Test public void distinguishesJniArgumentsGoRejectionAndClosedHandle(){
        NativeTcp.load(InstrumentationRegistry.getInstrumentation().getTargetContext());
        assertEquals(0,NativeTcp.connections(0));
        NativeRestricted.load();
        String[] result=new String[1];
        assertEquals(0,NativeRestricted.provisionBegin(null,null,null,null,3000,this,result));
        JsonObject jni=JsonParser.parseString(result[0]).getAsJsonObject();
        assertFalse(jni.get("go_entered").getAsBoolean());
        assertEquals("JNI_ARGUMENTS",jni.get("first_failure").getAsString());
        assertEquals(0,NativeRestricted.provisionBegin(new byte[0],new byte[32],"nl-amsterdam-1","127.0.0.1:53",3000,this,result));
        JsonObject go=JsonParser.parseString(result[0]).getAsJsonObject();
        assertTrue(go.get("go_entered").getAsBoolean());
        assertTrue(go.get("security").getAsBoolean());
        assertEquals("LOCATOR",go.get("first_failure").getAsString());
        assertEquals(0,NativeTcp.connections(0));
        assertEquals(-1,NativeRestricted.state(-1));
        assertEquals(-1,NativeRestricted.chatState(-1));
        assertNull(NativeRestricted.provisionPost(-1,"/friends/restricted-readiness/challenge","{}","11111111111111111111111111111111",result));
        JsonObject closed=JsonParser.parseString(result[0]).getAsJsonObject();
        assertEquals(-1,closed.get("handle").getAsLong());
        assertEquals("CLOSED",closed.get("reason").getAsString());
        assertNull(NativeRestricted.provisionClose(-1));
        assertEquals(closed,JsonParser.parseString(result[0]).getAsJsonObject());
        assertEquals(0,NativeTcp.connections(0));
        System.out.println("PROVIDER_FREE_ANDROID_JNI_DIAGNOSTICS_PASS");
    }
}
