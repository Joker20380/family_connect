package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class AutoPolicyTest {
 @Test public void finiteOrder(){AutoPolicy p=new AutoPolicy();assertEquals(Transport.WG,p.next());assertEquals(Transport.AWG,p.next());assertEquals(Transport.TCP,p.next());assertNull(p.next());assertNull(p.next());}
 @Test public void isolatedFailureDoesNotSwitch(){AutoPolicy p=new AutoPolicy();assertFalse(p.advance(false));assertFalse(p.advance(true));assertFalse(p.advance(false));assertTrue(p.advance(false));}
 @Test public void candidateGetsFreshBudget(){AutoPolicy p=new AutoPolicy();p.next();assertFalse(p.advance(false));p.next();assertFalse(p.advance(false));assertTrue(p.advance(false));}
 @Test public void dnsRequiresMatchingTransactionQuestionAndResponse(){byte[] q=VpnHealth.query(123,"fc-test"),r=q.clone();r[2]=(byte)0x81;r[3]=(byte)0x80;assertTrue(VpnHealth.valid(q,r,r.length));assertFalse(VpnHealth.valid(q,q,q.length));r[1]++;assertFalse(VpnHealth.valid(q,r,r.length));r[1]--;r[13]++;assertFalse(VpnHealth.valid(q,r,r.length));}
 @Test public void dnsRejectsTruncationAndServerFailure(){byte[] q=VpnHealth.query(1,"fc-test"),r=q.clone();r[2]=(byte)0x83;r[3]=(byte)0x80;assertFalse(VpnHealth.valid(q,r,r.length));r[2]=(byte)0x81;r[3]=(byte)0x82;assertFalse(VpnHealth.valid(q,r,r.length));r[3]=(byte)0x83;assertTrue(VpnHealth.valid(q,r,r.length));assertFalse(VpnHealth.valid(q,r,12));}
}
