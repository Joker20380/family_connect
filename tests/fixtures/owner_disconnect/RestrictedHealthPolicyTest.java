package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedHealthPolicyTest {
    private static final String SESSION="a".repeat(64);
    private RestrictedHealthPolicy.Sample sample(long bytes,long at){return new RestrictedHealthPolicy.Sample(SESSION,bytes,bytes,at);}
    @Test public void failedProbeMustNotTearDownFreshBidirectionalApplicationProgress(){
        RestrictedHealthPolicy policy=new RestrictedHealthPolicy();policy.begin(sample(100,0));
        for(int index=1;index<=3;index++){
            RestrictedHealthPolicy.Decision decision=policy.observe(false,sample(100+index*100,35000L*index));
            assertTrue(decision.progress);assertFalse(decision.recover);
        }
    }
    @Test public void threeFailedProbesWithoutProgressStillRecover(){
        RestrictedHealthPolicy policy=new RestrictedHealthPolicy();policy.begin(sample(100,0));
        assertFalse(policy.observe(false,sample(100,35000)).recover);
        assertFalse(policy.observe(false,sample(100,70000)).recover);
        assertTrue(policy.observe(false,sample(100,105000)).recover);
    }
    @Test public void transmitAloneIsNotDelivery(){
        RestrictedHealthPolicy policy=new RestrictedHealthPolicy();policy.begin(sample(100,0));
        for(int index=1;index<=3;index++){
            RestrictedHealthPolicy.Decision decision=policy.observe(false,new RestrictedHealthPolicy.Sample(SESSION,100,100+index,35000L*index));
            assertFalse(decision.progress);assertEquals(index==3,decision.recover);
        }
    }
    @Test public void lateSampleOrNewSessionCannotSupplyProgress(){
        for(RestrictedHealthPolicy.Sample next:new RestrictedHealthPolicy.Sample[]{sample(200,45001),sample(200,0),sample(200,-1),sample(90,1),new RestrictedHealthPolicy.Sample("b".repeat(64),200,200,1),null}){
            RestrictedHealthPolicy policy=new RestrictedHealthPolicy();policy.begin(sample(100,0));
            assertFalse(policy.observe(false,next).progress);
        }
    }
    @Test public void severalRecoveryGenerationsHaveIndependentFailureBudget(){
        for(int cycle=0;cycle<5;cycle++){
            RestrictedHealthPolicy policy=new RestrictedHealthPolicy();policy.begin(sample(100,0));
            assertFalse(policy.observe(false,null).recover);assertFalse(policy.observe(false,null).recover);
            assertTrue(policy.observe(false,null).recover);
            assertFalse(policy.observe(true,sample(100,105000)).recover);
            assertFalse(policy.observe(false,sample(100,140000)).recover);
        }
    }
    @Test public void parsesOnlyActiveAuthorizedDataCounters(){
        String raw="{\"state\":2,\"packet\":{\"diagnostic\":{\"terminal_reason\":\"NONE\",\"session_tag\":\""+SESSION+"\",\"sent_bytes\":100,\"received_bytes\":200}}}";
        assertNotNull(RestrictedHealthPolicy.sample(raw,10,false));
        assertNull(RestrictedHealthPolicy.sample(raw,10,true));
        assertNull(RestrictedHealthPolicy.sample(raw.replace("\"state\":2","\"state\":3"),10,false));
        assertNull(RestrictedHealthPolicy.sample(raw.replace("NONE","IO_CLOSED"),10,false));
        assertNull(RestrictedHealthPolicy.sample(raw.replace("200","-1"),10,false));
        assertNull(RestrictedHealthPolicy.sample(raw.replace("200","1.5"),10,false));
        assertNull(RestrictedHealthPolicy.sample("{}",10,false));
    }
    @Test public void failedProbeRemainsVisibleWhenProgressPreventsRestart(){
        DiagnosticRing ring=new DiagnosticRing(null,"test",102,31);
        ring.dns(false,1);ring.dnsProgress(2);
        JsonArray events=ring.snapshot().getAsJsonArray("events");
        assertEquals("DNS_PROBE_FAILED",events.get(0).getAsJsonObject().get("reason_code").getAsString());
        assertEquals("DNS_TRAFFIC_PROGRESS",events.get(1).getAsJsonObject().get("reason_code").getAsString());
    }
}
