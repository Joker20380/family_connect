package com.familyconnect.app;

import android.content.*;
import android.net.*;
import android.os.Build;
import android.util.AtomicFile;
import com.google.gson.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

final class Diagnostics {
    private static Diagnostics instance;
    private final Context context;
    private final DiagnosticRing ring;
    private Diagnostics(Context context){
        this.context=context.getApplicationContext();String support=DeviceSupport.cached(context);
        ring=new DiagnosticRing(support,BuildConfig.VERSION_NAME,BuildConfig.VERSION_CODE,Build.VERSION.SDK_INT);
    }
    private static synchronized Diagnostics get(Context context){if(instance==null)instance=new Diagnostics(context);return instance;}
    static void event(Context context,ConnectivityOrchestrator.Event event){
        try{Diagnostics store=get(context);synchronized(store){store.network();boolean incident=store.ring.event(event,System.currentTimeMillis());store.save(incident);}}catch(Exception ignored){}
    }
    static void readiness(Context context,boolean ready){try{Diagnostics store=get(context);synchronized(store){store.ring.readiness(ready,System.currentTimeMillis());store.save(false);}}catch(Exception ignored){}}
    static void readinessResult(Context context,ReadinessImportResult.Code code){try{Diagnostics store=get(context);synchronized(store){store.ring.readinessResult(code,System.currentTimeMillis());store.save(false);}}catch(Exception ignored){}}
    static void vpn(Context context,boolean open){try{Diagnostics store=get(context);synchronized(store){store.ring.vpn(open,System.currentTimeMillis());store.save(false);}}catch(Exception ignored){}}
    static void dns(Context context,boolean good){try{Diagnostics store=get(context);synchronized(store){store.ring.dns(good,System.currentTimeMillis());store.save(false);}}catch(Exception ignored){}}
    static void cleanup(Context context,boolean success){try{Diagnostics store=get(context);synchronized(store){store.ring.cleanup(success,System.currentTimeMillis());store.save(false);}}catch(Exception ignored){}}
    static void nativeStats(Context context,org.json.JSONObject stats){
        try{Diagnostics store=get(context);synchronized(store){
            org.json.JSONArray events=stats.optJSONArray("events");
            if(events!=null)for(int index=0;index<Math.min(32,events.length());index++)store.ring.nativeEvent(events.optString(index),System.currentTimeMillis());
            for(String name:new String[]{"protect_ok","protect_denied"})store.ring.counter(name,stats.optLong(name,-1));
            org.json.JSONObject packet=stats.optJSONObject("packet");
            if(packet!=null)for(String name:new String[]{"dns","tcp","tcp_active","tcp_peak","udp_denied","ipv6_denied"})store.ring.counter(name,packet.optLong(name,-1));
            org.json.JSONObject diagnostic=packet==null?null:packet.optJSONObject("diagnostic");
            JsonObject safeInput=diagnostic==null?new JsonObject():JsonParser.parseString(diagnostic.toString()).getAsJsonObject();
            store.ring.restricted(safeInput,stats.optInt("state",-1),stats.optBoolean("authorization_denied",false),System.currentTimeMillis());
            store.save(false);
        }}catch(Exception ignored){}
    }
    private void network(){
        ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);NetworkCapabilities caps=manager.getNetworkCapabilities(manager.getActiveNetwork());
        ring.network(caps==null?"NONE":caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)?"CELLULAR":caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?"WIFI":caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN)?"VPN":caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)?"ETHERNET":"UNKNOWN");
    }
    private AtomicFile file(String name){return new AtomicFile(new File(context.getNoBackupFilesDir(),"diag-"+name+".json"));}
    private void save(boolean incident)throws IOException{
        ring.support(DeviceSupport.observed());
        byte[] raw=ring.snapshot().toString().getBytes(StandardCharsets.UTF_8);write(file("ring"),raw);if(incident)write(file("incident"),raw);
    }
    private static void write(AtomicFile file,byte[] raw)throws IOException{
        if(raw.length>DiagnosticRing.RECORD_LIMIT)throw new IOException("Diagnostic bound");FileOutputStream output=file.startWrite();
        try{output.write(raw);file.finishWrite(output);}catch(IOException failure){file.failWrite(output);throw failure;}
    }
    static void share(android.app.Activity activity){
        new android.app.AlertDialog.Builder(activity).setTitle(R.string.diagnostics_send).setMessage(R.string.diagnostics_privacy)
            .setNegativeButton(android.R.string.cancel,null).setPositiveButton(R.string.diagnostics_send,(dialog,which)->{
                try{Diagnostics store=get(activity);String support=DeviceSupport.cached(activity);JsonObject bundle=new JsonObject();String filename="diagnostics-"+UUID.randomUUID().toString().replace("-","")+".json";synchronized(store){
                    store.ring.support(support);
                    for(String name:new String[]{"ring","incident"}){
                        try{byte[] raw=store.file(name).readFully();if(raw.length>DiagnosticRing.RECORD_LIMIT)throw new IOException("Diagnostic bound");JsonObject record=JsonParser.parseString(new String(raw,StandardCharsets.UTF_8)).getAsJsonObject();record.addProperty("device_support_id",support);bundle.add(name,record);}
                        catch(FileNotFoundException missing){if(name.equals("ring"))bundle.add(name,store.ring.snapshot());}
                    }
                    File[] previous=activity.getCacheDir().listFiles((directory,name)->name.matches("diagnostics-[0-9a-f]{32}\\.json"));
                    if(previous!=null)for(File file:previous){
                        activity.revokeUriPermission(Uri.parse("content://"+activity.getPackageName()+".diagnostics/"+file.getName()),Intent.FLAG_GRANT_READ_URI_PERMISSION);
                        if(!file.delete())throw new IOException("Diagnostic cleanup");
                    }
                    byte[] encoded=bundle.toString().getBytes(StandardCharsets.UTF_8);
                    if(encoded.length>DiagnosticRing.EXPORT_LIMIT)throw new IOException("Diagnostic bound");
                    File target=new File(activity.getCacheDir(),filename);try(FileOutputStream output=new FileOutputStream(target)){output.write(encoded);}
                }
                Uri uri=Uri.parse("content://"+activity.getPackageName()+".diagnostics/"+filename);
                Intent send=new Intent(Intent.ACTION_SEND).setType("application/json").putExtra(Intent.EXTRA_STREAM,uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                send.setClipData(ClipData.newRawUri("Diagnostics",uri));activity.startActivity(Intent.createChooser(send,activity.getString(R.string.diagnostics_send)));
                }catch(Exception failure){android.widget.Toast.makeText(activity,R.string.diagnostics_failed,android.widget.Toast.LENGTH_LONG).show();}
            }).show();
    }
}
