package com.familyconnect.app;

import com.google.gson.*;
import java.util.*;

final class DiagnosticRing {
    static final int RECORD_LIMIT=256*1024,EXPORT_LIMIT=2*RECORD_LIMIT+1024;
    enum Component { ORCHESTRATOR, READINESS, BOOTSTRAP, FAMILY_AUTH, ROOM_BROKER, SESSION, VPN, DNS }
    enum Code { NONE, CANCELLED, AUTH, CONFIGURATION, NETWORK, TRANSPORT_UNAVAILABLE, BOOTSTRAP_UNAVAILABLE, INTERNAL,
        READY, NOT_READY, VPN_CAPTURE_READY, VPN_RELEASED, BOOT_CACHE_READY, BOOT_CARRIER_READY, FAMILY_AUTH_READY,
        BROKER_DESCRIPTOR_READY, BOOT_CLOSED, SESSION_READY, STARTUP_REJECTED, CONTROL_UNAVAILABLE, STARTUP_FAILED,
        NATIVE_VALIDATION_FAILED, BOOTSTRAP_VALIDATION_FAILED, ATOMIC_IMPORT_FAILED, PERSISTENCE_FAILED,
        EXPIRED_ON_IMPORT, ORCHESTRATOR_NOT_USABLE, INTERNAL_ERROR, STALE_STATE, AUTHORIZATION_REJECTED, FETCH_FAILED, MISSING,
        DNS_PROBE_OK, DNS_PROBE_FAILED, SIGNAL_WS_CLOSE, ICE_DISCONNECTED, ICE_FAILED, PEER_CONNECTION_FAILED,
        CARRIER_EOF, CARRIER_ERROR, FAMILY_TLS_EOF, FAMILY_TLS_ERROR, GATEWAY_CLOSE, HEARTBEAT_TIMEOUT, REMOTE_CLOSE,
        RECOVERY_CLEANUP_FAILED, RECOVERY_DESCRIPTOR_FAILED, RECOVERY_JOIN_FAILED, RECOVERY_CARRIER_FAILED, UNKNOWN_INTERNAL }
    private String supportId;
    private final String version;
    private final int build,os;
    private final ArrayDeque<JsonObject> events=new ArrayDeque<>();
    private final JsonObject outcomes=new JsonObject(),counters=new JsonObject();
    private JsonObject restrictedSession=new JsonObject();
    private final ArrayDeque<JsonObject> restrictedHistory=new ArrayDeque<>();
    private String connectionId=UUID.randomUUID().toString(),incidentId=UUID.randomUUID().toString();
    private String state="DISCONNECTED",network="UNKNOWN",readiness="UNKNOWN",bootstrap="UNKNOWN";
    private boolean vpn;
    private int retries;
    DiagnosticRing(String supportId,String version,int build,int os){this.supportId=supportId;this.version=version;this.build=build;this.os=os;}
    synchronized void support(String value){supportId=SupportId.valid(value)?value:null;}
    synchronized void network(String value){network=Arrays.asList("CELLULAR","WIFI","ETHERNET","VPN","NONE").contains(value)?value:"UNKNOWN";}
    synchronized boolean event(ConnectivityOrchestrator.Event event,long now){
        if("connect_requested".equals(event.name)){
            connectionId=UUID.randomUUID().toString();incidentId=UUID.randomUUID().toString();retries=0;
            for(String key:new ArrayList<>(outcomes.keySet()))outcomes.remove(key);
            for(String key:new ArrayList<>(counters.keySet()))counters.remove(key);
            readiness="UNKNOWN";bootstrap="UNKNOWN";
            archiveRestricted();restrictedSession=new JsonObject();
        }
        if("restoration_attempted".equals(event.name)){incidentId=UUID.randomUUID().toString();retries++;}
        String transport=transport(event.candidate);
        if("candidate_failed".equals(event.name)||"candidate_succeeded".equals(event.name))outcomes.addProperty(transport,event.failure==null?"SUCCESS":event.failure.name());
        String before=state;state=event.state.name();
        Code diagnostic=event.failure==null?Code.NONE:Code.valueOf(event.failure.name());
        if(diagnostic==Code.INTERNAL&&("restricted".equals(transport)||"restoration_failed".equals(event.name)&&restrictedSession.size()>0))diagnostic=Code.valueOf(RestrictedTrace.firstReason(restrictedSession));
        add(Component.ORCHESTRATOR,diagnostic,before,state,transport,event.elapsedMs,now);
        if(Arrays.asList("restoration_attempted","restoration_succeeded","restoration_failed","cleanup_failed").contains(event.name)){
            JsonObject recent=events.getLast();recent.addProperty("event",event.name);
            recent.addProperty("recovery_stage",event.name.equals("cleanup_failed")?"CLEANUP":"RECOVERY");
            recent.addProperty("recovery_state",event.name.equals("restoration_attempted")?"STARTED":event.name.equals("restoration_succeeded")?"ESTABLISHED":"FAILED");
            recent.addProperty("restricted_descriptor",incidentId.equals(text(restrictedSession,"incident_id"))?"ATTEMPTED":"NOT_ATTEMPTED");
            if(RestrictedTrace.tag(text(restrictedSession,"session_tag")))recent.addProperty("previous_session_tag",text(restrictedSession,"session_tag"));
            if(event.failure!=null)recent.addProperty("policy_reason",event.failure.name());
        }
        return state.equals("FAILED")&&(before.equals("CONNECTING")||before.equals("RESTORING"));
    }
    synchronized void readiness(boolean usable,long now){
        readiness=usable?"READY":"NOT_READY";bootstrap=usable?"USABLE":"NOT_USABLE";
        add(Component.READINESS,usable?Code.READY:Code.NOT_READY,state,state,"restricted",0,now);
    }
    synchronized void readinessResult(ReadinessImportResult.Code code,long now){
        readiness=code.name();bootstrap=code==ReadinessImportResult.Code.READY?"USABLE":"NOT_USABLE";
        add(Component.READINESS,Code.valueOf(code.name()),state,state,"restricted",0,now);
    }
    synchronized void vpn(boolean open,long now){vpn=open;add(Component.VPN,open?Code.VPN_CAPTURE_READY:Code.VPN_RELEASED,state,state,"none",0,now);}
    synchronized void dns(boolean good,long now){add(Component.DNS,good?Code.DNS_PROBE_OK:Code.DNS_PROBE_FAILED,state,state,"none",0,now);}
    synchronized void nativeEvent(String event,long now){
        switch(event){
            case "bootstrap_cache_loaded": add(Component.BOOTSTRAP,Code.BOOT_CACHE_READY,state,state,"restricted",0,now);break;
            case "bootstrap_carrier_connected": add(Component.BOOTSTRAP,Code.BOOT_CARRIER_READY,state,state,"restricted",0,now);break;
            case "bootstrap_family_auth": case "family_auth": add(Component.FAMILY_AUTH,Code.FAMILY_AUTH_READY,state,state,"restricted",0,now);break;
            case "bootstrap_descriptor_received": add(Component.ROOM_BROKER,Code.BROKER_DESCRIPTOR_READY,state,state,"restricted",0,now);break;
            case "bootstrap_closed_before_dedicated": add(Component.BOOTSTRAP,Code.BOOT_CLOSED,state,state,"restricted",0,now);break;
            case "dedicated_data_ready": add(Component.SESSION,Code.SESSION_READY,state,state,"restricted",0,now);break;
            case "startup_credentials_rejected": add(Component.FAMILY_AUTH,Code.STARTUP_REJECTED,state,state,"restricted",0,now);break;
            case "startup_control_unavailable": add(Component.ROOM_BROKER,Code.CONTROL_UNAVAILABLE,state,state,"restricted",0,now);break;
            case "startup_failed": add(Component.SESSION,Code.STARTUP_FAILED,state,state,"restricted",0,now);break;
            case "bootstrap_exchange_failed": add(Component.ROOM_BROKER,Code.STARTUP_FAILED,state,state,"restricted",0,now);break;
            default: break;
        }
    }
    synchronized void counter(String name,long value){
        if(Arrays.asList("dns","tcp","tcp_active","tcp_peak","udp_denied","ipv6_denied","protect_ok","protect_denied").contains(name)&&value>=0&&value<=9007199254740991L)counters.addProperty(name,value);
    }
    synchronized void restricted(JsonObject source,int nativeState,boolean denied,long now){
        JsonObject safe=new JsonObject();
        safe.addProperty("native_state",nativeState>=0&&nativeState<=5?nativeState:-1);
        safe.addProperty("authorization_denied",denied);
        String tag=text(source,"session_tag");
        if(RestrictedTrace.tag(tag))safe.addProperty("session_tag",tag);
        String correlation=text(source,"correlation_status");
        safe.addProperty("correlation_status",RestrictedTrace.tag(tag)?"VALID":"INVALID".equals(correlation)?"INVALID":tag.isEmpty()?"MISSING":"INVALID");
        JsonObject lifecycle=RestrictedTrace.project(source.get("lifecycle"),tag);
        boolean same=text(restrictedSession,"session_tag").equals(text(safe,"session_tag"));
        if(same&&restrictedSession.has("terminal_observed_at_ms"))safe=restrictedSession.deepCopy();
        if(lifecycle!=null){
            if(same&&restrictedSession.has("lifecycle")){
                JsonObject previous=restrictedSession.getAsJsonObject("lifecycle");
                if(previous.has("first_failure"))lifecycle.add("first_failure",previous.get("first_failure").deepCopy());
            }
            safe.add("lifecycle",lifecycle);
        }
        if(same&&restrictedSession.has("terminal_observed_at_ms")){restrictedSession=safe;return;}
        enumField(source,safe,"terminal_reason","NONE","CANCELLED","DEADLINE","EOF","IO_CLOSED","FAMILY_REJECTED","MUX_PROTOCOL","RELIABLE_PROTOCOL","RELIABLE_EXHAUSTED","REMOTE_RESET","RELIABLE_CLOSED","NETWORK_TIMEOUT","NETWORK_ERROR","UNKNOWN");
        enumField(source,safe,"reliable_terminal","","closed","recovery_exhausted","protocol_violation","remote_reset","cancelled","carrier_closed","UNKNOWN");
        enumField(source,safe,"signaling_failure","NONE","UNKNOWN","read_error","read_timeout","invalid_json","close_code_1000","close_code_1001","close_code_1002","close_code_1003","close_code_1006","close_code_1007","close_code_1008","close_code_1009","close_code_1010","close_code_1011","close_code_1012","close_code_1013","close_code_1015");
        enumField(source,safe,"ice_failure","NONE","UNKNOWN","SUBSCRIBER_failed","SUBSCRIBER_disconnected","PUBLISHER_failed","PUBLISHER_disconnected");
        for(String field:new String[]{"subscriber_state","publisher_state"})enumField(source,safe,field,"new","connecting","connected","disconnected","failed","closed","UNKNOWN");
        for(String field:new String[]{"terminal_at_ms","observed_at_ms","retransmissions","recovery_timeouts","received_frames","sent_frames","protocol_errors","dns_responses","dns_errors","tcp_open_ok","tcp_open_errors","sent_bytes","received_bytes","evidence_dropped"}){
            JsonElement value=source.get(field);
            if(value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isNumber()){
                try{long count=value.getAsBigDecimal().longValueExact();if(count>=0&&count<=9007199254740991L)safe.addProperty(field,count);}catch(ArithmeticException|NumberFormatException ignored){}
            }
        }
        if(denied||nativeState==3||nativeState==5||!text(safe,"terminal_reason").equals("NONE")&&!text(safe,"terminal_reason").equals("UNKNOWN"))safe.addProperty("terminal_observed_at_ms",now);
        if(!same)archiveRestricted();
        if(RestrictedTrace.tag(tag)){
            for(String field:new String[]{"device_support_id","connection_id","incident_id"}){
                if(same&&restrictedSession.has(field))safe.add(field,restrictedSession.get(field).deepCopy());
                else safe.addProperty(field,field.equals("device_support_id")?supportId:field.equals("connection_id")?connectionId:incidentId);
            }
        }
        restrictedSession=safe;
    }
    private void archiveRestricted(){
        if(!RestrictedTrace.tag(text(restrictedSession,"session_tag")))return;
        if(restrictedHistory.size()==4)restrictedHistory.removeFirst();
        JsonObject archived=restrictedSession.deepCopy();
        if(archived.has("lifecycle")){
            JsonObject lifecycle=archived.getAsJsonObject("lifecycle");JsonArray trace=lifecycle.getAsJsonArray("trace");
            int removed=Math.max(0,trace.size()-32);
            while(trace.size()>32)trace.remove(0);
            lifecycle.addProperty("archive_dropped",removed);
        }
        restrictedHistory.addLast(archived);
    }
    synchronized void cleanup(boolean success,long now){
        add(Component.SESSION,success?Code.NONE:Code.RECOVERY_CLEANUP_FAILED,state,state,"restricted",0,now);
        JsonObject recent=events.getLast();recent.addProperty("event",success?"cleanup_completed":"cleanup_failed");
        String tag=text(restrictedSession,"session_tag");if(RestrictedTrace.tag(tag))recent.addProperty("session_tag",tag);
        if(!success)recent.addProperty("recovery_stage","CLEANUP");
    }
    private static String text(JsonObject source,String field){
        JsonElement value=source.get(field);return value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isString()?value.getAsString():"";
    }
    private static void enumField(JsonObject source,JsonObject target,String field,String... allowed){
        String value=text(source,field);target.addProperty(field,Arrays.asList(allowed).contains(value)?value:"UNKNOWN");
    }
    private static String transport(String value){return Arrays.asList("awg","wg","tcp","restricted").contains(value)?value:"none";}
    private void add(Component component,Code reason,String before,String after,String transport,long duration,long now){
        JsonObject event=new JsonObject();event.addProperty("timestamp",now);event.addProperty("connection_id",connectionId);event.addProperty("incident_id",incidentId);
        event.addProperty("component",component.name());event.addProperty("state_from",before);event.addProperty("state_to",after);
        event.addProperty("transport_class",transport);event.addProperty("reason_code",reason.name());event.addProperty("duration_ms",Math.max(0,duration));
        event.addProperty("retry_count",retries);event.addProperty("app_version",version);
        if(events.size()==128)events.removeFirst();events.addLast(event);
    }
    synchronized JsonObject snapshot(){
        JsonObject result=new JsonObject();result.addProperty("schema",1);result.addProperty("device_support_id",supportId);
        result.addProperty("connection_id",connectionId);result.addProperty("incident_id",incidentId);result.addProperty("app_version",version);
        result.addProperty("version_code",build);result.addProperty("os_api",os);result.addProperty("network_class",network);
        result.addProperty("state",state);result.addProperty("vpn_capture_open",vpn);result.addProperty("restricted_readiness",readiness);result.addProperty("bootstrap_directory",bootstrap);
        result.add("transport_outcomes",outcomes.deepCopy());result.add("counters",counters.deepCopy());
        result.add("restricted_session",restrictedSession.deepCopy());
        JsonArray history=new JsonArray();for(JsonObject session:restrictedHistory)history.add(session.deepCopy());result.add("restricted_history",history);
        JsonArray recent=new JsonArray();for(JsonObject event:events)recent.add(event.deepCopy());result.add("events",recent);return result;
    }
}
