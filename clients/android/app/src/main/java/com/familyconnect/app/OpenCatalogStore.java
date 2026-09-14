package com.familyconnect.app;

import android.content.Context;
import android.util.AtomicFile;
import java.io.*;
import java.net.URL;
import java.util.Arrays;
import javax.net.ssl.HttpsURLConnection;

/** HTTPS refresh with a verified offline cache; public test profiles contain no device identity. */
final class OpenCatalogStore {
    private final Context context;
    OpenCatalogStore(Context context){this.context=context;}
    ControlOpenCatalog load()throws Exception{
        byte[] anchor=ControlTrust.anchor(context);AtomicFile cache=new AtomicFile(new File(context.getNoBackupFilesDir(),"open-test-catalog.json"));
        byte[] prior=null;ControlOpenCatalog saved=null;
        if(cache.getBaseFile().exists()){
            if(cache.getBaseFile().length()>16384)throw new IOException("Invalid cache size");
            prior=cache.readFully();saved=ControlOpenCatalog.verify(prior,anchor,0);
        }
        HttpsURLConnection connection=null;
        try{
            connection=(HttpsURLConnection)new URL("https://185.251.89.19:8443/friends/catalog.json").openConnection();
            connection.setConnectTimeout(5000);connection.setReadTimeout(5000);connection.setInstanceFollowRedirects(false);connection.setUseCaches(false);
            if(connection.getResponseCode()!=200)throw new IOException("Catalog unavailable");
            long deadline=System.nanoTime()+15_000_000_000L;ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            try(InputStream in=connection.getInputStream()){byte[] buffer=new byte[1024];int count;while((count=in.read(buffer))!=-1){if(Thread.currentThread().isInterrupted()||System.nanoTime()>deadline||bytes.size()+count>16384)throw new IOException("Invalid catalog");bytes.write(buffer,0,count);}}
            byte[] raw=bytes.toByteArray();ControlOpenCatalog next=ControlOpenCatalog.verify(raw,anchor,saved==null?0:saved.sequence);
            if(saved!=null&&next.sequence==saved.sequence&&!Arrays.equals(raw,prior))throw new IOException("Catalog sequence replaced");
            FileOutputStream out=null;
            try{out=cache.startWrite();out.write(raw);cache.finishWrite(out);out=null;
                if(!Arrays.equals(cache.readFully(),raw))throw new IOException("Catalog not saved");}
            catch(Exception failure){if(out!=null)cache.failWrite(out);throw failure;}
            return next;
        }catch(Exception failure){if(saved!=null)return saved;throw failure;}
        finally{if(connection!=null)connection.disconnect();}
    }
}
