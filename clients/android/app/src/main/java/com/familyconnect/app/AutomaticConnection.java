package com.familyconnect.app;

import android.content.Context;
import android.os.SystemClock;
import android.util.AtomicFile;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.json.JSONArray;
import org.json.JSONObject;

final class AutomaticConnection implements TunnelEngine,ConnectivityOrchestrator.Host {
    private final Context context;
    private final String country;
    private final Consumer<ConnectivityOrchestrator.Event> changed;
    private final AutomaticVpnOwner owner;
    private final ConnectivityOrchestrator orchestrator=new ConnectivityOrchestrator(this);
    private final Map<Transport,String> profiles=new LinkedHashMap<>();
    private volatile TunnelEngine candidate;
    private volatile VpnHealth health;
    private volatile FriendsAccessAndroid access;
    private volatile ConnectivityOrchestrator.Failure interrupted;
    private int unhealthy;
    private boolean ownerOpen;
    private final boolean debug;
    AutomaticConnection(Context context,String country,Consumer<ConnectivityOrchestrator.Event> changed) {
        this.context=context;this.country=country;this.changed=changed;owner=new AutomaticVpnOwner(context);
        debug=(context.getApplicationInfo().flags&android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0;
    }
    public void up(String preferred) {
        String hint=context.getSharedPreferences("connectivity",Context.MODE_PRIVATE).getString("normal_hint",null);
        orchestrator.connect(new ArrayList<>(),preferred,hint);
    }
    public long now() { return SystemClock.elapsedRealtime(); }
    public void pause(long millis) throws InterruptedException { Thread.sleep(millis); }
    public List<String> configure(List<String> ignored,long deadline) throws Exception {
        orchestrator.check(deadline);
        owner.open(()->interrupt(ConnectivityOrchestrator.Failure.AUTH));ownerOpen=true;
        orchestrator.check(deadline);
        if(country!=null) {
            access=new FriendsAccessAndroid(context,deadline);
            try { profiles.putAll(access.normalProfiles(country)); }
            catch(FriendsAccessAndroid.Denied denied) { throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.AUTH); }
            catch(java.io.IOException unavailable) { orchestrator.check(Long.MAX_VALUE); }
            finally { access=null; }
        } else {
            for(Transport type:Transport.values()) {
                ProfileStore store=new ProfileStore(context,type);
                if(store.exists())profiles.put(type,ProfileValidator.validate(store.load(),type));
            }
        }
        List<String> configured=new ArrayList<>();for(Transport type:profiles.keySet())configured.add(type.id);
        return configured;
    }
    public void open(String id,long deadline) throws Exception {
        orchestrator.check(deadline);ConnectionService.activeTransport=id;
        if(ConnectivityOrchestrator.RESTRICTED.equals(id)) {
            RestrictedTunnelEngine restricted=new RestrictedTunnelEngine(context,()->interrupted!=null,up->{},owner,deadline);
            candidate=restricted;restricted.up("");ConnectionService.vpnSource="10.79.0.2";
        } else {
            if(debug&&context.getSharedPreferences("orchestrator-diagnostic",Context.MODE_PRIVATE).getBoolean("deny_"+id,false))
                throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.TRANSPORT_UNAVAILABLE);
            Transport transport=Transport.parse(id);
            AutomaticNormalEngine normal=new AutomaticNormalEngine(context,owner,transport);
            candidate=normal;normal.up(profiles.get(transport));ConnectionService.vpnSource=normal.source;
            health=new VpnHealth(context);
            while(true) {
                orchestrator.check(deadline);
                boolean good=health.check(normal.source,deadline);Diagnostics.dns(context,good);
                if(good)break;
                pause(100);
            }
        }
        orchestrator.check(deadline);unhealthy=0;
    }
    void interrupt(ConnectivityOrchestrator.Failure reason) {
        interrupted=reason;orchestrator.interrupt(reason);
        VpnHealth probe=health;if(probe!=null)probe.cancel();
        FriendsAccessAndroid pending=access;if(pending!=null)pending.cancel();
    }
    void poll() {
        if(orchestrator.state()!=ConnectivityOrchestrator.State.CONNECTED)return;
        if(interrupted!=null) { orchestrator.lost(interrupted);return; }
        if(debug&&context.getSharedPreferences("orchestrator-diagnostic",Context.MODE_PRIVATE).getBoolean("fail_active",false)) {
            context.getSharedPreferences("orchestrator-diagnostic",Context.MODE_PRIVATE).edit().remove("fail_active").apply();
            orchestrator.lost(ConnectivityOrchestrator.Failure.NETWORK);return;
        }
        TunnelEngine active=candidate;
        if(active instanceof RestrictedTunnelEngine) {
            RestrictedTunnelEngine restricted=(RestrictedTunnelEngine)active;
            ConnectivityOrchestrator.Failure failure=restricted.connectionFailure();
            if(failure!=null)orchestrator.lost(failure);
        } else if(active instanceof AutomaticNormalEngine) {
            boolean good=health.check(((AutomaticNormalEngine)active).source);
            Diagnostics.dns(context,good);
            if(interrupted!=null)orchestrator.lost(interrupted);
            else if(good)unhealthy=0;
            else if(++unhealthy>=2)orchestrator.lost(ConnectivityOrchestrator.Failure.NETWORK);
        }
    }
    boolean connected() { return orchestrator.state()==ConnectivityOrchestrator.State.CONNECTED; }
    public void closeCandidate() throws Exception {
        VpnHealth probe=health;if(probe!=null) { probe.cancel();health=null; }
        if(candidate!=null) {
            Exception blocked=null;
            try { owner.block(); }catch(Exception failure) { blocked=failure; }
            candidate.down();candidate=null;
            if(blocked!=null)throw blocked;
        }
    }
    public void release() throws Exception { owner.close();ownerOpen=false;profiles.clear(); }
    public void down() throws Exception {
        orchestrator.disconnect();
        if(ownerOpen)throw new IllegalStateException("Owner cleanup required");
    }
    public void remember(String id) {
        Transport.parse(id);context.getSharedPreferences("connectivity",Context.MODE_PRIVATE).edit().putString("normal_hint",id).apply();
    }
    public void event(ConnectivityOrchestrator.Event event) {
        Diagnostics.event(context,event);
        if(event.failure==ConnectivityOrchestrator.Failure.AUTH||event.failure==ConnectivityOrchestrator.Failure.CONFIGURATION)
            context.getSharedPreferences("connectivity",Context.MODE_PRIVATE).edit().remove("normal_hint").apply();
        changed.accept(event);
        AtomicFile file=new AtomicFile(new File(context.getFilesDir(),"connectivity-events.json"));
        FileOutputStream stream=null;
        try {
            JSONArray records=new JSONArray();
            for(ConnectivityOrchestrator.Event item:orchestrator.events()) {
                JSONObject record=new JSONObject();record.put("event",item.name);record.put("state",item.state.name());
                record.put("candidate",item.candidate);record.put("category",item.failure==null?null:item.failure.name());
                record.put("elapsed_ms",item.elapsedMs);records.put(record);
            }
            stream=file.startWrite();stream.write(records.toString().getBytes(StandardCharsets.UTF_8));file.finishWrite(stream);
        }catch(Exception ignored) { if(stream!=null)file.failWrite(stream); }
    }
}
