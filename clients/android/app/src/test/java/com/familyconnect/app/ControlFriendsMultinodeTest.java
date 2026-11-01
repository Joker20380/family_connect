package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlFriendsMultinodeTest {
    @Test public void assignedCatalogsPreserveSchemaAndRejectLowerSequence() throws Exception {
        try (var input = getClass().getResourceAsStream("/friends-multinode-v2.json")) {
            assertNotNull(input);
            JsonObject fixture = ControlJson.parse(input.readAllBytes()).getAsJsonObject();
            byte[] anchor = Base64.getDecoder().decode(fixture.get("anchor").getAsString());
            long previous = 0;
            String ru = null;
            for (var entry : fixture.getAsJsonArray("cases")) {
                JsonObject sample = entry.getAsJsonObject();
                long sequence = sample.get("sequence").getAsLong();
                byte[] envelope = sample.getAsJsonObject("reply").getAsJsonObject("catalog")
                        .toString().getBytes(StandardCharsets.UTF_8);
                var catalog = ControlFriendsCatalog.verify(envelope, anchor, previous);
                assertEquals(sequence, catalog.sequence);
                assertEquals(2, catalog.profiles.size());
                JsonObject tcp = ControlJson.parse(catalog.profiles.get("nl")
                        .getBytes(StandardCharsets.UTF_8)).getAsJsonObject();
                assertEquals(sample.get("host").getAsString(), tcp.get("server").getAsString());
                assertTrue(catalog.awgProfiles.get("nl").contains("Endpoint = " + sample.get("host").getAsString() + ":"));
                if (ru != null) assertEquals(ru, catalog.profiles.get("ru"));
                ru = catalog.profiles.get("ru");
                assertThrows(Exception.class, () -> ControlFriendsCatalog.verify(envelope, anchor, sequence + 1));
                previous = sequence;
            }
            assertEquals(6, previous);
        }
    }
}
