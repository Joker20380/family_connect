package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class AwgProfileTest {
    static String profile(){return "[Interface]\nPrivateKey = AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=\nAddress = 10.78.0.4/32, fd78:92::4/128\nDNS = 1.1.1.1\nJc = 3\nJmin = 40\nJmax = 80\nS1 = 17\nS2 = 29\nS3 = 3\nS4 = 9\nH1 = 1001-1010\nH2 = 2001-2010\nH3 = 3001-3010\nH4 = 4001-4010\nI1 = <b 0x11223344><r 16>\n[Peer]\nPublicKey = AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgI=\nEndpoint = 192.0.2.10:51821\nAllowedIPs = 0.0.0.0/0, ::/0\n";}
    static void reject(String p,Transport t)throws Exception{try{ProfileValidator.validate(p,t);fail("accepted invalid profile");}catch(IllegalArgumentException expected){}}
    @Test public void acceptsAwg2()throws Exception{assertTrue(ProfileValidator.validate(profile(),Transport.AWG).contains("H1 = 1001-1010"));}
    @Test public void cannotDowngradeAwgToWg()throws Exception{reject(profile(),Transport.WG);}
    @Test public void requiresAllParameters()throws Exception{for(String k:AwgParameters.REQUIRED)reject(profile().replaceAll("(?m)^"+k+" = .*\\n",""),Transport.AWG);}
    @Test public void rejectsHeaderOverlapAndOverflow()throws Exception{for(String h:new String[]{"2005","4294967296","4","10-5","x"})reject(profile().replace("1001-1010",h),Transport.AWG);}
    @Test public void rejectsBadPadding()throws Exception{reject(profile().replace("Jc = 3","Jc = 0"),Transport.AWG);reject(profile().replace("Jmax = 80","Jmax = 30"),Transport.AWG);reject(profile().replace("S1 = 17","S1 = 257"),Transport.AWG);}
    @Test public void rejectsPacketsAndHooks()throws Exception{for(String p:new String[]{"<b 0x1>","<r 1281>","<r 0>","<r 1> bad","bad"})reject(profile().replace("<b 0x11223344><r 16>",p),Transport.AWG);reject(profile()+"PostUp = command\n",Transport.AWG);}
    @Test public void rejectsDuplicatesAndSize()throws Exception{reject(profile().replace("Jc = 3","Jc = 3\nJc = 3"),Transport.AWG);reject(profile()+"#"+"x".repeat(ProfileValidator.LIMIT),Transport.AWG);}
    @Test public void unknownTransportRejected(){try{Transport.parse("tcp");fail("unimplemented transport");}catch(IllegalArgumentException expected){}}
}
