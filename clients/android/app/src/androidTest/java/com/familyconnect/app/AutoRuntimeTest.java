package com.familyconnect.app;
import android.app.Activity;
import android.content.*;
import android.net.*;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class AutoRuntimeTest {
 final AwgRuntimeTest helper=new AwgRuntimeTest();final Context context=helper.context;
 void control(String mode)throws Exception{
  ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
  for(Network network:manager.getAllNetworks()){
   NetworkCapabilities c=manager.getNetworkCapabilities(network);if(c==null||c.hasTransport(NetworkCapabilities.TRANSPORT_VPN)||!c.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET))continue;
   try(Socket s=network.getSocketFactory().createSocket()){
    s.connect(new java.net.InetSocketAddress("10.0.2.2",51902),3000);s.setSoTimeout(3000);
    s.getOutputStream().write(("GET /"+mode+" HTTP/1.0\r\nHost: fixture\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
    byte[] b=new byte[512];int n=s.getInputStream().read(b);assertTrue(n>0&&new String(b,0,n,StandardCharsets.US_ASCII).contains(" 200 "));return;
   }
  }throw new AssertionError("No emulator control network");
 }
 void start(){context.startForegroundService(new Intent(context,ConnectionService.class).setAction("connect").putExtra("transport","auto"));}
 void on(String type)throws Exception{
  long until=System.currentTimeMillis()+90000;while(System.currentTimeMillis()<until){if(ConnectionService.status.equals("on")&&ConnectionService.activeTransport.equals(type))return;Thread.sleep(100);}fail("Auto did not reach "+type+": "+ConnectionService.status+"/"+ConnectionService.activeTransport);
 }
 void off()throws Exception{
  long until=System.currentTimeMillis()+90000;while(!ConnectionService.status.equals("off")&&System.currentTimeMillis()<until)Thread.sleep(100);
  assertEquals("off",ConnectionService.status);helper.clean();assertEquals(0,NativeTcp.connections(0));Thread.sleep(500);
 }
 void stop()throws Exception{context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));off();}
 @Test public void automaticFallbackHealthLossExhaustionCancelAndRevoke()throws Exception{
  assertTrue(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));helper.clean();
  helper.shell("appops set "+context.getPackageName()+" ACTIVATE_VPN allow");helper.shell("pm grant "+context.getPackageName()+" android.permission.POST_NOTIFICATIONS");
  Activity activity=InstrumentationRegistry.getInstrumentation().startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
  ProfileStore wg=new ProfileStore(context,Transport.WG),awg=new ProfileStore(context,Transport.AWG),tcp=new ProfileStore(context,Transport.TCP);
  try{
   wg.save(ProfileValidator.validate(AwgRuntimeTest.profile(Transport.WG)));awg.save(ProfileValidator.validate(AwgRuntimeTest.profile(Transport.AWG),Transport.AWG));tcp.save(TcpProfile.validate(TcpRuntimeTest.profile()));
   control("wg-down");start();on("awg");helper.traffic(Transport.AWG);
   control("udp-down");on("tcp");new TcpRuntimeTest().traffic();stop();
   control("up");start();on("wg");helper.traffic(Transport.WG);stop();
   control("all-down");start();Thread.sleep(500);off();assertTrue(ConnectionService.failed);
   start();Thread.sleep(500);stop();Thread.sleep(3000);assertEquals("off",ConnectionService.status);helper.clean();
   control("up");start();on("wg");helper.shell("appops set "+context.getPackageName()+" ACTIVATE_VPN deny");helper.revokeThroughSystemDialog();off();assertNotNull(VpnService.prepare(context));
   assertTrue(wg.exists());assertTrue(awg.exists());assertTrue(tcp.exists());
   android.util.Log.i("FamilyConnect","AUTO PASS: blocked WG to AWG, live AWG loss to TCP, WG priority, exhaustion, cancel, system revoke; 12 UDP, 6 REALITY HTTP, 1 OS DNS; 5 cleanup scenarios");
  }finally{control("up");context.stopService(new Intent(context,ConnectionService.class));wg.clear();awg.clear();tcp.clear();InstrumentationRegistry.getInstrumentation().runOnMainSync(activity::finish);}
 }
}
