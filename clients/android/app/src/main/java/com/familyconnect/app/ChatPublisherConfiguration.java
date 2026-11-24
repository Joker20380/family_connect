package com.familyconnect.app;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

final class ChatPublisherConfiguration {
    static void validate(JsonObject value, String device, String chatPublic, long now) {
        require(value != null && value.keySet().equals(new HashSet<>(Arrays.asList("schema", "device", "chat_public", "revision", "expires_at", "publishers"))));
        require(number(value.get("schema")) == 1 && text(value.get("device")).equals(device)
                && text(value.get("chat_public")).equals(chatPublic));
        long revision = number(value.get("revision")), expires = number(value.get("expires_at"));
        require(revision >= 1 && revision <= 9007199254740991L && expires > now && expires - now <= 120);
        JsonElement entries = value.get("publishers");
        require(entries.isJsonArray() && entries.getAsJsonArray().size() <= 4);
        Set<String> seen = new HashSet<>();
        for (JsonElement entry : entries.getAsJsonArray()) {
            require(entry.isJsonObject());
            JsonObject publisher = entry.getAsJsonObject();
            require(publisher.keySet().equals(new HashSet<>(Arrays.asList("role", "public_key")))
                    && text(publisher.get("role")).equals("service_publisher"));
            String key = text(publisher.get("public_key"));
            require(key.matches("[0-9a-f]{128}") && !key.equals(chatPublic) && seen.add(key));
        }
    }

    private static String text(JsonElement value) {
        require(value != null && value.isJsonPrimitive() && value.getAsJsonPrimitive().isString());
        return value.getAsString();
    }

    private static long number(JsonElement value) {
        require(value != null && value.isJsonPrimitive() && value.getAsJsonPrimitive().isNumber()
                && value.toString().matches("[0-9]{1,16}"));
        return Long.parseLong(value.toString());
    }

    private static void require(boolean condition) {
        if (!condition) throw new SecurityException("Invalid publisher configuration");
    }
}
