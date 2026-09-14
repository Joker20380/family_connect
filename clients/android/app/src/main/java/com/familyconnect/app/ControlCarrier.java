package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.function.LongSupplier;
import static com.familyconnect.app.ControlJson.*;

/** RNS request protocol. Transport never receives device private keys. */
final class ControlCarrier implements ControlTransaction.Sender {
    interface Wire { byte[] request(String path,byte[] body)throws Exception; boolean cancelled(); }
    private final Wire wire;private final ControlIdentity identity;private final LongSupplier clock;
    ControlCarrier(Wire wire,ControlIdentity identity,LongSupplier clock){this.wire=wire;this.identity=identity;this.clock=clock;}
    private byte[] request(String path,byte[] body)throws Exception {
        if(wire.cancelled()||body.length>4096)throw new IOException("Carrier unavailable");
        byte[] result=wire.request(path,body.clone());
        if(wire.cancelled()||result==null||result.length==0||result.length>65536)throw new IOException("Invalid carrier reply");return result.clone();
    }
    byte[] receive()throws Exception {
        JsonObject keys=new JsonObject();keys.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));keys.addProperty("wireguard_public_key",identity.wireguardPublicKey());
        JsonObject reply=ControlJson.parse(request("/control/v1/challenge",ControlJson.canonical(keys,false))).getAsJsonObject();
        fields(reply,"challenge audience expires_at");require("family-connect/provisioning-fetch/v1".equals(text(reply.get("audience"))));
        long now=clock.getAsLong(),expires=integer(reply.get("expires_at"),1);require(now>=0&&expires>now&&expires-now<=120);
        JsonObject proof=identity.proveFetch(text(reply.get("challenge")));require(clock.getAsLong()<expires);
        return request("/control/v1/fetch",ControlJson.canonical(proof,false));
    }
    public boolean send(byte[] raw)throws Exception {
        JsonObject body=ControlProtocol.verifyAck(raw);require(text(body.get("device")).equals(identity.reference()));
        return java.util.Arrays.equals("ACK_STORED".getBytes(StandardCharsets.US_ASCII),request("/control/v1/ack",raw));
    }
}
