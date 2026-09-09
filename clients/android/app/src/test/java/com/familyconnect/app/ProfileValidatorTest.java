package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;

public class ProfileValidatorTest {
    private String profile(){return "[Interface]\nPrivateKey = AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\nAddress = 10.77.0.2/32\nDNS = 1.1.1.1\n[Peer]\nPublicKey = AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=\nEndpoint = 185.251.89.19:51820\nAllowedIPs = 0.0.0.0/0, ::/0\n";}
    @Test public void acceptsFullTunnel() throws Exception {assertTrue(ProfileValidator.validate(profile()).contains("[Peer]"));}
    @Test public void rejectsExecutableHooks() throws Exception {reject(profile().replace("Address =", "PostUp = run-me\nAddress ="));}
    @Test public void rejectsSplitTunnel() throws Exception {reject(profile().replace(", ::/0",""));}
    @Test public void rejectsDuplicatePeer() throws Exception {reject(profile()+"[Peer]\nPublicKey = ignored\n");}
    private void reject(String value)throws Exception{try{ProfileValidator.validate(value);fail("accepted invalid profile");}catch(IllegalArgumentException expected){}}
}
