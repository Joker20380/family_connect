package com.familyconnect.app;

import android.content.Context;
import android.net.VpnService;
import android.os.Bundle;
import android.os.SystemClock;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.gson.JsonObject;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.lang.reflect.Field;
import java.net.InetAddress;
import java.net.URL;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.crypto.KeyGenerator;
import javax.net.ssl.HttpsURLConnection;
import org.junit.Test;
import static org.junit.Assert.*;

public final class ColdProvisionRuntimeTest {
    private AutomaticConnection connection;
    private Context context;
    private final AtomicBoolean connected=new AtomicBoolean();
    private static Object field(Object source,String name)throws Exception{
        Field selected=source.getClass().getDeclaredField(name);selected.setAccessible(true);return selected.get(source);
    }
    private synchronized void record(String stage,JsonObject value){
        value.addProperty("stage",stage);value.addProperty("monotonic_ms",SystemClock.elapsedRealtime());
        Bundle status=new Bundle();status.putString("cold_evidence",value.toString());
        InstrumentationRegistry.getInstrumentation().sendStatus(2,status);
    }
    private void phase(String stage){record(stage,new JsonObject());}
    private void snapshot(String stage){
        try{
            JsonObject value=new JsonObject();
            Object candidate=connection==null?null:field(connection,"candidate");
            if(candidate instanceof RestrictedTunnelEngine){
                long deadline=(Long)field(candidate,"connectDeadline"),handle=(Long)field(candidate,"handle");
                value.addProperty("candidate_deadline_ms",deadline);
                value.addProperty("remaining_ms",Math.max(0,deadline-SystemClock.elapsedRealtime()));
                value.addProperty("engine_stage",(String)field(candidate,"startupStage"));
                value.addProperty("native_handle_present",handle>0);
                if(handle>0){
                    value.addProperty("native_state",NativeRestricted.state(handle));
                    org.json.JSONObject stats=new org.json.JSONObject(NativeRestricted.stats(handle));
                    Diagnostics.nativeStats(context,stats);
                    for(String key:new String[]{"state","events","protect_ok","protect_denied"})
                        if(stats.has(key))value.add(key,com.google.gson.JsonParser.parseString(stats.get(key).toString()));
                    org.json.JSONObject packet=stats.optJSONObject("packet");
                    org.json.JSONObject mux=packet==null?null:packet.optJSONObject("mux");
                    if(mux!=null){
                        JsonObject counters=new JsonObject();
                        for(String key:new String[]{"DNSRequests","DNSResponses","DNSErrors","DNSTimeouts","OpenOK","OpenErrors","ProtocolErrors","SentBytes","ReceivedBytes"})
                            if(mux.has(key))counters.addProperty(key,mux.getLong(key));
                        value.add("mux_counters",counters);
                    }
                }
            }
            Field primary=FriendsRestricted.class.getDeclaredField("primary");primary.setAccessible(true);
            Object scope=primary.get(null);ReadinessFetchTrace trace=(ReadinessFetchTrace)field(scope,"trace");
            if(trace!=null)value.add("readiness_fetch",trace.json());
            OwnerPrewarmReceipt receipt=(OwnerPrewarmReceipt)field(scope,"observation");
            if(receipt!=null)value.add("owner_acceptance",com.google.gson.JsonParser.parseString(receipt.summary()));
            value.addProperty("refresh",(String)field(scope,"refresh"));
            JsonObject diagnostics=Diagnostics.supportSnapshot(context);
            for(String key:new String[]{"restricted_startup","counters"})if(diagnostics.has(key))value.add(key,diagnostics.get(key));
            value.addProperty("readiness_file_exists",new File(context.getNoBackupFilesDir(),"restricted-readiness.enc").exists());
            record(stage,value);
        }catch(Exception|LinkageError failure){phase("SNAPSHOT_UNAVAILABLE");}
    }
    private static byte[] asset(Context source,String name)throws Exception{
        try(InputStream input=source.getAssets().open(name);ByteArrayOutputStream output=new ByteArrayOutputStream()){
            byte[] buffer=new byte[2048];int count;while((count=input.read(buffer))!=-1){assertTrue(output.size()+count<=16384);output.write(buffer,0,count);}return output.toByteArray();
        }
    }
    private static byte[] https(String address)throws Exception{
        HttpsURLConnection request=(HttpsURLConnection)new URL(address).openConnection();
        request.setConnectTimeout(10000);request.setReadTimeout(10000);
        try{assertEquals(200,request.getResponseCode());try(InputStream input=request.getInputStream();ByteArrayOutputStream output=new ByteArrayOutputStream()){
            byte[] buffer=new byte[2048];int count;while((count=input.read(buffer))!=-1){assertTrue(output.size()+count<=65536);output.write(buffer,0,count);}return output.toByteArray();
        }}finally{request.disconnect();}
    }
    private void originalDnsTarget(){
        JsonObject evidence=new JsonObject();
        try(java.net.DatagramSocket socket=new java.net.DatagramSocket()){
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            java.io.DataOutputStream output=new java.io.DataOutputStream(bytes);
            output.writeShort(0x4731);output.writeShort(0x0100);output.writeShort(1);
            output.writeShort(0);output.writeShort(0);output.writeShort(0);
            output.writeByte(7);output.writeBytes("example");output.writeByte(3);output.writeBytes("com");output.writeByte(0);
            output.writeShort(1);output.writeShort(1);
            socket.setSoTimeout(5000);socket.connect(InetAddress.getByName("10.79.0.1"),53);
            byte[] query=bytes.toByteArray();socket.send(new java.net.DatagramPacket(query,query.length));
            byte[] response=new byte[4096];java.net.DatagramPacket packet=new java.net.DatagramPacket(response,response.length);socket.receive(packet);
            boolean valid=packet.getLength()>=12&&response[0]==query[0]&&response[1]==query[1]&&(response[2]&0x80)!=0;
            evidence.addProperty("id_and_header_valid",valid);
            if(valid){evidence.addProperty("rcode",response[3]&15);evidence.addProperty("answer_count",((response[6]&255)<<8)|(response[7]&255));}
        }catch(java.net.SocketTimeoutException failure){evidence.addProperty("error","TIMEOUT");}
        catch(Exception failure){evidence.addProperty("error","IO");}
        record("ORIGINAL_TARGET_DNS_OBSERVATION",evidence);
    }
    @Test public void uncachedRealTelemost()throws Exception{
        context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests=InstrumentationRegistry.getInstrumentation().getContext();
        assertEquals("com.familyconnect.app.friends",context.getPackageName());
        assertNull(VpnService.prepare(context));
        android.net.ConnectivityManager manager=context.getSystemService(android.net.ConnectivityManager.class);
        for(android.net.Network network:manager.getAllNetworks())assertFalse(manager.getNetworkCapabilities(network).hasTransport(android.net.NetworkCapabilities.TRANSPORT_VPN));
        File identityFile=new File(context.getNoBackupFilesDir(),"friends-identity.enc");
        assertFalse(identityFile.exists());assertNull(new RestrictedVault(context).read());
        assertTrue(ProvisioningCarrier.configured(context,RestrictedGateway.PRIMARY));
        byte[] locator=asset(context,"provisioning/"+RestrictedGateway.PRIMARY+".json");
        JsonObject locatorObject=ControlJson.parse(locator).getAsJsonObject();
        JsonObject address=ControlJson.parse(java.util.Base64.getDecoder().decode(locatorObject.get("payload").getAsString())).getAsJsonObject();
        assertTrue(address.get("expires_at").getAsLong()>System.currentTimeMillis()/1000);
        byte[] material=asset(tests,"identity96.private");assertEquals(96,material.length);
        KeyGenerator generator=KeyGenerator.getInstance("AES","AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder("family-connect-friends-identity-v1",KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());
        try{Files.write(identityFile.toPath(),ControlIdentityEnvelope.seal(generator.generateKey(),material));}finally{Arrays.fill(material,(byte)0);}
        phase("COLD_PREREQUISITES_VERIFIED");
        connection=new AutomaticConnection(context,RestrictedGateway.PRIMARY,true,event->{
            JsonObject value=new JsonObject();value.addProperty("event",event.name);value.addProperty("state",event.state.name());value.addProperty("elapsed_ms",event.elapsedMs);
            if(event.failure!=null)value.addProperty("category",event.failure.name());
            if(event.triggerReason!=null)value.addProperty("trigger_reason",event.triggerReason.name());
            if(event.cleanupReason!=null)value.addProperty("cleanup_reason",event.cleanupReason.name());
            record("ORCHESTRATOR",value);
            if(event.name.equals("candidate_failed"))snapshot("BEFORE_CANDIDATE_CLEANUP");
            if(event.name.equals("candidate_succeeded"))connected.set(true);
        });
        AtomicBoolean sampling=new AtomicBoolean(true);
        Thread sampler=new Thread(()->{while(sampling.get()){snapshot("LIVE");try{Thread.sleep(1000);}catch(InterruptedException done){return;}}},"cold-evidence");
        try{
            phase("CONNECT_START");sampler.start();connection.up(ConnectivityOrchestrator.RESTRICTED);
            snapshot("CONNECT_RETURNED");assertTrue("Positive path did not reach READY",connected.get());phase("NATIVE_READY");
            byte[] readiness=new RestrictedVault(context).read();assertNotNull(readiness);
            byte[] encrypted=Files.readAllBytes(new File(context.getNoBackupFilesDir(),"restricted-readiness.enc").toPath());
            assertFalse(Arrays.equals(readiness,encrypted));Arrays.fill(readiness,(byte)0);phase("ENCRYPTED_READINESS_ACCEPTED");
            assertTrue(InetAddress.getAllByName("api.ipify.org").length>0);phase("DNS_OK");
            byte[] observed=https("https://api.ipify.org");
            assertTrue(observed.length>0);phase("VERIFIED_HTTPS_OK");
            byte[] expected=asset(tests,"egress.sha256");
            assertTrue(MessageDigest.isEqual(MessageDigest.getInstance("SHA-256").digest(observed),expected));phase("EGRESS_VERIFIED");
            originalDnsTarget();
        }catch(Exception|AssertionError|LinkageError failure){
            JsonObject value=new JsonObject();value.addProperty("category",ConnectivityOrchestrator.classify(failure).name());record("HARNESS_FAILURE",value);
            throw new AssertionError("Cold runtime failed; see typed pre-cleanup evidence");
        }finally{
            sampling.set(false);sampler.interrupt();
            try{sampler.join(2000);snapshot("BEFORE_FINAL_CLEANUP");}finally{
                try{connection.down();phase("OWN_CLIENT_CLEANUP_RETURNED");}
                catch(Exception|LinkageError failure){phase("OWN_CLIENT_CLEANUP_FAILED");throw new AssertionError("Owned cleanup failed");}
            }
        }
    }
}
