package com.familyconnect.app;

import android.content.Context;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Build;
import android.telephony.SubscriptionManager;
import android.telephony.TelephonyManager;
import com.google.gson.JsonObject;

final class TechnicalMetadataAndroid {
    private TechnicalMetadataAndroid(){}
    static JsonObject sample(Context context){
        long generation=ConnectionService.sessionId;String rawState=ConnectionService.status;
        long now=System.currentTimeMillis();JsonObject groups=new JsonObject();
        JsonObject profile=new JsonObject();profile.addProperty("manufacturer",TechnicalMetadataSnapshot.text(Build.MANUFACTURER,80));
        profile.addProperty("model",TechnicalMetadataSnapshot.text(Build.MODEL,100));
        profile.addProperty("android_version",TechnicalMetadataSnapshot.text(Build.VERSION.RELEASE,40));
        profile.addProperty("api_level",Build.VERSION.SDK_INT);profile.addProperty("app_version",BuildConfig.VERSION_NAME);
        profile.addProperty("version_code",BuildConfig.VERSION_CODE);
        groups.add("profile",TechnicalMetadataSnapshot.observation("android_build_package","partial","none",profile,now,0));
        groups.add("network",network(context,now));groups.add("mobile",mobile(context,now));
        String active=ConnectionService.activeTransport,gateway=ConnectionService.observedGateway,preference=ConnectionService.requestedTransport;
        ConnectionTerminal.Snapshot terminal=ConnectionTerminal.VPN.snapshot();String attempt="NONE";
        if("connecting".equals(rawState)||"restoring".equals(rawState))for(ConnectionTerminal.Stage stage:terminal.lines){
            if(stage==ConnectionTerminal.Stage.AWG)attempt="AWG";
            if(stage==ConnectionTerminal.Stage.TCP)attempt="TCP";
            if(stage==ConnectionTerminal.Stage.TELEMOST)attempt="MESH";
        }
        String state=TechnicalMetadataSnapshot.state(rawState);
        if(generation!=ConnectionService.sessionId||!rawState.equals(ConnectionService.status)){
            state="UNKNOWN";attempt="NONE";
            JsonObject network=new JsonObject();network.addProperty("kind","UNKNOWN");network.addProperty("scope","unknown");
            groups.add("network",TechnicalMetadataSnapshot.observation("unavailable","unavailable","not_observed",network,now,0));
        }
        groups.add("session",TechnicalMetadataSnapshot.observation("connection_service","available","none",
            TechnicalMetadataSnapshot.session(preference,attempt,active,gateway,state),now,0));
        JsonObject diagnostic=new JsonObject();String error="NONE";
        if(terminal.failureAt>0&&now-terminal.failureAt<TechnicalMetadataSnapshot.RETENTION_MS){error=terminal.failureStage==ConnectionTerminal.Stage.CANCELLED?"CANCELLED":terminal.failureStage==ConnectionTerminal.Stage.AUTH?"AUTH":"TRANSPORT";}
        diagnostic.addProperty("error",error);diagnostic.addProperty("error_at_ms",!"NONE".equals(error)?terminal.failureAt:null);
        String readiness="UNKNOWN";
        try{JsonObject current=Diagnostics.supportSnapshot(context);String value=current.has("restricted_readiness")?current.get("restricted_readiness").getAsString():"UNKNOWN";if("READY".equals(value)||"NOT_READY".equals(value))readiness=value;}catch(RuntimeException ignored){}
        diagnostic.addProperty("readiness",readiness);
        groups.add("diagnostic",TechnicalMetadataSnapshot.observation("connection_terminal","partial","not_observed",diagnostic,now,0));
        return groups;
    }
    static String kind(NetworkCapabilities caps){
        if(caps==null)return "UNKNOWN";
        int count=(caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?1:0)+(caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)?1:0)+(caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)?1:0);
        if(count!=1)return "UNKNOWN";
        if(caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI))return "WIFI";
        if(caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR))return "CELLULAR";
        if(caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET))return "ETHERNET";
        return "UNKNOWN";
    }
    static JsonObject network(Context context,long now){
        String type="UNKNOWN",source="unavailable",scope="unknown",reason="underlay_not_exposed";
        try{
            ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
            Network current=manager==null?null:manager.getActiveNetwork();
            NetworkCapabilities caps=manager==null?null:manager.getNetworkCapabilities(current);
            boolean session="on".equals(ConnectionService.status)||"restoring".equals(ConnectionService.status);
            if(!session&&current==null){type="OFFLINE";source="android_default_network";scope="default_network";reason="none";}
            else if(!session&&caps!=null&&caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN)){
                type=kind(caps);source="android_default_network";scope="default_network";reason="UNKNOWN".equals(type)?"not_observed":"none";
            }else if(session&&manager!=null){
                NetworkCapabilities selected=null;int count=0;
                for(Network vpn:manager.getAllNetworks()){
                    NetworkCapabilities own=manager.getNetworkCapabilities(vpn);
                    if(own==null||!own.hasTransport(NetworkCapabilities.TRANSPORT_VPN))continue;
                    if(Build.VERSION.SDK_INT>=30&&own.getOwnerUid()!=android.os.Process.myUid())continue;
                    selected=own;count++;
                }
                if(count==1){type=kind(selected);source="vpn_transport_capabilities";scope="session_underlay";reason="UNKNOWN".equals(type)?"underlay_not_exposed":"none";}
            }
        }catch(SecurityException unavailable){reason="permission_not_granted";}
        catch(RuntimeException unavailable){reason="service_unavailable";}
        JsonObject values=new JsonObject();values.addProperty("kind",type);values.addProperty("scope",scope);
        return TechnicalMetadataSnapshot.observation(source,"UNKNOWN".equals(type)?"unavailable":"available",reason,values,now,0);
    }
    static JsonObject mobile(Context context,long now){
        String sim=null,registered=null,radio="UNKNOWN",simReason="service_unavailable",registeredReason="service_unavailable",radioReason="permission_not_granted";
        try{
            TelephonyManager manager=context.getSystemService(TelephonyManager.class);
            if(manager!=null){
                int subscription=SubscriptionManager.getDefaultDataSubscriptionId();
                if(subscription>=0){
                    manager=manager.createForSubscriptionId(subscription);
                    sim=TechnicalMetadataSnapshot.text(manager.getSimOperatorName(),100);
                    registered=TechnicalMetadataSnapshot.text(manager.getNetworkOperatorName(),100);
                    simReason=sim==null?"no_sim":"none";registeredReason=registered==null?"no_registered_network":"none";
                    if(Build.VERSION.SDK_INT>=33&&context.checkSelfPermission(android.Manifest.permission.READ_BASIC_PHONE_STATE)==PackageManager.PERMISSION_GRANTED){
                        int type=manager.getDataNetworkType();
                        radio=type==TelephonyManager.NETWORK_TYPE_NR?"5G":type==TelephonyManager.NETWORK_TYPE_LTE?"LTE_4G":"UNKNOWN";
                        radioReason="UNKNOWN".equals(radio)?"not_observed":"none";
                    }
                }else{
                    simReason=manager.getSimState()==TelephonyManager.SIM_STATE_ABSENT?"no_sim":"ambiguous_subscription";
                    registeredReason="no_registered_network";radioReason=simReason;
                }
            }
        }catch(SecurityException unavailable){simReason=sim==null?"permission_not_granted":simReason;registeredReason=registered==null?"permission_not_granted":registeredReason;radioReason="permission_not_granted";}
        catch(RuntimeException unavailable){radioReason="service_unavailable";}
        JsonObject values=new JsonObject();values.addProperty("sim_operator",sim);values.addProperty("registered_operator",registered);
        values.addProperty("radio",radio);values.addProperty("sim_reason",simReason);values.addProperty("registered_reason",registeredReason);values.addProperty("radio_reason",radioReason);
        return TechnicalMetadataSnapshot.observation("android_telephony_public","partial","not_observed",values,now,0);
    }
}
