package com.familyconnect.app;

import com.google.gson.*;

final class MuxLifecycle {
    static void project(JsonObject source,JsonObject safe){
        JsonObject raw=object(source,"mux_lifecycle");
        if(raw==null)return;
        JsonObject result=new JsonObject();
        numbers(raw,result,"dropped","failure_at","close_at");
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
        if(incident!=null){
            JsonObject selected=new JsonObject();
            numbers(incident,selected,"failure_at");
            bools(incident,selected,"known","cancelled");
            JsonObject first=object(incident,"event");if(first!=null)selected.add("event",event(first));
            JsonObject stream=object(incident,"stream");
            if(stream!=null){
                JsonObject record=new JsonObject();
                numbers(stream,record,"id","created","opened","finished","removed","sent","received","used","send_credit","receive_credit");
                bools(stream,record,"local_fin","remote_fin");
                choice(stream,record,"reason","none","eof","reset","protocol","cancelled","deadline","closed_pipe","other","");
                selected.add("stream",record);
            }
            result.add("first_unknown",selected);
        }
        if(result.toString().length()<=8192)safe.add("mux_lifecycle",result);
    }
    static JsonObject event(JsonObject raw){
        JsonObject result=new JsonObject();numbers(raw,result,"index","at","id","kind");
        choice(raw,result,"stage","create","opened","enqueue","send_start","send_done","receive","finish","remove","unknown","failure","close");
        choice(raw,result,"reason","new","peer","lease","socket","control","data","batch","local","wire","terminal","missing","caller","none","eof","reset","protocol","cancelled","deadline","closed_pipe","other");
        return result;
    }
    static JsonObject object(JsonObject raw,String key){return raw.has(key)&&raw.get(key).isJsonObject()?raw.getAsJsonObject(key):null;}
    static void numbers(JsonObject raw,JsonObject result,String...keys){for(String key:keys)try{JsonElement value=raw.get(key);if(value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isNumber()){long number=value.getAsLong();if(number>=0)result.addProperty(key,number);}}catch(RuntimeException ignored){}}
    static void bools(JsonObject raw,JsonObject result,String...keys){for(String key:keys){JsonElement value=raw.get(key);if(value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isBoolean())result.addProperty(key,value.getAsBoolean());}}
    static void choice(JsonObject raw,JsonObject result,String key,String...allowed){try{String value=raw.get(key).getAsString();for(String item:allowed)if(item.equals(value)){result.addProperty(key,value);return;}}catch(RuntimeException ignored){}}
}
