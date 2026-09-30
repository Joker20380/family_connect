package com.familyconnect.app;

import android.app.Activity;
import android.content.Intent;
import android.net.VpnService;
import android.os.Bundle;

public final class RestrictedDiagnosticActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if("stop".equals(getIntent().getStringExtra("mode"))){
            startService(new Intent(this,ConnectionService.class).setAction("disconnect"));
            finish();return;
        }
        if("probe".equals(getIntent().getStringExtra("mode"))){probe();return;}
        if("failure-probe".equals(getIntent().getStringExtra("mode"))){failureProbe();return;}
        Intent permission=VpnService.prepare(this);
        if(permission!=null) startActivityForResult(permission,6); else begin();
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(request==6&&result==RESULT_OK)begin();else finish();
    }
    private void begin() {
        String mode=getIntent().getStringExtra("mode");
        if(!"refresh".equals(mode)&&!"recover".equals(mode)){finish();return;}
        startForegroundService(new Intent(this,ConnectionService.class).setAction("connect")
            .putExtra("transport","refresh".equals(mode)?"restricted-refresh":"restricted")
            .putExtra("control",getIntent().getStringExtra("control")));
        finish();
    }
    private void probe() {
        new Thread(()->{
            org.json.JSONObject result=new org.json.JSONObject();
            try {
                android.net.ConnectivityManager manager=getSystemService(android.net.ConnectivityManager.class);
                android.net.NetworkCapabilities network=manager.getNetworkCapabilities(manager.getActiveNetwork());
                boolean vpn=network!=null&&network.hasTransport(android.net.NetworkCapabilities.TRANSPORT_VPN);
                result.put("vpn_active",vpn);
                if(!vpn)throw new IllegalStateException("VPN required");
                org.json.JSONArray https=new org.json.JSONArray();
                for(String host:new String[]{"example.com","example.org"}) {
                    javax.net.ssl.HttpsURLConnection connection=(javax.net.ssl.HttpsURLConnection)new java.net.URL("https://"+host+"/?fc6="+System.nanoTime()).openConnection();
                    connection.setConnectTimeout(15000);connection.setReadTimeout(15000);connection.setInstanceFollowRedirects(false);
                    try {
                        org.json.JSONObject request=new org.json.JSONObject();request.put("site",host);
                        request.put("status",connection.getResponseCode());request.put("tls_verified",connection.getCipherSuite()!=null);
                        https.put(request);
                    }finally{connection.disconnect();}
                }
                result.put("https",https);
                try { java.net.InetAddress.getAllByName("fc6-"+System.nanoTime()+".example.com");result.put("nxdomain",false); }
                catch(java.net.UnknownHostException expected){result.put("nxdomain",true);}
                try(java.net.DatagramSocket socket=new java.net.DatagramSocket()) {
                    byte[] payload=new byte[]{70,67,54};
                    socket.send(new java.net.DatagramPacket(payload,payload.length,java.net.InetAddress.getByName("1.1.1.1"),443));
                    result.put("udp443_probe_sent",true);
                }
                try(java.net.Socket socket=new java.net.Socket()) {
                    socket.connect(new java.net.InetSocketAddress("2606:4700:4700::1111",443),3000);
                    result.put("ipv6_failed_closed",false);
                } catch(java.io.IOException expected){result.put("ipv6_failed_closed",true);}
                result.put("owner_transport",ConnectionService.activeTransport);
                result.put("owner_health",ConnectionService.healthStatus);
            }catch(Exception failure){try{result.put("probe_failed",true);}catch(Exception ignored){}}
            try(java.io.FileOutputStream output=openFileOutput("restricted-probes.json",MODE_PRIVATE)) {
                output.write(result.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
            }catch(Exception ignored){}
            runOnUiThread(this::finish);
        },"fc-restricted-probe").start();
    }
    private void failureProbe() {
        new Thread(()->{
            org.json.JSONObject result=new org.json.JSONObject();
            try {
                android.net.ConnectivityManager manager=getSystemService(android.net.ConnectivityManager.class);
                android.net.NetworkCapabilities before=manager.getNetworkCapabilities(manager.getActiveNetwork());
                result.put("vpn_before",before!=null&&before.hasTransport(android.net.NetworkCapabilities.TRANSPORT_VPN));
                if(!result.getBoolean("vpn_before"))throw new IllegalStateException("VPN required");
                try(java.net.Socket socket=new java.net.Socket()) {
                    socket.connect(new java.net.InetSocketAddress("1.1.1.1",443),5000);
                    result.put("ordinary_tcp_failed",false);
                }catch(java.io.IOException expected){result.put("ordinary_tcp_failed",true);}
                android.net.NetworkCapabilities after=manager.getNetworkCapabilities(manager.getActiveNetwork());
                result.put("vpn_after",after!=null&&after.hasTransport(android.net.NetworkCapabilities.TRANSPORT_VPN));
                result.put("owner_health",ConnectionService.healthStatus);
            }catch(Exception failure){try{result.put("probe_failed",true);}catch(Exception ignored){}}
            try(java.io.FileOutputStream output=openFileOutput("restricted-failure-probe.json",MODE_PRIVATE)) {
                output.write(result.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
            }catch(Exception ignored){}
            runOnUiThread(this::finish);
        },"fc-restricted-failure-probe").start();
    }
}
