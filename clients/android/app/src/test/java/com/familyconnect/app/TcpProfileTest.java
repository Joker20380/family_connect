package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class TcpProfileTest {
 static final String GOOD="{\"type\":\"vless-reality-v1\",\"server\":\"192.0.2.1\",\"port\":443,\"id\":\"11111111-2222-4333-8444-555555555555\",\"public_key\":\"zo060cy2M-x7cMF4FKXHbs0CloUFDTRHRboFhw5YfVk\",\"server_name\":\"android.test\",\"short_id\":\"0102030405060708\"}";
 void bad(String raw)throws Exception{try{TcpProfile.validate(raw);fail("Accepted invalid profile");}catch(IllegalArgumentException expected){}}
 @Test public void validAndDispatch()throws Exception{assertEquals(GOOD,TcpProfile.validate(GOOD));assertEquals(GOOD,ProfileValidator.validate(GOOD,Transport.TCP));assertEquals(Transport.TCP,Transport.parse("tcp"));}
 @Test public void exactFields()throws Exception{bad(GOOD.replace("{","{\"server\":\"192.0.2.2\","));bad(GOOD.replace("{","{\"outbounds\":[],"));bad(GOOD.replace("\"port\":443,",""));bad(GOOD+"{}");bad(GOOD.replace("}",",}"));}
 @Test public void endpoints()throws Exception{for(String value:new String[]{"example.com","127.0.0.1","0.0.0.0","224.0.0.1","192.000.2.1","256.0.0.1","[::1]"})bad(GOOD.replace("192.0.2.1",value));}
 @Test public void numbersAndIdentity()throws Exception{for(String value:new String[]{"0","65536","443.0","\"443\"","true","0443"})bad(GOOD.replace(":443",":"+value));bad(GOOD.replace("11111111-2222-4333-8444-555555555555","00000000-0000-0000-0000-000000000000"));}
 @Test public void realityRequired()throws Exception{bad(GOOD.replace("vless-reality-v1","vless"));bad(GOOD.replace("android.test","android.test/evil"));bad(GOOD.replace("0102030405060708","0"));bad(GOOD.replace("zo060cy2M-x7cMF4FKXHbs0CloUFDTRHRboFhw5YfVk","AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"));}
 @Test public void limitsAndEscapes()throws Exception{bad(" ".repeat(4096)+GOOD);bad(GOOD.replace("android.test","android\\u002etest"));bad(GOOD.replace("android.test","android\ntest"));}
}
