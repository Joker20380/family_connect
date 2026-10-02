package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.util.UUID;
import static com.familyconnect.app.ControlJson.*;

final class OwnerPrewarmReceipt {
    final String challengeId=UUID.randomUUID().toString().replace("-","");
    final String fetchId=UUID.randomUUID().toString().replace("-","");
    private String challenge="not_attempted",fetch="not_attempted",imported="not_attempted";
    private long revision,expires,observed;
    synchronized void challengeIssued(){challenge="issued";observed=System.currentTimeMillis()/1000;}
    synchronized void fetchAuthorized(){fetch="authorized";observed=System.currentTimeMillis()/1000;}
    synchronized void imported(byte[] response)throws java.io.IOException{
        require(challenge.equals("issued")&&fetch.equals("authorized"));
        JsonObject value=parse(response).getAsJsonObject();
        long nextRevision=integer(value.get("revision"),1),nextExpiry=integer(value.get("expires_at"),1);
        require(nextRevision<=9007199254740991L&&nextExpiry<=9007199254740991L);
        revision=nextRevision;expires=nextExpiry;imported="accepted";observed=System.currentTimeMillis()/1000;
    }
    synchronized void failed(){
        if(!challenge.equals("issued"))challenge="failed";
        else if(!fetch.equals("authorized"))fetch="failed";
        else imported="failed";
        observed=System.currentTimeMillis()/1000;
    }
    synchronized String summary(){
        JsonObject value=new JsonObject();value.addProperty("receipt_class","real_owner_product");
        value.addProperty("challenge_id",challengeId);value.addProperty("fetch_id",fetchId);
        value.addProperty("challenge_result",challenge);value.addProperty("fetch_result",fetch);
        value.addProperty("import_result",imported);value.addProperty("revision",revision);
        value.addProperty("expires_at",expires);value.addProperty("observed_at",observed);
        return value.toString();
    }
}
