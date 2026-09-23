package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class ServerLoadTest {
    private static final String JSON="{\"schema\":1,\"gateways\":{\"nl\":{\"country\":\"nl\",\"observed_at\":1000,\"cpu_percent\":30,\"rx_mbps\":900,\"tx_mbps\":100,\"capacity_mbps\":200,\"capacity_direction\":\"egress\",\"capacity_basis\":\"provider-default-estimate\"}}}";
    @Test public void egressEstimate(){ServerLoad s=ServerLoad.parse(JSON,"nl",1010);assertEquals(50,s.percent,0);assertTrue(s.estimated);}
    @Test public void unknownCapacity(){assertNull(ServerLoad.parse(JSON.replace("\"capacity_mbps\":200","\"capacity_mbps\":null"),"nl",1010).percent);}
    @Test public void staleAndWrongServer(){for(String country:new String[]{"ru","xx"}){try{ServerLoad.parse(JSON,country,1010);fail();}catch(RuntimeException expected){}}for(double now:new double[]{1046,980}){try{ServerLoad.parse(JSON,"nl",now);fail();}catch(RuntimeException expected){}}}
}
