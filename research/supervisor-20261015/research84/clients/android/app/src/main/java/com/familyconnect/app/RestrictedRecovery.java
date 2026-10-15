package com.familyconnect.app;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import static com.familyconnect.app.ConnectivityOrchestrator.Failure;

final class RestrictedRecovery {
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
            if(!"recovery_exhausted".equals(RestrictedTrace.text(diagnostic,"reliable_terminal")))return Failure.INTERNAL;
            String tag=RestrictedTrace.text(diagnostic,"session_tag");
            if(!"VALID".equals(RestrictedTrace.text(diagnostic,"correlation_status")))return Failure.INTERNAL;
            JsonObject lifecycle=RestrictedTrace.project(diagnostic.get("lifecycle"),tag);
            if(lifecycle==null||!lifecycle.has("first_failure"))return Failure.INTERNAL;
            JsonObject first=lifecycle.getAsJsonObject("first_failure");
            if("CARRIER".equals(RestrictedTrace.text(first,"stage"))
                &&"FAILED".equals(RestrictedTrace.text(first,"state"))
                &&"RELIABLE_RETRY_EXHAUSTED".equals(RestrictedTrace.text(first,"reason")))return Failure.NETWORK;
        } catch(RuntimeException invalid) {}
        return Failure.INTERNAL;
    }
}
