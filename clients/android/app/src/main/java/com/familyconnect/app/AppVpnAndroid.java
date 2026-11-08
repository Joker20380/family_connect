package com.familyconnect.app;

import android.content.Context;
import android.content.pm.PackageManager;
import android.net.VpnService;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.amnezia.awg.config.Config;
import org.amnezia.awg.config.Interface;

final class AppVpnAndroid {
    private final Context context;
    final AppVpnPolicy policy;
    private final Map<String,Integer> identities;
    AppVpnAndroid(Context context,AppVpnPolicy policy){
        this.context=context;this.policy=policy;policy.requireConnectable();
        try{identities=resolve();}catch(PackageManager.NameNotFoundException missing){throw new IllegalArgumentException("APP_POLICY_UNAVAILABLE");}
    }
    private Map<String,Integer> resolve()throws PackageManager.NameNotFoundException{
        Map<String,Integer> result=new TreeMap<>();
        for(String name:policy.selected()){
            android.content.pm.ApplicationInfo info=context.getPackageManager().getApplicationInfo(name,0);
            if(!info.enabled)throw new PackageManager.NameNotFoundException("APP_POLICY_UNAVAILABLE");
            result.put(name,info.uid);
        }
        return result;
    }
    void validate()throws PackageManager.NameNotFoundException{
        try{
            if(!identities.equals(resolve()))throw new PackageManager.NameNotFoundException("APP_POLICY_CHANGED");
        }catch(PackageManager.NameNotFoundException missing){throw new PackageManager.NameNotFoundException("APP_POLICY_UNAVAILABLE");}
    }
    boolean routesOwnUid(){
        String[] names=context.getPackageManager().getPackagesForUid(android.os.Process.myUid());
        boolean selected=false;
        if(names!=null)for(String name:names)if(policy.selected().contains(name))selected=true;
        return policy.mode==AppVpnPolicy.Mode.ALL||policy.mode==AppVpnPolicy.Mode.INCLUDE&&selected||policy.mode==AppVpnPolicy.Mode.EXCLUDE&&!selected;
    }
    VpnService.Builder apply(VpnService.Builder builder)throws PackageManager.NameNotFoundException{
        validate();
        try{for(String name:policy.selected()){
            if(policy.mode==AppVpnPolicy.Mode.INCLUDE)builder.addAllowedApplication(name);
            else builder.addDisallowedApplication(name);
        }}catch(PackageManager.NameNotFoundException missing){throw new PackageManager.NameNotFoundException("APP_POLICY_UNAVAILABLE");}
        validate();return builder;
    }
    Config awg(Config original)throws Exception{
        validate();
        if(!original.getInterface().getIncludedApplications().isEmpty()||!original.getInterface().getExcludedApplications().isEmpty())
            throw new IllegalArgumentException("APP_POLICY_PROFILE");
        String face=original.getInterface().toAwgQuickString();
        if(!policy.selected().isEmpty())face+=(policy.mode==AppVpnPolicy.Mode.INCLUDE?"IncludedApplications":"ExcludedApplications")+" = "+String.join(", ",policy.selected())+"\n";
        Interface local=Interface.parse(List.of(face.split("\\n")));
        Config result=new Config.Builder().setInterface(local).addPeers(original.getPeers()).build();
        validate();return result;
    }
}
