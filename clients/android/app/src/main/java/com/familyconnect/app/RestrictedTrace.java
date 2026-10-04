package com.familyconnect.app;

import com.google.gson.*;
import java.util.Arrays;

final class RestrictedTrace {
    static final String REASONS="NONE|SIGNAL_WS_CLOSE|ICE_DISCONNECTED|ICE_FAILED|PEER_CONNECTION_FAILED|CARRIER_EOF|CARRIER_ERROR|FAMILY_TLS_EOF|FAMILY_TLS_ERROR|GATEWAY_CLOSE|HEARTBEAT_TIMEOUT|REMOTE_CLOSE|RECOVERY_CLEANUP_FAILED|RECOVERY_DESCRIPTOR_FAILED|RECOVERY_JOIN_FAILED|RECOVERY_CARRIER_FAILED|RELIABLE_HANDSHAKE_TIMEOUT|RELIABLE_FRAME_TIMEOUT|RELIABLE_RETRY_EXHAUSTED|UNKNOWN_INTERNAL";
    static final String STAGES="AUTHORIZED|ROOM_CREATION|DESCRIPTOR|GATEWAY_JOIN|SIGNALING|WEBSOCKET|ICE|PEER_CONNECTION|CARRIER|CARRIER_ACTIVITY|FAMILY_TLS|GATEWAY_SESSION|HEARTBEAT|LIVENESS|LOCAL_CLOSE|REMOTE_CLOSE|RECOVERY|CLEANUP";
    static final String STATES="STARTED|ESTABLISHED|ISSUED|TX|RX|FAILED|CLOSED|COMPLETED|ATTEMPTED|NOT_ATTEMPTED|new|checking|connecting|connected|completed|disconnected|failed|closed";
    static String text(JsonObject source,String field){
        JsonElement value=source.get(field);
        return value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isString()?value.getAsString():"";
    }
    static boolean allowed(String value,String choices){return Arrays.asList(choices.split("\\|",-1)).contains(value);}
    static boolean tag(String value){return value.matches("[0-9a-f]{64}");}
    static void number(JsonObject source,JsonObject target,String field){
        JsonElement value=source.get(field);
        if(value==null||!value.isJsonPrimitive()||!value.getAsJsonPrimitive().isNumber())return;
        try{long count=value.getAsBigDecimal().longValueExact();if(count>=0&&count<=9007199254740991L)target.addProperty(field,count);}catch(ArithmeticException|NumberFormatException ignored){}
    }
    static JsonObject event(JsonElement input,String tag){
        if(input==null||!input.isJsonObject())return null;
        JsonObject source=input.getAsJsonObject(),safe=new JsonObject();
        if(!tag.equals(text(source,"session_tag")))return null;
        for(String field:new String[]{"stage","state","reason"}){
            String value=text(source,field),choices=field.equals("stage")?STAGES:field.equals("state")?STATES:REASONS;
            if(!allowed(value,choices))return null;
            safe.addProperty(field,value);
        }
        safe.addProperty("session_tag",tag);
        JsonObject delivery=RestrictedDelivery.project(source.get("delivery"));if(delivery!=null)safe.add("delivery",delivery);
        for(String field:new String[]{"sequence","timestamp_ms","tx","rx","reliable_age_ms","reliable_retries","reliable_pending","reliable_sacked","reliable_ack_age_ms","reliable_progress_age_ms","reliable_ack_received"})number(source,safe,field);
        if(!safe.has("sequence")||safe.get("sequence").getAsLong()==0||!safe.has("timestamp_ms"))return null;
        String target=text(source,"target");if(allowed(target,"SUBSCRIBER|PUBLISHER"))safe.addProperty("target",target);
        String heartbeat=text(source,"heartbeat_kind");if(allowed(heartbeat,"APPLICATION|WEBSOCKET"))safe.addProperty("heartbeat_kind",heartbeat);
        String close=text(source,"close_reason");if(allowed(close,"ping|timeout|duplicate|expired|inactivity|shutdown|restart|invalid|ack|idle|session|READ_ERROR|READ_TIMEOUT|INVALID_MESSAGE|WRITE_ERROR"))safe.addProperty("close_reason",close);
        number(source,safe,"close_code");
        if(safe.has("close_code")&&(safe.get("close_code").getAsLong()<1000||safe.get("close_code").getAsLong()>4999))safe.remove("close_code");
        return safe;
    }
    static JsonObject project(JsonElement input,String tag){
        if(!tag(tag)||input==null||!input.isJsonObject())return null;
        JsonObject source=input.getAsJsonObject(),safe=new JsonObject();
        if(!tag.equals(text(source,"session_tag"))||!"VALID".equals(text(source,"correlation_status")))return null;
        safe.addProperty("session_tag",tag);safe.addProperty("correlation_status","VALID");
        for(String field:new String[]{"trace_dropped","export_dropped","delivery_dropped"})number(source,safe,field);
        JsonObject first=event(source.get("first_failure"),tag);
        if(first!=null&&!"NONE".equals(text(first,"reason")))safe.add("first_failure",first);
        JsonArray trace=new JsonArray();int rejected=0;
        JsonElement entries=source.get("trace");
        if(entries!=null&&entries.isJsonArray()){
            JsonArray list=entries.getAsJsonArray();rejected=Math.max(0,list.size()-192);long sequence=0;
            for(int index=Math.max(0,list.size()-192);index<list.size();index++){
                JsonObject item=event(list.get(index),tag);
                if(item!=null&&item.get("sequence").getAsLong()>sequence){sequence=item.get("sequence").getAsLong();trace.add(item);}else rejected++;
            }
        }
        int retained=0,removed=0;
        for(int index=trace.size()-1;index>=0;index--){
            JsonObject item=trace.get(index).getAsJsonObject();
            if(item.has("delivery")&&++retained>RestrictedDelivery.LIMIT){item.remove("delivery");removed++;}
        }
        safe.addProperty("delivery_projection_dropped",removed);
        safe.add("trace",trace);safe.addProperty("projection_dropped",rejected);return safe;
    }
    static String firstReason(JsonObject session){
        JsonElement lifecycle=session.get("lifecycle");
        if(lifecycle==null||!lifecycle.isJsonObject())return "UNKNOWN_INTERNAL";
        JsonElement first=lifecycle.getAsJsonObject().get("first_failure");
        return first!=null&&first.isJsonObject()?text(first.getAsJsonObject(),"reason"):"UNKNOWN_INTERNAL";
    }
}
