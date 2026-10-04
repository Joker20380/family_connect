package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import static com.familyconnect.app.ControlJson.*;

final class RestrictedCache {
    interface Storage { byte[] read() throws Exception; void write(byte[] raw) throws Exception; }
    interface Validator { boolean valid(byte[] response) throws Exception; }
    interface DetailedValidator { ReadinessImportResult.Code validate(byte[] response) throws Exception; }
    static final class PersistenceFailure extends java.io.IOException {}
    static final class ImportFailure extends IllegalArgumentException {
        final ReadinessImportResult.Code code;
        ImportFailure(ReadinessImportResult.Code value){super(value.name());code=value;}
    }
    private final Storage storage;
    private final Validator validator;
    private DetailedValidator detailed;
    RestrictedCache(Storage storage, Validator validator) { this.storage=storage;this.validator=validator;detailed=raw->validator.valid(raw)?ReadinessImportResult.Code.READY:ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED; }
    static RestrictedCache detailed(Storage storage,DetailedValidator validator){RestrictedCache cache=new RestrictedCache(storage,raw->validator.validate(raw)==ReadinessImportResult.Code.READY);cache.detailed=validator;return cache;}
    private JsonObject state() throws Exception {
        byte[] raw=storage.read();
        if(raw==null){JsonObject fresh=new JsonObject();fresh.add("response",JsonNull.INSTANCE);fresh.addProperty("denied",false);fresh.addProperty("next_attempt",0);return fresh;}
        require(raw.length<=70000);JsonObject value=parse(raw).getAsJsonObject();fields(value,value.has("receipt_context")?"response denied next_attempt receipt_context":"response denied next_attempt");
        require(value.get("denied").isJsonPrimitive()&&value.get("denied").getAsJsonPrimitive().isBoolean());integer(value.get("next_attempt"),0);return value;
    }
    private static byte[] bytes(JsonElement value){return value.toString().getBytes(StandardCharsets.UTF_8);}
    private void save(JsonObject value)throws Exception{storage.write(bytes(value));}
    byte[] usable()throws Exception{
        JsonObject value=state();if(value.get("denied").getAsBoolean()||value.get("response").isJsonNull())return null;
        byte[] raw=bytes(value.get("response"));return validator.valid(raw)?raw:null;
    }
    OwnerPrewarmReceipt context()throws Exception{
        JsonObject value=state();if(!value.has("receipt_context"))return null;
        JsonObject saved=value.getAsJsonObject("receipt_context");fields(saved,"challenge_id fetch_id");
        return new OwnerPrewarmReceipt(text(saved.get("challenge_id")),text(saved.get("fetch_id")));
    }
    ReadinessImportResult evaluate(OwnerPrewarmReceipt attempt,long now,String phase,String version,int build){
        ReadinessImportResult.Code code=ReadinessImportResult.Code.PERSISTENCE_FAILED;JsonObject material=null;
        try{
            JsonObject value=state();code=ReadinessImportResult.Code.MISSING;
            if(value.get("denied").getAsBoolean())code=ReadinessImportResult.Code.AUTHORIZATION_REJECTED;
            else if(!value.get("response").isJsonNull()){
                byte[] raw=bytes(value.get("response"));
                try{code=validation(raw,now);if(code==ReadinessImportResult.Code.READY){
                    byte[] usable=usable();if(usable==null)code=ReadinessImportResult.Code.ORCHESTRATOR_NOT_USABLE;
                    else {try{if(!java.util.Arrays.equals(raw,usable))code=ReadinessImportResult.Code.ORCHESTRATOR_NOT_USABLE;else material=value.getAsJsonObject("response");}finally{java.util.Arrays.fill(usable,(byte)0);}}
                }}finally{java.util.Arrays.fill(raw,(byte)0);}
            }
        }catch(Exception | LinkageError failure){code=ReadinessImportResult.Code.PERSISTENCE_FAILED;material=null;}
        return new ReadinessImportResult(attempt,code,material,now,phase,version,build);
    }
    private ReadinessImportResult.Code validation(byte[] raw,long now)throws Exception{
        require(raw.length>0&&raw.length<=65536);
        if(integer(parse(raw).getAsJsonObject().get("expires_at"),1)<=now)return ReadinessImportResult.Code.EXPIRED_ON_IMPORT;
        return detailed.validate(raw);
    }
    boolean attempt(long now)throws Exception{
        JsonObject value=state();if(integer(value.get("next_attempt"),0)>now)return false;
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
    void importProduct(byte[] raw,OwnerPrewarmReceipt attempt,long now)throws Exception{
        ReadinessImportResult.Code code;
        try{code=validation(raw,now);}catch(Exception | LinkageError failure){throw new ImportFailure(ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED);}
        if(code!=ReadinessImportResult.Code.READY)throw new ImportFailure(code);
        Storage transaction=new Storage(){
            public byte[] read()throws Exception{return storage.read();}
            public void write(byte[] next)throws Exception{
                JsonObject value=parse(next).getAsJsonObject(),context=new JsonObject();
                context.addProperty("challenge_id",attempt.challengeId);context.addProperty("fetch_id",attempt.fetchId);value.add("receipt_context",context);
                byte[] encoded=bytes(value);
                try{storage.write(encoded);}catch(PersistenceFailure failure){throw new ImportFailure(ReadinessImportResult.Code.PERSISTENCE_FAILED);}
                catch(Exception failure){throw new ImportFailure(ReadinessImportResult.Code.ATOMIC_IMPORT_FAILED);}
                byte[] persisted;
                try{persisted=storage.read();}catch(Exception failure){throw new ImportFailure(ReadinessImportResult.Code.PERSISTENCE_FAILED);}
                try{if(!java.util.Arrays.equals(encoded,persisted))throw new ImportFailure(ReadinessImportResult.Code.PERSISTENCE_FAILED);}
                finally{if(persisted!=null)java.util.Arrays.fill(persisted,(byte)0);java.util.Arrays.fill(encoded,(byte)0);}
            }
        };
        try{new RestrictedCache(transaction,validator).accept(raw);}
        catch(ImportFailure failure){throw failure;}
        catch(IllegalArgumentException failure){throw new ImportFailure(ReadinessImportResult.Code.STALE_STATE);}
        catch(Exception failure){throw new ImportFailure(ReadinessImportResult.Code.PERSISTENCE_FAILED);}
    }
    private static JsonObject issuer(JsonObject value)throws Exception{return parse(Base64.getDecoder().decode(text(value.getAsJsonObject("issuer").get("payload")))).getAsJsonObject();}
    String summary() {
        try {JsonObject value=state();if(value.get("denied").getAsBoolean())return "NOT READY — authorization rejected";
            if(value.get("response").isJsonNull())return "NOT READY — provisioning missing";
            return usable()!=null?"READY — provisioning PRESENT_VALID; BOOT-1 PRESENT_VALID; usable YES":"NOT READY — expired or invalid material";
        }catch(Exception | LinkageError failure){return "NOT READY — secure state unavailable";}
    }
}
