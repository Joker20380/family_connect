package com.familyconnect.app;

import com.google.gson.*;

final class RestrictedHealthPolicy {
    static final long MAX_SAMPLE_GAP_MS=45000;
    static final class Sample {
        final String session;
        final long received,sent,at;
        Sample(String session,long received,long sent,long at){this.session=session;this.received=received;this.sent=sent;this.at=at;}
    }
    static final class Decision {
        final boolean progress,recover;
        final int failures;
        Decision(boolean progress,boolean recover,int failures){this.progress=progress;this.recover=recover;this.failures=failures;}
    }
    private Sample previous;
    private int failures;
    void begin(Sample sample){if(previous==null)previous=sample;}
    Decision observe(boolean probe,Sample current){
        boolean progress=current!=null&&previous!=null&&current.session.equals(previous.session)
            &&current.at>previous.at&&current.at-previous.at<=MAX_SAMPLE_GAP_MS
            &&current.received>previous.received&&current.sent>previous.sent;
        previous=current;
        failures=probe||progress?0:Math.min(3,failures+1);
        return new Decision(progress,failures>=3,failures);
    }
    static Sample sample(String raw,long now,boolean denied){
        if(denied||raw==null||raw.length()>524288)return null;
        try{
            JsonObject root=JsonParser.parseString(raw).getAsJsonObject();
            if(root.get("state").getAsInt()!=2)return null;
            JsonObject diagnostic=root.getAsJsonObject("packet").getAsJsonObject("diagnostic");
            if(!"NONE".equals(diagnostic.get("terminal_reason").getAsString()))return null;
            String tag=diagnostic.get("session_tag").getAsString();
            if(!tag.matches("[0-9a-f]{64}"))return null;
            long received=diagnostic.get("received_bytes").getAsBigDecimal().longValueExact();
            long sent=diagnostic.get("sent_bytes").getAsBigDecimal().longValueExact();
            if(received<0||sent<0||now<0)return null;
            return new Sample(tag,received,sent,now);
        }catch(RuntimeException invalid){return null;}
    }
}
