package com.familyconnect.app;

import android.content.Context;
import com.google.gson.JsonObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.IOException;
import static com.familyconnect.app.ControlJson.*;

final class ProvisioningCarrier implements AutoCloseable {
    static boolean configured(Context context,String gateway){
        try(InputStream input=context.getAssets().open("provisioning/"+RestrictedGateway.target(gateway)+".json")){return true;}
        catch(IOException missing){return false;}
    }
    private final Context context;
    private final String gateway;
    private final long deadline;
    private long handle;
    private boolean closed;
    ProvisioningCarrier(Context context,String gateway,long deadline){this.context=context;this.gateway=RestrictedGateway.target(gateway);this.deadline=deadline;}
    private synchronized long acquire()throws Exception{
        if(closed||android.os.SystemClock.elapsedRealtime()>=deadline)throw new IOException("Provisioning cancelled");
        if(handle!=0)return handle;
        byte[] locator;
        try(InputStream input=context.getAssets().open("provisioning/"+gateway+".json");ByteArrayOutputStream output=new ByteArrayOutputStream()){
            byte[] buffer=new byte[2048];int count;
            while((count=input.read(buffer))!=-1){if(output.size()+count>16384)throw new SecurityException("Provisioning locator rejected");output.write(buffer,0,count);}
            locator=output.toByteArray();
        }
        NativeRestricted.load();
        ChatNetworkAndroid network=new ChatNetworkAndroid(context);
        handle=NativeRestricted.provisionBegin(locator,ControlTrust.anchor(context),gateway,network.provisioningResolver(),Math.min(30000,deadline-android.os.SystemClock.elapsedRealtime()),network);
        if(handle==0)throw new SecurityException("Provisioning locator rejected");
        return handle;
    }
    JsonObject post(String path,JsonObject body,String requestId)throws Exception{
        if(!path.equals("/friends/restricted-readiness/challenge")&&!path.equals("/friends/restricted-readiness"))throw new SecurityException("Provisioning operation rejected");
        JsonObject request=body;
        if(RestrictedGateway.PRIMARY.equals(gateway)){request=new JsonObject();request.addProperty("gateway_id",gateway);request.add("request",body);}
        long current=acquire();
        String raw=NativeRestricted.provisionPost(current,path,request.toString(),requestId);
        synchronized(this){if(closed||android.os.SystemClock.elapsedRealtime()>=deadline)throw new IOException("Provisioning cancelled");}
        if(raw==null)throw new IOException("Provisioning unavailable");
        JsonObject reply=parse(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();fields(reply,"status body");
        int status=(int)integer(reply.get("status"),0);
        if(status==0)throw new SecurityException("Provisioning authentication rejected");
        if(path.endsWith("/challenge"))FriendsReadinessProtocol.challengeStatus(status);
        if(status==401||status==403)throw new FriendsReadinessProtocol.AuthorizationFailure();
        if(status!=200)throw new IOException("Provisioning unavailable");
        JsonObject result=reply.getAsJsonObject("body");fields(result,"gateway_id response");require(gateway.equals(text(result.get("gateway_id"))));
        return RestrictedGateway.PRIMARY.equals(gateway)?result.getAsJsonObject("response"):result;
    }
    public synchronized void close(){closed=true;if(handle!=0){NativeRestricted.provisionClose(handle);handle=0;}}
}
