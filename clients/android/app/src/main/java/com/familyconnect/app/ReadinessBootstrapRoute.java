package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.io.IOException;
import javax.net.ssl.SSLException;

final class ReadinessBootstrapRoute {
    private final FriendsReadinessProtocol.Transport https;
    private final FriendsReadinessProtocol.Transport relay;
    private boolean relaySelected;

    ReadinessBootstrapRoute(FriendsReadinessProtocol.Transport https, FriendsReadinessProtocol.Transport relay) {
        this.https=https;this.relay=relay;
    }

    static boolean allowed(String path) {
        return path.equals("/friends/restricted-readiness") || path.equals("/friends/restricted-readiness/challenge")
            || path.equals("/friends/restricted-readiness/ack-challenge") || path.equals("/friends/restricted-readiness/ack");
    }

    JsonObject post(String path,JsonObject body,String requestId)throws Exception {
        if(!allowed(path))throw new IllegalArgumentException("Unsupported readiness path");
        if(relaySelected)return relay.post(path,body,requestId);
        try{return https.post(path,body,requestId);}
        catch(SSLException trustFailure){throw trustFailure;}
        catch(IOException unavailable){
            if(!path.endsWith("/challenge")&&!path.endsWith("/ack-challenge"))throw unavailable;
            relaySelected=true;
            return relay.post(path,body,requestId);
        }
    }
}
