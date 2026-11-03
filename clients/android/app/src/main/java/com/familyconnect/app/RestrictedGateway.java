package com.familyconnect.app;

import com.google.gson.JsonObject;
import static com.familyconnect.app.ControlJson.*;

final class RestrictedGateway {
    static final String PRIMARY="nl-amsterdam-1";
    static final String SECONDARY="nl-amsterdam-2";

    private RestrictedGateway(){}

    static String target(String value){
        if(value==null||"nl".equals(value)||PRIMARY.equals(value))return PRIMARY;
        require(SECONDARY.equals(value));return SECONDARY;
    }

    static String namespace(String value){return PRIMARY.equals(target(value))?"":"-"+SECONDARY;}

    static FriendsReadinessProtocol.Transport route(FriendsReadinessProtocol.Transport transport,String value){
        String gateway=target(value);
        if(PRIMARY.equals(gateway))return transport;
        return (path,body,requestId)->{
            require(ReadinessBootstrapRoute.allowed(path));
            JsonObject request=new JsonObject();request.addProperty("gateway_id",gateway);request.add("request",body);
            JsonObject reply=transport.post(path,request,requestId);
            fields(reply,"gateway_id response");require(gateway.equals(text(reply.get("gateway_id"))));
            require(reply.get("response").isJsonObject());return reply.getAsJsonObject("response");
        };
    }
}
