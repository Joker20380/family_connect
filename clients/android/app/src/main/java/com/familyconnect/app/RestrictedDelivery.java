package com.familyconnect.app;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;

final class RestrictedDelivery {
    static final int LIMIT=8;
    static final String BOUNDARY_STAGES="reliable_send|carrier_queued|carrier_written|rtp_written|rtp_received|vp8_reassembled|carrier_message_completed|reliable_data_accepted|ack_generated|ack_sent|ack_received";
    static final String BOUNDARY_RESULTS="ok|write_error|no_rtp|incomplete|duplicate|stale|recent|capacity|conflict|expired|crc|malformed|protocol|old_rtp|window|frame_discard";
    static JsonObject boundaries(JsonElement element){
        if(element==null||!element.isJsonObject())return null;
        JsonObject source=element.getAsJsonObject(),safe=new JsonObject();
        RestrictedTrace.number(source,safe,"dropped");
        JsonElement raw=source.get("events");
        if(!safe.has("dropped")||raw==null||!raw.isJsonArray())return null;
        JsonArray entries=raw.getAsJsonArray(),output=new JsonArray();
        long previous=0;int rejected=Math.max(0,entries.size()-64);
        for(int index=Math.max(0,entries.size()-64);index<entries.size();index++){
            JsonElement item=entries.get(index);
            if(!item.isJsonObject()){rejected++;continue;}
            JsonObject input=item.getAsJsonObject(),point=new JsonObject();
            String stage=RestrictedTrace.text(input,"stage"),result=RestrictedTrace.text(input,"result"),direction=RestrictedTrace.text(input,"direction");
            if(!RestrictedTrace.allowed(stage,BOUNDARY_STAGES)||!RestrictedTrace.allowed(result,BOUNDARY_RESULTS)||!RestrictedTrace.allowed(direction,"tx|rx")){rejected++;continue;}
            boolean valid=true;
            for(String field:"index at_ms data_sequence attempt sender message fragment total timestamp media_track first_rtp last_rtp packets ack_base ack_mask".split(" ")){
                if(!input.has(field))continue;
                RestrictedTrace.number(input,point,field);
                if(!point.has(field)){valid=false;break;}
                long value=count(point,field);
                if(RestrictedTrace.allowed(field,"attempt")&&value>32||RestrictedTrace.allowed(field,"sender|message|timestamp|media_track|ack_mask|packets")&&value>4294967295L
                    ||RestrictedTrace.allowed(field,"first_rtp|last_rtp")&&value>65535||RestrictedTrace.allowed(field,"fragment|total")&&value>8)valid=false;
            }
            for(String field:"data_known attempt_known message_known frame_known".split(" ")){
                if(!input.has(field))continue;
                JsonElement flag=input.get(field);
                if(!flag.isJsonPrimitive()||!flag.getAsJsonPrimitive().isBoolean()){valid=false;break;}
                point.addProperty(field,flag.getAsBoolean());
            }
            if(!valid||!point.has("index")||!point.has("at_ms")||count(point,"index")<=previous){rejected++;continue;}
            previous=count(point,"index");
            point.addProperty("stage",stage);point.addProperty("result",result);point.addProperty("direction",direction);output.add(point);
        }
        safe.add("events",output);safe.addProperty("projection_dropped",rejected);return safe;
    }
    static JsonObject component(JsonObject source,String key,String numbers,String flags){
        JsonElement element=source.get(key);
        if(element==null||!element.isJsonObject())return null;
        JsonObject input=element.getAsJsonObject(),safe=new JsonObject();
        for(String field:numbers.split(" ")){
            RestrictedTrace.number(input,safe,field);
            if(!safe.has(field))return null;
        }
        if(!flags.isEmpty())for(String field:flags.split(" ")){
            JsonElement value=input.get(field);
            if(value==null||!value.isJsonPrimitive()||!value.getAsJsonPrimitive().isBoolean())return null;
            safe.addProperty(field,value.getAsBoolean());
        }
        return safe;
    }
    static long count(JsonObject value,String field){return value.get(field).getAsLong();}
    static JsonObject project(JsonElement element){
        if(element==null||!element.isJsonObject())return null;
        JsonObject source=element.getAsJsonObject(),safe=new JsonObject();
        JsonObject flow=component(source,"flow","send_base send_next receive_next receive_mask ack_base ack_mask pending buffered head_retries","ack_seen head_sacked");
        if(flow!=null&&count(flow,"send_next")>=count(flow,"send_base")&&count(flow,"send_next")-count(flow,"send_base")<=32
            &&count(flow,"pending")<=32&&count(flow,"buffered")<=32&&count(flow,"head_retries")<=32
            &&count(flow,"receive_mask")<=4294967295L&&count(flow,"ack_mask")<=4294967295L&&count(flow,"ack_base")<=count(flow,"send_next"))safe.add("flow",flow);
        JsonObject assembly=component(source,"assembly","fragments completed expired malformed duplicate conflict capacity crc_failed recent pending rtp rtp_gaps vp8_frames","");
        if(assembly!=null&&count(assembly,"pending")<=16)safe.add("assembly",assembly);
        for(String key:new String[]{"pending","queued","written","received"}){
            JsonObject point=component(source,key,"sender message total mask data_sequence","data_known");
            if(point==null)continue;
            long total=count(point,"total");
            if(count(point,"sender")>4294967295L||count(point,"message")>4294967295L||total<1||total>8
                ||count(point,"mask")>=(1L<<total)||!point.get("data_known").getAsBoolean()&&count(point,"data_sequence")!=0)continue;
            safe.add(key,point);
        }
        return safe.size()==0?null:safe;
    }
}
