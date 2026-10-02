package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.junit.Test;
import static org.junit.Assert.*;

public class ReadinessProductTest {
    static class Memory implements RestrictedCache.Storage {
        byte[] raw;boolean fail,corrupt;
        public byte[] read(){return raw==null?null:raw.clone();}
        public void write(byte[] next)throws Exception{if(fail)throw new java.io.IOException("SECRET_PRIVATE_KEY");raw=corrupt?new byte[]{123,125}:next.clone();}
    }
    static byte[] response(long issued,long expiry){
        JsonObject value=new JsonObject();value.addProperty("issued_at",issued);value.addProperty("expires_at",expiry);value.addProperty("revision",2);value.addProperty("minimum_crl",3);
        value.addProperty("challenge","PROOF_SENTINEL");value.addProperty("certificate","CERTIFICATE_SECRET");
        JsonObject issuer=new JsonObject();issuer.addProperty("payload",Base64.getEncoder().encodeToString("{\"sequence\":2}".getBytes(StandardCharsets.UTF_8)));value.add("issuer",issuer);
        JsonObject directory=new JsonObject();directory.addProperty("issued_at",java.time.Instant.ofEpochSecond(issued).toString());directory.addProperty("join_url","https://SECRET_ROOM.invalid");value.add("directory",directory);
        return value.toString().getBytes(StandardCharsets.UTF_8);
    }
    static RestrictedCache cache(Memory memory){return new RestrictedCache(memory,raw->true);}
    static ReadinessProduct product(RestrictedCache cache,Memory receipts){return new ReadinessProduct(cache,receipts,"0.1.18-canary55-receipt",55,()->0);}
    @Test public void readyOnlyAfterReadbackAndSameOrchestratorPredicate()throws Exception{
        Memory vault=new Memory(),receipts=new Memory();RestrictedCache cache=cache(vault);ReadinessProduct product=product(cache,receipts);
        OwnerPrewarmReceipt attempt=new OwnerPrewarmReceipt();ReadinessImportResult result=product.imported(response(1000,2000),attempt,1100);
        assertEquals(ReadinessImportResult.Code.READY,result.code());assertNotNull(cache.usable());
        product.publish(result,payload->{assertNotNull(receipts.read());assertTrue(payload.get("orchestrator_usable").getAsBoolean());});
        assertTrue(product.durable);assertEquals("ACK_RECEIVED",product.delivery);
        assertEquals(attempt.challengeId,cache(vault).context().challengeId);
    }
    @Test public void nativeAndBootstrapFailureNeverImport()throws Exception{
        for(ReadinessImportResult.Code code:new ReadinessImportResult.Code[]{ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED,ReadinessImportResult.Code.BOOTSTRAP_VALIDATION_FAILED}){
            Memory vault=new Memory();ReadinessProduct product=product(RestrictedCache.detailed(vault,raw->code),new Memory());
            assertEquals(code,product.imported(response(1000,2000),new OwnerPrewarmReceipt(),1100).code());assertNull(vault.raw);
        }
    }
    @Test public void atomicFailurePreservesPreviousBundle()throws Exception{
        Memory vault=new Memory();RestrictedCache cache=cache(vault);cache.importProduct(response(1000,2000),new OwnerPrewarmReceipt(),1100);byte[] before=vault.read();vault.fail=true;
        assertEquals(ReadinessImportResult.Code.ATOMIC_IMPORT_FAILED,product(cache,new Memory()).imported(response(1001,2001),new OwnerPrewarmReceipt(),1100).code());
        assertArrayEquals(before,vault.read());assertNotNull(cache(vault).usable());
    }
    @Test public void persistenceReadbackMustMatch()throws Exception{
        Memory vault=new Memory();vault.corrupt=true;
        assertEquals(ReadinessImportResult.Code.PERSISTENCE_FAILED,product(cache(vault),new Memory()).imported(response(1000,2000),new OwnerPrewarmReceipt(),1100).code());
    }
    @Test public void receiptAndAckFailureCannotInvalidateBundle()throws Exception{
        for(boolean diskFailure:new boolean[]{false,true}){
            Memory vault=new Memory(),receipt=new Memory();receipt.fail=diskFailure;RestrictedCache cache=cache(vault);ReadinessProduct product=product(cache,receipt);
            ReadinessImportResult result=product.imported(response(1000,2000),new OwnerPrewarmReceipt(),1100);
            product.publish(result,payload->{throw new java.io.IOException("OAUTH_SECRET");});
            assertEquals(ReadinessImportResult.Code.READY,result.code());assertNotNull(cache(vault).usable());assertEquals("ACK_PENDING",product.delivery);assertEquals(!diskFailure,product.durable);
        }
    }
    @Test public void restartRevalidatesActualBundleNotReceipt()throws Exception{
        Memory vault=new Memory(),receipt=new Memory();ReadinessProduct original=product(cache(vault),receipt);
        original.publish(original.imported(response(1000,2000),new OwnerPrewarmReceipt(),1100),payload->{});
        int[] validations={0};RestrictedCache restarted=RestrictedCache.detailed(vault,raw->{validations[0]++;return ReadinessImportResult.Code.READY;});
        ReadinessImportResult result=product(restarted,receipt).restart(1200);
        assertEquals(ReadinessImportResult.Code.READY,result.code());assertTrue(validations[0]>=2);assertEquals("restart",result.json().get("phase").getAsString());
        assertEquals(ReadinessImportResult.Code.EXPIRED_ON_IMPORT,product(restarted,receipt).restart(2000).code());
        assertEquals(ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED,product(RestrictedCache.detailed(vault,raw->ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED),receipt).restart(1200).code());
        restarted.denied();assertEquals(ReadinessImportResult.Code.AUTHORIZATION_REJECTED,product(restarted,receipt).restart(1200).code());
    }
    @Test public void staleAndExpiredCannotBecomeReady()throws Exception{
        Memory vault=new Memory();ReadinessProduct product=product(cache(vault),new Memory());
        assertEquals(ReadinessImportResult.Code.READY,product.imported(response(1000,2000),new OwnerPrewarmReceipt(),1100).code());
        assertEquals(ReadinessImportResult.Code.STALE_STATE,product.imported(response(999,2000),new OwnerPrewarmReceipt(),1100).code());
        assertEquals(ReadinessImportResult.Code.EXPIRED_ON_IMPORT,product.imported(response(1001,1100),new OwnerPrewarmReceipt(),1100).code());
    }
    @Test public void unavailableUiHasNoRoleAndReceiptsContainOnlyAllowlist()throws Exception{
        Memory vault=new Memory(),receipt=new Memory();ReadinessProduct product=product(cache(vault),receipt);
        for(ReadinessImportResult.Code code:ReadinessImportResult.Code.values()){
            ReadinessImportResult result=code==ReadinessImportResult.Code.READY?product.imported(response(1000,2000),new OwnerPrewarmReceipt(),1100):product.failed(new OwnerPrewarmReceipt(),code,1100);
            product.publish(result,payload->ReadinessImportResult.validate(payload));
            String raw=new String(receipt.read(),StandardCharsets.UTF_8);
            for(String secret:new String[]{"SECRET","PROOF_SENTINEL","join_url","certificate","private_key","public_identity","oauth","https://"})assertFalse(raw.contains(secret));
        }
    }
    @Test public void noReadyWhenConsumerRevalidationFails()throws Exception{
        Memory vault=new Memory();int[] count={0};
        RestrictedCache cache=RestrictedCache.detailed(vault,raw->++count[0]<4?ReadinessImportResult.Code.READY:ReadinessImportResult.Code.NATIVE_VALIDATION_FAILED);
        assertEquals(ReadinessImportResult.Code.ORCHESTRATOR_NOT_USABLE,product(cache,new Memory()).imported(response(1000,2000),new OwnerPrewarmReceipt(),1100).code());
    }
    @Test public void expirationDuringImportCannotEmitReady()throws Exception{
        Memory vault=new Memory();ReadinessProduct product=new ReadinessProduct(cache(vault),new Memory(),"test",55,()->2000);
        assertEquals(ReadinessImportResult.Code.EXPIRED_ON_IMPORT,product.imported(response(1000,2000),new OwnerPrewarmReceipt(),1100).code());
    }
}
