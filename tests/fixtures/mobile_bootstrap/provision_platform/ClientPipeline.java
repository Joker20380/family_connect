package com.familyconnect.app;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.*;
import java.security.cert.Certificate;
import java.security.spec.AlgorithmParameterSpec;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.crypto.*;

public final class ClientPipeline {
    private static final Map<String,SecretKey> keys=new HashMap<>();
    public static final class Store extends KeyStoreSpi {
        public Key engineGetKey(String alias,char[] password){return keys.get(alias);}
        public boolean engineContainsAlias(String alias){return keys.containsKey(alias);}
        public Certificate[] engineGetCertificateChain(String alias){return null;}public Certificate engineGetCertificate(String alias){return null;}
        public Date engineGetCreationDate(String alias){return null;}public int engineSize(){return keys.size();}
        public Enumeration<String> engineAliases(){return Collections.enumeration(keys.keySet());}
        public void engineSetKeyEntry(String alias,Key key,char[] password,Certificate[] chain){throw new AssertionError();}
        public void engineSetKeyEntry(String alias,byte[] key,Certificate[] chain){throw new AssertionError();}
        public void engineSetCertificateEntry(String alias,Certificate certificate){throw new AssertionError();}
        public void engineDeleteEntry(String alias){throw new AssertionError();}
        public boolean engineIsKeyEntry(String alias){return keys.containsKey(alias);}public boolean engineIsCertificateEntry(String alias){return false;}
        public String engineGetCertificateAlias(Certificate certificate){return null;}
        public void engineStore(OutputStream output,char[] password){throw new AssertionError();}public void engineLoad(InputStream input,char[] password){}
    }
    public static final class Generator extends KeyGeneratorSpi {
        private String alias;
        protected void engineInit(SecureRandom random){throw new AssertionError();}
        protected void engineInit(int size,SecureRandom random){throw new AssertionError();}
        protected void engineInit(AlgorithmParameterSpec parameters,SecureRandom random){alias=((KeyGenParameterSpec)parameters).alias;}
        protected SecretKey engineGenerateKey(){try{KeyGenerator generator=KeyGenerator.getInstance("AES","SunJCE");generator.init(256);SecretKey key=generator.generateKey();keys.put(alias,key);return key;}catch(Exception error){throw new AssertionError(error);}}
    }
    public static void main(String[] args)throws Exception {
        Provider provider=new Provider("AndroidKeyStore","1","Isolated OS keystore boundary"){};
        provider.put("KeyStore.AndroidKeyStore",Store.class.getName());provider.put("KeyGenerator.AES",Generator.class.getName());Security.addProvider(provider);
        URL.setURLStreamHandlerFactory(protocol->protocol.equals("https")?new URLStreamHandler(){protected URLConnection openConnection(URL address)throws IOException{throw new SocketTimeoutException("Isolated direct HTTPS disabled");}}:null);
        Context context=new Context();
        byte[] material=Files.readAllBytes(Path.of(System.getProperty("fixture.identity")));
        KeyGenerator generator=KeyGenerator.getInstance("AES","AndroidKeyStore");generator.init(new KeyGenParameterSpec.Builder("family-connect-friends-identity-v1",3).build());
        Files.write(new File(context.getNoBackupFilesDir(),"friends-identity.enc").toPath(),ControlIdentityEnvelope.seal(generator.generateKey(),material));Arrays.fill(material,(byte)0);
        if(new RestrictedVault(context).read()!=null)throw new AssertionError("Readiness must be absent");
        AtomicBoolean cancelled=new AtomicBoolean(),connected=new AtomicBoolean();
        AutomaticVpnOwner owner=new AutomaticVpnOwner(context);owner.open(()->cancelled.set(true));
        RestrictedTunnelEngine engine=new RestrictedTunnelEngine(context,cancelled::get,connected::set,owner,android.os.SystemClock.elapsedRealtime()+30000,false,RestrictedGateway.PRIMARY);
        try{
            if(Boolean.getBoolean("fixture.late")){
                java.util.concurrent.CompletableFuture<Throwable> outcome=new java.util.concurrent.CompletableFuture<>();
                new Thread(()->{try{engine.up("");outcome.complete(null);}catch(Throwable failure){outcome.complete(failure);}}).start();
                if(!NativeRestricted.delivered.await(8,java.util.concurrent.TimeUnit.SECONDS))throw new AssertionError("No real delivery to delay");
                cancelled.set(true);
                Throwable failure=outcome.get(2,java.util.concurrent.TimeUnit.SECONDS);
                if(!(failure instanceof ConnectivityOrchestrator.Rejected)||((ConnectivityOrchestrator.Rejected)failure).category!=ConnectivityOrchestrator.Failure.CANCELLED)throw new AssertionError("Owner cancellation",failure);
                engine.down();owner.close();
                if(Boolean.getBoolean("fixture.identityChanged"))try(ControlIdentity replacement=ControlIdentity.generate()){
                    byte[] changed=replacement.material();
                    try{Files.write(new File(context.getNoBackupFilesDir(),"friends-identity.enc").toPath(),ControlIdentityEnvelope.seal(keys.get("family-connect-friends-identity-v1"),changed));}finally{Arrays.fill(changed,(byte)0);}
                }
                NativeRestricted.release.countDown();
                if(!Diagnostics.refreshed.await(3,java.util.concurrent.TimeUnit.SECONDS))throw new AssertionError("Refresh completion missing");
                if(Boolean.getBoolean("fixture.identityChanged")){
                    byte[] saved=new RestrictedVault(context).read();
                    try{if(saved!=null&&!ControlJson.parse(saved).getAsJsonObject().get("response").isJsonNull())throw new AssertionError("Previous identity delivery entered replacement cache");}finally{if(saved!=null)Arrays.fill(saved,(byte)0);}
                }else if(new RestrictedVault(context).read()==null)throw new AssertionError("Late verified bundle not processed");
                if(connected.get()||NativeRestricted.begins!=0)throw new AssertionError("Late response resurrected owner");
                System.out.println("PASS Disconnect before real provisioning response: no native/owner revival; replaced identity rejects old delivery="+Boolean.getBoolean("fixture.identityChanged"));return;
            }
            engine.up("");
            if(!connected.get()||!engine.healthy()||ChatNetworkAndroid.blocked==0||ControlRnsAndroid.blocked==0)throw new AssertionError("Cold path did not connect");
            if(Boolean.getBoolean("fixture.blackhole")&&(NativeRestricted.provisioningBudget<=0||NativeRestricted.provisioningBudget>10000))throw new AssertionError("Shared deadline budget not consumed");
            if(!ControlJson.parse(new ReadinessReceiptStore(context).read()).getAsJsonObject().get("ack_state").getAsString().equals("ACK_PENDING"))throw new AssertionError("Deferred receipt lost or claimed as received");
            byte[] stored=new RestrictedVault(context).read();if(stored==null)throw new AssertionError("No encrypted cache");
            byte[] disk=Files.readAllBytes(new File(context.getNoBackupFilesDir(),"restricted-readiness.enc").toPath());
            if(Arrays.equals(stored,disk)||disk[0]!=1)throw new AssertionError("Cache not encrypted");
            Arrays.fill(stored,(byte)0);
            if(!NativeRestricted.call("traffic").get("passed").getAsBoolean())throw new AssertionError("Native traffic");
            cancelled.set(true);
            try{engine.up("");throw new AssertionError("Disconnected owner restarted");}catch(ConnectivityOrchestrator.Rejected expected){if(expected.category!=ConnectivityOrchestrator.Failure.CANCELLED)throw expected;}
        }finally{engine.down();owner.close();}
        System.out.println("PASS actual FriendsReadinessProtocol/validator/encrypted RestrictedVault/AutomaticVpnOwner/RestrictedTunnelEngine/native MESH/TCP/DNS/verified HTTPS; OS and JNI boundaries are fixtures");
        System.out.println("PASS wall-clock modeled blackholes: HTTPS TLS/write15s + RNS5s; provisioning fits the remaining unchanged30s deadline");
    }
}
