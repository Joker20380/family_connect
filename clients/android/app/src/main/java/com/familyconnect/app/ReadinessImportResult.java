package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import static com.familyconnect.app.ControlJson.*;

final class ReadinessImportResult {
    enum Code { READY, NATIVE_VALIDATION_FAILED, BOOTSTRAP_VALIDATION_FAILED, ATOMIC_IMPORT_FAILED,
        PERSISTENCE_FAILED, EXPIRED_ON_IMPORT, ORCHESTRATOR_NOT_USABLE, INTERNAL_ERROR,
        STALE_STATE, AUTHORIZATION_REJECTED, FETCH_FAILED, MISSING }
    static final String FIELDS="version type correlation_id challenge_id fetch_id result provisioning bootstrap orchestrator_usable revision minimum_crl expires_at observed_at phase app_version version_code failure_reason";
    private final JsonObject value;
    ReadinessImportResult(OwnerPrewarmReceipt attempt,Code code,JsonObject material,long now,String phase,String version,int build){
        require(phase.equals("import")||phase.equals("restart"));
        require(version.matches("[A-Za-z0-9._-]{1,64}")&&build>0);
        value=new JsonObject();value.addProperty("version",1);value.addProperty("type","READINESS_IMPORT_RESULT");
        value.addProperty("correlation_id",attempt.challengeId);value.addProperty("challenge_id",attempt.challengeId);value.addProperty("fetch_id",attempt.fetchId);
        value.addProperty("result",code.name());value.addProperty("provisioning",code==Code.READY?"PRESENT_VALID":"NOT_READY");
        value.addProperty("bootstrap",code==Code.READY?"PRESENT_VALID":"NOT_READY");value.addProperty("orchestrator_usable",code==Code.READY);
        for(String field:new String[]{"revision","minimum_crl","expires_at"})value.addProperty(field,material==null?0:integer(material.get(field),1));
        value.addProperty("observed_at",now);value.addProperty("phase",phase);value.addProperty("app_version",version);value.addProperty("version_code",build);
        value.addProperty("failure_reason",code==Code.READY?"NONE":code.name());
        validate(value);
    }
    static void validate(JsonObject value){
        fields(value,FIELDS);require(integer(value.get("version"),1)==1&&text(value.get("type")).equals("READINESS_IMPORT_RESULT"));
        for(String field:new String[]{"correlation_id","challenge_id","fetch_id"})require(text(value.get(field)).matches("[a-f0-9]{32}"));
        require(value.get("correlation_id").equals(value.get("challenge_id"))&&!value.get("challenge_id").equals(value.get("fetch_id")));
        Code code=Code.valueOf(text(value.get("result")));boolean ready=code==Code.READY;
        require(value.get("orchestrator_usable").isJsonPrimitive()&&value.get("orchestrator_usable").getAsJsonPrimitive().isBoolean()&&value.get("orchestrator_usable").getAsBoolean()==ready);
        for(String field:new String[]{"provisioning","bootstrap"})require(text(value.get(field)).equals(ready?"PRESENT_VALID":"NOT_READY"));
        require(text(value.get("failure_reason")).equals(ready?"NONE":code.name()));
        for(String field:new String[]{"revision","minimum_crl","expires_at"})require(integer(value.get(field),ready?1:0)<=9007199254740991L);
        for(String field:new String[]{"observed_at","version_code"})require(integer(value.get(field),1)<=9007199254740991L);
        require(text(value.get("app_version")).matches("[A-Za-z0-9._-]{1,64}"));
        require(text(value.get("phase")).matches("import|restart"));
        if(ready)require(integer(value.get("expires_at"),1)>integer(value.get("observed_at"),1));
    }
    JsonObject json(){return value.deepCopy();}
    byte[] bytes(){return value.toString().getBytes(StandardCharsets.UTF_8);}
    Code code(){return Code.valueOf(text(value.get("result")));}
}
