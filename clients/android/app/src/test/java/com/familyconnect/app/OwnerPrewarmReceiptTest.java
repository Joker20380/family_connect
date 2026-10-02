package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import org.junit.Test;
import static org.junit.Assert.*;

public class OwnerPrewarmReceiptTest {
    private byte[] response(){return ("{\"revision\":2,\"expires_at\":1800000000,\"private_key\":\"secret-sentinel\",\"join_url\":\"secret-room\"}").getBytes(StandardCharsets.UTF_8);}
    @Test public void successfulProductStagesExposeOnlySafeMetadata()throws Exception{
        OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
        assertTrue(receipt.challengeId.matches("[a-f0-9]{32}"));assertNotEquals(receipt.challengeId,receipt.fetchId);
        receipt.challengeIssued();receipt.fetchAuthorized();receipt.imported(response());
        JsonObject value=ControlJson.parse(receipt.summary().getBytes(StandardCharsets.UTF_8)).getAsJsonObject();
        assertEquals("real_owner_product",value.get("receipt_class").getAsString());
        assertEquals("issued",value.get("challenge_result").getAsString());
        assertEquals("authorized",value.get("fetch_result").getAsString());
        assertEquals("accepted",value.get("import_result").getAsString());
        assertEquals(2,value.get("revision").getAsLong());assertEquals(9,value.size());
        assertFalse(receipt.summary().contains("secret"));assertFalse(receipt.summary().contains("private_key"));
    }
    @Test public void cannotSignOrFetchIsNotImportSuccess(){
        OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();receipt.challengeIssued();receipt.failed();
        assertTrue(receipt.summary().contains("\"fetch_result\":\"failed\""));
        assertFalse(receipt.summary().contains("\"accepted\""));
    }
    @Test public void rejectedImportNeverClaimsReadiness(){
        OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();receipt.challengeIssued();receipt.fetchAuthorized();receipt.failed();
        assertTrue(receipt.summary().contains("\"import_result\":\"failed\""));
    }
    @Test public void missingChallengeIsFailure(){
        OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();receipt.failed();
        assertTrue(receipt.summary().contains("\"challenge_result\":\"failed\""));
    }
    @Test public void cannotReportImportBeforeProductProtocol()throws Exception{
        OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
        try{receipt.imported(response());fail();}catch(IllegalArgumentException expected){}
        assertFalse(receipt.summary().contains("\"accepted\""));
    }
    @Test public void malformedMetadataCannotBecomeDiagnostics()throws Exception{
        OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();receipt.challengeIssued();receipt.fetchAuthorized();
        try{receipt.imported("{\"revision\":\"secret-sentinel\"}".getBytes(StandardCharsets.UTF_8));fail();}catch(IllegalArgumentException expected){}
        receipt.failed();assertFalse(receipt.summary().contains("secret"));
    }
}
