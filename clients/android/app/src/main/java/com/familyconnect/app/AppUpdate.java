package com.familyconnect.app;

import com.google.gson.*;
import java.io.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import javax.net.ssl.HttpsURLConnection;

/** HTTPS discovery; APK signing identity is independently checked before installation. */
final class AppUpdate {
    static final String BASE="https://185.251.89.19:8443";
    static final String INDEX=BASE+"/updates/android-friends.json";
    final int code;final String version,sha256,url;final long size;
    private AppUpdate(int code,String version,String sha256,String url,long size){this.code=code;this.version=version;this.sha256=sha256;this.url=url;this.size=size;}
    static AppUpdate parse(byte[] bytes){
        if(bytes.length==0||bytes.length>8192)throw new IllegalArgumentException();
        JsonObject o=JsonParser.parseString(new String(bytes,StandardCharsets.UTF_8)).getAsJsonObject();
        if(number(o,"schema")!=1||!text(o,"package").equals("com.familyconnect.app.friends")||!text(o,"abi").equals("arm64-v8a"))throw new IllegalArgumentException();
        long code=number(o,"version_code"),size=number(o,"size");String version=text(o,"version"),hash=text(o,"sha256"),url=text(o,"url");
        if(code<1||code>Integer.MAX_VALUE||size<1024||size>150_000_000||!version.matches("[0-9]+\\.[0-9]+\\.[0-9]+-beta[0-9]+")||!hash.matches("[0-9a-f]{64}")||!url.equals(BASE+"/downloads/FamilyConnect-Test-"+version+".apk"))throw new IllegalArgumentException();
        return new AppUpdate((int)code,version,hash,url,size);
    }
    private static long number(JsonObject o,String k){JsonPrimitive p=o.getAsJsonPrimitive(k);if(!p.isNumber()||!p.getAsString().matches("[0-9]{1,12}"))throw new IllegalArgumentException();return p.getAsLong();}
    private static String text(JsonObject o,String k){JsonPrimitive p=o.getAsJsonPrimitive(k);if(!p.isString())throw new IllegalArgumentException();return p.getAsString();}
    static HttpsURLConnection open(String url)throws IOException{
        HttpsURLConnection c=(HttpsURLConnection)new URL(url).openConnection();c.setConnectTimeout(10000);c.setReadTimeout(10000);c.setInstanceFollowRedirects(false);c.setUseCaches(false);
        if(c.getResponseCode()!=200){c.disconnect();throw new IOException("HTTP response");}return c;
    }
    static AppUpdate check()throws IOException{
        HttpsURLConnection c=open(INDEX);
        try(InputStream in=c.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[2048];int n;while((n=in.read(b))!=-1){if(out.size()+n>8192)throw new IOException("Oversized manifest");out.write(b,0,n);}return parse(out.toByteArray());
        }finally{c.disconnect();}
    }
    interface Progress { void update(int percent)throws IOException; }
    static String hex(byte[] bytes){StringBuilder s=new StringBuilder();for(byte b:bytes)s.append(String.format(java.util.Locale.ROOT,"%02x",b&255));return s.toString();}
    void receive(InputStream in,OutputStream out,Progress progress)throws Exception{
        MessageDigest hash=MessageDigest.getInstance("SHA-256");byte[] buffer=new byte[65536];long total=0;int n,last=-1;
        while((n=in.read(buffer))!=-1){if(Thread.currentThread().isInterrupted())throw new InterruptedIOException();total+=n;if(total>size)throw new IOException("Oversized APK");out.write(buffer,0,n);hash.update(buffer,0,n);int p=(int)(total*100/size);if(p!=last){progress.update(p);last=p;}}
        if(total!=size||!hex(hash.digest()).equals(sha256))throw new IOException("APK checksum");
    }
}
