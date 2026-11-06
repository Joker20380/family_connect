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
    private JsonObject fixtureControl(String action)throws Exception{
        HttpsURLConnection request=(HttpsURLConnection)new java.net.URL("https://185.251.89.19:8443/qualification/"+action).openConnection();
        request.setConnectTimeout(10000);request.setReadTimeout(10000);
        try(InputStream input=request.getInputStream();ByteArrayOutputStream output=new ByteArrayOutputStream()){
            byte[] buffer=new byte[1024];int count;
            while((count=input.read(buffer))!=-1){assertTrue(output.size()+count<=8192);output.write(buffer,0,count);}
            return JsonParser.parseString(new String(output.toByteArray(),StandardCharsets.UTF_8)).getAsJsonObject();
        }finally{request.disconnect();}
    }
    private void partialPublication(ControlIdentity identity,String gateway,long lease,long serviceOwner,long originalExpiry,long originalCrl)throws Exception{
        fixtureControl("connected"+Build.VERSION.SDK_INT);
        long deadline=SystemClock.elapsedRealtime()+300000;
        while(!"PARTIAL".equals(fixtureControl("state").get("state").getAsString())){
            assertTrue("Partial publication starts",SystemClock.elapsedRealtime()<deadline);echo(lease);Thread.sleep(1000);
        }
        status("PARTIAL_PUBLICATION",gateway,null);
        for(int attempt=0;attempt<2;attempt++){
            byte[] duplicate=FriendsRestricted.ready(context,identity,SystemClock.elapsedRealtime()+60000,()->false,false,gateway);
            if(duplicate!=null)Arrays.fill(duplicate,(byte)0);
        }
        long cooldown=SystemClock.elapsedRealtime()+310000;
        while(SystemClock.elapsedRealtime()<cooldown){
            assertEquals(serviceOwner,ConnectionService.sessionId);assertEquals("on",ConnectionService.status);assertFalse(ConnectionService.failed);echo(lease);
            byte[] retained=cached(identity,gateway);assertNotNull("Usable predecessor retained during partial publication",retained);
            try{
                JsonObject value=JsonParser.parseString(new String(retained,StandardCharsets.UTF_8)).getAsJsonObject();
                assertEquals(originalExpiry,value.get("expires_at").getAsLong());assertEquals(originalCrl,value.get("minimum_crl").getAsLong());
            }finally{Arrays.fill(retained,(byte)0);}
            Thread.sleep(1000);
        }
        fixtureControl("release"+Build.VERSION.SDK_INT);status("REAL_COOLDOWN_PARTIAL_RELEASED",gateway,null);
    }
    private void awaitImportBlocked()throws Exception{
        long deadline=SystemClock.elapsedRealtime()+5000;
        while(SystemClock.elapsedRealtime()<deadline){
            for(java.util.Map.Entry<Thread,StackTraceElement[]> entry:Thread.getAllStackTraces().entrySet()){
                if(!entry.getKey().getName().equals("friends-readiness")||entry.getKey().getState()!=Thread.State.BLOCKED)continue;
                for(StackTraceElement frame:entry.getValue())
                    if(frame.getClassName().equals(RestrictedBootstrap.class.getName())&&frame.getMethodName().equals("refresh"))return;
            }
            Thread.sleep(20);
        }
        fail("Real HTTP completion must reach the existing cache import monitor");
    }
    private void ownerRace(ControlIdentity identity,String gateway,long lease,long serviceOwner,long originalExpiry,Intent connect)throws Exception{
        fixtureControl("connected"+Build.VERSION.SDK_INT);
        long deadline=SystemClock.elapsedRealtime()+600000;
        while(!"READINESS_HELD".equals(fixtureControl("state").get("state").getAsString())){
            assertTrue("Normal owner must refresh after real cache cooldown",SystemClock.elapsedRealtime()<deadline);
            assertEquals(serviceOwner,ConnectionService.sessionId);assertEquals("on",ConnectionService.status);echo(lease);Thread.sleep(500);
        }
        long replacement;
        synchronized(RestrictedVault.LOCK){
            fixtureControl("response"+Build.VERSION.SDK_INT);
            awaitImportBlocked();status("HTTP_COMPLETED_IMPORT_PENDING",gateway,null);
            NativeRestricted.chatRelease(lease);
            context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));
            deadline=SystemClock.elapsedRealtime()+10000;
            while(!"off".equals(ConnectionService.status)&&SystemClock.elapsedRealtime()<deadline)Thread.sleep(50);
            assertEquals("off",ConnectionService.status);assertNotEquals(serviceOwner,ConnectionService.sessionId);
            status("OLD_OWNER_CLOSED_BEFORE_IMPORT",gateway,null);
            long closed=ConnectionService.sessionId;
            context.startForegroundService(connect);
            deadline=SystemClock.elapsedRealtime()+10000;
            while(ConnectionService.sessionId==closed&&SystemClock.elapsedRealtime()<deadline)Thread.sleep(50);
            assertNotEquals(closed,ConnectionService.sessionId);assertNotEquals(serviceOwner,ConnectionService.sessionId);
            assertNotEquals("on",ConnectionService.status);replacement=ConnectionService.sessionId;
            status("NEW_EXPLICIT_OWNER_WAITING_FOR_IMPORT",gateway,null);
        }
        deadline=SystemClock.elapsedRealtime()+180000;
        while(!"on".equals(ConnectionService.status)){
            assertFalse("Replacement owner must not fail",ConnectionService.failed);
            assertTrue("Replacement connect deadline",SystemClock.elapsedRealtime()<deadline);Thread.sleep(100);
        }
        assertEquals(replacement,ConnectionService.sessionId);
        byte[] successor=cached(identity,gateway);assertNotNull(successor);
        try{
            assertTrue(NativeRestricted.validateDelivery(successor,identity.publicIdentity(),ControlTrust.anchor(context)));
            JsonObject response=JsonParser.parseString(new String(successor,StandardCharsets.UTF_8)).getAsJsonObject();
            assertTrue(response.get("expires_at").getAsLong()>originalExpiry);
            long next=borrow(successor,identity,new AutomaticVpnOwner(context));assertTrue(next>0);
            try{assertEquals(2,NativeRestricted.chatState(next));echo(next);Thread.sleep(6000);echo(next);
                assertEquals(replacement,ConnectionService.sessionId);assertEquals("on",ConnectionService.status);}
            finally{NativeRestricted.chatRelease(next);}
        }finally{Arrays.fill(successor,(byte)0);}
        status("OWNER_RACE_VALID_SUCCESSOR_NEW_EXPLICIT_OWNER",gateway,null);
    }
    private void servicePath(ControlIdentity identity,String gateway,byte[] predecessor,JsonObject settings)throws Exception{
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
            if(settings.has("scenario")){
                if("partial-connect".equals(settings.get("scenario").getAsString())){
                    fixtureControl("connected"+Build.VERSION.SDK_INT);
                    long partialDeadline=SystemClock.elapsedRealtime()+180000;
                    while(!"PARTIAL".equals(fixtureControl("state").get("state").getAsString())){
                        assertTrue("Partial publication starts",SystemClock.elapsedRealtime()<partialDeadline);echo(lease);Thread.sleep(500);
                    }
                    NativeRestricted.chatRelease(lease);lease=0;
                    context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));
                    long stopped=SystemClock.elapsedRealtime()+30000;
                    while(!"off".equals(ConnectionService.status)&&SystemClock.elapsedRealtime()<stopped)Thread.sleep(100);
                    assertEquals("off",ConnectionService.status);
                    context.startForegroundService(connect);
                    started=SystemClock.elapsedRealtime()+180000;
                    while(!"on".equals(ConnectionService.status)){
                        assertFalse("Explicit Connect during partial publication",ConnectionService.failed);
                        assertTrue("Partial Connect deadline",SystemClock.elapsedRealtime()<started);Thread.sleep(100);
                    }
                    assertNotEquals(serviceOwner,ConnectionService.sessionId);
                    serviceOwner=ConnectionService.sessionId;
                    byte[] retained=cached(identity,gateway);assertNotNull(retained);
                    try{
                        JsonObject retainedResponse=JsonParser.parseString(new String(retained,StandardCharsets.UTF_8)).getAsJsonObject();
                        for(String field:new String[]{"device","revision","issuer","certificate","revocations","minimum_crl","directory","expires_at"})
                            assertEquals("Predecessor security material: "+field,original.get(field),retainedResponse.get(field));
                        assertTrue(NativeRestricted.validateDelivery(retained,identity.publicIdentity(),ControlTrust.anchor(context)));
                        lease=borrow(retained,identity,resolver);
                    }
                    finally{Arrays.fill(retained,(byte)0);}
                    assertTrue(lease>0);assertEquals(2,NativeRestricted.chatState(lease));echo(lease);
                    assertEquals("PARTIAL",fixtureControl("state").get("state").getAsString());
                    status("NEW_EXPLICIT_CONNECT_DURING_PARTIAL",gateway,null);
                    fixtureControl("release"+Build.VERSION.SDK_INT);
                    long resumed=SystemClock.elapsedRealtime()+180000;
                    while(!"SUCCESSOR_PUBLISHED".equals(fixtureControl("state").get("state").getAsString())){
                        assertTrue("Same COMMIT resume deadline",SystemClock.elapsedRealtime()<resumed);
                        assertEquals(serviceOwner,ConnectionService.sessionId);echo(lease);Thread.sleep(500);
                    }
                    status("PARTIAL_EXPLICIT_CONNECT_AND_SAME_COMMIT_RESUME",gateway,null);return;
                }
                if("owner-race".equals(settings.get("scenario").getAsString())){
                    ownerRace(identity,gateway,lease,serviceOwner,originalExpiry,connect);return;
                }
                if("late-closed-owner".equals(settings.get("scenario").getAsString())){
                    lateClosedOwner(identity,gateway,lease,serviceOwner,originalExpiry,connect);return;
                }
                if("legacy".equals(settings.get("scenario").getAsString())){
                    legacyPeer(identity,gateway,lease,serviceOwner,originalExpiry,connect);return;
                }
                assertEquals("partial",settings.get("scenario").getAsString());
                partialPublication(identity,gateway,lease,serviceOwner,originalExpiry,originalCrl);
            }
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
    private void lateClosedOwner(ControlIdentity identity,String gateway,long lease,long serviceOwner,long originalExpiry,Intent connect)throws Exception{
        fixtureControl("connected"+Build.VERSION.SDK_INT);
        long deadline=SystemClock.elapsedRealtime()+600000;
        while(!"READINESS_HELD".equals(fixtureControl("state").get("state").getAsString())){
            assertTrue("Real owner refresh deadline",SystemClock.elapsedRealtime()<deadline);
            assertEquals(serviceOwner,ConnectionService.sessionId);echo(lease);Thread.sleep(500);
        }
        java.util.concurrent.CompletableFuture<byte[]> completion;
        long closedOwner;
        synchronized(RestrictedVault.LOCK){
            completion=FriendsRestricted.renewal(context,gateway);
            fixtureControl("response"+Build.VERSION.SDK_INT);
            awaitImportBlocked();status("LATE_HTTP_COMPLETED_IMPORT_PENDING",gateway,null);
            NativeRestricted.chatRelease(lease);
            context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));
            deadline=SystemClock.elapsedRealtime()+30000;
            while(!"off".equals(ConnectionService.status)&&SystemClock.elapsedRealtime()<deadline)Thread.sleep(50);
            assertEquals("off",ConnectionService.status);assertNotEquals(serviceOwner,ConnectionService.sessionId);
            closedOwner=ConnectionService.sessionId;
            assertTrue("Closed native lease cannot serve",NativeRestricted.chatState(lease)!=2);
            status("LATE_OWNER_CLOSED_BEFORE_IMPORT",gateway,null);
        }
        byte[] completed=completion.get(30,TimeUnit.SECONDS);
        try{
            assertNotNull("Actual HTTP completion after owner close",completed);
            assertTrue(NativeRestricted.validateDelivery(completed,identity.publicIdentity(),ControlTrust.anchor(context)));
        }finally{if(completed!=null)Arrays.fill(completed,(byte)0);}
        byte[] successor=cached(identity,gateway);assertNotNull("Validated successor in encrypted cache",successor);
        try{
            JsonObject response=JsonParser.parseString(new String(successor,StandardCharsets.UTF_8)).getAsJsonObject();
            assertTrue(response.get("expires_at").getAsLong()>originalExpiry);
            Thread.sleep(6000);
            assertEquals("No late automatic resurrection","off",ConnectionService.status);
            assertEquals(closedOwner,ConnectionService.sessionId);
            assertTrue("Old native lease stays closed",NativeRestricted.chatState(lease)!=2);
            assertTrue("Old native stream cannot reopen",NativeRestricted.chatOpen(lease,1000)<0);
            status("LATE_COMPLETION_IGNORED_CLOSED_OWNER",gateway,null);
            context.startForegroundService(connect);
            deadline=SystemClock.elapsedRealtime()+180000;
            while(!"on".equals(ConnectionService.status)){
                assertFalse(ConnectionService.failed);assertTrue(SystemClock.elapsedRealtime()<deadline);Thread.sleep(100);
            }
            assertNotEquals(closedOwner,ConnectionService.sessionId);assertNotEquals(serviceOwner,ConnectionService.sessionId);
            long next=borrow(successor,identity,new AutomaticVpnOwner(context));assertTrue(next>0);
            try{assertEquals(2,NativeRestricted.chatState(next));echo(next);}
            finally{NativeRestricted.chatRelease(next);}
            assertTrue(NativeRestricted.chatState(lease)!=2);
            status("LATE_NEW_EXPLICIT_CONNECT_NOT_RENEWAL",gateway,null);
        }finally{Arrays.fill(successor,(byte)0);}
    }
    private void legacyPeer(ControlIdentity identity,String gateway,long lease,long serviceOwner,long originalExpiry,Intent connect)throws Exception{
        fixtureControl("connected"+Build.VERSION.SDK_INT);
        long deadline=SystemClock.elapsedRealtime()+600000;
        byte[] successor=null;
        while(SystemClock.elapsedRealtime()<deadline){
            assertEquals(serviceOwner,ConnectionService.sessionId);assertEquals("on",ConnectionService.status);echo(lease);
            byte[] candidate=cached(identity,gateway);
            if(candidate!=null){
                JsonObject response=JsonParser.parseString(new String(candidate,StandardCharsets.UTF_8)).getAsJsonObject();
                if(response.get("expires_at").getAsLong()>originalExpiry){successor=candidate;break;}
                Arrays.fill(candidate,(byte)0);
            }
            Thread.sleep(500);
        }
        assertNotNull("Real HTTP validated and cached successor",successor);
        try{
            assertTrue(NativeRestricted.validateDelivery(successor,identity.publicIdentity(),ControlTrust.anchor(context)));
            status("LEGACY_HTTP_SUCCESSOR_CACHED",gateway,null);
            for(int attempt=0;attempt<10;attempt++){
                Thread.sleep(5000);
                assertEquals(serviceOwner,ConnectionService.sessionId);assertEquals("on",ConnectionService.status);
                assertFalse(ConnectionService.failed);assertEquals(2,NativeRestricted.chatState(lease));echo(lease);
                long changed=borrow(successor,identity,new AutomaticVpnOwner(context));
                try{assertEquals("Legacy peer cannot commit the successor fingerprint",0,changed);}
                finally{if(changed>0)NativeRestricted.chatRelease(changed);}
            }
            byte[] repeated=FriendsRestricted.renewal(context,gateway).get(15,TimeUnit.SECONDS);
            if(repeated!=null)Arrays.fill(repeated,(byte)0);
            assertEquals(serviceOwner,ConnectionService.sessionId);echo(lease);
            status("LEGACY_NO_UNAUTHENTICATED_PROFILE_COMMIT",gateway,null);
            NativeRestricted.chatRelease(lease);
            context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));
            deadline=SystemClock.elapsedRealtime()+30000;
            while(!"off".equals(ConnectionService.status)&&SystemClock.elapsedRealtime()<deadline)Thread.sleep(50);
            assertEquals("off",ConnectionService.status);long closedOwner=ConnectionService.sessionId;
            Thread.sleep(6000);
            assertEquals(closedOwner,ConnectionService.sessionId);assertEquals("off",ConnectionService.status);
            assertTrue(NativeRestricted.chatState(lease)!=2);assertTrue(NativeRestricted.chatOpen(lease,1000)<0);
            status("LEGACY_CLOSED_OWNER_STAYS_CLOSED",gateway,null);
            context.startForegroundService(connect);deadline=SystemClock.elapsedRealtime()+180000;
            while(!"on".equals(ConnectionService.status)){
                assertFalse(ConnectionService.failed);assertTrue(SystemClock.elapsedRealtime()<deadline);Thread.sleep(100);
            }
            assertNotEquals(serviceOwner,ConnectionService.sessionId);assertNotEquals(closedOwner,ConnectionService.sessionId);
            long next=borrow(successor,identity,new AutomaticVpnOwner(context));assertTrue(next>0);
            try{assertEquals(2,NativeRestricted.chatState(next));echo(next);}
            finally{NativeRestricted.chatRelease(next);}
            status("LEGACY_NEW_CONNECT_NOT_RENEWAL",gateway,null);
        }finally{Arrays.fill(successor,(byte)0);}
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
        NativeRestricted.load();
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
                    servicePath(identity,gateway,predecessor,settings);return;
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
