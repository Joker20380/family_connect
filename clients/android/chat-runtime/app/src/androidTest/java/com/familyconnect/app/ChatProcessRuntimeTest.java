package com.familyconnect.app;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import static com.familyconnect.app.ChatLocalRuntimeTest.*;

/** Run individual methods in order with am force-stop between them; see run.py. */
@RunWith(AndroidJUnit4.class)
public class ChatProcessRuntimeTest {
    @Test public void prepare() throws Exception {
        reset();
        ChatLocalAndroid chat = ChatLocalAndroid.open(context(), true);
        JsonObject receipt = new JsonObject();
        receipt.add("profile", chat.call("profile", args()));
        JsonObject peer = peer(chat); trust(chat, peer); receipt.add("peer", peer);
        receipt.add("id", chat.call("queue", args("address", peer.get("address").getAsString(), "text", "after force-stop")));
        Files.write(new File(root(), "chat-receipt.json").toPath(), receipt.toString().getBytes(StandardCharsets.UTF_8));
        // Intentionally leave the owner open. The harness stops this app's process.
    }
    @Test public void resume() throws Exception {
        JsonObject receipt = JsonParser.parseString(new String(Files.readAllBytes(
            new File(root(), "chat-receipt.json").toPath()), StandardCharsets.UTF_8)).getAsJsonObject();
        try (ChatLocalAndroid chat = ChatLocalAndroid.open(context(), false)) {
            assertEquals(receipt.get("profile"), chat.call("profile", args()));
            JsonObject message = history(chat, receipt.getAsJsonObject("peer")).getAsJsonArray("messages").get(0).getAsJsonObject();
            assertEquals(receipt.get("id"), message.get("id"));
            assertEquals("after force-stop", message.get("text").getAsString());
            assertEquals("queued", message.get("status").getAsString());
        }
        reset();
    }
}
