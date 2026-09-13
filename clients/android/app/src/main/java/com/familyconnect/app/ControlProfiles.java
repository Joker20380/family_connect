package com.familyconnect.app;

import com.google.gson.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;
import static com.familyconnect.app.ControlJson.*;

/** Schema2 profiles, distinct from Android's legacy import parser. Never resolves names. */
final class ControlProfiles {
    private static final List<String> AWG=Arrays.asList("Jc Jmin Jmax S1 S2 S3 S4 H1 H2 H3 H4 I1 I2 I3 I4 I5".split(" "));
    private static String s(JsonObject v,String key){return text(v.get(key));}
    private static void id(String v){require(v.matches("[a-zA-Z0-9_-]{1,64}"));}
    private static InetAddress ip(String value)throws Exception {
        require(value.matches("[0-9a-fA-F:.]+"));
        if(!value.contains(":")) {
            String[] parts=value.split("\\.",-1);require(parts.length==4);
            for(String p:parts){require(p.matches("0|[1-9][0-9]{0,2}"));require(Integer.parseInt(p)<=255);}
        }
        return InetAddress.getByName(value);
    }
    private static String canonical(InetAddress ip) {
        byte[] bytes=ip.getAddress();if(bytes.length==4)return ip.getHostAddress();
        int[] words=new int[8];for(int i=0;i<8;i++)words[i]=((bytes[2*i]&255)<<8)|(bytes[2*i+1]&255);
        int best=-1,length=1;
        for(int i=0;i<8;){if(words[i]!=0){i++;continue;}int end=i;while(end<8&&words[end]==0)end++;if(end-i>length){best=i;length=end-i;}i=end;}
        StringBuilder result=new StringBuilder();
        for(int i=0;i<8;i++) {
            if(i==best){result.append("::");i+=length-1;continue;}
            if(result.length()>0 && result.charAt(result.length()-1)!=':')result.append(':');result.append(Integer.toHexString(words[i]));
        }
        return result.toString();
    }
    private static void key(String value,boolean canonical,boolean nonzero) {
        byte[] raw=ControlProtocol.base64(value,canonical);require(raw.length==32);boolean any=false;for(byte b:raw)any|=b!=0;require(!nonzero||any);
    }
    private static long number(String value,long low,long high) {
        require(value.matches("[+-]?[0-9]+"));long result=Long.parseLong(value);require(result>=low&&result<=high);return result;
    }
    private static final class Endpoint {
        final String host;final long port;Endpoint(String host,long port){this.host=host;this.port=port;}
        boolean same(Endpoint other){return other!=null&&host.equals(other.host)&&port==other.port;}
    }
    static void validate(JsonObject state)throws Exception {
        fields(state,"schema_version config_id revision issued_at expires_at recipient audience wireguard_public_key min_client_version previous_config_hash signer_key_id gateways transport_profiles");
        id(s(state,"config_id"));integer(state.get("revision"),1);
        long issued=integer(state.get("issued_at"),1),expires=integer(state.get("expires_at"),1);require(expires>issued&&expires-issued<=86400);
        key(s(state,"wireguard_public_key"),true,true);ControlProtocol.version(s(state,"min_client_version"));
        JsonElement previous=state.get("previous_config_hash");require(previous.isJsonNull()||text(previous).matches("[0-9a-f]{64}"));
        require(state.get("gateways").isJsonArray()&&state.get("transport_profiles").isJsonArray());
        JsonArray gateways=state.getAsJsonArray("gateways"),profiles=state.getAsJsonArray("transport_profiles");
        require(gateways.size()>=1&&gateways.size()<=8&&profiles.size()>=1&&profiles.size()<=8);
        Map<String,Endpoint> endpoints=new HashMap<>();
        for(JsonElement value:gateways) {
            fields(value,"gateway_id endpoint port");JsonObject g=value.getAsJsonObject();id(s(g,"gateway_id"));
            String host=s(g,"endpoint");InetAddress address=ip(host);
            require(canonical(address).equals(host)&&!address.isAnyLocalAddress()&&!address.isLoopbackAddress()&&!address.isMulticastAddress());
            long port=integer(g.get("port"),1);require(port<=65535);
            require(endpoints.put(s(g,"gateway_id"),new Endpoint(host,port))==null);
        }
        Set<String> ids=new HashSet<>();
        for(JsonElement value:profiles) {
            fields(value,"profile_id gateway_id transport transport_version config");JsonObject p=value.getAsJsonObject();
            id(s(p,"profile_id"));id(s(p,"gateway_id"));require(ids.add(s(p,"profile_id")));
            String config=s(p,"config");require(!config.isEmpty()&&config.getBytes(StandardCharsets.UTF_8).length<=16384);
            String transport=s(p,"transport");require(Arrays.asList("wireguard","amneziawg","vless-reality").contains(transport));
            require(s(p,"transport_version").equals(transport.equals("amneziawg")?"2.0":"1"));
            Endpoint endpoint=transport.equals("vless-reality")?tcp(config):wg(config,transport.equals("amneziawg"));
            require(endpoint.same(endpoints.get(s(p,"gateway_id"))));
        }
    }
    private static Endpoint tcp(String config)throws Exception {
        JsonElement value=parse(config.getBytes(StandardCharsets.UTF_8));fields(value,"type server port id public_key server_name short_id");JsonObject p=value.getAsJsonObject();
        require(s(p,"type").equals("vless-reality-v1"));String host=s(p,"server");require(!host.contains(":")&&ip(host) instanceof Inet4Address);
        long port=integer(p.get("port"),1);require(port<=65535);
        String id=s(p,"id");require(UUID.fromString(id).toString().equals(id)&&!id.equals("00000000-0000-0000-0000-000000000000"));
        String key=s(p,"public_key");require(key.matches("[A-Za-z0-9_-]{43}"));key(key.replace('-','+').replace('_','/')+"=",true,true);
        String name=s(p,"server_name");require(name.length()<=253&&name.matches("(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-z]{2,63}"));
        require(s(p,"short_id").matches("(?:[0-9a-f]{2}){1,8}"));return new Endpoint(host,port);
    }
    private static Endpoint wg(String text,boolean awg)throws Exception {
        require(!text.contains("\0"));Map<String,Map<String,String>> sections=new HashMap<>();Map<String,String> current=null;String section="";
        for(String raw:text.split("\\r\\n|[\\n\\r\\u000b\\f\\u001c-\\u001e\\u0085\\u2028\\u2029]")) {
            String line=raw.split("#",2)[0].trim();if(line.isEmpty())continue;
            if(line.startsWith("[")) {
                require(line.equals("[Interface]")||line.equals("[Peer]"));section=line.substring(1,line.length()-1);current=new HashMap<>();require(sections.put(section,current)==null);continue;
            }
            String[] parts=line.split("=",2);require(current!=null&&parts.length==2);String key=parts[0].trim(),v=parts[1].trim();
            String allowed=section.equals("Interface")?"PrivateKey Address DNS MTU ListenPort":"PublicKey PresharedKey Endpoint AllowedIPs PersistentKeepalive";
            require(Arrays.asList(allowed.split(" ")).contains(key)||(section.equals("Interface")&&awg&&AWG.contains(key)));
            require(!v.isEmpty()&&current.put(key,v)==null);
        }
        require(sections.size()==2);Map<String,String> i=sections.get("Interface"),p=sections.get("Peer");
        require("LOCAL_DEVICE_KEY".equals(i.get("PrivateKey"))&&text.split("LOCAL_DEVICE_KEY",-1).length==2);
        key(p.get("PublicKey"),false,false);if(p.containsKey("PresharedKey"))key(p.get("PresharedKey"),false,false);
        for(String address:i.get("Address").split(",",-1)) {
            String[] bits=address.trim().split("/",-1);require(bits.length<=2);InetAddress a=ip(bits[0]);if(bits.length==2)number(bits[1],0,a instanceof Inet4Address?32:128);
        }
        for(String dns:i.get("DNS").split(",",-1))ip(dns.trim());
        Set<String> routes=new HashSet<>();for(String r:p.get("AllowedIPs").split(",",-1))routes.add(r.trim());require(routes.equals(new HashSet<>(Arrays.asList("0.0.0.0/0","::/0"))));
        String endpoint=p.get("Endpoint");int at=endpoint.lastIndexOf(':');require(at>0);String host=endpoint.substring(0,at).replaceAll("^[\\[\\]]+|[\\[\\]]+$","");ip(host);long port=number(endpoint.substring(at+1),1,65535);
        if(i.containsKey("MTU"))number(i.get("MTU"),1280,1500);if(i.containsKey("ListenPort"))number(i.get("ListenPort"),0,65535);if(p.containsKey("PersistentKeepalive"))number(p.get("PersistentKeepalive"),0,65535);
        if(awg)awg(i);return new Endpoint(host,port);
    }
    private static void awg(Map<String,String> fields) {
        for(String name:AWG.subList(0,7)){String value=fields.get(name);require(value.matches("[0-9]{1,5}"));number(value,0,name.equals("Jc")?12:name.startsWith("J")?1280:256);}
        require(Long.parseLong(fields.get("Jmin"))<=Long.parseLong(fields.get("Jmax")));List<long[]> ranges=new ArrayList<>();
        for(String name:AWG.subList(7,11)) {
            String value=fields.get(name);require(value.matches("[0-9]{1,10}(?:-[0-9]{1,10})?"));String[] parts=value.split("-");long low=number(parts[0],5,4294967295L),high=number(parts[parts.length-1],low,4294967295L);
            for(long[] range:ranges)require(low>range[1]||range[0]>high);ranges.add(new long[]{low,high});
        }
        Pattern packet=Pattern.compile("<(?:b 0x([0-9a-fA-F]+)|(r|rd|rc) ([0-9]{1,4})|(t))>");
        for(String name:AWG.subList(11,16)) {
            String value=fields.get(name);if(value==null)continue;Matcher m=packet.matcher(value);int position=0,size=0;
            while(m.find()){require(m.start()==position);position=m.end();if(m.group(1)!=null){require(m.group(1).length()%2==0);size+=m.group(1).length()/2;}else size+=m.group(2)!=null?Integer.parseInt(m.group(3)):4;}
            require(position==value.length()&&size>=1&&size<=1280);
        }
    }
}
