package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.io.IOException;
import org.junit.Test;
import static org.junit.Assert.*;

public class SubscriptionRequestTest {
    private static final String DEVICE="ab".repeat(16);
    static final class Exchange implements SubscriptionRequest.Exchange {
        boolean legacy,denyIdentity,denyStatus,unavailable,denyEndpoint;
        int calls;
        String registrationDevice=DEVICE;
        boolean active=true;
        final JsonObject response=new JsonObject();
        public String device(){return DEVICE;}
        public JsonObject proof(String purpose)throws Exception{
            calls++;
            if(unavailable)throw new IOException();
            if(denyIdentity||legacy&&purpose.equals("subscription")||denyStatus&&purpose.equals("status"))throw new SubscriptionRequest.IdentityRejected();
            JsonObject proof=new JsonObject();proof.addProperty("purpose",purpose);return proof;
        }
        public JsonObject post(String path,JsonObject proof)throws Exception{
            calls++;
            if(path.equals("/friends/device/status")){
                assertEquals("status",proof.get("purpose").getAsString());
                JsonObject status=new JsonObject();status.addProperty("device",registrationDevice);
                status.addProperty("registered",true);status.addProperty("revoked",!active);status.addProperty("active",active);return status;
            }
            assertEquals(SubscriptionRequest.PATH,path);assertEquals("subscription",proof.get("purpose").getAsString());
            if(denyEndpoint)throw new SubscriptionRequest.IdentityRejected();
            return response;
        }
    }

    @Test public void supportedOperationUsesOnlyOneFreshPurposeAndRequest()throws Exception{
        Exchange exchange=new Exchange();
        assertSame(exchange.response,SubscriptionRequest.fetch(exchange));assertEquals(2,exchange.calls);
    }
    @Test public void legacyPurposeRejectionNeedsVerifiedRegistrationBeforeUnsupported()throws Exception{
        Exchange exchange=new Exchange();exchange.legacy=true;
        assertThrows(SubscriptionRequest.Unsupported.class,()->SubscriptionRequest.fetch(exchange));assertEquals(3,exchange.calls);
    }
    @Test public void rejectedRegistrationIsNeverUnsupported(){
        Exchange exchange=new Exchange();exchange.legacy=true;exchange.active=false;
        assertThrows(SubscriptionRequest.IdentityRejected.class,()->SubscriptionRequest.fetch(exchange));
        exchange.denyStatus=true;
        assertThrows(SubscriptionRequest.IdentityRejected.class,()->SubscriptionRequest.fetch(exchange));
    }
    @Test public void fallbackCannotUseAnotherIdentity(){
        Exchange exchange=new Exchange();exchange.legacy=true;exchange.registrationDevice="cd".repeat(16);
        assertThrows(SubscriptionRequest.InvalidResponse.class,()->SubscriptionRequest.fetch(exchange));
    }
    @Test public void temporaryFailureHasNoRetryOrRegistrationFallback(){
        Exchange exchange=new Exchange();exchange.unavailable=true;
        assertThrows(IOException.class,()->SubscriptionRequest.fetch(exchange));assertEquals(1,exchange.calls);
    }
    @Test public void endpointRejectionDoesNotFallback(){
        Exchange exchange=new Exchange();exchange.denyEndpoint=true;
        assertThrows(SubscriptionRequest.IdentityRejected.class,()->SubscriptionRequest.fetch(exchange));assertEquals(2,exchange.calls);
    }
    @Test public void onlyAbsentSubscriptionRouteIsUnsupported()throws Exception{
        for(int status:new int[]{404,405,501})assertThrows(SubscriptionRequest.Unsupported.class,()->SubscriptionRequest.status(SubscriptionRequest.PATH,status));
        for(int status:new int[]{200,400,401,403,429,500,503})SubscriptionRequest.status(SubscriptionRequest.PATH,status);
        SubscriptionRequest.status("/friends/device/status",404);
    }
}
