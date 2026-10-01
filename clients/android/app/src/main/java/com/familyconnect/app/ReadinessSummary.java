package com.familyconnect.app;

import com.google.gson.JsonObject;

final class ReadinessSummary {
    static String restricted(JsonObject value) {
        StringBuilder text=new StringBuilder();
        for(String name:new String[]{"restricted_provisioning","cache","structurally_valid","expired"}) {
            String state="UNKNOWN";
            if(value.has(name)&&value.get(name).isJsonPrimitive()) {
                String candidate=value.get(name).getAsString();
                if(candidate.matches("PRESENT|ABSENT|INVALID|UNKNOWN|YES|NO"))state=candidate;
            }
            text.append(name).append(": ").append(state).append('\n');
        }
        boolean usable=value.has("usable")&&value.get("usable").isJsonPrimitive()
            &&value.get("usable").getAsJsonPrimitive().isBoolean()&&value.get("usable").getAsBoolean();
        text.append("usable: ").append(usable).append('\n');
        for(String name:new String[]{"seeds","remaining_seconds"}) {
            long count=-1;
            try {
                if(value.has(name)&&value.get(name).getAsJsonPrimitive().isNumber())count=value.get(name).getAsLong();
            } catch(RuntimeException ignored) {}
            if(count < -3600 || count > (name.equals("seeds")?4:3600))count=-1;
            text.append(name).append(": ").append(count).append('\n');
        }
        return text.toString();
    }
}
