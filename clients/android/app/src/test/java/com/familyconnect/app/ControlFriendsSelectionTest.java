package com.familyconnect.app;

import java.util.Base64;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlFriendsSelectionTest {
    @Test public void sharedSelectionVectors() throws Exception {
        try(var input=getClass().getResourceAsStream("/friends-selection-v3.json")){
            assertNotNull(input);
            var fixture=ControlJson.parse(input.readAllBytes()).getAsJsonObject();
            byte[] anchor=Base64.getDecoder().decode(fixture.get("anchor").getAsString());
            String device=fixture.get("device").getAsString();
            for(var entry:fixture.getAsJsonArray("cases")){
                var sample=entry.getAsJsonObject();
                String target=sample.get("target").getAsString();
                String hash=sample.has("previous_hash")?sample.get("previous_hash").getAsString():null;
                var reply=sample.getAsJsonObject("reply");
                long floor=sample.get("floor").getAsLong();
                if(sample.get("valid").getAsBoolean()){
                    var accepted=ControlFriendsCatalog.verifySelection(reply,anchor,device,target,floor,hash);
                    assertEquals(2,accepted.profiles.size());assertTrue(accepted.profiles.containsKey(target));
                    assertFalse(accepted.profiles.containsKey("nl"));
                }else assertThrows(sample.get("name").getAsString(),Exception.class,()->ControlFriendsCatalog.verifySelection(reply,anchor,device,target,floor,hash));
                assertThrows(Exception.class,()->ControlFriendsCatalog.verify(reply.getAsJsonObject("catalog").toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),anchor,0));
            }
        }
    }
}
