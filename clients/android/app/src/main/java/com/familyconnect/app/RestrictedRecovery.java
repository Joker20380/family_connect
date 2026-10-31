package com.familyconnect.app;

import com.google.gson.JsonObject;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import static com.familyconnect.app.ConnectivityOrchestrator.Failure;

final class RestrictedRecovery {
    static boolean bootstrapRetryable(long handle,int phase,boolean cancelled,boolean denied,String snapshot) {
        if(handle<=0||phase!=3||cancelled||denied||snapshot==null)return false;
        try {
            JsonObject source=JsonParser.parseString(snapshot).getAsJsonObject().getAsJsonObject("owner_startup");
            JsonObject startup=RestrictedStartup.project(source);
            if(startup==null||!startup.has("observation"))return false;
            JsonObject observation=startup.getAsJsonObject("observation");
            if(!"NONE".equals(RestrictedTrace.text(observation,"stop_at_observation"))
                ||!RestrictedTrace.allowed(RestrictedTrace.text(observation,"context_state"),"LIVE|DEADLINE")
                ||!RestrictedTrace.text(startup,"cause").equals(RestrictedTrace.text(observation,"error_category")))return false;
            if(source.has("local_stop")){
                JsonObject stop=startup.getAsJsonObject("local_stop");
                if(stop==null||!"CLEANUP".equals(RestrictedTrace.text(stop,"source"))
                    ||!stop.has("elapsed_ms")||!observation.has("elapsed_ms")
                    ||stop.get("elapsed_ms").getAsLong()<observation.get("elapsed_ms").getAsLong())return false;
            }
            if(startup.get("attempt").getAsLong()!=handle||!startup.get("complete").getAsBoolean()
                ||!"FAILED".equals(RestrictedTrace.text(startup,"status")))return false;
            if("SEED_ADMISSION".equals(RestrictedTrace.text(startup,"stage")))
                return "STARTUP_CALLER".equals(RestrictedTrace.text(observation,"point"))
                    &&RestrictedTrace.allowed(RestrictedTrace.text(startup,"cause"),"DEADLINE|IO_DEADLINE");
            if(!"HELLO_RECEIVE".equals(RestrictedTrace.text(startup,"stage"))
                ||!"CLOSED_PIPE".equals(RestrictedTrace.text(startup,"cause"))
                ||!"FAMILY_RECEIVE".equals(RestrictedTrace.text(observation,"point"))
                ||!"LIVE".equals(RestrictedTrace.text(observation,"context_state"))
                ||!source.has("bootstrap_exchanges_dropped")||!startup.has("bootstrap_exchanges")
                ||startup.get("bootstrap_exchanges_dropped").getAsLong()!=0)return false;
            String tag=RestrictedTrace.text(observation,"bootstrap_exchange_tag");
            if(!RestrictedTrace.tag(tag))return false;
            int matches=0;
            for(JsonElement entry:startup.getAsJsonArray("bootstrap_exchanges")) {
                JsonObject exchange=entry.getAsJsonObject();
                if(!tag.equals(RestrictedTrace.text(exchange,"bootstrap_exchange_tag")))continue;
                if(!exchange.get("family_authenticated").getAsBoolean())return false;
                matches++;
            }
            return matches==1;
        } catch(RuntimeException invalid) { return false; }
    }
    static Failure failure(int phase,boolean cancelled,boolean denied,String snapshot) {
        if(denied||phase==5)return Failure.AUTH;
        if(cancelled)return Failure.CANCELLED;
        if(phase==2)return null;
        if(phase!=3||snapshot==null)return Failure.INTERNAL;
        try {
            JsonObject diagnostic=JsonParser.parseString(snapshot).getAsJsonObject()
                .getAsJsonObject("packet").getAsJsonObject("diagnostic");
            String terminal=RestrictedTrace.text(diagnostic,"terminal_reason");
            if("FAMILY_REJECTED".equals(terminal))return Failure.AUTH;
            if("CANCELLED".equals(terminal))return Failure.CANCELLED;
            if(!RestrictedTrace.allowed(terminal,"RELIABLE_EXHAUSTED|IO_CLOSED|EOF"))return Failure.INTERNAL;
            String reliable=RestrictedTrace.text(diagnostic,"reliable_terminal");
            if(!RestrictedTrace.allowed(reliable,"recovery_exhausted|carrier_closed"))return Failure.INTERNAL;
            String tag=RestrictedTrace.text(diagnostic,"session_tag");
            if(!"VALID".equals(RestrictedTrace.text(diagnostic,"correlation_status")))return Failure.INTERNAL;
            JsonObject lifecycle=RestrictedTrace.project(diagnostic.get("lifecycle"),tag);
            if(lifecycle==null||!lifecycle.has("first_failure"))return Failure.INTERNAL;
            JsonObject first=lifecycle.getAsJsonObject("first_failure");
            if("recovery_exhausted".equals(reliable)&&"CARRIER".equals(RestrictedTrace.text(first,"stage"))
                &&"FAILED".equals(RestrictedTrace.text(first,"state"))
                &&"RELIABLE_RETRY_EXHAUSTED".equals(RestrictedTrace.text(first,"reason")))return Failure.NETWORK;
            if(!"carrier_closed".equals(reliable)||!lifecycle.has("first_close"))return Failure.INTERNAL;
            JsonObject close=lifecycle.getAsJsonObject("first_close");
            String source=RestrictedTrace.text(close,"close_source");
            if("WEBSOCKET".equals(RestrictedTrace.text(first,"stage"))
                &&"CLOSED".equals(RestrictedTrace.text(first,"state"))
                &&"SIGNAL_WS_CLOSE".equals(RestrictedTrace.text(first,"reason"))
                &&RestrictedTrace.allowed(source,"SIGNAL_READ|SIGNAL_WRITE")
                &&RestrictedTrace.allowed(RestrictedTrace.text(first,"close_reason"),"READ_ERROR|READ_TIMEOUT|WRITE_ERROR|timeout|restart|shutdown")
                &&(!first.has("close_code")||RestrictedTrace.allowed(first.get("close_code").getAsString(),"1000|1001|1006|1011|1012|1013")))return Failure.NETWORK;
            if("ICE".equals(RestrictedTrace.text(first,"stage"))
                &&RestrictedTrace.allowed(RestrictedTrace.text(first,"reason"),"ICE_FAILED|ICE_DISCONNECTED")
                &&RestrictedTrace.allowed(source,"SUBSCRIBER_DISCONNECTED|PUBLISHER_DISCONNECTED"))return Failure.NETWORK;
            if("FAMILY_CREDENTIAL_EXPIRY".equals(source)
                &&"FAMILY_TLS".equals(RestrictedTrace.text(first,"stage")))return Failure.NETWORK;
        } catch(RuntimeException invalid) {}
        return Failure.INTERNAL;
    }
}
