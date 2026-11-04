package com.familyconnect.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class ServerLoadTest {
    private static final String JSON="{\"schema\":1,\"gateways\":{\"nl\":{\"country\":\"nl\",\"observed_at\":1000,\"cpu_percent\":30,\"rx_mbps\":900,\"tx_mbps\":100,\"capacity_mbps\":200,\"capacity_direction\":\"egress\",\"capacity_basis\":\"provider-default-estimate\"}}}";
    @Test public void egressEstimate(){ServerLoad s=ServerLoad.parse(JSON,"nl",1010);assertEquals(50,s.percent,0);assertTrue(s.estimated);}
    @Test public void unknownCapacity(){assertNull(ServerLoad.parse(JSON.replace("\"capacity_mbps\":200","\"capacity_mbps\":null"),"nl",1010).percent);}
    @Test public void staleAndWrongServer(){for(String country:new String[]{"ru","xx"}){try{ServerLoad.parse(JSON,country,1010);fail();}catch(RuntimeException expected){}}for(double now:new double[]{1046,980}){try{ServerLoad.parse(JSON,"nl",now);fail();}catch(RuntimeException expected){}}}
    private String nodes(){
        com.google.gson.JsonObject root=com.google.gson.JsonParser.parseString(JSON).getAsJsonObject();
        com.google.gson.JsonObject nodes=new com.google.gson.JsonObject();
        for(int index=1;index<=2;index++){
            String target="nl-amsterdam-"+index;
            com.google.gson.JsonObject node=root.getAsJsonObject("gateways").getAsJsonObject("nl").deepCopy();
            node.addProperty("gateway_id",target);node.addProperty("cpu_percent",index*40);
            nodes.add(target,node);
        }
        root.add("nodes",nodes);return root.toString();
    }
    @Test public void explicitNodesHaveIndependentLoadAndIdentity(){
        assertEquals(50,ServerLoad.parse(nodes(),"nl-amsterdam-1",1010).percent,0);
        ServerLoad secondary=ServerLoad.parse(nodes(),"nl-amsterdam-2",1010);
        assertEquals(80,secondary.percent,0);assertEquals("nl-amsterdam-2",secondary.country);
    }
    @Test public void countryAggregateNeverSubstitutesForMissingNode(){
        assertFalse(ServerLoad.parseAll(JSON,1010).containsKey("nl-amsterdam-1"));
        assertFalse(ServerLoad.parseAll(JSON,1010).containsKey("nl-amsterdam-2"));
    }
    @Test public void wrongBindingStaleAndMalformedNodesAreIsolated(){
        for(String mutation:new String[]{"wrong-id","stale","country","malformed","missing-id"}){
            com.google.gson.JsonObject root=com.google.gson.JsonParser.parseString(nodes()).getAsJsonObject();
            com.google.gson.JsonObject node=root.getAsJsonObject("nodes").getAsJsonObject("nl-amsterdam-2");
            if(mutation.equals("wrong-id"))node.addProperty("gateway_id","nl-amsterdam-1");
            if(mutation.equals("stale"))node.addProperty("observed_at",900);
            if(mutation.equals("country"))node.addProperty("country","ru");
            if(mutation.equals("malformed"))node.add("cpu_percent",new com.google.gson.JsonArray());
            if(mutation.equals("missing-id"))node.remove("gateway_id");
            java.util.Map<String,ServerLoad> result=ServerLoad.parseAll(root.toString(),1010);
            assertTrue(result.containsKey("nl-amsterdam-1"));assertTrue(result.containsKey("nl"));
            assertFalse(mutation,result.containsKey("nl-amsterdam-2"));
        }
    }
}
