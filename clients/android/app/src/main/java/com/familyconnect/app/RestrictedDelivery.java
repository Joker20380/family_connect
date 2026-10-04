package com.familyconnect.app;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

final class RestrictedDelivery {
    static final int LIMIT=8;
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
