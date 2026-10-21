package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class SupportSnapshotTest {
    @Test public void projectionDropsTrafficAndSecrets(){
        JsonObject ring=JsonParser.parseString("{\"private_key\":\"SECRET\",\"network_class\":\"WIFI\",\"events\":[\"private.example\"],\"restricted_session\":{\"protocol_errors\":17,\"session_tag\":\""+"a".repeat(64)+"\",\"error\":\"SECRET\"}}").getAsJsonObject();
        JsonObject report=SupportSnapshot.project(ring,98,123);
        assertEquals(17,report.getAsJsonObject("metrics").get("protocol_errors").getAsInt());
        assertFalse(report.toString().contains("SECRET"));assertFalse(report.toString().contains("private.example"));
        assertEquals("WIFI",report.getAsJsonObject("metrics").get("network").getAsString());
    }
    @Test public void badTypesAndBoundsOmitted(){
        JsonObject ring=JsonParser.parseString("{\"restricted_session\":{\"protocol_errors\":true,\"retry_bytes\":-1,\"received_bytes\":9007199254740992,\"sent_bytes\":1.5,\"session_tag\":\"https://room\"}}").getAsJsonObject();
        JsonObject metrics=SupportSnapshot.project(ring,98,1).getAsJsonObject("metrics");
        for(String key:new String[]{"protocol_errors","retry_bytes","received_bytes","sent_bytes","session_tag"})assertFalse(metrics.has(key));
    }
    @Test public void usbPermissionExpiresAndCannotBeGrantedByCaller(){
        SupportAccess access=new SupportAccess();assertFalse(access.allows(2000,1));access.enable(100);
        assertTrue(access.allows(2000,101));assertFalse(access.allows(10001,101));assertFalse(access.allows(0,101));
        assertFalse(access.allows(2000,3600100));access.disable();assertFalse(access.allows(2000,102));
    }
}
