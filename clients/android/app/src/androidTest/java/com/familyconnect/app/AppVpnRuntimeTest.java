package com.familyconnect.app;

import android.content.Context;
import android.content.Intent;
import android.os.ParcelFileDescriptor;
import android.os.SystemClock;
import androidx.test.platform.app.InstrumentationRegistry;
import org.json.JSONObject;
import org.json.JSONArray;
import org.junit.Test;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.Set;
import java.util.UUID;
import static org.junit.Assert.*;

public class AppVpnRuntimeTest {
    private static final String ALPHA="com.familyconnect.appprobe.alpha",BETA="com.familyconnect.appprobe.beta";
    private final AwgRuntimeTest helper=new AwgRuntimeTest();
    private final Context context=helper.context;
    private final JSONArray results=new JSONArray();

    private String shell(String command)throws Exception{
        try(ParcelFileDescriptor descriptor=InstrumentationRegistry.getInstrumentation().getUiAutomation().executeShellCommand(command);
            InputStream stream=new ParcelFileDescriptor.AutoCloseInputStream(descriptor)){
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[1024];int count;
            while((count=stream.read(buffer))!=-1){assertTrue(bytes.size()+count<65536);bytes.write(buffer,0,count);}return bytes.toString("UTF-8");
        }
    }
    private JSONObject probe(String name)throws Exception{
        String nonce=UUID.randomUUID().toString();
        shell("am force-stop "+name);
        shell("am start -W -n "+name+"/com.familyconnect.appprobe.ProbeActivity --es nonce "+nonce);
        long deadline=SystemClock.elapsedRealtime()+30000;
        while(SystemClock.elapsedRealtime()<deadline){
            String raw=shell("run-as "+name+" cat files/routing-result.json");
            if(raw.startsWith("{")){
                JSONObject result=new JSONObject(raw);
                if(nonce.equals(result.optString("nonce"))){result.put("api",android.os.Build.VERSION.SDK_INT);results.put(result);return result;}
            }
            SystemClock.sleep(200);
        }
        throw new AssertionError("PROBE_TIMEOUT");
    }
    private void route(String name,String expected)throws Exception{
        JSONObject result=probe(name);String nonce=result.getString("nonce");
        assertEquals(expected+"/"+nonce,result.optString("ipv4"));
        assertFalse(result.getString("ipv4_tls").isEmpty());
        assertTrue(result.has("dns")&&result.getJSONArray("dns").length()>0);
        if(expected.startsWith("VPN")){
            assertEquals(expected+"/"+nonce,result.optString("ipv6"));
            assertFalse(result.getString("ipv6_tls").isEmpty());
            assertTrue(result.getJSONArray("dns").toString().contains("198.19.1.1"));
        }else{
            assertFalse(result.optString("ipv6").startsWith("VPN"));
            assertFalse(result.getJSONArray("dns").toString().contains("198.19.1.1"));
        }
    }
    private AppVpnPolicy policy(AppVpnPolicy.Mode mode){return new AppVpnPolicy(mode,Set.of(ALPHA),Set.of(BETA));}
    private void pair(AppVpnPolicy.Mode mode,String vpn)throws Exception{
        route(ALPHA,vpn);route(BETA,mode==AppVpnPolicy.Mode.ALL?vpn:"DIRECT");
    }
    private void prepare()throws Exception{
        assertEquals("true",InstrumentationRegistry.getArguments().getString("fc_app_vpn"));
        assertTrue(android.os.Build.FINGERPRINT.contains("generic")||android.os.Build.MODEL.contains("sdk"));
        assertNotEquals(context.getPackageManager().getApplicationInfo(ALPHA,0).uid,context.getPackageManager().getApplicationInfo(BETA,0).uid);
        assertNotEquals(android.os.Process.myUid(),context.getPackageManager().getApplicationInfo(ALPHA,0).uid);
        helper.clean();shell("appops set "+context.getPackageName()+" ACTIVATE_VPN allow");
    }
    private void receipt(String name)throws Exception{
        try(var output=context.openFileOutput("app-vpn-"+name+".json",Context.MODE_PRIVATE)){output.write(results.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    }
    @Test public void ownerUnderlayAndCarrierHealthRemainSeparate()throws Exception{
        org.junit.Assume.assumeTrue("Dedicated fixture", "true".equals(InstrumentationRegistry.getArguments().getString("fc_app_vpn")));
        prepare();AutomaticVpnOwner owner=new AutomaticVpnOwner(context,new AppVpnAndroid(context,policy(AppVpnPolicy.Mode.INCLUDE)));
        AutomaticNormalEngine engine=new AutomaticNormalEngine(context,owner,Transport.TCP);
        try{
            owner.open(()->{});engine.up(TcpRuntimeTest.profile());SystemClock.sleep(700);
            android.net.ConnectivityManager manager=context.getSystemService(android.net.ConnectivityManager.class);
            JSONObject record=new JSONObject();JSONArray networks=new JSONArray();
            for(android.net.Network network:manager.getAllNetworks()){
                android.net.NetworkCapabilities capabilities=manager.getNetworkCapabilities(network);
                JSONObject item=new JSONObject().put("vpn",capabilities!=null&&capabilities.hasTransport(android.net.NetworkCapabilities.TRANSPORT_VPN));
                if(capabilities!=null&&capabilities.hasTransport(android.net.NetworkCapabilities.TRANSPORT_VPN)){
                    try(java.net.DatagramSocket socket=new java.net.DatagramSocket(null)){
                        network.bindSocket(socket);item.put("bound_network",true);
                        socket.bind(new java.net.InetSocketAddress(java.net.InetAddress.getByName("10.79.0.2"),0));item.put("bound_address",true);
                        socket.connect(java.net.InetAddress.getByName("1.1.1.1"),53);socket.setSoTimeout(2000);
                        byte[] query=VpnHealth.query(123,"diagnostic");socket.send(new java.net.DatagramPacket(query,query.length));
                        java.net.DatagramPacket reply=new java.net.DatagramPacket(new byte[1232],1232);socket.receive(reply);item.put("dns_reply",true);
                    }catch(Exception failure){item.put("failure",failure.getClass().getSimpleName());}
                }
                networks.put(item);
            }
            boolean health=new VpnHealth(context,engine::probeDns).check("10.79.0.2");
            record.put("networks",networks).put("carrier_dns_health",health);results.put(record);
            assertTrue("Excluded owner health must use the authenticated carrier",health);
            pair(AppVpnPolicy.Mode.INCLUDE,"VPN_TCP");
        }finally{engine.down();owner.close();helper.clean();receipt("owner-health");}
    }
    @Test public void independentUidsUseRealBuildersAndTraffic()throws Exception{
        org.junit.Assume.assumeTrue("Dedicated distinct-UID routing fixture", "true".equals(InstrumentationRegistry.getArguments().getString("fc_app_vpn")));
        prepare();AppVpnStore settings=new AppVpnStore(context);AppVpnPolicy previous=settings.read();
        try{
            route(ALPHA,"DIRECT");route(BETA,"DIRECT");
            for(AppVpnPolicy.Mode mode:AppVpnPolicy.Mode.values()){
                settings.save(policy(mode));AppVpnAndroid snapshot=new AppVpnAndroid(context,settings.read());
                for(Transport transport:new Transport[]{Transport.AWG,Transport.TCP}){
                    TunnelEngine engine=TunnelEngine.create(context,transport,up->{},snapshot);
                    try{
                        engine.up(transport==Transport.AWG?ProfileValidator.validate(AwgRuntimeTest.profile(transport),transport):TcpRuntimeTest.profile());
                        SystemClock.sleep(700);pair(mode,transport==Transport.AWG?"VPN_AWG":"VPN_TCP");
                    }finally{engine.down();helper.clean();}
                }
                AutomaticVpnOwner owner=new AutomaticVpnOwner(context,snapshot);long carrier=0;
                try{
                    owner.open(()->{});
                    ParcelFileDescriptor tunnel=RestrictedTunnelEngine.establishOwnedTun(owner);
                    NativeTcp.load(context);carrier=NativeTcp.start(tunnel.getFd(),TcpRuntimeTest.profile(),owner.service());assertTrue(carrier>0);
                    SystemClock.sleep(700);pair(mode,"VPN_TCP");
                    results.put(new JSONObject().put("scope","MESH production owned-TUN attachment; REALITY substitute carrier, not MESH wire qualification").put("mode",mode.name()));
                    owner.block();assertTrue(NativeTcp.stop(carrier));carrier=0;
                    JSONObject denied=probe(ALPHA);assertFalse(denied.has("ipv4"));assertFalse(denied.has("ipv6"));
                    if(mode!=AppVpnPolicy.Mode.ALL)route(BETA,"DIRECT");
                    settings.save(new AppVpnPolicy(AppVpnPolicy.Mode.EXCLUDE,Set.of(ALPHA),Set.of(ALPHA)));
                    assertEquals(mode,snapshot.policy.mode);
                    tunnel=RestrictedTunnelEngine.establishOwnedTun(owner);
                    carrier=NativeTcp.start(tunnel.getFd(),TcpRuntimeTest.profile(),owner.service());assertTrue(carrier>0);
                    SystemClock.sleep(700);pair(mode,"VPN_TCP");
                }finally{if(carrier>0)assertTrue(NativeTcp.stop(carrier));owner.close();helper.clean();}
                AutomaticVpnOwner next=new AutomaticVpnOwner(context,new AppVpnAndroid(context,settings.read()));
                AutomaticNormalEngine engine=new AutomaticNormalEngine(context,next,Transport.TCP);
                try{next.open(()->{});engine.up(TcpRuntimeTest.profile());SystemClock.sleep(700);route(ALPHA,"DIRECT");route(BETA,"VPN_TCP");}
                finally{engine.down();next.close();helper.clean();}
            }
        }finally{settings.save(previous);receipt("routing");}
    }
    @Test public void automaticHandoffKeepsCapturedPolicy()throws Exception{
        org.junit.Assume.assumeTrue("Dedicated distinct-UID routing fixture", "true".equals(InstrumentationRegistry.getArguments().getString("fc_app_vpn")));
        prepare();AppVpnStore settings=new AppVpnStore(context);AppVpnPolicy previous=settings.read();
        ProfileStore awg=new ProfileStore(context,Transport.AWG),tcp=new ProfileStore(context,Transport.TCP);
        String previousAwg=awg.exists()?awg.load():null,previousTcp=tcp.exists()?tcp.load():null;
        var diagnostic=context.getSharedPreferences("orchestrator-diagnostic",Context.MODE_PRIVATE);
        try{
            awg.save(ProfileValidator.validate(AwgRuntimeTest.profile(Transport.AWG),Transport.AWG));tcp.save(TcpRuntimeTest.profile());
            for(AppVpnPolicy.Mode mode:AppVpnPolicy.Mode.values()){
                assertTrue(context.getSharedPreferences("connectivity",Context.MODE_PRIVATE).edit().remove("normal_hint").commit());
                settings.save(policy(mode));AppVpnAndroid snapshot=new AppVpnAndroid(context,settings.read());
                AutomaticConnection automatic=new AutomaticConnection(context,null,false,event->{},snapshot);
                try{
                    automatic.up("awg");assertTrue("Auto must connect",automatic.connected());pair(mode,"VPN_AWG");
                    settings.save(new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,Set.of(BETA),Set.of(ALPHA)));
                    assertTrue(diagnostic.edit().putBoolean("fail_active",true).putBoolean("deny_awg",true).commit());
                    automatic.poll();assertTrue("Auto handoff must connect",automatic.connected());pair(mode,"VPN_TCP");
                }finally{automatic.down();diagnostic.edit().clear().commit();helper.clean();}
            }
        }finally{
            if(previousAwg==null)awg.clear();else awg.save(previousAwg);
            if(previousTcp==null)tcp.clear();else tcp.save(previousTcp);
            settings.save(previous);diagnostic.edit().clear().commit();receipt("automatic");
        }
    }
    @Test public void storageAndInvalidSelectionDoNotBecomeAll()throws Exception{
        org.junit.Assume.assumeTrue("Dedicated distinct-UID routing fixture", "true".equals(InstrumentationRegistry.getArguments().getString("fc_app_vpn")));
        prepare();AppVpnStore settings=new AppVpnStore(context);AppVpnPolicy previous=settings.read();
        try{
            AppVpnPolicy captured=policy(AppVpnPolicy.Mode.INCLUDE);settings.save(captured);
            assertEquals(captured,new AppVpnStore(context).read());
            String serialized=AppVpnStore.encode(captured);settings.save(policy(AppVpnPolicy.Mode.EXCLUDE));
            assertEquals(captured,AppVpnStore.decode(serialized));assertNotEquals(captured,settings.read());
            assertThrows(IllegalArgumentException.class,()->new AppVpnAndroid(context,new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,Set.of(),Set.of())));
            assertThrows(IllegalArgumentException.class,()->new AppVpnAndroid(context,new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,Set.of("not.installed.fixture"),Set.of())));
            assertThrows(IllegalArgumentException.class,()->AppVpnStore.decode("{}"));
            assertThrows(IllegalArgumentException.class,()->AppVpnStore.decode("{\"schema\":\"1\",\"mode\":\"ALL\",\"included\":[],\"excluded\":[]}"));
            assertTrue(context.getSharedPreferences("app-vpn",Context.MODE_PRIVATE).edit().putBoolean("policy",true).commit());
            assertThrows(IllegalArgumentException.class,settings::read);
            assertEquals(AppVpnPolicy.all(),AppVpnStore.decode(null));
            String query=android.util.Base64.encodeToString(VpnHealth.query(7,"bounded"),android.util.Base64.NO_WRAP);
            NativeRestricted.load();assertNull(NativeRestricted.dns(-1,query,25));
            NativeTcp.load(context);assertNull(NativeTcp.tcpDns(-1,query,25));
            assertNull(NativeRestricted.dns(-1,query,25));
        }finally{settings.save(previous);}
    }
    @Test public void removedLastPackageCannotEstablishAll()throws Exception{
        org.junit.Assume.assumeTrue("Dedicated distinct-UID routing fixture", "true".equals(InstrumentationRegistry.getArguments().getString("fc_app_vpn")));
        prepare();AppVpnPolicy policy=policy(AppVpnPolicy.Mode.INCLUDE);
        AppVpnAndroid captured=new AppVpnAndroid(context,policy);
        assertTrue(shell("ls /data/local/tmp/fc-app-probe-alpha.apk").contains("fc-app-probe-alpha.apk"));
        try{
            shell("am force-stop "+ALPHA);SystemClock.sleep(300);
            assertTrue(shell("pm uninstall "+ALPHA).contains("Success"));
            assertThrows(android.content.pm.PackageManager.NameNotFoundException.class,captured::validate);
            assertThrows(IllegalArgumentException.class,()->new AppVpnAndroid(context,policy));
            AutomaticVpnOwner owner=new AutomaticVpnOwner(context,captured);
            try{assertThrows(android.content.pm.PackageManager.NameNotFoundException.class,()->owner.open(()->{}));route(BETA,"DIRECT");}
            finally{owner.close();helper.clean();}
        }finally{assertTrue(shell("pm install /data/local/tmp/fc-app-probe-alpha.apk").contains("Success"));}
        AppVpnAndroid reinstalled=new AppVpnAndroid(context,policy);
        AutomaticVpnOwner owner=new AutomaticVpnOwner(context,reinstalled);AutomaticNormalEngine engine=new AutomaticNormalEngine(context,owner,Transport.TCP);
        try{owner.open(()->{});engine.up(TcpRuntimeTest.profile());SystemClock.sleep(700);pair(AppVpnPolicy.Mode.INCLUDE,"VPN_TCP");}
        finally{engine.down();owner.close();helper.clean();receipt("package-removal");}
    }
    @Test public void serviceConnectPendingAndResumeUseDifferentSnapshots()throws Exception{
        org.junit.Assume.assumeTrue("Dedicated distinct-UID routing fixture", "true".equals(InstrumentationRegistry.getArguments().getString("fc_app_vpn")));
        prepare();AppVpnStore settings=new AppVpnStore(context);AppVpnPolicy previous=settings.read();
        ProfileStore profile=new ProfileStore(context,Transport.TCP);String previousProfile=profile.exists()?profile.load():null;
        AppVpnPolicy initial=policy(AppVpnPolicy.Mode.INCLUDE);
        Intent connect=new Intent(context,ConnectionService.class).setAction("connect").putExtra("transport","tcp");
        Intent disconnect=new Intent(context,ConnectionService.class).setAction("disconnect");
        try{
            profile.save(TcpRuntimeTest.profile());settings.save(initial);
            context.startForegroundService(connect);helper.waitState("on");pair(AppVpnPolicy.Mode.INCLUDE,"VPN_TCP");
            assertEquals(initial,ConnectionService.activeApplications);
            assertTrue(context.getSharedPreferences("app-vpn",Context.MODE_PRIVATE).edit().putBoolean("policy",true).commit());
            try(androidx.test.core.app.ActivityScenario<AppVpnActivity> invalidScreen=androidx.test.core.app.ActivityScenario.launch(AppVpnActivity.class)){
                InstrumentationRegistry.getInstrumentation().waitForIdleSync();
                assertEquals("on",ConnectionService.status);assertEquals(initial,ConnectionService.activeApplications);
                pair(AppVpnPolicy.Mode.INCLUDE,"VPN_TCP");
            }
            settings.save(new AppVpnPolicy(AppVpnPolicy.Mode.INCLUDE,Set.of(),Set.of(ALPHA)));
            pair(AppVpnPolicy.Mode.INCLUDE,"VPN_TCP");assertEquals(initial,ConnectionService.activeApplications);
            String retained=context.getSharedPreferences("connection-request",0).getString("app-policy",null);
            assertEquals(initial,AppVpnStore.decode(retained));
            context.startService(disconnect);helper.waitState("off");helper.clean();
            context.startForegroundService(new Intent(connect).putExtra("resume-app-policy",true));
            helper.waitState("on");pair(AppVpnPolicy.Mode.INCLUDE,"VPN_TCP");assertEquals(initial,ConnectionService.activeApplications);
            context.startService(disconnect);helper.waitState("off");helper.clean();
            settings.save(new AppVpnPolicy(AppVpnPolicy.Mode.EXCLUDE,Set.of(ALPHA),Set.of(ALPHA)));
            context.startForegroundService(connect);helper.waitState("on");route(ALPHA,"DIRECT");route(BETA,"VPN_TCP");
            assertEquals(AppVpnPolicy.Mode.EXCLUDE,ConnectionService.activeApplications.mode);
        }finally{
            context.startService(disconnect);helper.waitState("off");helper.clean();settings.save(previous);
            if(previousProfile==null)profile.clear();else profile.save(previousProfile);receipt("service");
        }
    }
    @Test public void screenSavesRealRoutingAndPendingSelection()throws Exception{
        org.junit.Assume.assumeTrue("Dedicated distinct-UID routing fixture", "true".equals(InstrumentationRegistry.getArguments().getString("fc_app_vpn")));
        prepare();AppVpnStore settings=new AppVpnStore(context);AppVpnPolicy previous=settings.read();settings.save(AppVpnPolicy.all());
        String language=AppLanguage.selected(context);String requested=InstrumentationRegistry.getArguments().getString("app_vpn_language");
        if(requested!=null)AppLanguage.select(context,requested);
        try(androidx.test.core.app.ActivityScenario<AppVpnActivity> screen=androidx.test.core.app.ActivityScenario.launch(AppVpnActivity.class)){
            long deadline=SystemClock.elapsedRealtime()+10000;java.util.concurrent.atomic.AtomicBoolean loaded=new java.util.concurrent.atomic.AtomicBoolean();
            while(!loaded.get()&&SystemClock.elapsedRealtime()<deadline){screen.onActivity(activity->loaded.set(((android.widget.ListView)activity.getWindow().getDecorView().findViewWithTag("app_vpn_list")).getCount()>1));SystemClock.sleep(100);}
            assertTrue("Installed package inventory",loaded.get());
            screen.onActivity(activity->{
                ((android.widget.Spinner)activity.getWindow().getDecorView().findViewWithTag("app_vpn_modes")).setSelection(1);
                ((android.widget.EditText)activity.getWindow().getDecorView().findViewWithTag("app_vpn_search")).setText(ALPHA);
            });
            InstrumentationRegistry.getInstrumentation().waitForIdleSync();
            scroll(screen,1);
            screen.onActivity(activity->{
                android.widget.ListView list=activity.getWindow().getDecorView().findViewWithTag("app_vpn_list");assertEquals(2,list.getCount());
                list.getChildAt(1-list.getFirstVisiblePosition()).performClick();activity.getWindow().getDecorView().findViewWithTag("app_vpn_save").performClick();
            });
            captureScreen(screen,"selected");
            assertEquals(Set.of(ALPHA),settings.read().selected());assertEquals(AppVpnPolicy.Mode.INCLUDE,settings.read().mode);
            AppVpnAndroid snapshot=new AppVpnAndroid(context,settings.read());ConnectionService.activeApplications=snapshot.policy;
            AutomaticVpnOwner owner=new AutomaticVpnOwner(context,snapshot);AutomaticNormalEngine engine=new AutomaticNormalEngine(context,owner,Transport.TCP);
            try{
                owner.open(()->{});engine.up(TcpRuntimeTest.profile());SystemClock.sleep(700);pair(AppVpnPolicy.Mode.INCLUDE,"VPN_TCP");
                scroll(screen,0);
                screen.onActivity(activity->{((android.widget.Spinner)activity.getWindow().getDecorView().findViewWithTag("app_vpn_modes")).setSelection(2);});
                InstrumentationRegistry.getInstrumentation().waitForIdleSync();
                scroll(screen,1);
                screen.onActivity(activity->{
                    android.widget.ListView list=activity.getWindow().getDecorView().findViewWithTag("app_vpn_list");list.getChildAt(1-list.getFirstVisiblePosition()).performClick();
                    activity.getWindow().getDecorView().findViewWithTag("app_vpn_save").performClick();
                });
                scroll(screen,0);
                screen.onActivity(activity->{
                    assertTrue(((android.widget.TextView)activity.getWindow().getDecorView().findViewWithTag("app_vpn_summary")).getText().toString().contains(activity.getString(R.string.app_vpn_pending)));
                });
                captureScreen(screen,"pending");
                pair(AppVpnPolicy.Mode.INCLUDE,"VPN_TCP");assertEquals(Set.of(ALPHA),settings.read().excluded);
            }finally{engine.down();owner.close();ConnectionService.activeApplications=null;helper.clean();}
        }finally{settings.save(previous);AppLanguage.select(context,language);ConnectionService.activeApplications=null;receipt("screen");}
    }
    private void scroll(androidx.test.core.app.ActivityScenario<AppVpnActivity> screen,int position){
        screen.onActivity(activity->{android.widget.ListView list=activity.getWindow().getDecorView().findViewWithTag("app_vpn_list");list.setSelection(position);});
        InstrumentationRegistry.getInstrumentation().waitForIdleSync();SystemClock.sleep(200);
    }
    private void captureScreen(androidx.test.core.app.ActivityScenario<AppVpnActivity> screen,String name){
        scroll(screen,0);screen.onActivity(activity->render(activity,name+"-controls"));
        scroll(screen,1);screen.onActivity(activity->render(activity,name));
    }
    private void render(AppVpnActivity activity,String name){
        assertTrue((activity.getWindow().getAttributes().flags&android.view.WindowManager.LayoutParams.FLAG_SECURE)!=0);
        android.view.View root=activity.findViewById(android.R.id.content);
        assertTrue(root.getWidth()>0&&root.getHeight()>0);
        android.widget.ListView list=root.findViewWithTag("app_vpn_list");assertTrue("App list remains reachable",list.getHeight()>80*activity.getResources().getDisplayMetrics().density);
        for(String tag:new String[]{"app_vpn_save","app_vpn_back"}){
            android.view.View button=root.findViewWithTag(tag);android.graphics.Rect bounds=new android.graphics.Rect();
            assertTrue("Action remains visible",button.getGlobalVisibleRect(bounds));assertEquals(button.getHeight(),bounds.height());
        }
        android.graphics.Bitmap image=android.graphics.Bitmap.createBitmap(root.getWidth(),root.getHeight(),android.graphics.Bitmap.Config.ARGB_8888);
        root.draw(new android.graphics.Canvas(image));
        try(var output=new java.io.FileOutputStream(new java.io.File(activity.getExternalFilesDir("app-vpn-visual"),name+".png"))){assertTrue(image.compress(android.graphics.Bitmap.CompressFormat.PNG,100,output));}
        catch(Exception failure){throw new AssertionError("VISUAL_RECEIPT",failure);}finally{image.recycle();}
    }
}
