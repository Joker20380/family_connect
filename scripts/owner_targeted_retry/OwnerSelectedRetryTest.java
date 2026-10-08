package com.familyconnect.app;

import android.net.*;
import android.os.SystemClock;
import com.google.gson.*;
import java.io.*;
import java.lang.reflect.*;
import java.net.*;
import java.util.concurrent.atomic.AtomicReference;
import javax.net.ssl.HttpsURLConnection;
import org.junit.Test;
import static org.junit.Assert.*;

public class OwnerSelectedRetryTest extends OwnerFieldAcceptanceTest {
    JsonObject fault(String command) throws Exception {
        Method method=OwnerFaultReceiver.class.getDeclaredMethod("control",String.class);
        method.setAccessible(true);
        return JsonParser.parseString((String)method.invoke(null,command)).getAsJsonObject();
    }
    JsonObject traffic() throws Exception {
        JsonObject value=new JsonObject();
        assertTrue(InetAddress.getAllByName("example.com").length>0);value.addProperty("dns",true);
        HttpsURLConnection connection=(HttpsURLConnection)new URL("https://example.com/").openConnection();
        connection.setConnectTimeout(12000);connection.setReadTimeout(12000);long total=0;
        try {assertEquals(200,connection.getResponseCode());try(InputStream stream=connection.getInputStream()){byte[] bytes=new byte[2048];int count;while((count=stream.read(bytes))!=-1)total+=count;}}
        finally {connection.disconnect();}
        assertTrue(total>0);value.addProperty("https_full_body_bytes",total);
        try(Socket socket=new Socket()) {
            socket.connect(new InetSocketAddress("example.com",80),12000);socket.setSoTimeout(12000);
            socket.getOutputStream().write("GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n".getBytes("US-ASCII"));
            socket.getOutputStream().flush();assertTrue(socket.getInputStream().read(new byte[512])>0);
        }
        value.addProperty("tcp",true);return value;
    }
    @Test public void singleExperiment() throws Exception {
        guard();assertEquals("70",arguments.getString("expected_version"));assertEquals("off",ConnectionService.status);
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        NetworkCapabilities network=manager.getNetworkCapabilities(manager.getActiveNetwork());
        assertNotNull(network);assertTrue(network.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR));
        assertFalse(network.hasTransport(NetworkCapabilities.TRANSPORT_WIFI));assertFalse(network.hasTransport(NetworkCapabilities.TRANSPORT_VPN));
        NativeRestricted.load();AutomaticVpnOwner owner=new AutomaticVpnOwner(context);RestrictedTunnelEngine engine=null;
        LocalServerSocket server=new LocalServerSocket(arguments.getString("bridge"));LocalSocket client=null;
        Thread transfer=null;AtomicReference<JsonObject> trafficResult=new AtomicReference<>();AtomicReference<Throwable> trafficError=new AtomicReference<>();
        try {
            client=server.accept();assertEquals(2000,client.getPeerCredentials().getUid());client.setSoTimeout(90000);
            BufferedReader input=new BufferedReader(new InputStreamReader(client.getInputStream(),"UTF-8"));
            PrintWriter wire=new PrintWriter(new OutputStreamWriter(client.getOutputStream(),"UTF-8"),true);
            owner.open(()->{});engine=new RestrictedTunnelEngine(context,()->false,connected->{},owner,SystemClock.elapsedRealtime()+180000);
            engine.up("");assertTrue(engine.healthy());
            Field field=RestrictedTunnelEngine.class.getDeclaredField("handle");field.setAccessible(true);long handle=field.getLong(engine);
            JsonObject baseline=traffic();baseline.add("stats",JsonParser.parseString(NativeRestricted.stats(handle)));baseline.add("fault",fault("status"));wire.println(baseline);
            boolean armed=false,started=false;long deadline=SystemClock.elapsedRealtime()+120000;
            while(SystemClock.elapsedRealtime()<deadline) {
                String line=input.readLine();if(line==null)break;
                JsonObject request=JsonParser.parseString(line).getAsJsonObject();String operation=request.get("operation").getAsString();
                JsonObject response=new JsonObject();
                if(operation.equals("status")) {
                    response.add("stats",JsonParser.parseString(NativeRestricted.stats(handle)));response.add("fault",fault("status"));response.addProperty("healthy",engine.healthy());
                    if(trafficResult.get()!=null)response.add("traffic",trafficResult.get());
                    if(trafficError.get()!=null)response.addProperty("traffic_error",trafficError.get().getClass().getSimpleName());
                } else if(operation.equals("correlation")) {
                    response=fault("correlation:"+request.getAsJsonObject("request").toString());
                    if(request.getAsJsonObject("request").get("operation").getAsString().equals("targeted_arm")) {
                        assertFalse(armed);
                        armed=response.has("result")&&response.get("result").getAsString().equals("ARMED");
                    }
                } else if(operation.equals("traffic")) {
                    assertTrue(armed);assertFalse(started);started=true;
                    transfer=new Thread(()->{
                        try {
                            Thread[] workers=new Thread[3];JsonObject[] results=new JsonObject[3];
                            for(int index=0;index<3;index++){final int slot=index;workers[index]=new Thread(()->{try{results[slot]=traffic();}catch(Throwable failure){trafficError.set(failure);}});workers[index].start();}
                            for(Thread worker:workers){worker.join(40000);assertFalse(worker.isAlive());}
                            if(trafficError.get()==null){JsonObject result=new JsonObject();JsonArray values=new JsonArray();for(JsonObject value:results)values.add(value);result.add("requests",values);trafficResult.set(result);}
                        }catch(Throwable failure){trafficError.set(failure);}
                    });transfer.start();response.addProperty("started",true);
                } else if(operation.equals("stop")) {wire.println(fault("disarm"));break;}
                else {throw new AssertionError("Unsupported operator command");}
                wire.println(response);
            }
        } finally {
            report(fault("disarm"));
            if(transfer!=null)transfer.join(15000);
            try {if(engine!=null)engine.down();}finally {owner.close();}
            if(client!=null)client.close();server.close();report(fault("status"));
        }
    }
}
