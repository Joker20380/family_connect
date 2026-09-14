package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.io.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import javax.net.ssl.HttpsURLConnection;

/** System TLS verification, fixed API paths, no redirects, bounded responses and cooperative cancellation. */
final class ControlEnrollmentHttp implements ControlEnrollment.Remote,AutoCloseable {
    private volatile boolean cancelled;
    private volatile HttpsURLConnection connection;
    private final ScheduledExecutorService watchdog=Executors.newSingleThreadScheduledExecutor();
    public boolean cancelled(){return cancelled;}
    public void close(){cancelled=true;HttpsURLConnection c=connection;if(c!=null)c.disconnect();watchdog.shutdownNow();}
    public JsonObject post(String origin,String path,JsonObject body)throws Exception {
        if(!java.util.Arrays.asList("/v2/registration/challenge","/v2/registration/complete","/v2/provisioning/challenge").contains(path))throw new IOException("Invalid enrollment path");
        byte[] raw=body.toString().getBytes(StandardCharsets.UTF_8);if(raw.length>8192||cancelled)throw new IOException("Enrollment unavailable");
        HttpsURLConnection c=(HttpsURLConnection)new URL(ControlEnrollment.origin(origin)+path).openConnection();connection=c;
        ScheduledFuture<?> timeout=null;
        try {
            if(cancelled)throw new IOException("Enrollment cancelled");
            timeout=watchdog.schedule(()->{cancelled=true;c.disconnect();},15,TimeUnit.SECONDS);
            c.setInstanceFollowRedirects(false);c.setUseCaches(false);c.setConnectTimeout(5000);c.setReadTimeout(5000);
            c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");c.setRequestProperty("Accept","application/json");
            c.setFixedLengthStreamingMode(raw.length);try(OutputStream output=c.getOutputStream()){output.write(raw);}
            if(c.getResponseCode()!=200)throw new IOException("Enrollment request refused or unavailable");
            String type=c.getContentType();if(type==null||!type.split(";",2)[0].trim().equalsIgnoreCase("application/json"))throw new IOException("Invalid enrollment response");
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();try(InputStream in=c.getInputStream()){
                byte[] buffer=new byte[1024];int n;while((n=in.read(buffer))!=-1){if(cancelled||bytes.size()+n>8192)throw new IOException("Invalid enrollment response");bytes.write(buffer,0,n);}
            }
            if(cancelled)throw new IOException("Enrollment cancelled");
            return ControlJson.parse(bytes.toByteArray()).getAsJsonObject();
        } finally {java.util.Arrays.fill(raw,(byte)0);if(timeout!=null)timeout.cancel(false);c.disconnect();connection=null;}
    }
}
