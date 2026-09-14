package com.familyconnect.app;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.PowerManager;
import android.os.SystemClock;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.net.*;
import java.nio.charset.StandardCharsets;
import static org.junit.Assert.*;

/** Synthetic emulator acceptance; no real profile, production server or mobile-radio claim. */
@RunWith(AndroidJUnit4.class)
public class ManualAwgStabilityTest {
    final AwgRuntimeTest helper=new AwgRuntimeTest();
    final AutoRuntimeTest control=new AutoRuntimeTest();
    final Context context=helper.context;

    void start(){context.startForegroundService(new Intent(context,ConnectionService.class)
        .setAction("connect").putExtra("transport","awg"));}
    void stop()throws Exception{
        context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));
        helper.waitState("off");helper.clean();
    }
    void waitHealth(String expected)throws Exception{
        long until=SystemClock.elapsedRealtime()+30000;
        while(SystemClock.elapsedRealtime()<until){
            if(expected.equals(ConnectionService.healthStatus))return;
            SystemClock.sleep(100);
        }
        fail("Manual health did not reach "+expected+": "+ConnectionService.healthStatus);
    }
    void assertBlackhole()throws Exception{
        try(DatagramSocket socket=new DatagramSocket(new InetSocketAddress("10.78.0.4",0))){
            socket.setSoTimeout(1500);
            byte[] bytes="synthetic-outage-probe".getBytes(StandardCharsets.US_ASCII);
            socket.send(new DatagramPacket(bytes,bytes.length,InetAddress.getByName("198.19.0.1"),18765));
            try{socket.receive(new DatagramPacket(new byte[128],128));fail("Fixture did not block UDP");}
            catch(SocketTimeoutException expected){}
        }
    }
    @Test public void screenOffOutageRecoveryAndExplicitDisconnect()throws Exception{
        assertTrue(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));
        helper.clean();
        helper.shell("appops set "+context.getPackageName()+" ACTIVATE_VPN allow");
        helper.shell("pm grant "+context.getPackageName()+" android.permission.POST_NOTIFICATIONS");
        Activity activity=InstrumentationRegistry.getInstrumentation().startActivitySync(
            new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        ProfileStore store=new ProfileStore(context,Transport.AWG);
        try{
            control.control("up");store.save(ProfileValidator.validate(AwgRuntimeTest.profile(Transport.AWG),Transport.AWG));
            start();helper.waitState("on");waitHealth("ok");helper.traffic(Transport.AWG);
            helper.shell("input keyevent 223");SystemClock.sleep(1000);
            assertFalse("Display did not sleep",context.getSystemService(PowerManager.class).isInteractive());
            SystemClock.sleep(5000);assertTrue("VPN disappeared while display was off",helper.vpn());
            helper.shell("input keyevent 224");helper.shell("wm dismiss-keyguard");
            helper.traffic(Transport.AWG);
            control.control("udp-down");assertBlackhole();SystemClock.sleep(20000);
            waitHealth("unavailable");assertEquals("on",ConnectionService.status);assertTrue(helper.vpn());
            control.control("up");long restored=SystemClock.elapsedRealtime();
            helper.traffic(Transport.AWG);
            long recovery=SystemClock.elapsedRealtime()-restored;
            assertTrue("Restored UDP exceeded 30s budget",recovery<30000);
            assertEquals("awg",ConnectionService.activeTransport);waitHealth("ok");
            long previousSession=ConnectionService.sessionId;stop();
            // Explicit disconnect during another outage must remain terminal after link recovery.
            start();helper.waitState("on");waitHealth("ok");helper.traffic(Transport.AWG);
            assertNotEquals("Session identity reused after service restart",previousSession,ConnectionService.sessionId);
            control.control("udp-down");assertBlackhole();
            long cancelled=SystemClock.elapsedRealtime();stop();
            assertTrue("Disconnect exceeded 5s",SystemClock.elapsedRealtime()-cancelled<5000);
            control.control("up");SystemClock.sleep(5000);
            assertEquals("off",ConnectionService.status);assertEquals("off",ConnectionService.healthStatus);helper.clean();assertTrue(store.exists());
            android.util.Log.i("FamilyConnect","MANUAL AWG STABILITY PASS: screen off 5s, UDP outage 20s, recovery_ms="+recovery+", disconnect during outage remains off");
        }finally{
            helper.shell("input keyevent 224");helper.shell("wm dismiss-keyguard");
            try{control.control("up");}finally{
                context.stopService(new Intent(context,ConnectionService.class));store.clear();
                InstrumentationRegistry.getInstrumentation().runOnMainSync(activity::finish);
            }
        }
    }
}
