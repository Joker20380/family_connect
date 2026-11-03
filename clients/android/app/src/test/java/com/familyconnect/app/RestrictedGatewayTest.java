package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.io.IOException;
import org.junit.Test;
import static org.junit.Assert.*;

public class RestrictedGatewayTest {
    private static final String ROOT="/friends/restricted-readiness";

    @Test public void primaryKeepsExistingNamespaceAndWireContract()throws Exception{
        for(String target:new String[]{null,"nl",RestrictedGateway.PRIMARY}){
            assertEquals(RestrictedGateway.PRIMARY,RestrictedGateway.target(target));
            assertEquals("",RestrictedGateway.namespace(target));
            JsonObject body=new JsonObject();body.addProperty("proof","fixture");
            FriendsReadinessProtocol.Transport transport=(path,request,id)->{
                assertEquals(ROOT,path);assertSame(body,request);assertEquals("correlation",id);return request;
            };
            assertSame(transport,RestrictedGateway.route(transport,target));
            assertSame(body,RestrictedGateway.route(transport,target).post(ROOT,body,"correlation"));
        }
    }

    @Test public void secondaryWrapsAllProofAndAckRequestsWithoutChangingThem()throws Exception{
        assertEquals("-nl-amsterdam-2",RestrictedGateway.namespace(RestrictedGateway.SECONDARY));
        for(String suffix:new String[]{"","/challenge","/ack-challenge","/ack"}){
            JsonObject body=new JsonObject();body.addProperty("proof","fixture");JsonObject response=new JsonObject();
            FriendsReadinessProtocol.Transport target=RestrictedGateway.route((path,request,id)->{
                assertEquals(ROOT+suffix,path);assertEquals("correlation",id);
                assertEquals(2,request.size());assertEquals(RestrictedGateway.SECONDARY,request.get("gateway_id").getAsString());
                assertSame(body,request.get("request"));
                JsonObject reply=new JsonObject();reply.addProperty("gateway_id",RestrictedGateway.SECONDARY);reply.add("response",response);return reply;
            },RestrictedGateway.SECONDARY);
            assertSame(response,target.post(ROOT+suffix,body,"correlation"));
            assertEquals(1,body.size());
        }
    }

    @Test public void unsupportedTargetsNeverCreateStoragePathsOrRequests(){
        for(String target:new String[]{"","ru","../nl-amsterdam-2","NL-AMSTERDAM-2","nl-amsterdam-3"}){
            assertThrows(IllegalArgumentException.class,()->RestrictedGateway.namespace(target));
            assertThrows(IllegalArgumentException.class,()->RestrictedGateway.route((path,body,id)->{fail("network called");return null;},target));
        }
    }

    @Test public void wrongOrLegacyResponseCannotBeImportedForSecondary()throws Exception{
        for(String returned:new String[]{null,RestrictedGateway.PRIMARY,RestrictedGateway.SECONDARY}){
            for(int shape=0;shape<3;shape++){
                JsonObject reply=new JsonObject();
                if(returned!=null)reply.addProperty("gateway_id",returned);
                if(shape==0)reply.addProperty("response","not-an-object");
                else if(shape==1){reply.add("response",new JsonObject());reply.addProperty("extra",true);}
                FriendsReadinessProtocol.Transport target=RestrictedGateway.route((path,body,id)->reply,RestrictedGateway.SECONDARY);
                assertThrows(IllegalArgumentException.class,()->target.post(ROOT,new JsonObject(),null));
            }
        }
        JsonObject wrong=new JsonObject();wrong.addProperty("gateway_id",RestrictedGateway.PRIMARY);wrong.add("response",new JsonObject());
        FriendsReadinessProtocol.Transport target=RestrictedGateway.route((path,body,id)->wrong,RestrictedGateway.SECONDARY);
        assertThrows(IllegalArgumentException.class,()->target.post(ROOT,new JsonObject(),null));
    }

    @Test public void targetSurvivesHttpsFailureAndRelaySelection()throws Exception{
        int[] calls={0,0};
        ReadinessBootstrapRoute routes=new ReadinessBootstrapRoute((path,body,id)->{
            calls[0]++;throw new IOException("synthetic unavailable");
        },(path,body,id)->{
            calls[1]++;assertEquals(RestrictedGateway.SECONDARY,body.get("gateway_id").getAsString());
            JsonObject reply=new JsonObject();reply.addProperty("gateway_id",RestrictedGateway.SECONDARY);reply.add("response",body.get("request"));return reply;
        });
        FriendsReadinessProtocol.Transport target=RestrictedGateway.route(routes::post,RestrictedGateway.SECONDARY);
        JsonObject body=new JsonObject();
        assertSame(body,target.post(ROOT+"/challenge",body,"first"));
        assertSame(body,target.post(ROOT,body,"second"));
        assertArrayEquals(new int[]{1,2},calls);
    }

    @Test public void targetAdapterDoesNotRetryOrExpandEndpointScope()throws Exception{
        int[] calls={0};IOException unavailable=new IOException("synthetic");
        FriendsReadinessProtocol.Transport target=RestrictedGateway.route((path,body,id)->{calls[0]++;throw unavailable;},RestrictedGateway.SECONDARY);
        assertSame(unavailable,assertThrows(IOException.class,()->target.post(ROOT,new JsonObject(),null)));
        assertEquals(1,calls[0]);
        assertThrows(IllegalArgumentException.class,()->target.post("/friends/activate",new JsonObject(),null));
        assertEquals(1,calls[0]);
    }
}
