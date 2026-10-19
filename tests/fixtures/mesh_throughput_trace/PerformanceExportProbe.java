package com.familyconnect.app;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

public final class PerformanceExportProbe {
    public static void main(String[] arguments)throws Exception{
        JsonObject nativeSnapshot=JsonParser.parseString(Files.readString(Path.of(arguments[0]))).getAsJsonObject();
        JsonObject diagnostic=nativeSnapshot.getAsJsonObject("packet").getAsJsonObject("diagnostic");
        JsonObject original=diagnostic.getAsJsonObject("restricted_performance_v1");
        original.addProperty("secret","MUST_NOT_EXPORT");
        original.getAsJsonObject("Trace").getAsJsonArray("points").get(0).getAsJsonObject().addProperty("payload","MUST_NOT_EXPORT");
        DiagnosticRing ring=new DiagnosticRing(null,"trace-probe",89,35);
        ring.restricted(diagnostic,2,false,1);
        JsonObject export=new JsonObject();export.add("ring",ring.snapshot());
        byte[] exported=DiagnosticRing.exportBytes(export);
        if(new String(exported,StandardCharsets.UTF_8).contains("MUST_NOT_EXPORT"))throw new AssertionError("unsafe projection");
        JsonObject safe=ring.snapshot().getAsJsonObject("restricted_session").getAsJsonObject("restricted_performance_v1");
        if(safe==null||safe.getAsJsonObject("Trace").getAsJsonArray("points").size()==0)throw new AssertionError("empty export");
        List<String> chunks=new ArrayList<>();PerformanceTrace.chunks(diagnostic.get("session_tag").getAsString(),safe,chunks::add);
        for(String chunk:chunks)if(chunk.length()>3200)throw new AssertionError("chunk size");
        Files.write(Path.of(arguments[1]),exported);
        Files.write(Path.of(arguments[2]),chunks,StandardCharsets.UTF_8);
        JsonObject invalid=original.deepCopy();invalid.getAsJsonObject("Trace").addProperty("count",-1);
        if(PerformanceTrace.project(invalid)!=null)throw new AssertionError("negative count accepted");
        JsonObject full=diagnostic.deepCopy();JsonObject trace=full.getAsJsonObject("restricted_performance_v1").getAsJsonObject("Trace");
        JsonObject largest=null;for(JsonElement item:trace.getAsJsonArray("points"))if(largest==null||item.toString().length()>largest.toString().length())largest=item.getAsJsonObject();
        JsonArray points=new JsonArray();for(int index=1;index<=512;index++){
            JsonObject point=largest.deepCopy();point.addProperty("i",index);point.addProperty("seq",new java.math.BigInteger("18446744073709551615"));points.add(point);
        }
        trace.add("points",points);trace.addProperty("count",512);trace.addProperty("overwritten",0);
        for(int index=1;index<=6;index++){
            full.addProperty("session_tag",String.format("%064x",index));ring.restricted(full,2,false,index+1);
        }
        byte[] fullRecord=ring.snapshot().toString().getBytes(StandardCharsets.UTF_8);
        if(fullRecord.length>DiagnosticRing.RECORD_LIMIT)throw new AssertionError("full ring exceeds persisted record");
        JsonObject fullExport=new JsonObject();fullExport.add("ring",ring.snapshot());fullExport.add("incident",ring.snapshot());
        byte[] fullExported=DiagnosticRing.exportBytes(fullExport);
        System.out.println("PASS_JNI_SHAPE_ANDROID_RING_EXPORT_CHUNKS " + chunks.size()+" chunks "+exported.length+" bytes; bounded_record="+fullRecord.length+" bounded_export="+fullExported.length);
    }
}
