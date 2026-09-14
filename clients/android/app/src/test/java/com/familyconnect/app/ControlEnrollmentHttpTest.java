package com.familyconnect.app;

import java.io.*;
import java.net.*;
import java.security.cert.Certificate;
import javax.net.ssl.HttpsURLConnection;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.junit.Assert.*;

/** Exercises HTTP policy with a fake connection, not TLS/Android network acceptance. */
public class ControlEnrollmentHttpTest {
    static Stub next;
    static class Stub extends HttpsURLConnection {
        int status=200;String type="application/json";byte[] response="{\"ok\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8);boolean disconnected;
        ByteArrayOutputStream sent=new ByteArrayOutputStream();
        Stub()throws Exception{super(new URL("https://enroll.example"));}
        public void connect(){}public void disconnect(){disconnected=true;}public boolean usingProxy(){return false;}
        public String getCipherSuite(){return "test";}public Certificate[] getLocalCertificates(){return null;}public Certificate[] getServerCertificates(){return null;}
        public OutputStream getOutputStream(){return sent;}public int getResponseCode(){return status;}public String getContentType(){return type;}
        public InputStream getInputStream(){return new ByteArrayInputStream(response);}
    }
    @BeforeClass public static void install(){URL.setURLStreamHandlerFactory(protocol->protocol.equals("https")?new URLStreamHandler(){
        protected URLConnection openConnection(URL url){return next;}
    }:null);}
    @Test public void postHasFixedPolicyAndClosesConnection()throws Exception {
        next=new Stub();try(var http=new ControlEnrollmentHttp()){
            var body=new com.google.gson.JsonObject();body.addProperty("test","public");
            assertTrue(http.post("https://enroll.example","/v2/registration/challenge",body).get("ok").getAsBoolean());
            assertFalse(next.getInstanceFollowRedirects());assertFalse(next.getUseCaches());assertEquals("POST",next.getRequestMethod());
            assertEquals(5000,next.getReadTimeout());assertEquals(5000,next.getConnectTimeout());assertTrue(next.disconnected);
            assertEquals(body.toString(),next.sent.toString("UTF-8"));
        }
    }
    @Test public void redirectAndWrongTypeAreRejected()throws Exception {
        for(int scenario=0;scenario<2;scenario++){
            next=new Stub();if(scenario==0)next.status=307;else next.type="text/html";
            try(var http=new ControlEnrollmentHttp()){assertThrows(IOException.class,()->http.post("https://enroll.example","/v2/registration/complete",new com.google.gson.JsonObject()));assertTrue(next.disconnected);}
        }
    }
    @Test public void oversizedAndDuplicateJsonResponsesAreRejected()throws Exception {
        for(byte[] body:new byte[][]{new byte[8193],"{\"ok\":true,\"ok\":false}".getBytes(java.nio.charset.StandardCharsets.UTF_8)}){
            next=new Stub();next.response=body;
            try(var http=new ControlEnrollmentHttp()){assertThrows(Exception.class,()->http.post("https://enroll.example","/v2/provisioning/challenge",new com.google.gson.JsonObject()));assertTrue(next.disconnected);}
        }
    }
    @Test public void cancellationAndUnknownPathNeverSend()throws Exception {
        next=new Stub();try(var http=new ControlEnrollmentHttp()){
            assertThrows(IOException.class,()->http.post("https://enroll.example","/admin",new com.google.gson.JsonObject()));
            http.close();assertThrows(IOException.class,()->http.post("https://enroll.example","/v2/registration/complete",new com.google.gson.JsonObject()));assertEquals(0,next.sent.size());
        }
    }
}
