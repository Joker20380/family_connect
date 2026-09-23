package com.familyconnect.app;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;
import com.google.gson.*;
import java.util.concurrent.TimeUnit;

@RunWith(AndroidJUnit4.class)
public class ServiceEventsRuntimeTest {
 @Test public void fetchesExistingAnnouncementAndKeepsReadState() throws Exception {
  String expected=InstrumentationRegistry.getArguments().getString("fcExpectedNotice","");
  assumeTrue(expected.matches("[a-f0-9]{32}"));
  android.content.Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
  ChatRuntime.WORKER.submit(()->{
   try{
    ChatLocalAndroid chat=ChatRuntime.open(context,false);
    ChatRuntime.syncEvents(context,chat,true);assertFalse("Public feed fetch failed",ChatRuntime.eventsUnavailable);
    JsonObject found=null;for(JsonElement item:chat.call("service_events",new JsonObject()).getAsJsonArray())if(item.getAsJsonObject().get("id").getAsString().equals(expected))found=item.getAsJsonObject();
    assertNotNull("Published announcement missing after immediate fetch",found);
    boolean read=found.get("read").getAsBoolean(),notified=found.get("notified").getAsBoolean();
    ChatRuntime.syncEvents(context,chat,true);assertFalse(ChatRuntime.eventsUnavailable);
    int count=0;for(JsonElement item:chat.call("service_events",new JsonObject()).getAsJsonArray())if(item.getAsJsonObject().get("id").getAsString().equals(expected)){
     count++;assertEquals(read,item.getAsJsonObject().get("read").getAsBoolean());assertEquals(notified,item.getAsJsonObject().get("notified").getAsBoolean());
    }
    assertEquals(1,count);
   }catch(Exception error){throw new AssertionError(error);}
  }).get(40,TimeUnit.SECONDS);
 }
}
