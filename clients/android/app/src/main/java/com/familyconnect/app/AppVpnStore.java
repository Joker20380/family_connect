package com.familyconnect.app;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;

final class AppVpnStore {
    private final SharedPreferences preferences;
    AppVpnStore(Context context){preferences=context.getSharedPreferences("app-vpn",Context.MODE_PRIVATE);}
    AppVpnPolicy read(){
        try{return decode(preferences.getString("policy",null));}
        catch(ClassCastException damaged){throw new IllegalArgumentException("APP_POLICY_INVALID");}
    }
    void save(AppVpnPolicy policy){
        if(!preferences.edit().putString("policy",encode(policy)).commit())throw new IllegalStateException("APP_POLICY_STORAGE");
    }
    static String encode(AppVpnPolicy policy){
        try{return new JSONObject().put("schema",1).put("mode",policy.mode.name())
            .put("included",new JSONArray(policy.included)).put("excluded",new JSONArray(policy.excluded)).toString();}
        catch(Exception invalid){throw new IllegalArgumentException("APP_POLICY_INVALID");}
    }
    static AppVpnPolicy decode(String raw){
        if(raw==null)return AppVpnPolicy.all();
        try{
            if(raw.length()>1048576)throw new IllegalArgumentException();
            JSONObject value=new JSONObject(raw);
            if(value.length()!=4||!(value.get("schema") instanceof Integer)||value.getInt("schema")!=1||!(value.get("mode") instanceof String))throw new IllegalArgumentException();
            return new AppVpnPolicy(AppVpnPolicy.Mode.valueOf(value.getString("mode")),names(value.getJSONArray("included")),names(value.getJSONArray("excluded")));
        }catch(Exception invalid){throw new IllegalArgumentException("APP_POLICY_INVALID");}
    }
    private static ArrayList<String> names(JSONArray values)throws Exception{
        ArrayList<String> names=new ArrayList<>();
        for(int index=0;index<values.length();index++){
            Object value=values.get(index);if(!(value instanceof String))throw new IllegalArgumentException();names.add((String)value);
        }
        return names;
    }
}
