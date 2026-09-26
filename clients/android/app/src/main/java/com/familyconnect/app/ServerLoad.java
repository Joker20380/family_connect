package com.familyconnect.app;

import com.google.gson.*;
import java.net.URL;
import javax.net.ssl.HttpsURLConnection;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Informational host utilization, never a VPN health or routing decision. */
final class ServerLoad {
    final String country;final double observed,cpu,rx,tx;final Double percent;final boolean estimated;
    ServerLoad(String c,double t,double p,double r,double x,Double v,boolean e){country=c;observed=t;cpu=p;rx=r;tx=x;percent=v;estimated=e;}
    boolean fresh(double now){return now-observed>=-15&&now-observed<=45;}
    static double number(JsonObject o,String name,double min,double max){
        JsonElement e=o.get(name);if(e==null||!e.isJsonPrimitive()||!e.getAsJsonPrimitive().isNumber())throw new IllegalArgumentException();
        double v=e.getAsDouble();if(!Double.isFinite(v)||v<min||v>max)throw new IllegalArgumentException();return v;
    }
    private static ServerLoad gateway(JsonObject o,String country,double now){
        if(!country.equals(o.get("country").getAsString()))throw new IllegalArgumentException();
        double t=number(o,"observed_at",0,1e12),cpu=number(o,"cpu_percent",0,100),rx=number(o,"rx_mbps",0,1e12),tx=number(o,"tx_mbps",0,1e12);
        String direction=o.has("capacity_direction")?o.get("capacity_direction").getAsString():"duplex";
        if(!direction.equals("duplex")&&!direction.equals("egress"))throw new IllegalArgumentException();
        Double value=null;
        if(o.has("capacity_mbps")&&!o.get("capacity_mbps").isJsonNull())value=Math.min(100,Math.max(cpu,100*(direction.equals("egress")?tx:Math.max(rx,tx))/number(o,"capacity_mbps",.001,1e9)));
        boolean estimated=o.has("capacity_basis")&&"provider-default-estimate".equals(o.get("capacity_basis").getAsString());
        ServerLoad result=new ServerLoad(country,t,cpu,rx,tx,value,estimated);if(!result.fresh(now))throw new IllegalArgumentException();return result;
    }
    static ServerLoad parse(String raw,String country,double now){
        if(raw.length()>8192||!(country.equals("ru")||country.equals("nl")))throw new IllegalArgumentException();
        JsonObject root=JsonParser.parseString(raw).getAsJsonObject();if(number(root,"schema",1,1)!=1)throw new IllegalArgumentException();
        JsonObject gateways=root.getAsJsonObject("gateways");if(!gateways.has(country))throw new IllegalArgumentException();
        return gateway(gateways.getAsJsonObject(country),country,now);
    }
    static Map<String,ServerLoad> fetchAll()throws IOException {
        HttpsURLConnection c=(HttpsURLConnection)new URL("https://185.251.89.19:8443/status/server-load.json").openConnection();
        c.setConnectTimeout(5000);c.setReadTimeout(5000);c.setInstanceFollowRedirects(false);c.setUseCaches(false);
        try{if(c.getResponseCode()!=200)throw new IOException();
            ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[1024];
            try(InputStream in=c.getInputStream()){int n;while((n=in.read(buffer))!=-1){out.write(buffer,0,n);if(out.size()>8192)throw new IOException();}}
            JsonObject root=JsonParser.parseString(out.toString(StandardCharsets.UTF_8.name())).getAsJsonObject();
            if(number(root,"schema",1,1)!=1)throw new IllegalArgumentException();
            JsonObject gateways=root.getAsJsonObject("gateways");double now=System.currentTimeMillis()/1000.0;
            Map<String,ServerLoad> result=new LinkedHashMap<>();
            for(String country:new String[]{"ru","nl"}){
                if(!gateways.has(country))continue;
                try{result.put(country,gateway(gateways.getAsJsonObject(country),country,now));}catch(IllegalArgumentException ignored){}
            }
            if(result.isEmpty())throw new IOException();return result;
        }finally{c.disconnect();}
    }
    static ServerLoad fetch(String country)throws IOException {
        HttpsURLConnection c=(HttpsURLConnection)new URL("https://185.251.89.19:8443/status/server-load.json").openConnection();
        c.setConnectTimeout(5000);c.setReadTimeout(5000);c.setInstanceFollowRedirects(false);c.setUseCaches(false);
        try{if(c.getResponseCode()!=200)throw new IOException();
            ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[1024];
            try(InputStream in=c.getInputStream()){int n;while((n=in.read(buffer))!=-1){out.write(buffer,0,n);if(out.size()>8192)throw new IOException();}}
            return parse(out.toString(StandardCharsets.UTF_8.name()),country,System.currentTimeMillis()/1000.0);
        }finally{c.disconnect();}
    }
}
