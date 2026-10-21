package com.familyconnect.app;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.Test;
import static org.junit.Assert.*;

public class SpeedReceiptTest {
    private JsonObject source() {return JsonParser.parseString("{\"speed_profile\":\"P2\",\"mux_profile\":\"CREDIT128\",\"mux_window\":131072,\"retry_bytes\":16384,\"secret\":\"never\",\"reliable_limits\":{\"local_send\":32,\"local_receive\":32,\"peer_receive\":16,\"effective_send\":16,\"local_write_completion\":true}}").getAsJsonObject();}
    @Test public void mixedPairShowsRealLimits() {JsonObject safe=new JsonObject();SpeedReceipt.project(source(),safe);assertEquals(16,safe.getAsJsonObject("reliable_limits").get("effective_send").getAsInt());assertFalse(safe.has("secret"));assertEquals(5,safe.size());}
    @Test public void noAssumedPeerWindow() {JsonObject value=source(),safe=new JsonObject();value.getAsJsonObject("reliable_limits").addProperty("effective_send",32);SpeedReceipt.project(value,safe);assertFalse(safe.has("reliable_limits"));}
    @Test public void malformedIsOmitted() {JsonObject value=source(),safe=new JsonObject();value.addProperty("speed_profile","key-secret");value.addProperty("mux_window",65536);value.addProperty("retry_bytes",-1);value.getAsJsonObject("reliable_limits").addProperty("local_receive",33);SpeedReceipt.project(value,safe);assertEquals(0,safe.size());}
}
