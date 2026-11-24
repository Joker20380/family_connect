package com.familyconnect.app;

import com.google.gson.JsonObject;
import static com.familyconnect.app.ControlJson.*;

final class SubscriptionRequest {
    static final String PATH="/friends/device/subscription";
    static final class Unsupported extends Exception {}
    static final class IdentityRejected extends Exception {}
    static final class InvalidResponse extends Exception {}
    interface Exchange {
        JsonObject proof(String purpose)throws Exception;
        JsonObject post(String path,JsonObject proof)throws Exception;
        String device();
    }

    static void status(String path,int status)throws Unsupported {
        if(path.equals(PATH)&&(status==404||status==405||status==501))throw new Unsupported();
    }

    static JsonObject fetch(Exchange exchange)throws Exception {
        JsonObject proof;
        try{proof=exchange.proof("subscription");}
        catch(IdentityRejected rejected){
            JsonObject registration=exchange.post("/friends/device/status",exchange.proof("status"));
            try{
                fields(registration,"device registered revoked active");
                require(text(registration.get("device")).equals(exchange.device()));
                for(String name:new String[]{"registered","revoked","active"})require(registration.get(name).isJsonPrimitive()&&registration.get(name).getAsJsonPrimitive().isBoolean());
            }catch(IllegalArgumentException invalid){throw new InvalidResponse();}
            if(registration.get("registered").getAsBoolean()&&!registration.get("revoked").getAsBoolean()&&registration.get("active").getAsBoolean())throw new Unsupported();
            throw new IdentityRejected();
        }
        return exchange.post(PATH,proof);
    }
}
