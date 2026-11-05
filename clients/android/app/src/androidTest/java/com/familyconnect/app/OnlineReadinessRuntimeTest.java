package com.familyconnect.app;

import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.os.SystemClock;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.KeyStore;
import java.security.MessageDigest;
import java.security.cert.CertificateFactory;
import java.util.Arrays;
import java.util.Base64;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManagerFactory;
import org.junit.Test;
import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;

public class OnlineReadinessRuntimeTest {
    private final Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();

    private byte[] asset(Context owner,String name)throws Exception{
        try(InputStream input=owner.getAssets().open(name);ByteArrayOutputStream output=new ByteArrayOutputStream()){
            byte[] buffer=new byte[4096];int count;
            while((count=input.read(buffer))!=-1){assertTrue(output.size()+count<=65536);output.write(buffer,0,count);}
            return output.toByteArray();
        }
    }
    private void status(String phase,String gateway,RestrictedHealthPolicy.Sample sample){
        Bundle receipt=new Bundle();receipt.putString("core_phase",phase);receipt.putString("gateway",gateway);
        receipt.putLong("wall_seconds",System.currentTimeMillis()/1000);
        if(sample!=null){receipt.putString("session",sample.session);receipt.putLong("received",sample.received);receipt.putLong("sent",sample.sent);}
        InstrumentationRegistry.getInstrumentation().sendStatus(2,receipt);
    }
    private byte[] cached(ControlIdentity identity,String gateway)throws Exception{
        synchronized(RestrictedVault.LOCK){return FriendsRestricted.cache(context,identity,gateway).usable(System.currentTimeMillis()/1000);}
    }
    private long borrow(byte[] response,ControlIdentity identity,AutomaticVpnOwner owner)throws Exception{
        byte[] full=identity.material(),material=Arrays.copyOf(full,64);Arrays.fill(full,(byte)0);
        try{return NativeRestricted.chatAcquire(response,material,ControlTrust.anchor(context),owner.resolver(),new ChatNetworkAndroid(context));}
        finally{Arrays.fill(material,(byte)0);}
    }
    private void echo(long lease)throws Exception{
        int descriptor=NativeRestricted.chatOpen(lease,10000);assertTrue("Existing native service stream",descriptor>=0);
        try(ParcelFileDescriptor socket=ParcelFileDescriptor.adoptFd(descriptor);
                ParcelFileDescriptor.AutoCloseInputStream input=new ParcelFileDescriptor.AutoCloseInputStream(ParcelFileDescriptor.dup(socket.getFileDescriptor()));
                ParcelFileDescriptor.AutoCloseOutputStream output=new ParcelFileDescriptor.AutoCloseOutputStream(ParcelFileDescriptor.dup(socket.getFileDescriptor()))){
            byte[] sent="android-owned-renewal".getBytes(StandardCharsets.US_ASCII),received=new byte[sent.length];
            output.write(sent);output.flush();int offset=0;
            while(offset<received.length){int count=input.read(received,offset,received.length-offset);assertTrue(count>0);offset+=count;}
            assertArrayEquals(sent,received);
        }
    }
    private void servicePath(ControlIdentity identity,String gateway,byte[] predecessor)throws Exception{
        AutomaticVpnOwner resolver=new AutomaticVpnOwner(context);
        JsonObject original=JsonParser.parseString(new String(predecessor,StandardCharsets.UTF_8)).getAsJsonObject();
        long originalExpiry=original.get("expires_at").getAsLong(),originalCrl=original.get("minimum_crl").getAsLong();
        Intent connect=new Intent(context,ConnectionService.class).setAction("connect").putExtra("transport","telemost").putExtra("country",gateway);
        long lease=0;
        try{
            context.startForegroundService(connect);
            long started=SystemClock.elapsedRealtime()+180000;
            while(!"on".equals(ConnectionService.status)){
                if(ConnectionService.failed){
                    java.io.File events=new java.io.File(context.getFilesDir(),"connectivity-events.json");
                    fail("Actual service failed: "+(events.exists()?new String(Files.readAllBytes(events.toPath()),StandardCharsets.UTF_8):"no connectivity events"));
                }
                assertTrue("Service connect deadline",SystemClock.elapsedRealtime()<started);Thread.sleep(200);
            }
            assertEquals(ConnectivityOrchestrator.RESTRICTED,ConnectionService.activeTransport);
            lease=borrow(predecessor,identity,resolver);assertTrue(lease>0);assertEquals(2,NativeRestricted.chatState(lease));echo(lease);
            long serviceOwner=ConnectionService.sessionId;
            status("SERVICE_OWNER_CONNECTED",gateway,null);
            HttpsURLConnection verified=(HttpsURLConnection)new java.net.URL("https://185.251.89.19:8443/").openConnection();
            verified.setConnectTimeout(5000);verified.setReadTimeout(5000);
            try(InputStream input=verified.getInputStream();ByteArrayOutputStream output=new ByteArrayOutputStream()){
                byte[] buffer=new byte[256];int count;
                while((count=input.read(buffer))!=-1){assertTrue(output.size()+count<=1024);output.write(buffer,0,count);}
                assertEquals("verified-isolated-origin",new String(output.toByteArray(),StandardCharsets.UTF_8));
            }finally{verified.disconnect();}
            status("SERVICE_VERIFIED_HTTPS",gateway,null);
            String other=gateway.equals(RestrictedGateway.PRIMARY)?RestrictedGateway.SECONDARY:RestrictedGateway.PRIMARY;
            FriendsRestricted.prewarm(context,other);
            long deadline=SystemClock.elapsedRealtime()+11000000;boolean committed=false;
            while(SystemClock.elapsedRealtime()<deadline){
                assertEquals("No internal reconnect",serviceOwner,ConnectionService.sessionId);
                assertEquals("on",ConnectionService.status);assertFalse(ConnectionService.failed);echo(lease);
                byte[] successor=cached(identity,gateway);
                if(successor!=null)try{
                    JsonObject candidate=JsonParser.parseString(new String(successor,StandardCharsets.UTF_8)).getAsJsonObject();
                    if(candidate.get("expires_at").getAsLong()>originalExpiry&&candidate.get("minimum_crl").getAsLong()>originalCrl){
                        long next=borrow(successor,identity,resolver);
                        if(next>0){
                            try{assertEquals(2,NativeRestricted.chatState(next));echo(next);}finally{NativeRestricted.chatRelease(next);}
                            assertTrue(System.currentTimeMillis()/1000<originalExpiry-55);
                            committed=true;status("SERVICE_SUCCESSOR_COMMITTED_SAME_OWNER",gateway,null);break;
                        }
                    }
                }finally{Arrays.fill(successor,(byte)0);}
                Thread.sleep(1000);
            }
            assertTrue("Service HTTP/cache/native successor before old expiry",committed);
        }finally{
            if(lease>0)NativeRestricted.chatRelease(lease);
            context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));
            long deadline=SystemClock.elapsedRealtime()+30000;
            while(!"off".equals(ConnectionService.status)&&SystemClock.elapsedRealtime()<deadline)Thread.sleep(100);
            assertEquals("off",ConnectionService.status);status("SERVICE_OWNER_CLEANED",gateway,null);
        }
    }
    @Test public void verifiedHttpCacheAndExistingOwnerReceiveSuccessor()throws Exception{
        assumeTrue("Explicit isolated runtime only","true".equals(InstrumentationRegistry.getArguments().getString("fc_core_runtime")));
        assertTrue(Build.FINGERPRINT.contains("generic")||Build.MODEL.contains("sdk"));
        assertTrue(Build.VERSION.SDK_INT==27||Build.VERSION.SDK_INT==35);
        assertEquals("com.familyconnect.app.friends",context.getPackageName());
        Context tests=InstrumentationRegistry.getInstrumentation().getContext();
        JsonObject settings=JsonParser.parseString(new String(asset(tests,"core-runtime.json"),StandardCharsets.UTF_8)).getAsJsonObject();
        JsonObject selected=settings.getAsJsonObject("apis").getAsJsonObject(Integer.toString(Build.VERSION.SDK_INT));
        JsonObject nativeBuild=JsonParser.parseString(new String(asset(context,"restricted-build.json"),StandardCharsets.UTF_8)).getAsJsonObject();
        assertEquals("isolated-local-core",nativeBuild.get("provider").getAsString());
        assertTrue(nativeBuild.get("diagnostic_only").getAsBoolean());
        assertEquals(settings.get("native_source").getAsString(),nativeBuild.get("source_revision").getAsString());
        assertArrayEquals(Base64.getDecoder().decode(settings.get("anchor").getAsString()),ControlTrust.anchor(context));
        assertEquals("off",ConnectionService.status);
        assertFalse(new java.io.File(context.getNoBackupFilesDir(),"friends-identity.enc").exists());
        String gateway=selected.get("gateway").getAsString();
        assertTrue(gateway.equals(RestrictedGateway.PRIMARY)||gateway.equals(RestrictedGateway.SECONDARY));
        KeyStore roots=KeyStore.getInstance(KeyStore.getDefaultType());roots.load(null);
        try(InputStream input=tests.getAssets().open("core-ca.pem")){roots.setCertificateEntry("isolated-core",CertificateFactory.getInstance("X.509").generateCertificate(input));}
        TrustManagerFactory trust=TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());trust.init(roots);
        SSLContext tls=SSLContext.getInstance("TLS");tls.init(null,trust.getTrustManagers(),null);
        SSLSocketFactory previous=HttpsURLConnection.getDefaultSSLSocketFactory();
        javax.net.ssl.HostnameVerifier hostname=HttpsURLConnection.getDefaultHostnameVerifier();
        HttpsURLConnection.setDefaultSSLSocketFactory(tls.getSocketFactory());
        AtomicBoolean cancelled=new AtomicBoolean(),connected=new AtomicBoolean();
        AutomaticVpnOwner owner=new AutomaticVpnOwner(context);
        RestrictedTunnelEngine engine=null;long lease=0;byte[] predecessor=null;
        try{
            new FriendsAccessAndroid(context,true).activate(selected.get("invitation").getAsString());
            try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
                byte[] fetched=FriendsRestricted.ready(context,identity,SystemClock.elapsedRealtime()+60000,()->false,false,gateway);
                assertNotNull(fetched);Arrays.fill(fetched,(byte)0);
                predecessor=cached(identity,gateway);assertNotNull("HTTP predecessor cached",predecessor);
                assertTrue(NativeRestricted.validateDelivery(predecessor,identity.publicIdentity(),ControlTrust.anchor(context)));
                byte[] encrypted=Files.readAllBytes(new java.io.File(context.getNoBackupFilesDir(),"restricted-readiness"+RestrictedGateway.namespace(gateway)+".enc").toPath());
                byte[] plain=new RestrictedVault(context,gateway).read();
                try{assertNotNull(plain);assertFalse(Arrays.equals(encrypted,plain));assertEquals(1,encrypted[0]);}
                finally{Arrays.fill(plain,(byte)0);Arrays.fill(encrypted,(byte)0);}
                JsonObject original=JsonParser.parseString(new String(predecessor,StandardCharsets.UTF_8)).getAsJsonObject();
                long originalExpiry=original.get("expires_at").getAsLong(),originalCrl=original.get("minimum_crl").getAsLong();
                if("true".equals(InstrumentationRegistry.getArguments().getString("fc_core_service"))){
                    servicePath(identity,gateway,predecessor);return;
                }
                owner.open(()->cancelled.set(true));
                engine=new RestrictedTunnelEngine(context,cancelled::get,connected::set,owner,SystemClock.elapsedRealtime()+200000,false,gateway);
                engine.up("auto");assertTrue(connected.get());assertTrue(engine.healthy());
                lease=borrow(predecessor,identity,owner);assertTrue(lease>0);assertEquals("Borrow existing VPN session",2,NativeRestricted.chatState(lease));
                echo(lease);engine.connectionFailure();RestrictedHealthPolicy.Sample first=engine.healthSample();assertNotNull(first);
                status("OWNER_CONNECTED",gateway,first);
                String other=gateway.equals(RestrictedGateway.PRIMARY)?RestrictedGateway.SECONDARY:RestrictedGateway.PRIMARY;
                FriendsRestricted.prewarm(context,other);
                long deadline=SystemClock.elapsedRealtime()+11000000;boolean committed=false;
                byte[] originalHash=MessageDigest.getInstance("SHA-256").digest(predecessor);
                while(SystemClock.elapsedRealtime()<deadline){
                    assertFalse(cancelled.get());assertNull(engine.connectionFailure());assertTrue(engine.healthy());echo(lease);
                    RestrictedHealthPolicy.Sample sample=engine.healthSample();assertNotNull(sample);assertEquals(first.session,sample.session);
                    byte[] successor=cached(identity,gateway);
                    if(successor!=null)try{
                        JsonObject candidate=JsonParser.parseString(new String(successor,StandardCharsets.UTF_8)).getAsJsonObject();
                        long expiry=candidate.get("expires_at").getAsLong();
                        if(expiry>originalExpiry&&candidate.get("minimum_crl").getAsLong()>originalCrl&&!Arrays.equals(originalHash,MessageDigest.getInstance("SHA-256").digest(successor))){
                            long next=borrow(successor,identity,owner);
                            if(next>0){
                                try{assertEquals("Authenticated owner committed new profile",2,NativeRestricted.chatState(next));echo(next);}
                                finally{NativeRestricted.chatRelease(next);}
                                assertTrue(expiry>originalExpiry);assertTrue(System.currentTimeMillis()/1000<originalExpiry-55);
                                assertTrue(sample.received>first.received&&sample.sent>first.sent);
                                committed=true;status("SUCCESSOR_COMMITTED_SAME_OWNER",gateway,sample);break;
                            }
                        }
                    }finally{Arrays.fill(successor,(byte)0);}
                    Thread.sleep(1000);
                }
                assertTrue("Actual successor before old expiry",committed);
                byte[] repeated=FriendsRestricted.renewal(context,gateway).get(60,TimeUnit.SECONDS);
                if(repeated!=null)Arrays.fill(repeated,(byte)0);
                assertNull(engine.connectionFailure());echo(lease);assertEquals(first.session,engine.healthSample().session);
            }
        }finally{
            cancelled.set(true);if(lease>0)NativeRestricted.chatRelease(lease);
            if(engine!=null)engine.down();owner.close();
            if(predecessor!=null)Arrays.fill(predecessor,(byte)0);
            HttpsURLConnection.setDefaultSSLSocketFactory(previous);
        }
        assertSame(hostname,HttpsURLConnection.getDefaultHostnameVerifier());
        assertFalse(connected.get());status("OWNER_CLEANED",gateway,null);
    }
}
