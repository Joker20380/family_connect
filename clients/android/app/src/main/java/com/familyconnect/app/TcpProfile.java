package com.familyconnect.app;
import java.util.*;
import java.util.regex.*;
import java.nio.charset.StandardCharsets;
/** Strict flat JSON shared with the Linux transport profile; never arbitrary Xray configuration. */
final class TcpProfile {
    private static final Set<String> FIELDS=new HashSet<>(Arrays.asList("type","server","port","id","public_key","server_name","short_id"));
    private static final Pattern FIELD=Pattern.compile("\\s*\"([a-z_]+)\"\\s*:\\s*(?:\"([^\"\\\\\\p{Cntrl}]*)\"|([0-9]+))\\s*");
    static void require(boolean ok){if(!ok)throw new IllegalArgumentException("Unsupported TCP profile");}
    static Map<String,String> parse(String raw)throws Exception{
        require(raw.getBytes(StandardCharsets.UTF_8).length<=4096);String s=raw.trim();require(s.startsWith("{")&&s.endsWith("}"));
        Map<String,String> p=new LinkedHashMap<>();String body=s.substring(1,s.length()-1);int pos=0;
        while(pos<body.length()){
            Matcher m=FIELD.matcher(body);m.region(pos,body.length());require(m.lookingAt());String key=m.group(1);
            require(FIELDS.contains(key)&&!p.containsKey(key));require(key.equals("port")?m.group(3)!=null:m.group(2)!=null);
            p.put(key,m.group(2)!=null?m.group(2):m.group(3));pos=m.end();if(pos==body.length())break;require(body.charAt(pos++)==',');require(pos<body.length());
        }
        require(p.keySet().equals(FIELDS)&&p.get("type").equals("vless-reality-v1"));
        String ip=p.get("server");require(ip.matches("[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+"));String[] parts=ip.split("\\.");
        for(String part:parts){int n=Integer.parseInt(part);require(n<=255&&Integer.toString(n).equals(part));}
        int first=Integer.parseInt(parts[0]);require(first>0&&first<224&&first!=127);
        String port=p.get("port");int n=Integer.parseInt(port);require(n>0&&n<=65535&&Integer.toString(n).equals(port));
        String id=p.get("id");require(id.matches("[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")&&!id.equals("00000000-0000-0000-0000-000000000000"));
        String key=p.get("public_key");require(key.matches("[A-Za-z0-9_-]{43}"));byte[] decoded=Base64.getUrlDecoder().decode(key+"=");
        require(decoded.length==32&&Base64.getUrlEncoder().withoutPadding().encodeToString(decoded).equals(key));boolean nonzero=false;for(byte b:decoded)nonzero|=b!=0;require(nonzero);
        require(p.get("server_name").length()<=253&&p.get("server_name").matches("(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-z]{2,63}"));
        require(p.get("short_id").matches("(?:[0-9a-f]{2}){1,8}"));return p;
    }
    static String validate(String raw)throws Exception{
        Map<String,String> p=parse(raw);StringBuilder out=new StringBuilder("{");
        for(String key:new String[]{"type","server","port","id","public_key","server_name","short_id"}){
            if(out.length()>1)out.append(',');out.append('"').append(key).append("\":");
            if(key.equals("port"))out.append(p.get(key));else out.append('"').append(p.get(key)).append('"');
        }
        return out.append('}').toString();
    }
}
