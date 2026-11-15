package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.util.Locale;

final class TechnicalMetadataSnapshot {
    static final long RETENTION_MS=7L*86400000;
    private TechnicalMetadataSnapshot(){}
    static String networkKind(boolean wifi,boolean cellular,boolean ethernet){
        if((wifi?1:0)+(cellular?1:0)+(ethernet?1:0)!=1)return "UNKNOWN";
        return wifi?"WIFI":cellular?"CELLULAR":"ETHERNET";
    }
    static JsonObject report(long epoch,long sequence,boolean enabled,JsonObject observations){
        if(epoch<=0||sequence<=0||epoch>9007199254740991L||sequence>9007199254740991L)throw new IllegalArgumentException("Metadata counter bound");
        JsonObject result=new JsonObject();result.addProperty("schema",1);
        result.addProperty("report_id",String.format(Locale.ROOT,"%016x%016x",epoch,sequence));
        result.addProperty("consent_epoch",epoch);result.addProperty("sequence",sequence);
        result.addProperty("operation",enabled?"sample":"revoke");
        result.add("observations",enabled?observations:new JsonObject());return result;
    }
    static JsonObject observation(String source,String status,String reason,JsonObject values,long sampled,long age){
        JsonObject result=new JsonObject();result.addProperty("sampled_at_ms",Math.max(0,sampled));
        result.addProperty("age_ms",Math.max(0,age));result.addProperty("source",source);
        result.addProperty("status",status);result.addProperty("reason",reason);result.add("values",values);return result;
    }
    static String transport(String raw){
        if("awg".equals(raw)||"wg".equals(raw))return "AWG";
        if("tcp".equals(raw))return "TCP";
        if("restricted".equals(raw)||"restricted-refresh".equals(raw)||"telemost".equals(raw))return "MESH";
        return "UNKNOWN";
    }
    static String state(String raw){
        switch(raw){
            case "on":return "CONNECTED";
            case "connecting":return "CONNECTING";
            case "restoring":return "RESTORING";
            case "failed":case "cleanup-required":return "FAILED";
            case "disconnecting":return "STOPPING";
            case "off":return "DISCONNECTED";
            default:return "UNKNOWN";
        }
    }
    static String gateway(String raw){
        if("ru".equals(raw)||"gateway-ru".equals(raw))return "gateway-ru";
        if("nl".equals(raw)||"nl-amsterdam-1".equals(raw))return "nl-amsterdam-1";
        if("nl-amsterdam-2".equals(raw))return raw;
        return "UNKNOWN";
    }
    static JsonObject session(String preference,String attempt,String active,String gateway,String state){
        JsonObject values=new JsonObject();values.addProperty("preference","auto".equals(preference)?"AUTO":transport(preference));
        values.addProperty("attempt",attempt);values.addProperty("state",state);
        boolean established="CONNECTED".equals(state);
        values.addProperty("transport",established?transport(active):"NONE");
        values.addProperty("gateway",established?gateway(gateway):"UNKNOWN");return values;
    }
    static String text(String raw,int limit){
        if(raw==null||raw.trim().isEmpty())return null;
        StringBuilder result=new StringBuilder();raw.codePoints().filter(code->!Character.isISOControl(code)&&!Character.isIdentifierIgnorable(code))
            .limit(limit).forEach(result::appendCodePoint);String value=result.toString().trim();return value.isEmpty()?null:value;
    }
}
