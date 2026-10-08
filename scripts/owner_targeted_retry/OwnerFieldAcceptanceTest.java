package com.familyconnect.app;

import android.app.*;
import android.content.*;
import android.net.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.*;
import com.google.gson.*;
import java.io.*;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import javax.net.ssl.HttpsURLConnection;
import org.junit.Test;
import static org.junit.Assert.*;

public class OwnerFieldAcceptanceTest {
    final Instrumentation instrumentation=InstrumentationRegistry.getInstrumentation();
    final Context context=instrumentation.getTargetContext();
    final Bundle arguments=InstrumentationRegistry.getArguments();
    void report(JsonObject value){Bundle result=new Bundle();result.putString("owner_evidence",value.toString());instrumentation.sendStatus(2,result);}
    String hash(byte[] raw)throws Exception{return AppUpdate.hex(MessageDigest.getInstance("SHA-256").digest(raw));}
    File file(String name){return new File(context.getNoBackupFilesDir(),name);}
    String text(File file)throws Exception{return new String(Files.readAllBytes(file.toPath()),java.nio.charset.StandardCharsets.UTF_8);}
    void guard()throws Exception{assertEquals("com.familyconnect.app.friends",context.getPackageName());assertEquals("31ce63ba",arguments.getString("owner_serial"));assertEquals("70",arguments.getString("expected_version"));assertEquals(70,context.getPackageManager().getPackageInfo(context.getPackageName(),0).versionCode);}
    FriendsActivity open(int tab)throws Exception{
        try(ParcelFileDescriptor descriptor=instrumentation.getUiAutomation().executeShellCommand("am start -W -n "+context.getPackageName()+"/com.familyconnect.app.FriendsActivity --ei tab "+tab)){try(InputStream stream=new FileInputStream(descriptor.getFileDescriptor())){while(stream.read()!=-1){}}}
        AtomicReference<FriendsActivity> found=new AtomicReference<>();long deadline=SystemClock.elapsedRealtime()+10000;
        while(found.get()==null&&SystemClock.elapsedRealtime()<deadline){instrumentation.runOnMainSync(()->{for(Activity activity:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED))if(activity instanceof FriendsActivity)found.set((FriendsActivity)activity);});if(found.get()==null)SystemClock.sleep(100);}
        assertNotNull("Normal Friends launcher not resumed",found.get());SystemClock.sleep(800);return found.get();
    }
    List<View> views(View root){List<View> result=new ArrayList<>();result.add(root);if(root instanceof ViewGroup){ViewGroup group=(ViewGroup)root;for(int index=0;index<group.getChildCount();index++)result.addAll(views(group.getChildAt(index)));}return result;}
    Button button(Activity activity,String label){for(View view:views(activity.getWindow().getDecorView()))if(view instanceof Button&&label.contentEquals(((Button)view).getText()))return (Button)view;throw new AssertionError("Expected product action absent");}
    void click(Activity activity,String label){instrumentation.runOnMainSync(()->assertTrue(button(activity,label).performClick()));instrumentation.waitForIdleSync();}
    @Test public void registrationSnapshot()throws Exception{
        guard();JsonObject value=new JsonObject(),encrypted=new JsonObject();
        for(String name:new String[]{"friends-identity.enc","friends-configuration.enc","restricted-readiness.enc"})encrypted.addProperty(name,hash(Files.readAllBytes(file(name).toPath())));
        value.add("encrypted_files",encrypted);
        android.content.SharedPreferences prefs=context.getSharedPreferences("com.familyconnect.app.FriendsActivity",0);
        JsonObject enrollment=new JsonObject();
        for(String name:new String[]{"activated","device","invitation"})enrollment.addProperty(name,String.valueOf(prefs.getAll().get(name)));
        value.addProperty("enrollment_fingerprint",hash(enrollment.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        value.addProperty("activated",prefs.getBoolean("activated",false));
        value.addProperty("owner_support_id",DeviceSupport.cached(context));
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){assertNotNull(identity);value.addProperty("identity_decrypts",true);}
        byte[] readiness=new RestrictedVault(context).read();assertNotNull(readiness);Arrays.fill(readiness,(byte)0);value.addProperty("readiness_decrypts",true);
        value.addProperty("uid",android.os.Process.myUid());report(value);
    }
    @Test public void preservesExistingRegistrationAndEncryptedState()throws Exception{
        guard();JsonObject value=new JsonObject();
        for(String name:new String[]{"friends-identity.enc","friends-configuration.enc","restricted-readiness.enc"}){
            String digest=hash(Files.readAllBytes(file(name).toPath()));assertEquals("Encrypted state changed: "+name,arguments.getString(name),digest);value.addProperty(name+"_unchanged",true);
        }
        assertEquals(10283,android.os.Process.myUid());
        assertTrue(context.getSharedPreferences("com.familyconnect.app.FriendsActivity",0).getBoolean("activated",false));
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){assertNotNull(identity);value.addProperty("identity_decrypts",true);}
        byte[] readiness=new RestrictedVault(context).read();assertNotNull(readiness);assertTrue(readiness.length>0);Arrays.fill(readiness,(byte)0);value.addProperty("readiness_decrypts",true);
        value.addProperty("cached_normal_provisioning_usable",new FriendsAccessAndroid(context).cachedProvisioningUsable());
        value.addProperty("uid",android.os.Process.myUid());value.addProperty("activated",true);report(value);
    }
    @Test public void existingIdentityStillAuthenticates()throws Exception{
        guard();JsonObject value=new JsonObject();boolean active=!new FriendsAccessAndroid(context,android.os.SystemClock.elapsedRealtime()+20000).deviceStatus().isEmpty();value.addProperty("server_enrollment_active",active);report(value);assertTrue("Existing signed device proof must remain active",active);
    }
    @Test public void supportVisibleCopiedAndStable()throws Exception{
        guard();FriendsActivity activity=open(3);instrumentation.runOnMainSync(()->assertTrue(button(activity,activity.getString(R.string.support_refresh)).performClick()));long deadline=SystemClock.elapsedRealtime()+22000;String support=null;
        while(SystemClock.elapsedRealtime()<deadline){support=DeviceSupport.cached(context);if(SupportId.valid(support))break;SystemClock.sleep(250);}
        JsonObject value=new JsonObject();value.addProperty("support_id_available",SupportId.valid(support));
        AtomicReference<String> label=new AtomicReference<>("");instrumentation.runOnMainSync(()->{for(View view:views(activity.getWindow().getDecorView()))if(view instanceof TextView&&activity.getString(R.string.support_unavailable).contentEquals(((TextView)view).getText()))label.set(((TextView)view).getText().toString());});
        value.addProperty("support_unavailable_message_visible",label.get().contains("недоступен")||label.get().contains("unavailable"));report(value);
        assertTrue("Support ID unavailable: server delivery has not been deployed",SupportId.valid(support));
        final String expected=support;AtomicReference<String> copied=new AtomicReference<>();
        instrumentation.runOnMainSync(()->{assertTrue(button(activity,activity.getString(R.string.support_copy)).performClick());ClipboardManager clipboard=activity.getSystemService(ClipboardManager.class);copied.set(clipboard.getPrimaryClip().getItemAt(0).coerceToText(activity).toString());});
        assertEquals(expected,copied.get());assertEquals(expected,DeviceSupport.cached(context));value.addProperty("copy_matches",true);value.addProperty("support_id",expected);report(value);
    }
    @Test public void normalProductTransport()throws Exception{
        guard();String requested=arguments.getString("transport");assertTrue(Arrays.asList("auto","awg","tcp").contains(requested));
        FriendsActivity activity=open(0);assertEquals("Start transport validation disconnected","off",ConnectionService.status);
        AtomicReference<Spinner> picker=new AtomicReference<>();AtomicReference<View> connect=new AtomicReference<>();
        instrumentation.runOnMainSync(()->{for(View view:views(activity.getWindow().getDecorView())){if(view instanceof Spinner&&view.getContentDescription()!=null&&activity.getString(R.string.terminal_transport).contentEquals(view.getContentDescription()))picker.set((Spinner)view);if(view instanceof TerminalUi.Dial)connect.set(view);}assertNotNull("Visible transport picker",picker.get());assertNotNull("Visible CONNECT dial",connect.get());picker.get().setSelection(requested.equals("auto")?0:requested.equals("awg")?1:2);});
        instrumentation.waitForIdleSync();SystemClock.sleep(500);long start=SystemClock.elapsedRealtime();
        JsonObject value=new JsonObject();value.addProperty("requested",requested);
        try{
            instrumentation.runOnMainSync(()->assertTrue(connect.get().performClick()));
            long deadline=start+150000;while(SystemClock.elapsedRealtime()<deadline&&!ConnectionService.status.equals("on")&&!ConnectionService.status.equals("failed"))SystemClock.sleep(250);
            value.addProperty("status",ConnectionService.status);value.addProperty("active_transport",ConnectionService.activeTransport);value.addProperty("duration_ms",SystemClock.elapsedRealtime()-start);report(value);
            assertEquals("Normal product CONNECT did not reach connected","on",ConnectionService.status);
            if(!requested.equals("auto"))assertEquals(requested,ConnectionService.activeTransport);
            ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);boolean vpn=false;for(Network network:manager.getAllNetworks()){NetworkCapabilities caps=manager.getNetworkCapabilities(network);if(caps!=null&&caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN))vpn=true;}assertTrue("VPN network absent",vpn);
            HttpsURLConnection connection=(HttpsURLConnection)new java.net.URL("https://example.com/").openConnection();connection.setConnectTimeout(15000);connection.setReadTimeout(15000);
            try{int status=connection.getResponseCode();value.addProperty("test_https_status",status);assertEquals(200,status);try(InputStream stream=connection.getInputStream()){assertTrue(stream.read(new byte[1024])>0);}}finally{connection.disconnect();}
            value.addProperty("vpn_present",true);report(value);
        }finally{
            if(!ConnectionService.status.equals("off")){instrumentation.runOnMainSync(()->connect.get().performClick());long deadline=SystemClock.elapsedRealtime()+20000;while(!ConnectionService.status.equals("off")&&SystemClock.elapsedRealtime()<deadline)SystemClock.sleep(100);}
            instrumentation.runOnMainSync(()->picker.get().setSelection(0));instrumentation.waitForIdleSync();
        }
    }
    @Test public void diagnosticSnapshotAndShare()throws Exception{
        guard();assertEquals("off",ConnectionService.status);FriendsActivity activity=open(3);
        Diagnostics.event(context,new ConnectivityOrchestrator.Event("connect_requested","tcp",null,ConnectivityOrchestrator.State.CONNECTING,0));
        org.json.JSONObject evidence=new org.json.JSONObject();
        evidence.put("session_tag","e1b8ac9f42012f22097916fece757a4f004325f58c07a9b3a24259b27f9530e3");
        evidence.put("terminal_reason","RELIABLE_EXHAUSTED");evidence.put("terminal_at_ms",System.currentTimeMillis());
        evidence.put("observed_at_ms",System.currentTimeMillis());evidence.put("reliable_terminal","recovery_exhausted");
        evidence.put("signaling_failure","close_code_1006");evidence.put("ice_failure","SUBSCRIBER_failed");
        evidence.put("subscriber_state","failed");evidence.put("publisher_state","connected");
        evidence.put("retransmissions",3);evidence.put("recovery_timeouts",2);evidence.put("private_key","SYNTHETIC_FORBIDDEN_VALUE");
        org.json.JSONObject cause=new org.json.JSONObject();
        cause.put("session_tag",evidence.getString("session_tag"));cause.put("sequence",1);
        cause.put("timestamp_ms",System.currentTimeMillis());cause.put("stage","CARRIER");cause.put("state","FAILED");
        cause.put("reason","RELIABLE_FRAME_TIMEOUT");cause.put("reliable_age_ms",20000);
        cause.put("reliable_retries",7);cause.put("reliable_pending",8);cause.put("reliable_sacked",1);
        cause.put("reliable_ack_received",17);cause.put("reliable_ack_age_ms",1000);cause.put("reliable_progress_age_ms",20000);
        cause.put("reliable_payload","SYNTHETIC_FORBIDDEN_VALUE");
        org.json.JSONObject lifecycle=new org.json.JSONObject();
        lifecycle.put("session_tag",evidence.getString("session_tag"));lifecycle.put("correlation_status","VALID");
        lifecycle.put("first_failure",cause);lifecycle.put("trace",new org.json.JSONArray().put(cause));
        evidence.put("lifecycle",lifecycle);
        org.json.JSONObject packet=new org.json.JSONObject().put("diagnostic",evidence);
        Diagnostics.nativeStats(context,new org.json.JSONObject().put("packet",packet).put("state",3).put("authorization_denied",false));
        Diagnostics.event(context,new ConnectivityOrchestrator.Event("connect_failed","tcp",ConnectivityOrchestrator.Failure.NETWORK,ConnectivityOrchestrator.State.FAILED,1));
        JsonObject first=JsonParser.parseString(text(file("diag-incident.json"))).getAsJsonObject();assertEquals("FAILED",first.get("state").getAsString());
        Diagnostics.event(context,new ConnectivityOrchestrator.Event("candidate_succeeded","tcp",null,ConnectivityOrchestrator.State.CONNECTED,2));
        Diagnostics.event(context,new ConnectivityOrchestrator.Event("restoration_attempted","tcp",ConnectivityOrchestrator.Failure.NETWORK,ConnectivityOrchestrator.State.RESTORING,3));
        Diagnostics.event(context,new ConnectivityOrchestrator.Event("restoration_failed","tcp",ConnectivityOrchestrator.Failure.NETWORK,ConnectivityOrchestrator.State.FAILED,4));
        JsonObject second=JsonParser.parseString(text(file("diag-incident.json"))).getAsJsonObject();assertNotEquals(first.get("incident_id"),second.get("incident_id"));
        click(activity,activity.getString(R.string.diagnostics_send));
        android.accessibilityservice.AccessibilityServiceInfo service=instrumentation.getUiAutomation().getServiceInfo();service.flags|=android.accessibilityservice.AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS|android.accessibilityservice.AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;instrumentation.getUiAutomation().setServiceInfo(service);
        android.view.accessibility.AccessibilityNodeInfo root=instrumentation.getUiAutomation().getRootInActiveWindow();assertNotNull(root);
        boolean accepted=false;for(android.view.accessibility.AccessibilityNodeInfo node:root.findAccessibilityNodeInfosByViewId("android:id/button1"))if(node.performAction(android.view.accessibility.AccessibilityNodeInfo.ACTION_CLICK)){accepted=true;break;}
        assertTrue("Diagnostics confirmation action unavailable",accepted);SystemClock.sleep(1500);
        File[] exports=context.getCacheDir().listFiles((folder,name)->name.matches("diagnostics-[0-9a-f]{32}\\.json"));assertNotNull(exports);assertEquals(1,exports.length);assertTrue(exports[0].length()<=256*1024);
        String raw=text(exports[0]);for(String forbidden:new String[]{"PRIVATE KEY","Bearer ","OAuth ","https://","http://","room_url","private_key","public_identity","query_name","wireguard_public_key"})assertFalse("Unsafe diagnostic content",raw.contains(forbidden));
        JsonObject bundle=JsonParser.parseString(raw).getAsJsonObject();assertEquals(new HashSet<>(Arrays.asList("ring","incident")),bundle.keySet());
        for(String section:new String[]{"ring","incident"}){
            JsonObject snapshot=bundle.getAsJsonObject(section),diagnostic=snapshot.getAsJsonObject("restricted_session");
            assertEquals("FC-4D8Q-REEG",snapshot.get("device_support_id").getAsString());
            assertTrue(snapshot.has("connection_id")&&snapshot.has("incident_id"));
            assertEquals("e1b8ac9f42012f22097916fece757a4f004325f58c07a9b3a24259b27f9530e3",diagnostic.get("session_tag").getAsString());
            assertEquals("RELIABLE_EXHAUSTED",diagnostic.get("terminal_reason").getAsString());
            assertEquals("close_code_1006",diagnostic.get("signaling_failure").getAsString());
            assertEquals("SUBSCRIBER_failed",diagnostic.get("ice_failure").getAsString());
            assertEquals(3,diagnostic.get("retransmissions").getAsInt());assertEquals(2,diagnostic.get("recovery_timeouts").getAsInt());
            assertTrue(diagnostic.has("terminal_at_ms")&&diagnostic.has("terminal_observed_at_ms"));
            JsonObject exportedCause=diagnostic.getAsJsonObject("lifecycle").getAsJsonObject("first_failure");
            assertEquals("RELIABLE_FRAME_TIMEOUT",exportedCause.get("reason").getAsString());
            assertEquals(20000,exportedCause.get("reliable_age_ms").getAsInt());
            assertEquals(7,exportedCause.get("reliable_retries").getAsInt());
            assertEquals(8,exportedCause.get("reliable_pending").getAsInt());
            assertEquals(1,exportedCause.get("reliable_sacked").getAsInt());
            assertEquals(17,exportedCause.get("reliable_ack_received").getAsInt());
            assertEquals(1000,exportedCause.get("reliable_ack_age_ms").getAsInt());
            assertEquals(20000,exportedCause.get("reliable_progress_age_ms").getAsInt());
            assertFalse(exportedCause.has("reliable_payload"));
            assertFalse(diagnostic.has("private_key"));
        }
        assertFalse(raw.contains("SYNTHETIC_FORBIDDEN_VALUE"));
        JsonObject value=new JsonObject();value.addProperty("synthetic_typed_events_only",true);value.addProperty("both_failure_snapshots",true);value.addProperty("bundle_bytes",exports[0].length());value.addProperty("bundle_sha256",hash(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8)));value.add("bundle",bundle);report(value);
    }
    @Test public void publishedUpdateIsCurrent()throws Exception{
        guard();FriendsActivity activity=open(3);
        AtomicReference<String> displayedAction=new AtomicReference<>();
        instrumentation.runOnMainSync(()->{
            activity.navigate(3);
            displayedAction.set(activity.getString(R.string.update_check));
            assertTrue(button(activity,displayedAction.get()).performClick());
        });
        AtomicReference<Boolean> current=new AtomicReference<>(false);
        long deadline=SystemClock.elapsedRealtime()+35000;
        while(!current.get()&&SystemClock.elapsedRealtime()<deadline){
            instrumentation.runOnMainSync(()->{
                for(View view:views(activity.getWindow().getDecorView())){
                    if(view instanceof TextView&&activity.getString(R.string.update_current).contentEquals(((TextView)view).getText()))current.set(true);
                }
            });
            if(!current.get())SystemClock.sleep(200);
        }
        assertTrue("Visible product check must report current beta60",current.get());
        JsonObject value=new JsonObject();value.addProperty("version_code",60);
        value.addProperty("action",displayedAction.get());value.addProperty("result",activity.getString(R.string.update_current));
        value.addProperty("application_context_action",context.getString(R.string.update_check));
        value.addProperty("support_id",DeviceSupport.cached(context));report(value);
    }
    @Test public void finalStateAndTestArtifactCleanup()throws Exception{
        guard();JsonObject value=new JsonObject();String expected=arguments.getString("identity_sha256");
        assertEquals(expected,hash(Files.readAllBytes(file("friends-identity.enc").toPath())));
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){value.addProperty("identity_preserved_and_decrypts",true);}
        android.content.SharedPreferences prefs=context.getSharedPreferences("com.familyconnect.app.FriendsActivity",0);
        assertTrue(prefs.getBoolean("activated",false));assertEquals("auto",prefs.getString("transport","auto"));value.addProperty("activated",true);value.addProperty("transport","auto");
        byte[] material=new RestrictedVault(context).read();assertNotNull(material);Arrays.fill(material,(byte)0);value.addProperty("readiness_decrypts",true);
        JsonObject receipt=JsonParser.parseString(text(file("restricted-readiness-result-v1.json"))).getAsJsonObject();JsonObject payload=receipt.getAsJsonObject("payload"),safe=new JsonObject();
        for(String name:new String[]{"result","provisioning","bootstrap","orchestrator_usable","expires_at","observed_at","app_version","version_code"})safe.add(name,payload.get(name));safe.add("ack_state",receipt.get("ack_state"));value.add("readiness_receipt",safe);
        String connection=arguments.getString("synthetic_connection");int removed=0;
        for(String name:new String[]{"diag-ring.json","diag-incident.json"}){File target=file(name);if(target.exists()&&connection.equals(JsonParser.parseString(text(target)).getAsJsonObject().get("connection_id").getAsString())){assertTrue(target.delete());removed++;}}
        File[] exports=context.getCacheDir().listFiles((folder,name)->name.matches("diagnostics-[0-9a-f]{32}\\.json"));if(exports!=null)for(File target:exports)if(hash(Files.readAllBytes(target.toPath())).equals(arguments.getString("export_sha256"))){context.revokeUriPermission(Uri.parse("content://"+context.getPackageName()+".diagnostics/"+target.getName()),Intent.FLAG_GRANT_READ_URI_PERMISSION);assertTrue(target.delete());removed++;}
        value.addProperty("test_diagnostic_files_removed",removed);value.addProperty("connection_status",ConnectionService.status);report(value);
    }
}
