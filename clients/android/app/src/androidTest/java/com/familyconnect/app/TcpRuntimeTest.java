package com.familyconnect.app;
import android.app.Activity;
import android.content.*;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class TcpRuntimeTest {
 final AwgRuntimeTest helper=new AwgRuntimeTest();final Context context=helper.context;
 static String profile(){return "{\"type\":\"vless-reality-v1\",\"server\":\"10.0.2.2\",\"port\":51900,\"id\":\"11111111-2222-4333-8444-555555555555\",\"public_key\":\"zo060cy2M-x7cMF4FKXHbs0CloUFDTRHRboFhw5YfVk\",\"server_name\":\"android.test\",\"short_id\":\"0102030405060708\"}";}
 void start(String transport)throws Exception{context.startForegroundService(new Intent(context,ConnectionService.class).setAction("connect").putExtra("transport",transport));helper.waitState("on");}
 void stop()throws Exception{context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));helper.waitState("off");helper.clean();assertEquals(0,NativeTcp.connections(0));}
 void traffic()throws Exception{
  for(int family=0;family<2;family++)for(int i=0;i<3;i++){
   String nonce="/"+UUID.randomUUID();
   try(Socket socket=new Socket()){
    socket.bind(new InetSocketAddress(family==0?"10.79.0.2":"fd79:fc::2",0));socket.connect(new InetSocketAddress(family==0?"198.19.1.1":"fd79:fc::1",18080),10000);socket.setSoTimeout(15000);
    socket.getOutputStream().write(("GET "+nonce+" HTTP/1.1\r\nHost: android.test\r\nConnection: close\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
    ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[1024];int n;while((n=socket.getInputStream().read(buffer))!=-1){assertTrue(bytes.size()+n<=8192);bytes.write(buffer,0,n);}
    String reply=bytes.toString("US-ASCII");assertTrue(reply.contains(" 200 "));assertTrue(reply.endsWith(nonce));
   }
  }
  String name=UUID.randomUUID()+".fc-tcp.invalid";Set<String> addresses=new HashSet<>();for(InetAddress a:InetAddress.getAllByName(name))addresses.add(a.getHostAddress());
  assertTrue(addresses.contains("198.19.1.1"));
 }
 @Test public void realityDataSwitchCancelRevokeAndProtectedStorage()throws Exception{
  assertTrue(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));helper.clean();
  helper.shell("appops set "+context.getPackageName()+" ACTIVATE_VPN allow");helper.shell("pm grant "+context.getPackageName()+" android.permission.POST_NOTIFICATIONS");
  Activity activity=InstrumentationRegistry.getInstrumentation().startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
  ProfileStore tcp=new ProfileStore(context,Transport.TCP),wg=new ProfileStore(context,Transport.WG),awg=new ProfileStore(context,Transport.AWG);
  try{
   tcp.save(TcpProfile.validate(profile()));wg.save(ProfileValidator.validate(AwgRuntimeTest.profile(Transport.WG)));awg.save(ProfileValidator.validate(AwgRuntimeTest.profile(Transport.AWG),Transport.AWG));
   assertEquals(TcpProfile.validate(profile()),tcp.load());tcp.clear();assertTrue(wg.exists());assertTrue(awg.exists());tcp.save(TcpProfile.validate(profile()));
   for(String t:new String[]{"tcp","wg","tcp","awg","tcp"}){
    android.util.Log.i("FamilyConnect","TCP integration connect "+t);start(t);
    if(t.equals("tcp"))traffic();else helper.traffic(Transport.parse(t));stop();
   }
   context.startForegroundService(new Intent(context,ConnectionService.class).setAction("connect").putExtra("transport","tcp"));context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));Thread.sleep(500);helper.waitState("off");helper.clean();assertEquals(0,NativeTcp.connections(0));
   start("tcp");helper.shell("appops set "+context.getPackageName()+" ACTIVATE_VPN deny");helper.revokeThroughSystemDialog();helper.waitState("off");helper.clean();assertEquals(0,NativeTcp.connections(0));
   assertNotNull(android.net.VpnService.prepare(context));assertTrue(tcp.exists());assertTrue(wg.exists());assertTrue(awg.exists());
   android.util.Log.i("FamilyConnect","TCP PASS: 18 REALITY HTTP, 3 OS DNS, 12 WG/AWG UDP, 5 stops, cancel and revoke");
  }finally{context.stopService(new Intent(context,ConnectionService.class));tcp.clear();wg.clear();awg.clear();InstrumentationRegistry.getInstrumentation().runOnMainSync(activity::finish);}
 }
}
