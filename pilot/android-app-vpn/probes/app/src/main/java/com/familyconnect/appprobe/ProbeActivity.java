package com.familyconnect.appprobe;

import android.app.Activity;
import android.os.Bundle;
import android.os.Process;
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import java.io.File;
import java.io.FileOutputStream;
import java.net.InetAddress;
import java.net.URL;
import java.security.KeyStore;
import java.security.cert.CertificateFactory;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManagerFactory;
import org.json.JSONArray;
import org.json.JSONObject;

public final class ProbeActivity extends Activity {
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        String nonce=getIntent().getStringExtra("nonce");
        if(nonce==null||!nonce.matches("[a-f0-9-]{36}")||!(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"))){finish();return;}
        new Thread(()->{
            JSONObject result=new JSONObject();
            try{
                result.put("nonce",nonce).put("uid",Process.myUid()).put("package",getPackageName());
                ConnectivityManager manager=getSystemService(ConnectivityManager.class);
                NetworkCapabilities network=manager.getNetworkCapabilities(manager.getActiveNetwork());
                result.put("vpn_capability",network!=null&&network.hasTransport(NetworkCapabilities.TRANSPORT_VPN));
                JSONArray dns=new JSONArray();
                java.util.concurrent.ExecutorService resolver=java.util.concurrent.Executors.newSingleThreadExecutor();
                java.util.concurrent.Future<InetAddress[]> lookup=resolver.submit(()->InetAddress.getAllByName("example.com"));
                try{for(InetAddress address:lookup.get(3,java.util.concurrent.TimeUnit.SECONDS))dns.put(address.getHostAddress());result.put("dns",dns);}
                catch(Exception failure){result.put("dns_error",failure.getClass().getSimpleName());}
                finally{lookup.cancel(true);resolver.shutdownNow();}
                KeyStore trust=KeyStore.getInstance(KeyStore.getDefaultType());trust.load(null);
                try(var certificate=getAssets().open("routing-ca.pem")){trust.setCertificateEntry("fixture",CertificateFactory.getInstance("X.509").generateCertificate(certificate));}
                TrustManagerFactory factory=TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());factory.init(trust);
                SSLContext tls=SSLContext.getInstance("TLS");tls.init(null,factory.getTrustManagers(),null);
                for(String family:new String[]{"ipv4","ipv6"}){
                    HttpsURLConnection connection=null;
                    try{
                        URL url=new URL("https://"+(family.equals("ipv4")?"10.0.2.2":"[fd79:fc::1]")+":51904/"+nonce);
                        connection=(HttpsURLConnection)url.openConnection();connection.setSSLSocketFactory(tls.getSocketFactory());connection.setConnectTimeout(4000);connection.setReadTimeout(4000);
                        try(var body=connection.getInputStream()){
                            java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();byte[] buffer=new byte[256];int count;
                            while((count=body.read(buffer))!=-1){if(bytes.size()+count>1024)throw new java.io.IOException("RESPONSE_LIMIT");bytes.write(buffer,0,count);}
                            result.put(family,bytes.toString("UTF-8"));
                            result.put(family+"_tls",connection.getCipherSuite());
                        }
                    }catch(Exception failure){result.put(family+"_error",failure.getClass().getSimpleName());}
                    finally{if(connection!=null)connection.disconnect();}
                }
            }catch(Exception failure){try{result.put("setup_error",failure.getClass().getSimpleName());}catch(Exception ignored){}}
            try(FileOutputStream output=new FileOutputStream(new File(getFilesDir(),"routing-result.json"))){output.write(result.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));}
            catch(Exception ignored){}
            runOnUiThread(this::finish);
        },"routing-probe").start();
    }
}
