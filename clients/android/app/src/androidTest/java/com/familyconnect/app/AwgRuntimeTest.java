package com.familyconnect.app;
import android.app.Activity;
import android.content.*;
import android.net.*;
import android.os.ParcelFileDescriptor;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class AwgRuntimeTest {
    final Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
    static String profile(Transport type){
        String address=type==Transport.WG?"10.77.0.4/32, fd77:92::4/128":"10.78.0.4/32, fd78:92::4/128";
        String awg=type==Transport.WG?"":"Jc = 3\nJmin = 40\nJmax = 80\nS1 = 17\nS2 = 29\nS3 = 3\nS4 = 9\nH1 = 1001-1010\nH2 = 2001-2010\nH3 = 3001-3010\nH4 = 4001-4010\nI1 = <b 0x11223344><r 16>\n";
        return "[Interface]\nPrivateKey = AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=\nAddress = "+address+"\nDNS = 1.1.1.1\nMTU = 1280\n"+awg+"[Peer]\nPublicKey = zo060cy2M+x7cMF4FKXHbs0CloUFDTRHRboFhw5YfVk=\nEndpoint = 10.0.2.2:"+(type==Transport.WG?51820:51821)+"\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n";
    }
    void shell(String command)throws Exception{try(ParcelFileDescriptor fd=InstrumentationRegistry.getInstrumentation().getUiAutomation().executeShellCommand(command);InputStream in=new ParcelFileDescriptor.AutoCloseInputStream(fd)){while(in.read()!=-1){}}}
    void waitState(String state)throws Exception{
        long until=System.currentTimeMillis()+30000;
        while(System.currentTimeMillis()<until){if(ConnectionService.status.equals(state))return;if(ConnectionService.failed)fail("Service failed: "+ConnectionService.status);Thread.sleep(100);}
        fail("State timeout: "+ConnectionService.status);
    }
    boolean vpn(){ConnectivityManager cm=context.getSystemService(ConnectivityManager.class);for(Network n:cm.getAllNetworks()){NetworkCapabilities c=cm.getNetworkCapabilities(n);if(c!=null&&c.hasTransport(NetworkCapabilities.TRANSPORT_VPN))return true;}return false;}
    void clean()throws Exception{long until=System.currentTimeMillis()+15000;while(vpn()&&System.currentTimeMillis()<until)Thread.sleep(100);assertFalse("VPN remains",vpn());}
    void traffic(Transport type)throws Exception{
        String[] sources=type==Transport.WG?new String[]{"10.77.0.4","fd77:92::4"}:new String[]{"10.78.0.4","fd78:92::4"};
        String[] targets={"198.19.0.1","fd78:fccc::1"};
        for(int family=0;family<2;family++)try(DatagramSocket socket=new DatagramSocket(new InetSocketAddress(InetAddress.getByName(sources[family]),0))){
            socket.setSoTimeout(2500);
            for(int i=0;i<3;i++){
                byte[] nonce=UUID.randomUUID().toString().getBytes(StandardCharsets.US_ASCII);boolean received=false;
                for(int attempt=0;attempt<4&&!received;attempt++){
                    socket.send(new DatagramPacket(nonce,nonce.length,InetAddress.getByName(targets[family]),18765));
                    DatagramPacket reply=new DatagramPacket(new byte[128],128);
                    try{socket.receive(reply);received=Arrays.equals(nonce,Arrays.copyOf(reply.getData(),reply.getLength()));}catch(SocketTimeoutException ignored){}
                }
                assertTrue("Encrypted UDP echo failed: "+type+" family="+family,received);
            }
        }
    }
    @Test public void profilesDataSwitchCancelAndRevoke()throws Exception{
        assertTrue(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));assertFalse(vpn());
        shell("appops set "+context.getPackageName()+" ACTIVATE_VPN allow");shell("pm grant "+context.getPackageName()+" android.permission.POST_NOTIFICATIONS");
        Activity activity=InstrumentationRegistry.getInstrumentation().startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        ProfileStore wg=new ProfileStore(context,Transport.WG),awg=new ProfileStore(context,Transport.AWG);
        try{
            wg.save(ProfileValidator.validate(profile(Transport.WG),Transport.WG));awg.save(ProfileValidator.validate(profile(Transport.AWG),Transport.AWG));
            assertEquals(ProfileValidator.validate(profile(Transport.WG),Transport.WG),wg.load());assertTrue(awg.load().contains("Jc = 3"));
            awg.clear();assertTrue(wg.exists());assertFalse(awg.exists());awg.save(ProfileValidator.validate(profile(Transport.AWG),Transport.AWG));
            for(Transport type:new Transport[]{Transport.WG,Transport.AWG,Transport.WG,Transport.AWG}){
                context.startForegroundService(new Intent(context,ConnectionService.class).setAction("connect").putExtra("transport",type.id));
                waitState("on");assertEquals(type.id,ConnectionService.activeTransport);traffic(type);
                context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));waitState("off");clean();
            }
            context.startForegroundService(new Intent(context,ConnectionService.class).setAction("connect").putExtra("transport","awg"));
            context.startService(new Intent(context,ConnectionService.class).setAction("disconnect"));Thread.sleep(500);waitState("off");clean();
            context.startForegroundService(new Intent(context,ConnectionService.class).setAction("connect").putExtra("transport","awg"));waitState("on");
            shell("appops set "+context.getPackageName()+" ACTIVATE_VPN deny");waitState("off");clean();
            assertTrue(wg.exists());assertTrue(awg.exists());
        }finally{
            context.stopService(new Intent(context,ConnectionService.class));wg.clear();awg.clear();
            InstrumentationRegistry.getInstrumentation().runOnMainSync(activity::finish);
        }
    }
}
