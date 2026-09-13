package com.familyconnect.app;
import org.junit.Test;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import org.amnezia.awg.config.Config;
import static org.junit.Assert.*;
public class Awg31ProfileTest {
    static final String KEY="AwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwM=";
    static String profile(){return AwgProfileTest.profile().replace("S1 = 17","S1 = 16").replace("S2 = 29","S2 = 16").replace("S3 = 3","S3 = 16").replace("S4 = 9","S4 = 16").replace("1001-1010","1").replace("2001-2010","2").replace("3001-3010","3").replace("4001-4010","4").replace("[Peer]","HeaderProtectionKey = "+KEY+"\nContentPaddingAddition = 0-32\nRandomTrailers = true\nDisableCookies = false\n[Peer]");}
    static Config parse(String p)throws Exception{return Config.parse(new ByteArrayInputStream(ProfileValidator.validate(p,Transport.AWG).getBytes(StandardCharsets.UTF_8)));}
    @Test public void serializesProtectedProfileWithoutDroppingFields()throws Exception{
        Config c=parse(profile());String ipc=c.toAwgUserspaceString();
        assertTrue(ipc.contains("header_protection_key="+"03".repeat(32)+"\n"));
        for(String line:new String[]{"content_padding_addition=0-32","random_trailers=true","disable_cookies=false","h1=1","s4=16"})assertTrue(ipc.contains(line+"\n"));
        assertEquals(ipc,Config.parse(new ByteArrayInputStream(c.toAwgQuickString().getBytes(StandardCharsets.UTF_8))).toAwgUserspaceString());
        assertNotEquals(ipc,parse(profile().replace("0-32","0-64")).toAwgUserspaceString());
        assertFalse(c.getInterface().toString().contains(KEY));
    }
    @Test public void requiresNonzeroFullKey()throws Exception{for(String k:new String[]{"bad","AAAA","AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="})AwgProfileTest.reject(profile().replace(KEY,k),Transport.AWG);}
    @Test public void enforcesHeaderProtectionNonceAndCompatibilityHeaders()throws Exception{
        for(int i=1;i<=4;i++)AwgProfileTest.reject(profile().replace("S"+i+" = 16","S"+i+" = 11"),Transport.AWG);
        AwgProfileTest.reject(profile().replace("H1 = 1","H1 = 10"),Transport.AWG);
        AwgProfileTest.reject(profile().replace("HeaderProtectionKey = "+KEY+"\n",""),Transport.AWG);
    }
    @Test public void rejectsInvalidRangesBooleansAndUnequalTrailerPrefixes()throws Exception{
        for(String s:new String[]{"32-0","65536","-1","257","0-32-64"})AwgProfileTest.reject(profile().replace("0-32",s),Transport.AWG);
        AwgProfileTest.reject(profile().replace("true","1"),Transport.AWG);
        AwgProfileTest.reject(profile().replace("S4 = 16","S4 = 17"),Transport.AWG);
    }
    @Test public void preservesTransportBoundaryAndRejectsUnsupportedTimings()throws Exception{
        AwgProfileTest.reject(profile(),Transport.WG);
        AwgProfileTest.reject(profile().replace("[Peer]","RekeyAfterTime = 60-120\n[Peer]"),Transport.AWG);
        AwgProfileTest.reject(profile().replace("HeaderProtectionKey = "+KEY,"HeaderProtectionKey = "+KEY+"\nHeaderProtectionKey = "+KEY),Transport.AWG);
    }
}
