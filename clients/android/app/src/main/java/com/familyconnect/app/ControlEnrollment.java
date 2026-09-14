package com.familyconnect.app;

import com.google.gson.*;
import java.io.IOException;
import java.net.URI;
import java.util.Base64;
import java.util.function.LongSupplier;
import static com.familyconnect.app.ControlJson.*;

/** Explicit enrollment. Durable completion intent prevents accidental identity rotation/re-enrollment. */
final class ControlEnrollment {
    interface Local {
        boolean present() throws Exception;
        boolean otherState() throws Exception;
        JsonObject read() throws Exception;
        void create(JsonObject record) throws Exception;
        void save(JsonObject record) throws Exception;
        ControlIdentity prepare(boolean initializing) throws Exception; // Load/create identity and empty journal, never reset.
    }
    interface Remote {
        JsonObject post(String origin,String path,JsonObject body) throws Exception;
        boolean cancelled();
    }
    private final Local local;private final Remote remote;private final LongSupplier clock;
    ControlEnrollment(Local local,Remote remote,LongSupplier clock){this.local=local;this.remote=remote;this.clock=clock;}
    static String origin(String input)throws Exception {
        if(input==null||input.length()>2048)throw new IOException("Invalid enrollment server");
        URI uri=new URI(input);
        if(!"https".equals(uri.getScheme())||uri.getHost()==null||uri.getRawUserInfo()!=null||uri.getRawQuery()!=null||uri.getRawFragment()!=null
            ||!(uri.getRawPath().isEmpty()||uri.getRawPath().equals("/"))||uri.getPort()==0||uri.getPort()>65535)
            throw new IOException("HTTPS server origin required");
        return new URI("https",null,uri.getHost().toLowerCase(java.util.Locale.ROOT),uri.getPort()==443?-1:uri.getPort(),null,null,null).toASCIIString();
    }
    private void active()throws IOException{if(remote.cancelled()||Thread.currentThread().isInterrupted())throw new IOException("Enrollment cancelled");}
    private JsonObject keys(ControlIdentity identity){JsonObject body=new JsonObject();body.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));body.addProperty("wireguard_public_key",identity.wireguardPublicKey());return body;}
    private String challenge(JsonObject value,String audience)throws Exception {
        fields(value,"challenge expires_at audience");require(text(value.get("audience")).equals(audience));
        String nonce=text(value.get("challenge"));require(ControlProtocol.base64(nonce,true).length==32);
        long now=clock.getAsLong(),expiry=integer(value.get("expires_at"),1);require(now>=0&&expiry>now&&expiry-now<=120);return nonce;
    }
    private void receipt(JsonObject response,String device) {
        fields(response,"device_identity entitlement_id entitlement_revision status");
        require(text(response.get("device_identity")).equals(device)&&text(response.get("status")).equals("enrolled"));
        require(text(response.get("entitlement_id")).matches("[0-9a-f]{32}"));integer(response.get("entitlement_revision"),1);
    }
    String enroll(String input,String invitation)throws Exception {
        String server=origin(input);Object owner=new Object();ControlOperations.APP.claim(owner);
        try {
            active();JsonObject record;
            if(!local.present()) {
                if(local.otherState())throw new IOException("Existing control state requires recovery");
                require(invitation!=null&&invitation.matches("[0-9a-f]{64}"));
                record=new JsonObject();record.addProperty("schema",1);record.addProperty("origin",server);record.addProperty("phase","INITIALIZING");
                record.add("device",JsonNull.INSTANCE);record.add("proof",JsonNull.INSTANCE);local.create(record);
            } else record=local.read();
            fields(record,"schema origin phase device proof");require(integer(record.get("schema"),1)==1);
            require(server.equals(text(record.get("origin"))));String phase=text(record.get("phase"));
            require(java.util.Arrays.asList("INITIALIZING","READY","COMPLETING","ENROLLED").contains(phase));
            require(phase.equals("COMPLETING")?record.get("proof").isJsonObject():record.get("proof").isJsonNull());
            if(phase.equals("INITIALIZING"))require(record.get("device").isJsonNull());else require(text(record.get("device")).matches("[0-9a-f]{32}"));
            try(ControlIdentity identity=local.prepare(phase.equals("INITIALIZING"))) {
                active();String device=identity.reference();
                if(phase.equals("INITIALIZING")){record.addProperty("device",device);record.addProperty("phase","READY");local.save(record);phase="READY";}
                require(device.equals(text(record.get("device"))));
                if(phase.equals("ENROLLED"))return device;
                if(phase.equals("COMPLETING")) {
                    // A lost reply is not permission to spend another invitation or create another identity.
                    JsonObject proof=record.getAsJsonObject("proof");
                    require(identity.proveTransportKey(text(proof.get("challenge"))).equals(proof));
                    JsonObject response=null;
                    // Retry only the exact persisted proof. Server single-use checks prevent a second enrollment.
                    try{response=remote.post(server,"/v2/registration/complete",proof);}
                    catch(IOException unavailable){active();}
                    if(response!=null)receipt(response,device);
                    else challenge(remote.post(server,"/v2/provisioning/challenge",keys(identity)),"family-connect/provisioning-fetch/v1");
                } else {
                    require(invitation!=null&&invitation.matches("[0-9a-f]{64}"));
                    JsonObject request=keys(identity);request.addProperty("invitation_token",invitation);
                    JsonObject reply=remote.post(server,"/v2/registration/challenge",request);active();
                    String nonce=challenge(reply,"family-connect/enrollment/v1");
                    JsonObject proof=identity.proveTransportKey(nonce);record.add("proof",proof);record.addProperty("phase","COMPLETING");local.save(record);
                    active();require(integer(reply.get("expires_at"),1)>clock.getAsLong());
                    JsonObject response=remote.post(server,"/v2/registration/complete",proof);
                    receipt(response,device);
                }
                active();record.addProperty("phase","ENROLLED");record.add("proof",JsonNull.INSTANCE);local.save(record);return device;
            }
        } finally {ControlOperations.APP.release(owner);}
    }
}
