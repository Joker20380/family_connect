package com.familyconnect.app;

import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.os.SystemClock;
import com.google.gson.*;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import org.junit.Test;
import static org.junit.Assert.*;

public class OwnerControlSessionTest extends OwnerFieldAcceptanceTest {
    void noWatch(JsonElement value){
        if(value.isJsonObject())for(java.util.Map.Entry<String,JsonElement> entry:value.getAsJsonObject().entrySet()){
            if(entry.getKey().equals("evidence_watch"))assertTrue(entry.getValue().isJsonNull());
            noWatch(entry.getValue());
        }
        else if(value.isJsonArray())for(JsonElement item:value.getAsJsonArray())noWatch(item);
    }
    @Test public void statusOnlySession() throws Exception {
        guard();assertEquals("70",arguments.getString("expected_version"));
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        NetworkCapabilities network=manager.getNetworkCapabilities(manager.getActiveNetwork());
        assertNotNull(network);assertTrue(network.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR));
        assertFalse(network.hasTransport(NetworkCapabilities.TRANSPORT_WIFI));
        AutomaticVpnOwner owner=new AutomaticVpnOwner(context);RestrictedTunnelEngine engine=null;
        try {
            owner.open(()->{});
            engine=new RestrictedTunnelEngine(context,()->false,connected->{},owner,SystemClock.elapsedRealtime()+180000);
            engine.up("");assertTrue(engine.healthy());
            Method control=OwnerFaultReceiver.class.getDeclaredMethod("control",String.class);control.setAccessible(true);
            JsonObject fault=JsonParser.parseString((String)control.invoke(null,"status")).getAsJsonObject();
            assertFalse(fault.get("armed").getAsBoolean());assertFalse(fault.get("consumed").getAsBoolean());assertFalse(fault.has("generation"));
            Field handle=RestrictedTunnelEngine.class.getDeclaredField("handle");handle.setAccessible(true);
            noWatch(JsonParser.parseString(NativeRestricted.stats(handle.getLong(engine))));
            JsonObject evidence=new JsonObject();evidence.addProperty("connected",true);evidence.add("fault",fault);evidence.addProperty("evidence_watch_absent",true);report(evidence);
            for(int sample=0;sample<20;sample++){assertTrue(engine.healthy());SystemClock.sleep(1000);}
        } finally {
            try{if(engine!=null)engine.down();}finally{owner.close();}
            JsonObject evidence=new JsonObject();evidence.addProperty("cleanup_complete",true);report(evidence);
        }
    }
}
