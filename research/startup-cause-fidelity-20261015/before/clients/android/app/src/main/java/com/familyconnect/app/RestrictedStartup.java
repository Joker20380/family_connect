package com.familyconnect.app;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

final class RestrictedStartup {
    static JsonObject project(JsonElement input) {
        if(input==null||!input.isJsonObject())return null;
        JsonObject source=input.getAsJsonObject(),safe=new JsonObject();
        for(String field:new String[]{"schema","attempt","started_unix_ms","observed_ms","completed_ms"})RestrictedTrace.number(source,safe,field);
        if(!safe.has("schema")||safe.get("schema").getAsLong()!=1||!safe.has("attempt")||safe.get("attempt").getAsLong()<1||!safe.has("started_unix_ms"))return null;
        String status=RestrictedTrace.text(source,"status"),stage=RestrictedTrace.text(source,"stage"),cause=RestrictedTrace.text(source,"cause");
        if(!RestrictedTrace.allowed(status,"RUNNING|SUCCEEDED|FAILED|CANCELLED"))return null;
        if(!RestrictedTrace.allowed(stage,"STARTUP|PROFILE|DIRECTORY|SEED_CREATE|SEED_CONNECT|SEED_ADMISSION|SEED_READ|FAMILY_AUTH|HELLO_RECEIVE|REQUEST_SEND|DESCRIPTOR_RECEIVE|DESCRIPTOR_VALIDATE|BYE_SEND|BYE_RECEIVE|DEDICATED_CREATE|DEDICATED_CONNECT|DEDICATED_AUTH|DEDICATED_BIND|DEDICATED_MUX|CONTROL_REFRESH|UNKNOWN"))stage="UNKNOWN";
        if(!RestrictedTrace.allowed(cause,"NONE|CANCELLED|DEADLINE|CERTIFICATE_TIME_INVALID|CERTIFICATE_INVALID|CERTIFICATE_AUTHORITY|CERTIFICATE_HOSTNAME|PROVIDER_API|CARRIER_CLOSED|EOF|PROTOCOL_REJECTED|CREDENTIALS_REJECTED|DESCRIPTOR_REJECTED|DESCRIPTOR_EXPIRED|EXCHANGE_CLOSED|UNKNOWN"))cause="UNKNOWN";
        safe.addProperty("status",status);safe.addProperty("stage",stage);safe.addProperty("cause",cause);
        JsonElement complete=source.get("complete");
        if(complete==null||!complete.isJsonPrimitive()||!complete.getAsJsonPrimitive().isBoolean())return null;
        safe.addProperty("complete",complete.getAsBoolean());
        String fingerprint=RestrictedTrace.text(source,"directory_fingerprint");
        if(RestrictedTrace.tag(fingerprint))safe.addProperty("directory_fingerprint",fingerprint);
        return safe;
    }
}
