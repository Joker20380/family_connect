package com.familyconnect.app;

import android.content.Context;
import android.os.Build;
import android.os.Bundle;
import androidx.test.platform.app.InstrumentationRegistry;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.KeyStore;
import java.security.cert.CertificateFactory;
import java.util.Arrays;
import java.util.Base64;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManagerFactory;
import org.junit.Test;
import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;

public class OnlineReadinessProbeTest {
    @Test public void retainActualHttpRejectionWithoutImporting()throws Exception{
        assumeTrue("true".equals(InstrumentationRegistry.getArguments().getString("fc_core_probe")));
        assertTrue(Build.FINGERPRINT.contains("generic")||Build.MODEL.contains("sdk"));
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        Context tests=InstrumentationRegistry.getInstrumentation().getContext();
        assertEquals("com.familyconnect.app.friends",context.getPackageName());
        assertEquals("off",ConnectionService.status);
        KeyStore roots=KeyStore.getInstance(KeyStore.getDefaultType());roots.load(null);
        try(InputStream input=tests.getAssets().open("core-ca.pem")){roots.setCertificateEntry("isolated-core",CertificateFactory.getInstance("X.509").generateCertificate(input));}
        TrustManagerFactory trust=TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());trust.init(roots);
        SSLContext tls=SSLContext.getInstance("TLS");tls.init(null,trust.getTrustManagers(),null);
        SSLSocketFactory previous=HttpsURLConnection.getDefaultSSLSocketFactory();
        HttpsURLConnection.setDefaultSSLSocketFactory(tls.getSocketFactory());
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            NativeRestricted.load();
            for(String gateway:new String[]{RestrictedGateway.PRIMARY,RestrictedGateway.SECONDARY}){
                byte[] raw=new FriendsAccessAndroid(context,true).restrictedReadiness(identity,new OwnerPrewarmReceipt(),gateway);
                try{
                    long now=System.currentTimeMillis();
                    int code=NativeRestricted.validationCode(raw,identity.publicIdentity(),ControlTrust.anchor(context));
                    JsonObject captured=new JsonObject();captured.add("response",JsonParser.parseString(new String(raw,StandardCharsets.UTF_8)));
                    captured.addProperty("public",Base64.getEncoder().encodeToString(identity.publicIdentity()));
                    captured.addProperty("anchor",Base64.getEncoder().encodeToString(ControlTrust.anchor(context)));
                    captured.addProperty("now",now/1000);captured.addProperty("now_ns",now*1000000);
                    Files.write(new java.io.File(context.getNoBackupFilesDir(),"core-probe-"+gateway+".json").toPath(),captured.toString().getBytes(StandardCharsets.UTF_8));
                    Bundle result=new Bundle();result.putString("gateway",gateway);result.putInt("native_validation",code);result.putLong("wall_ms",now);
                    InstrumentationRegistry.getInstrumentation().sendStatus(2,result);
                }finally{Arrays.fill(raw,(byte)0);}
            }
        }finally{HttpsURLConnection.setDefaultSSLSocketFactory(previous);}
    }
}
