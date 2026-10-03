package com.familyconnect.app;

import android.net.ConnectivityManager;
import android.net.LinkProperties;
import android.net.Network;
import android.os.SystemClock;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class AutoTcpAddressRuntimeTest {
    @Test public void automaticTcpBuilderAssignsBothFamilies() throws Exception {
        AwgRuntimeTest helper=new AwgRuntimeTest();
        assertTrue(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));
        helper.clean();
        helper.shell("appops set "+helper.context.getPackageName()+" ACTIVATE_VPN allow");
        AutomaticVpnOwner owner=new AutomaticVpnOwner(helper.context);
        AutomaticNormalEngine engine=new AutomaticNormalEngine(helper.context,owner,Transport.TCP);
        try {
            owner.open(()->{});
            engine.up(TcpRuntimeTest.profile());
            ConnectivityManager manager=helper.context.getSystemService(ConnectivityManager.class);
            long deadline=SystemClock.elapsedRealtime()+10000;
            LinkProperties link=null;
            while(SystemClock.elapsedRealtime()<deadline) {
                Network network=new VpnHealth(helper.context).find("10.79.0.2");
                if(network!=null)link=manager.getLinkProperties(network);
                if(link!=null&&link.getDnsServers().contains(java.net.InetAddress.getByName("1.1.1.1")))break;
                SystemClock.sleep(100);
            }
            assertNotNull("Auto TCP network missing",link);
            java.net.InetAddress ipv4=java.net.InetAddress.getByName("10.79.0.2");
            java.net.InetAddress ipv6=java.net.InetAddress.getByName("fd79:fc::2");
            assertTrue(link.getLinkAddresses().stream().anyMatch(address->address.getAddress().equals(ipv4)&&address.getPrefixLength()==32));
            assertTrue("Auto TCP IPv6 source missing",link.getLinkAddresses().stream().anyMatch(address->address.getAddress().equals(ipv6)&&address.getPrefixLength()==128));
            assertTrue(link.getRoutes().stream().anyMatch(route->route.isDefaultRoute()&&route.getDestination().getAddress() instanceof java.net.Inet4Address));
            assertTrue(link.getRoutes().stream().anyMatch(route->route.isDefaultRoute()&&route.getDestination().getAddress() instanceof java.net.Inet6Address));
            assertEquals(1280,link.getMtu());
            assertTrue(link.getDnsServers().contains(java.net.InetAddress.getByName("1.1.1.1")));
        } finally {
            try { engine.down(); } finally { owner.close(); }
            helper.clean();
        }
    }
}
