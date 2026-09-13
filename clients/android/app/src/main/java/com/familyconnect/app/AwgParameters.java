package com.familyconnect.app;
import java.util.*;
import java.util.regex.*;
final class AwgParameters {
    static final Set<String> REQUIRED=new HashSet<>(Arrays.asList("Jc","Jmin","Jmax","S1","S2","S3","S4","H1","H2","H3","H4"));
    static final Set<String> FIELDS=new HashSet<>(REQUIRED);
    static {FIELDS.addAll(Arrays.asList("I1","I2","I3","I4","I5","HeaderProtectionKey","ContentPaddingAddition","RandomTrailers","DisableCookies"));}
    static void require(boolean ok){if(!ok)throw new IllegalArgumentException("Invalid AWG parameters");}
    static int number(String value,int min,int max){require(value!=null&&value.matches("[0-9]{1,5}"));int n=Integer.parseInt(value);require(n>=min&&n<=max);return n;}
    static void validate(Map<String,String> face){
        require(face.keySet().containsAll(REQUIRED));number(face.get("Jc"),1,12);
        require(number(face.get("Jmin"),1,1280)<=number(face.get("Jmax"),1,1280));
        for(int i=1;i<=4;i++)number(face.get("S"+i),0,256);
        boolean protectedHeaders=face.containsKey("HeaderProtectionKey");
        if(protectedHeaders){
            byte[] key=Base64.getDecoder().decode(face.get("HeaderProtectionKey"));require(key.length==32);
            boolean nonzero=false;for(byte b:key)nonzero|=b!=0;require(nonzero);
            for(int i=1;i<=4;i++){require(number(face.get("S"+i),12,256)>=12);require(face.get("H"+i).equals(Integer.toString(i)));}
        }
        for(String key:Arrays.asList("RandomTrailers","DisableCookies"))if(face.containsKey(key))require(face.get(key).equals("true")||face.get(key).equals("false"));
        if(face.containsKey("ContentPaddingAddition")){
            String v=face.get("ContentPaddingAddition");require(v.matches("[0-9]{1,5}(-[0-9]{1,5})?"));String[] pair=v.split("-");
            require(number(pair[0],0,256)<=number(pair[pair.length-1],0,256));
        }
        if("true".equals(face.get("RandomTrailers")))for(int i=2;i<=4;i++)require(face.get("S1").equals(face.get("S"+i)));
        List<long[]> ranges=new ArrayList<>();
        for(int i=1;i<=4;i++){
            String value=face.get("H"+i);require(value.matches("[0-9]{1,10}(-[0-9]{1,10})?"));String[] parts=value.split("-");
            long low=Long.parseLong(parts[0]),high=Long.parseLong(parts[parts.length-1]);require(low>=(protectedHeaders?1:5)&&high>=low&&high<=4294967295L);
            for(long[] previous:ranges)require(low>previous[1]||high<previous[0]);ranges.add(new long[]{low,high});
        }
        Pattern packet=Pattern.compile("<(?:b 0x([0-9a-fA-F]+)|(r|rd|rc) ([0-9]{1,4})|(t))>");
        for(int i=1;i<=5;i++){
            String value=face.get("I"+i);if(value==null)continue;require(value.length()<=4096);
            Matcher matcher=packet.matcher(value);int pos=0,size=0;
            while(matcher.find()){
                require(matcher.start()==pos);pos=matcher.end();
                if(matcher.group(1)!=null){require(matcher.group(1).length()%2==0);size+=matcher.group(1).length()/2;}
                else size+=matcher.group(2)!=null?Integer.parseInt(matcher.group(3)):4;
            }
            require(pos==value.length()&&size>=1&&size<=1280);
        }
    }
}
