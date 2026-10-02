package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import static com.familyconnect.app.ControlJson.*;

final class FriendsReadinessProtocol {
    interface Transport { JsonObject post(String path,JsonObject body,String requestId)throws Exception; }
    static byte[] fetch(Transport transport,ControlIdentity identity,OwnerPrewarmReceipt receipt)throws Exception{
        JsonObject request=new JsonObject();request.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));request.addProperty("wireguard_public_key",identity.wireguardPublicKey());
        JsonObject challenge=transport.post("/friends/restricted-readiness/challenge",request,receipt.challengeId);fields(challenge,"challenge expires_at audience");
        long now=System.currentTimeMillis()/1000,expiry=integer(challenge.get("expires_at"),1);
        require(expiry>now&&expiry-now<=120&&text(challenge.get("audience")).equals("family-connect/enrollment/v1"));
        String nonce=text(challenge.get("challenge"));
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
