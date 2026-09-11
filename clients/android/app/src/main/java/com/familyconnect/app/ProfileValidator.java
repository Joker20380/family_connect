package com.familyconnect.app;

import java.nio.charset.StandardCharsets;
import java.util.*;

public final class ProfileValidator {
    public static final int LIMIT=16384;
    private static final Map<String,Set<String>> FIELDS=new HashMap<>();
    static {
        FIELDS.put("Interface",new HashSet<>(Arrays.asList("PrivateKey","Address","DNS","MTU","ListenPort")));
        FIELDS.put("Peer",new HashSet<>(Arrays.asList("PublicKey","PresharedKey","Endpoint","AllowedIPs","PersistentKeepalive")));
    }
    private static void require(boolean condition) { if(!condition)throw new IllegalArgumentException("Unsupported profile"); }
    public static String validate(String raw) throws Exception {return validate(raw,Transport.WG);}
    public static String validate(String raw,Transport transport) throws Exception {
        require(raw.getBytes(StandardCharsets.UTF_8).length<=LIMIT && !raw.contains("\0"));
        if(raw.startsWith("\uFEFF"))raw=raw.substring(1);
        Map<String,Map<String,String>> sections=new LinkedHashMap<>(); String section=null;
        for(String original:raw.split("\\R")) {
            String line=original.split("#",2)[0].trim(); if(line.isEmpty())continue;
            if(line.startsWith("[")) {
                require(line.endsWith("]"));section=line.substring(1,line.length()-1);
                require(FIELDS.containsKey(section)&&!sections.containsKey(section));sections.put(section,new LinkedHashMap<>());continue;
            }
            require(section!=null&&line.contains("="));String[] pair=line.split("=",2);
            String key=pair[0].trim(),value=pair[1].trim();
            require((FIELDS.get(section).contains(key)||(transport==Transport.AWG&&section.equals("Interface")&&AwgParameters.FIELDS.contains(key)))&&!sections.get(section).containsKey(key)&&!value.isEmpty());
            sections.get(section).put(key,value);
        }
        require(sections.keySet().equals(FIELDS.keySet()));
        Map<String,String> face=sections.get("Interface"),peer=sections.get("Peer");
        if(transport==Transport.AWG)AwgParameters.validate(face);
        key(face.get("PrivateKey"));key(peer.get("PublicKey"));if(peer.containsKey("PresharedKey"))key(peer.get("PresharedKey"));
        require(face.containsKey("Address")&&face.containsKey("DNS")&&peer.containsKey("Endpoint"));
        for(String dns:face.get("DNS").split(","))numeric(dns.trim());
        Set<String> routes=new HashSet<>();for(String route:peer.getOrDefault("AllowedIPs","").split(","))routes.add(route.trim());
        require(routes.equals(new HashSet<>(Arrays.asList("0.0.0.0/0","::/0"))));
        String endpoint=peer.get("Endpoint");int split=endpoint.lastIndexOf(':');require(split>0);
        numeric(endpoint.substring(0,split).replace("[","").replace("]",""));
        int port=Integer.parseInt(endpoint.substring(split+1));require(port>0&&port<=65535);
        StringBuilder normalized=new StringBuilder();
        for(var entry:sections.entrySet()) {
            normalized.append('[').append(entry.getKey()).append("]\n");
            for(var field:entry.getValue().entrySet())normalized.append(field.getKey()).append(" = ").append(field.getValue()).append('\n');
            normalized.append('\n');
        }
        return normalized.toString();
    }
    private static void key(String value) {require(value!=null&&Base64.getDecoder().decode(value).length==32);}
    private static void numeric(String value) throws Exception {
        require(value.matches("[0-9a-fA-F:.]+")&&(value.contains(":")||value.matches("[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+")));
        java.net.InetAddress.getByName(value);
    }
}
