package com.familyconnect.app;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Locale;

final class TcpTrafficDiagnostics {
    interface Cleanup { void run() throws Throwable; }
    static void cleanup(Throwable primary,Cleanup... actions)throws Throwable{
        Throwable retained=primary;
        for(Cleanup action:actions)try{action.run();}catch(Throwable failure){
            if(retained==null)retained=failure;
            else if(retained!=failure&&!Arrays.asList(retained.getSuppressed()).contains(failure))retained.addSuppressed(failure);
        }
        if(primary==null&&retained!=null)throw retained;
    }
    static final class Response {
        final String text;
        final int status,headerEnd,contentLength,bodyLength;
        Response(byte[] bytes){
            text=new String(bytes,StandardCharsets.US_ASCII);
            int parsed=-1,length=-1;
            String[] first=text.split("\\r\\n",2)[0].split(" ");
            if(first.length>=2&&first[0].matches("HTTP/1\\.[01]"))try{parsed=Integer.parseInt(first[1]);}catch(NumberFormatException ignored){}
            int boundary=text.indexOf("\r\n\r\n");headerEnd=boundary<0?-1:boundary+4;
            if(headerEnd>=0)for(String header:text.substring(0,boundary).split("\r\n"))
                if(header.toLowerCase(Locale.ROOT).startsWith("content-length:"))try{length=Integer.parseInt(header.substring(15).trim());}catch(NumberFormatException ignored){}
            status=parsed;contentLength=length;bodyLength=headerEnd<0?0:bytes.length-headerEnd;
        }
        String assertion(String nonce){return !text.contains(" 200 ")?"status":!text.endsWith(nonce)?"body":"none";}
        String category(String nonce,boolean eof){
            String assertion=assertion(nonce);
            if(assertion.equals("none"))return "PASS";
            if(eof&&(headerEnd<0||(contentLength>=0&&bodyLength<contentLength)))return "PREMATURE_EOF";
            return assertion.equals("status")?"STATUS_MISMATCH":"BODY_MISMATCH";
        }
        void require(String nonce,boolean eof){
            if(!text.contains(" 200 "))throw new AssertionError("TCP_PRIMARY assertion=status category="+category(nonce,eof)+" status="+status);
            if(!text.endsWith(nonce))throw new AssertionError("TCP_PRIMARY assertion=body category="+category(nonce,eof)+" status="+status);
        }
    }
    static String digest(byte[] bytes)throws Exception{
        StringBuilder output=new StringBuilder();for(byte value:MessageDigest.getInstance("SHA-256").digest(bytes))output.append(String.format(Locale.ROOT,"%02x",value&255));return output.toString();
    }
    static String preview(byte[] bytes,String nonce,boolean suffix){
        String text=new String(bytes,StandardCharsets.US_ASCII);
        char[] safe=new char[text.length()];Arrays.fill(safe,'.');
        for(String allowed:new String[]{"HTTP/1.0 200 OK","HTTP/1.1 200 OK","Content-Length:","\r\n",nonce}){
            int offset=0;while((offset=text.indexOf(allowed,offset))>=0){
                String replacement=allowed.equals(nonce)?"<fixture-path>":allowed;
                for(int index=0;index<allowed.length();index++)safe[offset+index]=index<replacement.length()?replacement.charAt(index):'.';
                offset+=allowed.length();
            }
        }
        int start=suffix?Math.max(0,safe.length-80):0;return new String(safe,start,Math.min(80,safe.length-start));
    }
}
