package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import static com.familyconnect.app.ControlJson.*;

final class RestrictedCache {
    interface Storage { byte[] read() throws Exception; void write(byte[] raw) throws Exception; }
    interface Validator { boolean valid(byte[] response) throws Exception; }
    private final Storage storage;
    private final Validator validator;
    RestrictedCache(Storage storage, Validator validator) { this.storage=storage;this.validator=validator; }
    private JsonObject state() throws Exception {
        byte[] raw=storage.read();
        if(raw==null){JsonObject fresh=new JsonObject();fresh.add("response",JsonNull.INSTANCE);fresh.addProperty("denied",false);fresh.addProperty("next_attempt",0);return fresh;}
        require(raw.length<=70000);JsonObject value=parse(raw).getAsJsonObject();fields(value,"response denied next_attempt");
        require(value.get("denied").isJsonPrimitive()&&value.get("denied").getAsJsonPrimitive().isBoolean());integer(value.get("next_attempt"),0);return value;
    }
    private static byte[] bytes(JsonElement value){return value.toString().getBytes(StandardCharsets.UTF_8);}
    private void save(JsonObject value)throws Exception{storage.write(bytes(value));}
    byte[] usable()throws Exception{
        JsonObject value=state();if(value.get("denied").getAsBoolean()||value.get("response").isJsonNull())return null;
        byte[] raw=bytes(value.get("response"));return validator.valid(raw)?raw:null;
    }
    boolean attempt(long now)throws Exception{
        JsonObject value=state();if(integer(value.get("next_attempt"),0)>now)return false;
        byte[] raw=usable();
        if(raw!=null&&integer(parse(raw).getAsJsonObject().get("expires_at"),1)>now+300)return false;
        value.addProperty("next_attempt",now+300);save(value);return true;
    }
    void denied()throws Exception{JsonObject value=state();value.addProperty("denied",true);save(value);}
    void accept(byte[] raw)throws Exception{
        require(raw.length>0&&raw.length<=65536&&validator.valid(raw));
        JsonObject incoming=parse(raw).getAsJsonObject(),value=state();
        if(!value.get("response").isJsonNull()) {
            JsonObject previous=value.getAsJsonObject("response");
            if(value.get("denied").getAsBoolean())require(integer(incoming.get("issued_at"),0)>integer(previous.get("issued_at"),0)
                &&!text(incoming.get("challenge")).equals(text(previous.get("challenge"))));
            for(String field:new String[]{"issued_at","revision","minimum_crl"})require(integer(incoming.get(field),0)>=integer(previous.get(field),0));
            JsonObject nextIssuer=issuer(incoming),oldIssuer=issuer(previous);
            long nextSequence=integer(nextIssuer.get("sequence"),1),oldSequence=integer(oldIssuer.get("sequence"),1);
            require(nextSequence>=oldSequence);
            if(nextSequence==oldSequence)require(nextIssuer.equals(oldIssuer));
            String nextTime=text(incoming.getAsJsonObject("directory").get("issued_at")),oldTime=text(previous.getAsJsonObject("directory").get("issued_at"));
            int order=java.time.Instant.parse(nextTime).compareTo(java.time.Instant.parse(oldTime));require(order>=0);
            if(order==0)require(incoming.get("directory").equals(previous.get("directory")));
        }
        value.add("response",incoming);value.addProperty("denied",false);save(value);
    }
    private static JsonObject issuer(JsonObject value)throws Exception{return parse(Base64.getDecoder().decode(text(value.getAsJsonObject("issuer").get("payload")))).getAsJsonObject();}
    String summary() {
        try {JsonObject value=state();if(value.get("denied").getAsBoolean())return "NOT READY — authorization rejected";
            if(value.get("response").isJsonNull())return "NOT READY — provisioning missing";
            return usable()!=null?"READY — provisioning PRESENT_VALID; BOOT-1 PRESENT_VALID; usable YES":"NOT READY — expired or invalid material";
        }catch(Exception | LinkageError failure){return "NOT READY — secure state unavailable";}
    }
}
