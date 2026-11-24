package com.familyconnect.app;

import com.google.gson.*;
import java.util.Base64;

public final class NativeRestricted {
    static native long provisionBegin(byte[] locator,byte[] anchor,String gateway,String resolver,long budget,Object owner,String[] diagnostic);
    static native String provisionPost(long handle,String path,String body,String id,String[] diagnostic);
    static native String provisionClose(long handle);
    static native String fixture();
    static native void waitPost();
    public boolean protect(int fd){return false;}
    public static final class ThrowingOwner {public boolean protect(int fd){throw new IllegalStateException("sensitive callback detail must not escape");}}
    static void require(boolean value){if(!value)throw new AssertionError("JNI diagnostic mismatch");}
    static JsonObject result(String[] raw){require(raw[0]!=null);return JsonParser.parseString(raw[0]).getAsJsonObject();}
    public static void main(String[] arguments)throws Exception{
        System.load(arguments[0]);
        String[] diagnostic=new String[1];
        require(provisionBegin(null,null,null,null,0,null,diagnostic)==0);
        require(!result(diagnostic).get("go_entered").getAsBoolean());
        System.out.println("JNI_ARGUMENTS "+diagnostic[0]);
        require(provisionBegin(new byte[0],new byte[32],"nl-amsterdam-1","127.0.0.1:53",3000,new NativeRestricted(),diagnostic)==0);
        require(result(diagnostic).get("first_failure").getAsString().equals("LOCATOR"));
        System.out.println("LOCATOR "+diagnostic[0]);
        JsonObject fixture=JsonParser.parseString(fixture()).getAsJsonObject();
        byte[] locator=Base64.getDecoder().decode(fixture.get("locator").getAsString()),anchor=Base64.getDecoder().decode(fixture.get("anchor").getAsString());
        for(Object owner:new Object[]{new Object(),new ThrowingOwner()}){
            long handle=provisionBegin(locator,anchor,"nl-amsterdam-1","127.0.0.2:53",3000,owner,diagnostic);
            require(handle>0);
            require(provisionPost(handle,"/friends/restricted-readiness/challenge","{}","11111111111111111111111111111111",diagnostic)==null);waitPost();
            String expected=owner instanceof ThrowingOwner?"JNI_CALLBACK_EXCEPTION":"JNI_CALLBACK_MISSING";
            require(result(diagnostic).get("reason").getAsString().equals(expected));
            require(!diagnostic[0].contains("sensitive"));System.out.println(expected+" "+diagnostic[0]);
            provisionClose(handle);
        }
        for(int scenario=2;scenario<=6;scenario++){
            long handle=provisionBegin(locator,anchor,"nl-amsterdam-1","127.0.0."+scenario+":53",3000,new NativeRestricted(),diagnostic);
            require(handle>0);
            String[] captured=new String[1];
            Thread post=new Thread(()->require(provisionPost(handle,"/friends/restricted-readiness/challenge","{}","11111111111111111111111111111111",captured)==null));
            post.setUncaughtExceptionHandler((thread,failure)->{failure.printStackTrace();System.exit(2);});
            post.start();waitPost();
            if(scenario==6)provisionClose(handle);
            post.join(5000);require(!post.isAlive());
            JsonObject snapshot=result(captured);
            System.out.println("CASE_"+scenario+" "+captured[0]);
            String expected=scenario==2?"SOCKET_DENIED":scenario==4?"TLS_TRUST":"EOF";
            require(snapshot.get("handle").getAsLong()==handle);
            require(snapshot.get("reason").getAsString().equals(expected));
            if(scenario==4)require(snapshot.get("security").getAsBoolean());
            if(scenario==5)require(snapshot.get("last_success").getAsString().equals("REQUEST_WRITE"));
            provisionClose(handle);
            require(result(captured).equals(snapshot));
        }
        System.out.println("JNI_DIAGNOSTICS_PASS");
    }
}
