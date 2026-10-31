package com.familyconnect.app;

import com.google.gson.*;

final class MuxLifecycle {
    static void project(JsonObject source,JsonObject safe){
        JsonObject raw=object(source,"mux_lifecycle");
        if(raw==null)return;
        JsonObject result=new JsonObject();
        numbers(raw,result,"dropped","failure_at","close_at","incident_dropped","expected_crossings","actual_violations","unclassified");
        choice(raw,result,"failure_reason","none","eof","reset","protocol","cancelled","deadline","closed_pipe","other","");
        JsonArray events=new JsonArray();
        if(raw.has("events")&&raw.get("events").isJsonArray()){
            JsonArray list=raw.getAsJsonArray("events");
            for(int index=Math.max(0,list.size()-32);index<list.size();index++){
                if(list.get(index).isJsonObject())events.add(event(list.get(index).getAsJsonObject()));
            }
        }
        result.add("events",events);
        JsonObject incident=object(raw,"first_unknown");
        if(incident!=null)result.add("first_unknown",incident(incident));
        JsonArray incidents=new JsonArray();
        if(raw.has("incidents")&&raw.get("incidents").isJsonArray()){
            JsonArray list=raw.getAsJsonArray("incidents");
            for(int index=0;index<Math.min(32,list.size());index++)if(list.get(index).isJsonObject())incidents.add(incident(list.get(index).getAsJsonObject()));
            if(list.size()>32)result.addProperty("projection_overflow",true);
        }
        result.add("incidents",incidents);
        if(result.toString().length()>98304){result.remove("incidents");result.addProperty("projection_overflow",true);}
        safe.add("mux_lifecycle",result);
    }
    static JsonObject incident(JsonObject incident){
            JsonObject selected=new JsonObject();
            numbers(incident,selected,"failure_at","bytes","credit");
            bools(incident,selected,"known","cancelled");
            choice(incident,selected,"class","expected","violation","unclassified");
            choice(incident,selected,"detail","no_retained_history","live_state","after_session_failure","malformed","after_peer_terminal","crossed_reset","not_local_abort","cancelled_open","not_opened","data_after_fin","credit_overflow","inflight_data_on_abort","inflight_credit_on_abort","duplicate_fin","inflight_fin_on_abort","close_before_fin","crossed_close","terminal_state");
            JsonObject first=object(incident,"event");if(first!=null)selected.add("event",event(first));
            JsonObject stream=object(incident,"stream");
            if(stream!=null){
                JsonObject record=new JsonObject();
                numbers(stream,record,"id","created","opened","finished","removed","sent","received","used","send_credit","receive_credit");
                bools(stream,record,"local_fin","remote_fin","local_abort","peer_terminal","peer_close");
                for(String key:new String[]{"enqueued","send_started","send_done","receive_at"}){
                    if(!stream.has(key)||!stream.get(key).isJsonArray())continue;
                    JsonArray times=stream.getAsJsonArray(key),bounded=new JsonArray();
                    for(int index=0;index<Math.min(9,times.size());index++){
                        JsonObject entry=new JsonObject(),safe=new JsonObject();entry.add("at",times.get(index));numbers(entry,safe,"at");
                        bounded.add(safe.has("at")?safe.get("at"):new JsonPrimitive(0));
                    }
                    record.add(key,bounded);
                }
                choice(stream,record,"reason","none","eof","reset","protocol","cancelled","deadline","closed_pipe","other","");
                selected.add("stream",record);
            }
            return selected;
    }
    static JsonObject event(JsonObject raw){
        JsonObject result=new JsonObject();numbers(raw,result,"index","at","id","kind");
        choice(raw,result,"stage","create","opened","enqueue","send_start","send_done","receive","finish","remove","unknown","failure","close","violation");
        choice(raw,result,"reason","new","peer","lease","socket","control","data","batch","local","wire","terminal","missing","caller","none","eof","reset","protocol","cancelled","deadline","closed_pipe","other");
        return result;
    }
    static JsonObject object(JsonObject raw,String key){return raw.has(key)&&raw.get(key).isJsonObject()?raw.getAsJsonObject(key):null;}
    static void numbers(JsonObject raw,JsonObject result,String...keys){for(String key:keys)try{JsonElement value=raw.get(key);if(value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isNumber()){long number=value.getAsLong();if(number>=0)result.addProperty(key,number);}}catch(RuntimeException ignored){}}
    static void bools(JsonObject raw,JsonObject result,String...keys){for(String key:keys){JsonElement value=raw.get(key);if(value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isBoolean())result.addProperty(key,value.getAsBoolean());}}
    static void choice(JsonObject raw,JsonObject result,String key,String...allowed){try{String value=raw.get(key).getAsString();for(String item:allowed)if(item.equals(value)){result.addProperty(key,value);return;}}catch(RuntimeException ignored){}}
}
