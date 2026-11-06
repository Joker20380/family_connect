package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

final class SubscriptionPresentation {
    interface Text { String get(String name,Object... arguments); }

    static String time(long seconds,Locale locale,ZoneId zone){
        if(seconds<0||seconds>253402300799L)throw new IllegalArgumentException("Invalid subscription time");
        return DateTimeFormatter.ofPattern("dd MMM uuuu, HH:mm:ss XXX '['VV']'",locale).format(Instant.ofEpochSecond(seconds).atZone(zone));
    }

    static String event(JsonObject notice,Text text){
        String kind=notice.get("subscription_event").getAsString();
        switch(kind){
            case "activated": case "renewed": case "confirmed": case "grace": case "expire": case "revoke":
                return text.get("subscription_event_"+kind);
            default: throw new IllegalArgumentException("Invalid subscription event");
        }
    }

    static String summary(JsonObject view,boolean online,Locale locale,ZoneId zone,long now,Text text){
        String availability=text.get(online?"subscription_refresh_unavailable":"subscription_offline");
        if(!view.has("snapshot")||view.get("snapshot").isJsonNull())return text.get("subscription_unknown")+"\n\n"+availability;
        JsonObject snapshot=view.getAsJsonObject("snapshot");
        String state=snapshot.get("effective_state").getAsString();
        switch(state){
            case "active": case "trial": case "grace": case "expired": case "revoked": break;
            default: throw new IllegalArgumentException("Invalid subscription state");
        }
        String result=text.get("subscription_last_state",text.get("subscription_state_"+state));
        long confirmed=view.get("confirmed_at").getAsLong();
        result+="\n"+text.get("subscription_checked",time(confirmed,locale,zone));
        boolean hasAccess=!snapshot.get("entitlement_until").isJsonNull();
        long until=snapshot.get(hasAccess?"entitlement_until":"paid_until").getAsLong();
        result+="\n"+text.get(hasAccess?"subscription_until":"subscription_last_until",time(until,locale,zone));
        if(now<confirmed)result+="\n"+text.get("subscription_clock");
        else if(hasAccess&&now>=until)result+="\n"+text.get("subscription_period_elapsed");
        if(state.equals("expired")||state.equals("grace"))result+="\n"+text.get("subscription_renewal_required");
        if(view.has("notice")&&!view.get("notice").isJsonNull())result+="\n"+text.get("subscription_last_event",event(view.getAsJsonObject("notice"),text));
        return result+"\n\n"+availability;
    }
}
