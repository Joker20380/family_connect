package com.familyconnect.app;

import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

final class AppVpnCatalog {
    enum Availability { AVAILABLE, DISABLED, UNAVAILABLE }
    static final class Entry {
        final String name,label;
        final ApplicationInfo info;
        final boolean launcher;
        final Availability availability;
        Entry(String name,String label,ApplicationInfo info,boolean launcher){
            this.name=name;this.label=label;this.info=info;this.launcher=launcher;
            availability=info==null?Availability.UNAVAILABLE:info.enabled?Availability.AVAILABLE:Availability.DISABLED;
        }
        boolean system(){return info!=null&&(info.flags&(ApplicationInfo.FLAG_SYSTEM|ApplicationInfo.FLAG_UPDATED_SYSTEM_APP))!=0;}
        boolean visible(boolean components,boolean selectedOnly,Set<String> selection,String query){
            query=query.trim().toLowerCase(Locale.ROOT);
            if(selectedOnly&&!selection.contains(name))return false;
            if(!components&&!launcher&&!selection.contains(name))return false;
            return label.toLowerCase(Locale.ROOT).contains(query)||name.toLowerCase(Locale.ROOT).contains(query);
        }
    }
    static List<Entry> read(PackageManager manager,Set<String> retained){
        Set<String> launchers=new HashSet<>();
        Intent intent=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);
        for(ResolveInfo resolved:manager.queryIntentActivities(intent,0)){
            if(resolved.activityInfo!=null&&resolved.activityInfo.enabled)launchers.add(resolved.activityInfo.packageName);
        }
        Map<String,Entry> entries=new TreeMap<>();
        for(ApplicationInfo info:manager.getInstalledApplications(PackageManager.MATCH_DISABLED_COMPONENTS)){
            entries.put(info.packageName,new Entry(info.packageName,manager.getApplicationLabel(info).toString(),info,launchers.contains(info.packageName)));
        }
        for(String name:retained)if(!entries.containsKey(name))entries.put(name,new Entry(name,name,null,false));
        List<Entry> result=new ArrayList<>(entries.values());
        result.sort(Comparator.comparing((Entry entry)->entry.label.toLowerCase(Locale.ROOT)).thenComparing(entry->entry.name));
        return result;
    }
}
