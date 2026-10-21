package com.familyconnect.app;

import com.google.gson.*;
import java.util.*;

final class SupportSnapshot {
    static final String[] COUNTERS={"protocol_errors","retransmissions","retry_bytes","sent_bytes","received_bytes","recovery_timeouts","mux_window","observed_at_ms"};
    static final String[] REASONS={"open_replay","unknown_stream","open_state","data_state","credit_state","fin_state","close_state","frame_kind","dns_replay","dns_role","dns_unmatched"};
    static void number(JsonObject input,JsonObject output,String name){
        try{JsonElement value=input.get(name);if(value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isNumber()){
            long count=value.getAsBigDecimal().longValueExact();if(count>=0&&count<=9007199254740991L)output.addProperty(name,count);
        }}catch(ArithmeticException|NumberFormatException ignored){}
    }
    static JsonObject object(JsonObject source,String name){JsonElement value=source.get(name);return value!=null&&value.isJsonObject()?value.getAsJsonObject():new JsonObject();}
    static void choice(JsonObject source,JsonObject target,String from,String to,String... allowed){
        JsonElement value=source.get(from);String text=value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isString()?value.getAsString():"";
        target.addProperty(to,Arrays.asList(allowed).contains(text)?text:"UNKNOWN");
    }
    static JsonObject project(JsonObject ring,int version,long now){
        JsonObject result=new JsonObject(),metrics=new JsonObject();
        result.addProperty("schema",1);result.addProperty("report_id",UUID.randomUUID().toString().replace("-",""));
        result.addProperty("platform","android");result.addProperty("version_code",version);result.addProperty("sampled_at_ms",now);result.addProperty("consent",true);
        choice(ring,metrics,"state","state","DISCONNECTED","CONNECTING","CONNECTED","RESTORING","FAILED","STOPPING");
        choice(ring,metrics,"network_class","network","WIFI","CELLULAR","ETHERNET","VPN","NONE");
        choice(ring,metrics,"restricted_readiness","readiness","READY","NOT_READY");
        JsonElement vpn=ring.get("vpn_capture_open");if(vpn!=null&&vpn.isJsonPrimitive()&&vpn.getAsJsonPrimitive().isBoolean())metrics.add("vpn_capture_open",vpn);
        JsonObject session=object(ring,"restricted_session");
        choice(session,metrics,"speed_profile","speed_profile","P0","P1","P2");
        choice(session,metrics,"mux_profile","mux_profile","LEGACY64","CREDIT128");
        choice(session,metrics,"terminal_reason","terminal_reason","NONE","CANCELLED","REMOTE_RESET","RELIABLE_EXHAUSTED","IO_CLOSED","MUX_PROTOCOL","RELIABLE_PROTOCOL","FAMILY_REJECTED","DEADLINE","NETWORK_TIMEOUT");
        JsonElement tag=session.get("session_tag");if(tag!=null&&tag.isJsonPrimitive()&&tag.getAsJsonPrimitive().isString()&&tag.getAsString().matches("[0-9a-f]{32}|[0-9a-f]{64}"))metrics.add("session_tag",tag);
        for(String key:COUNTERS)number(session,metrics,key);
        JsonObject limits=object(session,"reliable_limits");
        String[][] names={{"local_send","send_window"},{"local_receive","receive_window"},{"peer_receive","peer_receive_window"},{"effective_send","effective_send_window"}};
        for(String[] pair:names){JsonObject selected=new JsonObject();number(limits,selected,pair[0]);if(selected.has(pair[0]))metrics.add(pair[1],selected.get(pair[0]));}
        JsonObject reasons=object(session,"protocol_error_reasons");for(String key:REASONS)number(reasons,metrics,key);
        result.add("metrics",metrics);return result;
    }
}
