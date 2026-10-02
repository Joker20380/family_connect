package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import static com.familyconnect.app.ControlJson.*;

final class ReadinessProduct {
    interface Ack { void send(JsonObject payload)throws Exception; }
    private final RestrictedCache cache;
    private final RestrictedCache.Storage receipts;
    private final String version;
    private final int build;
    private final java.util.function.LongSupplier clock;
    String delivery="UNKNOWN";
    boolean durable;
    ReadinessProduct(RestrictedCache cache,RestrictedCache.Storage receipts,String version,int build){this(cache,receipts,version,build,()->System.currentTimeMillis()/1000);}
    ReadinessProduct(RestrictedCache cache,RestrictedCache.Storage receipts,String version,int build,java.util.function.LongSupplier clock){this.cache=cache;this.receipts=receipts;this.version=version;this.build=build;this.clock=clock;}
    ReadinessImportResult imported(byte[] raw,OwnerPrewarmReceipt attempt,long now){
        try{cache.importProduct(raw,attempt,now);return cache.evaluate(attempt,Math.max(now,clock.getAsLong()),"import",version,build);}
        catch(RestrictedCache.ImportFailure failure){return failed(attempt,failure.code,now);}
        catch(Exception | LinkageError failure){return failed(attempt,ReadinessImportResult.Code.INTERNAL_ERROR,now);}
    }
    ReadinessImportResult failed(OwnerPrewarmReceipt attempt,ReadinessImportResult.Code code,long now){return new ReadinessImportResult(attempt,code,null,now,"import",version,build);}
    ReadinessImportResult restart(long now){
        try{OwnerPrewarmReceipt attempt=cache.context();return cache.evaluate(attempt==null?new OwnerPrewarmReceipt():attempt,now,"restart",version,build);}
        catch(Exception | LinkageError failure){return new ReadinessImportResult(new OwnerPrewarmReceipt(),ReadinessImportResult.Code.PERSISTENCE_FAILED,null,now,"restart",version,build);}
    }
    private void persist(ReadinessImportResult result,String state){
        durable=false;
        try{JsonObject record=new JsonObject();record.add("payload",result.json());record.addProperty("ack_state",state);
            byte[] raw=record.toString().getBytes(StandardCharsets.UTF_8);require(raw.length<=4096);receipts.write(raw);
            require(java.util.Arrays.equals(raw,receipts.read()));durable=true;
        }catch(Exception failure){durable=false;}
    }
    void publish(ReadinessImportResult result,Ack ack){
        delivery="ACK_PENDING";persist(result,delivery);
        try{ack.send(result.json());delivery="ACK_RECEIVED";}catch(Exception | LinkageError failure){delivery="ACK_PENDING";}
        persist(result,delivery);
    }
    void record(ReadinessImportResult result){delivery="UNKNOWN";persist(result,delivery);}
}
