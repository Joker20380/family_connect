package com.familyconnect.app;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import org.junit.Test;
import static org.junit.Assert.*;

public class ChatPublisherConfigurationTest {
    private static final String DEVICE = "ab".repeat(16);
    private static final String CHAT = "cd".repeat(64);

    private JsonObject configuration() {
        JsonObject value = new JsonObject();
        value.addProperty("schema", 1);
        value.addProperty("device", DEVICE);
        value.addProperty("chat_public", CHAT);
        value.addProperty("revision", 2);
        value.addProperty("expires_at", 1100);
        JsonObject publisher = new JsonObject();
        publisher.addProperty("role", "service_publisher");
        publisher.addProperty("public_key", "ef".repeat(64));
        JsonArray entries = new JsonArray();
        entries.add(publisher);
        value.add("publishers", entries);
        return value;
    }

    @Test public void validOptionalConfigurationDoesNotBecomeSupportIdentity() {
        JsonObject value = configuration();
        String before = value.toString();
        ChatPublisherConfiguration.validate(value, DEVICE, CHAT, 1000);
        assertEquals(before, value.toString());
        value.add("publishers", new JsonArray());
        ChatPublisherConfiguration.validate(value, DEVICE, CHAT, 1000);
    }

    @Test public void recipientAndLeaseRemainBounded() {
        assertThrows(SecurityException.class, () -> ChatPublisherConfiguration.validate(configuration(), "other", CHAT, 1000));
        assertThrows(SecurityException.class, () -> ChatPublisherConfiguration.validate(configuration(), DEVICE, "other", 1000));
        for (long now : new long[]{979, 1100, 1101})
            assertThrows(SecurityException.class, () -> ChatPublisherConfiguration.validate(configuration(), DEVICE, CHAT, now));
    }

    @Test public void invalidRolesKeysDuplicatesAndQuotaFailClosed() {
        for (String kind : new String[]{"role", "key", "self", "duplicate", "quota", "extra"}) {
            JsonObject value = configuration();
            JsonArray entries = value.getAsJsonArray("publishers");
            JsonObject publisher = entries.get(0).getAsJsonObject();
            if (kind.equals("role")) publisher.addProperty("role", "support");
            if (kind.equals("key")) publisher.addProperty("public_key", "invalid");
            if (kind.equals("self")) publisher.addProperty("public_key", CHAT);
            if (kind.equals("duplicate")) entries.add(publisher.deepCopy());
            if (kind.equals("quota")) for (int index = 0; index < 4; index++) entries.add(publisher.deepCopy());
            if (kind.equals("extra")) publisher.addProperty("enabled", true);
            assertThrows(SecurityException.class, () -> ChatPublisherConfiguration.validate(value, DEVICE, CHAT, 1000));
        }
    }

    @Test public void unknownFieldsAndNumericTypesFailClosed() {
        JsonObject value = configuration();
        value.addProperty("sender_public", "ef".repeat(64));
        assertThrows(SecurityException.class, () -> ChatPublisherConfiguration.validate(value, DEVICE, CHAT, 1000));
        for (String field : new String[]{"schema", "revision", "expires_at"}) {
            JsonObject invalid = configuration();
            invalid.addProperty(field, "1");
            assertThrows(SecurityException.class, () -> ChatPublisherConfiguration.validate(invalid, DEVICE, CHAT, 1000));
            invalid.addProperty(field, true);
            assertThrows(SecurityException.class, () -> ChatPublisherConfiguration.validate(invalid, DEVICE, CHAT, 1000));
            invalid.addProperty(field, -1);
            assertThrows(SecurityException.class, () -> ChatPublisherConfiguration.validate(invalid, DEVICE, CHAT, 1000));
        }
    }
}
