package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.io.IOException;
import javax.net.ssl.SSLException;
import org.junit.Test;
import static org.junit.Assert.*;

public class ReadinessBootstrapRouteTest {
    private static final String ROOT="/friends/restricted-readiness";

    @Test public void firstChallengeSelectsRelayForWholeProofExchange()throws Exception {
        int[] calls={0,0};JsonObject body=new JsonObject();
        ReadinessBootstrapRoute route=new ReadinessBootstrapRoute((path,request,id)->{
            calls[0]++;throw new IOException("synthetic unavailable");
        },(path,request,id)->{calls[1]++;assertSame(body,request);return request;});
        assertSame(body,route.post(ROOT+"/challenge",body,"first"));
        assertSame(body,route.post(ROOT,body,"proof"));
        assertArrayEquals(new int[]{1,2},calls);
    }

    @Test public void successfulHttpsDoesNotUseRelay()throws Exception {
        ReadinessBootstrapRoute route=new ReadinessBootstrapRoute((path,body,id)->body,
            (path,body,id)->{fail("unexpected relay");return null;});
        JsonObject body=new JsonObject();
        assertSame(body,route.post(ROOT+"/challenge",body,"challenge"));
        assertSame(body,route.post(ROOT,body,"fetch"));
    }

    @Test public void ambiguousProofTimeoutIsNotReplayedOnAnotherPath()throws Exception {
        ReadinessBootstrapRoute route=new ReadinessBootstrapRoute((path,body,id)->{
            if(path.equals(ROOT))throw new IOException("response lost");return body;
        },(path,body,id)->{fail("proof must not be replayed");return null;});
        route.post(ROOT+"/challenge",new JsonObject(),"challenge");
        assertThrows(IOException.class,()->route.post(ROOT,new JsonObject(),"fetch"));
    }

    @Test public void trustAndAuthorizationFailuresNeverFallBack()throws Exception {
        for(Exception failure:new Exception[]{new SSLException("synthetic"),
                new FriendsReadinessProtocol.AuthorizationFailure(),
                new FriendsReadinessProtocol.ChallengeFailure(FriendsReadinessProtocol.ChallengeCode.CHALLENGE_UNAUTHORIZED)}) {
            ReadinessBootstrapRoute route=new ReadinessBootstrapRoute((path,body,id)->{throw failure;},
                (path,body,id)->{fail("security denial must be final");return null;});
            assertSame(failure,assertThrows(Exception.class,()->route.post(ROOT+"/challenge",new JsonObject(),"challenge")));
        }
    }

    @Test public void ackChallengeCanSelectRelayButEnrollmentCannot()throws Exception {
        ReadinessBootstrapRoute route=new ReadinessBootstrapRoute((path,body,id)->{throw new IOException();},
            (path,body,id)->body);
        JsonObject body=new JsonObject();
        assertSame(body,route.post(ROOT+"/ack-challenge",body,"challenge"));
        assertSame(body,route.post(ROOT+"/ack",body,"ack"));
        assertThrows(IllegalArgumentException.class,()->route.post("/friends/activate",body,"forbidden"));
    }
}
