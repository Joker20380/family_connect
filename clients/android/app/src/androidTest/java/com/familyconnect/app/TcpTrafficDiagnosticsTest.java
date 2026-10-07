package com.familyconnect.app;
import org.junit.Test;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import static org.junit.Assert.*;

public class TcpTrafficDiagnosticsTest {
    private TcpTrafficDiagnostics.Response response(String value){return new TcpTrafficDiagnostics.Response(value.getBytes(StandardCharsets.US_ASCII));}
    @Test public void statusAndBodyFailuresAreDistinct(){
        try{response("HTTP/1.0 503 Busy\r\nContent-Length: 2\r\n\r\n/x").require("/x",true);fail();}
        catch(AssertionError failure){assertTrue(failure.getMessage().contains("assertion=status"));assertTrue(failure.getMessage().contains("STATUS_MISMATCH"));}
        try{response("HTTP/1.0 200 OK\r\nContent-Length: 2\r\n\r\n/y").require("/x",true);fail();}
        catch(AssertionError failure){assertTrue(failure.getMessage().contains("assertion=body"));assertTrue(failure.getMessage().contains("BODY_MISMATCH"));}
    }
    @Test public void truncatedResponseReportsEof(){
        assertEquals("PREMATURE_EOF",response("").category("/x",true));
        assertEquals("PREMATURE_EOF",response("HTTP/1.0 200 OK\r\nContent-Length: 2\r\n\r\n/").category("/x",true));
    }
    @Test public void successfulAssertionsRemainUnchanged(){
        response("HTTP/1.0 200 OK\r\nContent-Length: 2\r\n\r\n/x").require("/x",true);
        assertEquals("PASS",response("HTTP/1.0 200 OK\r\nContent-Length: 2\r\n\r\n/x").category("/x",true));
    }
    @Test public void primarySurvivesAllCleanupFailures()throws Throwable{
        for(Throwable primary:new Throwable[]{new IOException("traffic"),new AssertionError("traffic")}){
            Throwable cleanup=new IOException("stop"),finish=new IllegalStateException("finish");int[] calls={0};
            try{try{throw primary;}finally{TcpTrafficDiagnostics.cleanup(primary,()->{calls[0]++;throw cleanup;},()->{calls[0]++;throw finish;});}}
            catch(Throwable observed){assertSame(primary,observed);}
            assertEquals(2,calls[0]);assertArrayEquals(new Throwable[]{cleanup,finish},primary.getSuppressed());
        }
    }
    @Test public void selfAndDuplicateSuppressionCannotMaskPrimary()throws Throwable{
        Throwable primary=new IOException("traffic"),cleanup=new IOException("cleanup");
        TcpTrafficDiagnostics.cleanup(primary,()->{throw primary;},()->{throw cleanup;},()->{throw cleanup;});
        assertArrayEquals(new Throwable[]{cleanup},primary.getSuppressed());
    }
    @Test public void cleanupOnlyFailureStillFailsAndFinishes()throws Throwable{
        Throwable cleanup=new IOException("cleanup");int[] calls={0};
        try{TcpTrafficDiagnostics.cleanup(null,()->{throw cleanup;},()->{throw cleanup;},()->{calls[0]++;});fail();}
        catch(Throwable observed){assertSame(cleanup,observed);}
        assertEquals(1,calls[0]);assertEquals(0,cleanup.getSuppressed().length);
    }
    @Test public void previewsCannotExposeUnknownResponseContent(){
        byte[] bytes="HTTP/1.0 200 OK\r\nAuthorization: secret-token\r\n\r\nsecret-body".getBytes(StandardCharsets.US_ASCII);
        assertFalse(TcpTrafficDiagnostics.preview(bytes,"/x",false).contains("secret"));
        assertFalse(TcpTrafficDiagnostics.preview(bytes,"/x",true).contains("secret"));
        assertTrue(TcpTrafficDiagnostics.preview(bytes,"/x",false).length()<=80);
    }
}
