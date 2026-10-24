package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;

final class DiagnosticRecordBudget {
    private final JsonObject omitted=new JsonObject();
    private int bytes;

    private DiagnosticRecordBudget(JsonObject record,int original){
        JsonObject budget=new JsonObject();
        budget.addProperty("limit_bytes",DiagnosticRing.RECORD_LIMIT);
        budget.addProperty("untrimmed_bytes",original);
        budget.add("omitted_detail_items",omitted);
        record.add("record_budget",budget);
        bytes=original+size(budget)+"\"record_budget\":".length()+1;
    }
    static JsonObject apply(JsonObject record){
        int original=size(record);
        if(original<=DiagnosticRing.RECORD_LIMIT)return record;
        DiagnosticRecordBudget budget=new DiagnosticRecordBudget(record,original);
        JsonArray history=record.getAsJsonArray("restricted_history");
        if(history!=null)for(int index=0;index<history.size();index++)
            budget.session(history.get(index).getAsJsonObject(),"restricted_history["+index+"]");
        JsonObject current=record.getAsJsonObject("restricted_session");
        if(current!=null)budget.session(current,"restricted_session");
        budget.trim(record,"events","events");
        return record;
    }
    private void session(JsonObject session,String path){
        JsonObject lifecycle=session.getAsJsonObject("lifecycle");
        if(lifecycle!=null){
            trim(lifecycle,"trace",path+".lifecycle.trace");
            JsonObject boundaries=lifecycle.getAsJsonObject("boundaries");
            if(boundaries!=null)trim(boundaries,"events",path+".lifecycle.boundaries.events");
        }
        JsonObject mux=session.getAsJsonObject("mux_lifecycle");
        if(mux!=null){
            trim(mux,"events",path+".mux_lifecycle.events");
            trim(mux,"incidents",path+".mux_lifecycle.incidents");
        }
    }
    private void trim(JsonObject parent,String field,String path){
        JsonArray details=parent.getAsJsonArray(field);
        if(details==null)return;
        int removed=0;
        while(bytes>DiagnosticRing.RECORD_LIMIT&&details.size()>2){
            int previous=size(omitted);
            bytes-=size(details.remove(1))+1;
            omitted.addProperty(path,++removed);
            bytes+=size(omitted)-previous;
        }
    }
    static int size(JsonElement value){return value.toString().getBytes(StandardCharsets.UTF_8).length;}
}
