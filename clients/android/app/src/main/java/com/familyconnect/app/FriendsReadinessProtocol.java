package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import static com.familyconnect.app.ControlJson.*;

final class FriendsReadinessProtocol {
    enum ChallengeCode { CHALLENGE_UNAUTHORIZED, CHALLENGE_TEMPORARY_SERVER_FAILURE, CHALLENGE_INCOMPATIBLE_RESPONSE, CHALLENGE_TIMEOUT, CHALLENGE_INTERNAL_ERROR }
    static final class ChallengeFailure extends IllegalArgumentException {
        final ChallengeCode code;
        ChallengeFailure(ChallengeCode code){super(code.name());this.code=code;}
    }
    static byte[] wireBytes(JsonObject body){return body.toString().getBytes(StandardCharsets.UTF_8);}
    static Map<String,String> wireHeaders(String requestId){
        Map<String,String> headers=new LinkedHashMap<>();headers.put("Content-Type","application/json");
        if(requestId!=null){require(requestId.matches("[a-f0-9]{32}"));headers.put("X-FC-Probe-ID",requestId);}
        return headers;
    }
    static void challengeStatus(int status){
        if(status==200)return;
        throw new ChallengeFailure(status==401||status==403?ChallengeCode.CHALLENGE_UNAUTHORIZED:
                status==429||status>=500&&status<=599?ChallengeCode.CHALLENGE_TEMPORARY_SERVER_FAILURE:ChallengeCode.CHALLENGE_INCOMPATIBLE_RESPONSE);
    }
    static String challengeResponse(JsonObject challenge,long now){
        try{
            fields(challenge,"challenge expires_at audience");long expiry=integer(challenge.get("expires_at"),1);
            require(expiry>now&&expiry-now<=120&&text(challenge.get("audience")).equals("family-connect/enrollment/v1"));
            String nonce=text(challenge.get("challenge"));require(ControlProtocol.base64(nonce,true).length==32);return nonce;
        }catch(Exception failure){throw new ChallengeFailure(ChallengeCode.CHALLENGE_INCOMPATIBLE_RESPONSE);}
    }
    interface Transport { JsonObject post(String path,JsonObject body,String requestId)throws Exception; }
    static byte[] fetch(Transport transport,ControlIdentity identity,OwnerPrewarmReceipt receipt)throws Exception{
        JsonObject request=new JsonObject();request.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));request.addProperty("wireguard_public_key",identity.wireguardPublicKey());
        String nonce;
        try{nonce=challengeResponse(transport.post("/friends/restricted-readiness/challenge",request,receipt.challengeId),System.currentTimeMillis()/1000);}
        catch(ChallengeFailure failure){throw failure;}
        catch(java.net.SocketTimeoutException failure){throw new ChallengeFailure(ChallengeCode.CHALLENGE_TIMEOUT);}
        catch(java.io.IOException failure){throw new ChallengeFailure(ChallengeCode.CHALLENGE_TEMPORARY_SERVER_FAILURE);}
        catch(Exception failure){throw new ChallengeFailure(ChallengeCode.CHALLENGE_INTERNAL_ERROR);}
        receipt.challengeIssued();
        JsonObject response=transport.post("/friends/restricted-readiness",identity.proveTransportKey(nonce),receipt.fetchId);
        require(text(response.get("challenge")).equals(nonce)&&text(response.get("device")).equals(identity.reference()));
        receipt.fetchAuthorized();
        return response.toString().getBytes(StandardCharsets.UTF_8);
    }
    static void acknowledge(Transport transport,ControlIdentity identity,JsonObject receipt)throws Exception{
        ReadinessImportResult.validate(receipt);
        JsonObject request=new JsonObject();request.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));request.addProperty("wireguard_public_key",identity.wireguardPublicKey());request.add("receipt",receipt);
        JsonObject challenge=transport.post("/friends/restricted-readiness/ack-challenge",request,java.util.UUID.randomUUID().toString().replace("-",""));
        fields(challenge,"challenge expires_at audience");long now=System.currentTimeMillis()/1000,expiry=integer(challenge.get("expires_at"),1);
        require(expiry>now&&expiry-now<=120&&text(challenge.get("audience")).equals("family-connect/enrollment/v1"));
        JsonObject body=new JsonObject();body.add("receipt",receipt);body.add("proof",identity.proveTransportKey(text(challenge.get("challenge"))));
        JsonObject result=transport.post("/friends/restricted-readiness/ack",body,java.util.UUID.randomUUID().toString().replace("-",""));
        fields(result,"version correlation_id status");require(integer(result.get("version"),1)==1&&result.get("correlation_id").equals(receipt.get("correlation_id"))&&text(result.get("status")).equals("ACK_RECEIVED"));
    }
}
