package com.familyconnect.app;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

final class SpeedReceipt {
    static void project(JsonObject source,JsonObject safe) {
        JsonElement profile=source.get("speed_profile"),mux=source.get("mux_profile");
        if(profile!=null&&profile.isJsonPrimitive()&&profile.getAsJsonPrimitive().isString()) {
            String value=profile.getAsString();
            if(value.equals("P0")||value.equals("P1")||value.equals("P2"))safe.addProperty("speed_profile",value);
        }
        if(mux!=null&&mux.isJsonPrimitive()&&mux.getAsJsonPrimitive().isString()) {
            String value=mux.getAsString();
            long window=number(source,"mux_window",131072);
            if(value.equals("LEGACY64")&&window==65536||value.equals("CREDIT128")&&window==131072) {
                safe.addProperty("mux_profile",value);safe.addProperty("mux_window",window);
            }
        }
        JsonElement raw=source.get("reliable_limits");
        if(raw!=null&&raw.isJsonObject()) {
            JsonObject limits=raw.getAsJsonObject(),receipt=new JsonObject();
            long send=number(limits,"local_send",32),receive=number(limits,"local_receive",32),peer=number(limits,"peer_receive",32),effective=number(limits,"effective_send",32);
            JsonElement completion=limits.get("local_write_completion");
            if(send>0&&receive>0&&peer>=0&&effective==Math.min(send,peer)&&completion!=null&&completion.isJsonPrimitive()&&completion.getAsJsonPrimitive().isBoolean()) {
                receipt.addProperty("local_send",send);receipt.addProperty("local_receive",receive);receipt.addProperty("peer_receive",peer);receipt.addProperty("effective_send",effective);
                receipt.addProperty("local_write_completion",completion.getAsBoolean());safe.add("reliable_limits",receipt);
            }
        }
        long retry=number(source,"retry_bytes",9007199254740991L);
        if(retry>=0)safe.addProperty("retry_bytes",retry);
    }
    private static long number(JsonObject source,String field,long maximum) {
        JsonElement value=source.get(field);
        if(value!=null&&value.isJsonPrimitive()&&value.getAsJsonPrimitive().isNumber()) {
            try {long count=value.getAsBigDecimal().longValueExact();if(count>=0&&count<=maximum)return count;}catch(ArithmeticException|NumberFormatException ignored){}
        }
        return -1;
    }
}
