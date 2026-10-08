package com.familyconnect.app;

import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.os.SystemClock;
import com.google.gson.*;
import java.lang.reflect.Method;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import javax.net.ssl.HttpsURLConnection;
import org.junit.Test;
import static org.junit.Assert.*;

public class OwnerPairBaselineTest extends OwnerFieldAcceptanceTest {
    JsonObject fault() throws Exception {
        Method method=OwnerFaultReceiver.class.getDeclaredMethod("control",String.class);
        method.setAccessible(true);
        JsonObject value=JsonParser.parseString((String)method.invoke(null,"status")).getAsJsonObject();
        assertEquals(1,value.get("schema").getAsInt());
        assertFalse(value.get("armed").getAsBoolean());
        assertFalse(value.get("consumed").getAsBoolean());
        assertEquals(0,value.get("count").getAsInt());
        assertFalse(value.has("generation"));
        return value;
    }

    @Test public void restrictedBaseline() throws Exception {
        guard();assertEquals("70",arguments.getString("expected_version"));
        assertEquals("off",ConnectionService.status);
        assertEquals("FC-4D8Q-REEG",DeviceSupport.cached(context));
        NativeRestricted.load();
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        NetworkCapabilities network=manager.getNetworkCapabilities(manager.getActiveNetwork());
        assertNotNull(network);assertTrue(network.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR));
        assertFalse(network.hasTransport(NetworkCapabilities.TRANSPORT_WIFI));
        assertFalse(network.hasTransport(NetworkCapabilities.TRANSPORT_VPN));
        for(int cycle=0;cycle<2;cycle++) {
            JsonObject evidence=new JsonObject();evidence.addProperty("cycle",cycle);
            evidence.addProperty("phase","starting");report(evidence);
            AutomaticVpnOwner owner=new AutomaticVpnOwner(context);
            RestrictedTunnelEngine engine=null;
            try {
                owner.open(()->{});
                engine=new RestrictedTunnelEngine(context,()->false,connected->{},owner,SystemClock.elapsedRealtime()+180000);
                engine.up("");assertTrue(engine.healthy());
                evidence.addProperty("phase","connected");evidence.add("fault",fault());
                assertEquals("DISARMED",evidence.getAsJsonObject("fault").get("state").getAsString());
                report(evidence);
                assertTrue(InetAddress.getAllByName("example.com").length>0);
                evidence.addProperty("dns",true);report(evidence);
                HttpsURLConnection connection=(HttpsURLConnection)new java.net.URL("https://example.com/").openConnection();
                connection.setConnectTimeout(15000);connection.setReadTimeout(15000);
                try {assertEquals(200,connection.getResponseCode());try(java.io.InputStream stream=connection.getInputStream()){java.io.ByteArrayOutputStream body=new java.io.ByteArrayOutputStream();byte[] buffer=new byte[1024];int count;while((count=stream.read(buffer))!=-1){body.write(buffer,0,count);assertTrue("Unexpected oversized response",body.size()<=65536);}String html=body.toString("UTF-8");assertTrue(html.contains("Example Domain"));assertTrue(html.toLowerCase(java.util.Locale.ROOT).contains("</html>"));evidence.addProperty("https_full_body_bytes",body.size());}}
                finally {connection.disconnect();}
                evidence.addProperty("https",true);report(evidence);
                try(Socket socket=new Socket()) {
                    socket.connect(new InetSocketAddress("example.com",80),15000);socket.setSoTimeout(15000);
                    socket.getOutputStream().write("GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n".getBytes(java.nio.charset.StandardCharsets.US_ASCII));
                    socket.getOutputStream().flush();assertTrue(socket.getInputStream().read(new byte[512])>0);
                }
                evidence.addProperty("tcp",true);
                for(int sample=0;sample<15;sample++){assertTrue(engine.healthy());SystemClock.sleep(1000);}
                evidence.add("fault_after_traffic",fault());evidence.addProperty("phase","traffic_pass");report(evidence);
            } finally {
                try {if(engine!=null)engine.down();} finally {owner.close();}
                evidence.add("fault_after_cleanup",fault());evidence.addProperty("cleanup_complete",true);report(evidence);
            }
        }
    }
}
