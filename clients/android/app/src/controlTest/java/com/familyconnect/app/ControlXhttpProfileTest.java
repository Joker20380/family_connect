package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class ControlXhttpProfileTest {
    static final String GOOD="{\"type\":\"vless-xhttp-tls-v1\",\"server\":\"192.0.2.1\",\"port\":443,\"id\":\"00000000-0000-4000-8000-000000000001\",\"server_name\":\"edge.example.com\",\"path\":\"/fc_test_only_path_1234/\",\"mode\":\"packet-up\"}";
    @Test public void explicitProfileRoundTrip()throws Exception {
        assertEquals(GOOD,TcpProfile.validate(GOOD));
        assertEquals(GOOD,ProfileValidator.validate(GOOD,Transport.TCP));
    }
    @Test public void refusesExtraOptionsAndDuplicateFields()throws Exception {
        for(String extra:new String[]{"\"mode\":\"packet-up\",","\"allowInsecure\":true,","\"public_key\":\"key\",","\"downloadSettings\":{},"})
            assertThrows(Exception.class,()->TcpProfile.validate(GOOD.replace("{","{"+extra)));
    }
    @Test public void strictPathAndMode()throws Exception {
        for(String path:new String[]{"/","/short/","/../fc_test_only_path_1234/","/fc_test_only_path_1234/?a=b","/fc_test_only_path_1234%2f/","/"+"a".repeat(129)+"/"})
            assertThrows(Exception.class,()->TcpProfile.validate(GOOD.replace("/fc_test_only_path_1234/",path)));
        for(String mode:new String[]{"auto","stream-one","stream-up"})
            assertThrows(Exception.class,()->TcpProfile.validate(GOOD.replace("packet-up",mode)));
    }
}
