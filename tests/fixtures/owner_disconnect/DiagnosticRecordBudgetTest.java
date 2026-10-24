package com.familyconnect.app;

import com.google.gson.*;
import org.junit.Test;
import static org.junit.Assert.*;
import java.nio.charset.StandardCharsets;

public class DiagnosticRecordBudgetTest {
    private JsonObject record(int detailSize){
        JsonObject result=new JsonObject();
        result.addProperty("device_support_id","FC-2345-6789");
        result.addProperty("state","CONNECTED");
        result.addProperty("network_class","WIFI");
        result.addProperty("vpn_capture_open",true);
        JsonArray history=new JsonArray();
        for(int index=0;index<4;index++)history.add(session(index,detailSize));
        result.add("restricted_history",history);
        result.add("restricted_session",session(4,detailSize));
        result.add("events",details(128,80));
        return result;
    }
    private JsonArray details(int count,int width){
        JsonArray result=new JsonArray();
        for(int index=0;index<count;index++){
            JsonObject event=new JsonObject();event.addProperty("index",index);
            event.addProperty("synthetic_detail","Я".repeat(width));result.add(event);
        }
        return result;
    }
    private JsonObject session(int index,int width){
        JsonObject result=new JsonObject();
        result.addProperty("session_tag",String.format("%064x",index+1));
        result.addProperty("observed_at_ms",1000+index);
        result.addProperty("protocol_errors",77);
        result.addProperty("terminal_reason","RELIABLE_EXHAUSTED");
        result.addProperty("speed_profile","P1");result.addProperty("mux_profile","CREDIT128");
        JsonObject lifecycle=new JsonObject();
        lifecycle.add("first_failure",details(1,100).get(0));
        lifecycle.add("trace",details(index==4?192:32,width));
        result.add("lifecycle",lifecycle);
        JsonObject mux=new JsonObject();
        mux.addProperty("actual_violations",31);mux.addProperty("unclassified",14);
        mux.add("first_unknown",details(1,200).get(0));
        mux.add("incidents",details(32,width));mux.add("events",details(32,80));
        result.add("mux_lifecycle",mux);return result;
    }
    @Test public void smallRecordsRemainByteIdentical(){
        JsonObject record=record(1);String before=record.toString();
        assertTrue(DiagnosticRecordBudget.size(record)<DiagnosticRing.RECORD_LIMIT);
        assertSame(record,DiagnosticRecordBudget.apply(record));assertEquals(before,record.toString());
    }
    @Test public void aggregateBoundUsesUtf8AndKeepsEverySessionAndFirstCause()throws Exception{
        JsonObject record=record(1200),before=record.deepCopy();
        int original=DiagnosticRecordBudget.size(record);
        assertTrue(original>DiagnosticRing.RECORD_LIMIT);
        DiagnosticRecordBudget.apply(record);
        assertTrue(DiagnosticRecordBudget.size(record)<=DiagnosticRing.RECORD_LIMIT);
        JsonObject budget=record.getAsJsonObject("record_budget");
        assertEquals(original,budget.get("untrimmed_bytes").getAsInt());
        assertTrue(budget.getAsJsonObject("omitted_detail_items").size()>0);
        assertEquals(4,record.getAsJsonArray("restricted_history").size());
        for(int index=0;index<5;index++){
            JsonObject old=index==4?before.getAsJsonObject("restricted_session"):before.getAsJsonArray("restricted_history").get(index).getAsJsonObject();
            JsonObject now=index==4?record.getAsJsonObject("restricted_session"):record.getAsJsonArray("restricted_history").get(index).getAsJsonObject();
            for(String key:new String[]{"session_tag","observed_at_ms","protocol_errors","terminal_reason","speed_profile","mux_profile"})assertEquals(old.get(key),now.get(key));
            assertEquals(old.getAsJsonObject("lifecycle").get("first_failure"),now.getAsJsonObject("lifecycle").get("first_failure"));
            assertEquals(old.getAsJsonObject("mux_lifecycle").get("first_unknown"),now.getAsJsonObject("mux_lifecycle").get("first_unknown"));
            assertEquals(old.getAsJsonObject("mux_lifecycle").get("actual_violations"),now.getAsJsonObject("mux_lifecycle").get("actual_violations"));
            assertEquals(old.getAsJsonObject("mux_lifecycle").get("unclassified"),now.getAsJsonObject("mux_lifecycle").get("unclassified"));
            assertEnds(old.getAsJsonObject("lifecycle").getAsJsonArray("trace"),now.getAsJsonObject("lifecycle").getAsJsonArray("trace"));
            assertEnds(old.getAsJsonObject("mux_lifecycle").getAsJsonArray("incidents"),now.getAsJsonObject("mux_lifecycle").getAsJsonArray("incidents"));
        }
        JsonObject exported=new JsonObject();byte[] raw=record.toString().getBytes(StandardCharsets.UTF_8);
        DiagnosticRing.exportRecord(exported,"ring",raw,"FC-2345-6789");
        DiagnosticRing.exportRecord(exported,"incident",raw,"FC-2345-6789");
        assertTrue(DiagnosticRing.exportBytes(exported).length<=DiagnosticRing.EXPORT_LIMIT);
    }
    private void assertEnds(JsonArray before,JsonArray after){
        assertTrue(after.size()>=2);assertEquals(before.get(0),after.get(0));
        assertEquals(before.get(before.size()-1),after.get(after.size()-1));
    }
    @Test public void omissionCountsExactlyAccountForRetainedDetails(){
        JsonObject record=record(400),before=record.deepCopy();DiagnosticRecordBudget.apply(record);
        int original=count(before),retained=count(record),omitted=0;
        for(JsonElement value:record.getAsJsonObject("record_budget").getAsJsonObject("omitted_detail_items").asMap().values())omitted+=value.getAsInt();
        assertEquals(original-retained,omitted);
        String once=record.toString();DiagnosticRecordBudget.apply(record);assertEquals(once,record.toString());
    }
    private int count(JsonElement value){
        if(value.isJsonArray()){int count=value.getAsJsonArray().size();for(JsonElement item:value.getAsJsonArray())count+=count(item);return count;}
        if(value.isJsonObject()){int count=0;for(JsonElement item:value.getAsJsonObject().asMap().values())count+=count(item);return count;}
        return 0;
    }
    @Test public void latestStateStillUpdatesWithoutChangingRetainedInput(){
        JsonObject original=record(800);String saved=original.toString();
        JsonObject next=original.deepCopy();next.addProperty("state","DISCONNECTED");
        next.addProperty("vpn_capture_open",false);
        next.getAsJsonObject("restricted_session").addProperty("observed_at_ms",999999);
        DiagnosticRecordBudget.apply(next);
        assertEquals(saved,original.toString());assertEquals("DISCONNECTED",next.get("state").getAsString());
        assertFalse(next.get("vpn_capture_open").getAsBoolean());
        assertEquals(999999,next.getAsJsonObject("restricted_session").get("observed_at_ms").getAsInt());
    }
    @Test public void boundaryDetailAlsoParticipatesInTotalBudget(){
        JsonObject record=record(1);
        for(JsonElement element:record.getAsJsonArray("restricted_history")){
            JsonObject boundary=new JsonObject();boundary.add("events",details(64,800));
            element.getAsJsonObject().getAsJsonObject("lifecycle").add("boundaries",boundary);
        }
        JsonObject before=record.deepCopy();DiagnosticRecordBudget.apply(record);
        assertTrue(DiagnosticRecordBudget.size(record)<=DiagnosticRing.RECORD_LIMIT);
        for(int index=0;index<4;index++)assertEnds(
            before.getAsJsonArray("restricted_history").get(index).getAsJsonObject().getAsJsonObject("lifecycle").getAsJsonObject("boundaries").getAsJsonArray("events"),
            record.getAsJsonArray("restricted_history").get(index).getAsJsonObject().getAsJsonObject("lifecycle").getAsJsonObject("boundaries").getAsJsonArray("events"));
    }
    @Test public void ringSnapshotIsBoundedWithoutMutatingItsInMemoryHistory()throws Exception{
        DiagnosticRing ring=new DiagnosticRing("FC-2345-6789","synthetic",106,31);
        JsonObject large=record(1200);
        java.lang.reflect.Field current=DiagnosticRing.class.getDeclaredField("restrictedSession");current.setAccessible(true);
        current.set(ring,large.getAsJsonObject("restricted_session"));
        java.lang.reflect.Field history=DiagnosticRing.class.getDeclaredField("restrictedHistory");history.setAccessible(true);
        @SuppressWarnings("unchecked") java.util.ArrayDeque<JsonObject> retained=(java.util.ArrayDeque<JsonObject>)history.get(ring);
        for(JsonElement session:large.getAsJsonArray("restricted_history"))retained.add(session.getAsJsonObject());
        String original=large.toString();
        JsonObject first=ring.snapshot();assertTrue(DiagnosticRecordBudget.size(first)<=DiagnosticRing.RECORD_LIMIT);
        assertEquals(original,large.toString());
        ring.network("WIFI");ring.vpn(true,123456789);
        JsonObject second=ring.snapshot();assertTrue(DiagnosticRecordBudget.size(second)<=DiagnosticRing.RECORD_LIMIT);
        assertEquals("WIFI",second.get("network_class").getAsString());assertTrue(second.get("vpn_capture_open").getAsBoolean());
        assertEquals(original,large.toString());assertEquals(4,retained.size());
    }
}
