package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.net.HttpURLConnection;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import org.junit.Test;
import static org.junit.Assert.*;

public class FriendsReadinessGoldenTest {
    static final String RESOURCE="friends-readiness-challenge.json";
    static JsonObject wire()throws Exception{
        JsonObject result=new JsonObject();
        try(ControlIdentity identity=ControlIdentity.restore(new byte[96])){
            try{FriendsReadinessProtocol.fetch((path,body,id)->{
                result.addProperty("method","POST");result.addProperty("path",path);
                JsonObject headers=new JsonObject();
                for(Map.Entry<String,String> header:FriendsReadinessProtocol.wireHeaders(id).entrySet())headers.addProperty(header.getKey(),header.getValue());
                result.add("headers",headers);result.addProperty("body",new String(FriendsReadinessProtocol.wireBytes(body),StandardCharsets.UTF_8));
                throw new FriendsReadinessProtocol.ChallengeFailure(FriendsReadinessProtocol.ChallengeCode.CHALLENGE_INTERNAL_ERROR);
            },identity,new OwnerPrewarmReceipt("a".repeat(32),"b".repeat(32)));fail();}
            catch(FriendsReadinessProtocol.ChallengeFailure expected){assertEquals(FriendsReadinessProtocol.ChallengeCode.CHALLENGE_INTERNAL_ERROR,expected.code);}
        }
        return result;
    }
    @Test public void exactAndroidWireMatchesGolden()throws Exception{
        try(java.io.InputStream input=getClass().getResourceAsStream("/"+RESOURCE)){
            assertNotNull(input);assertEquals(ControlJson.parse(input.readAllBytes()),wire());
        }
    }
    @Test public void statusAndTransportFailuresNeverFetchOrBecomeReady()throws Exception{
        int[] statuses={401,403,429,500,503,400,404};
        for(int status:statuses){
            try{FriendsReadinessProtocol.challengeStatus(status);fail();}
            catch(FriendsReadinessProtocol.ChallengeFailure failure){assertEquals(status==401||status==403?"CHALLENGE_UNAUTHORIZED":status==429||status>=500?"CHALLENGE_TEMPORARY_SERVER_FAILURE":"CHALLENGE_INCOMPATIBLE_RESPONSE",failure.code.name());}
        }
        Exception[] failures={new java.net.SocketTimeoutException("secret"),new java.io.IOException("secret"),new IllegalStateException("secret")};
        String[] codes={"CHALLENGE_TIMEOUT","CHALLENGE_TEMPORARY_SERVER_FAILURE","CHALLENGE_INTERNAL_ERROR"};
        for(int index=0;index<failures.length;index++){
            final Exception failure=failures[index];OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
            try(ControlIdentity identity=ControlIdentity.restore(new byte[96])){
                try{FriendsReadinessProtocol.fetch((path,body,id)->{assertTrue(path.endsWith("/challenge"));throw failure;},identity,receipt);fail();}
                catch(FriendsReadinessProtocol.ChallengeFailure result){assertEquals(codes[index],result.code.name());assertFalse(result.getMessage().contains("secret"));receipt.failed();}
                assertFalse(receipt.summary().contains("authorized"));assertFalse(receipt.summary().contains("accepted"));
            }
        }
    }
    @Test public void malformedResponseIsIncompatible(){
        for(String raw:new String[]{"{}","{\"challenge\":null}","{\"challenge\":\"bad\",\"expires_at\":999,\"audience\":\"family-connect/enrollment/v1\"}"}){
            try{FriendsReadinessProtocol.challengeResponse(ControlJson.parse(raw.getBytes(StandardCharsets.UTF_8)).getAsJsonObject(),900);fail();}
            catch(FriendsReadinessProtocol.ChallengeFailure failure){assertEquals("CHALLENGE_INCOMPATIBLE_RESPONSE",failure.code.name());}
            catch(Exception failure){throw new AssertionError(failure);}
        }
    }
    public static void main(String[] args)throws Exception{
        if(args[0].equals("emit")){Files.write(Path.of(args[1]),(wire().toString()+"\n").getBytes(StandardCharsets.UTF_8));return;}
        URI origin=URI.create(args[1]);assertEquals("http",origin.getScheme());assertEquals("127.0.0.1",origin.getHost());
        try(ControlIdentity identity=ControlIdentity.restore(new byte[96])){
            OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt("c".repeat(32),"d".repeat(32));
            byte[] result=FriendsReadinessProtocol.fetch((path,body,id)->{
                HttpURLConnection connection=(HttpURLConnection)origin.resolve(path).toURL().openConnection();
                try{
                    connection.setRequestMethod("POST");connection.setDoOutput(true);connection.setConnectTimeout(3000);connection.setReadTimeout(3000);
                    for(Map.Entry<String,String> header:FriendsReadinessProtocol.wireHeaders(id).entrySet())connection.setRequestProperty(header.getKey(),header.getValue());
                    byte[] raw=FriendsReadinessProtocol.wireBytes(body);connection.setFixedLengthStreamingMode(raw.length);
                    try(java.io.OutputStream output=connection.getOutputStream()){output.write(raw);}
                    int status=connection.getResponseCode();FriendsReadinessProtocol.challengeStatus(status);
                    try(java.io.InputStream input=connection.getInputStream()){return ControlJson.parse(input.readAllBytes()).getAsJsonObject();}
                }finally{connection.disconnect();}
            },identity,receipt);
            assertEquals(1,ControlJson.parse(result).getAsJsonObject().get("version").getAsInt());
            assertTrue(receipt.summary().contains("authorized"));assertFalse(receipt.summary().contains("accepted"));
            System.out.println("ANDROID_PYTHON_ROUNDTRIP_PASS");
        }
    }
}
