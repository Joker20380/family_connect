package com.familyconnect.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.os.SystemClock;
import android.widget.LinearLayout;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry;
import androidx.test.runner.lifecycle.Stage;
import com.google.gson.*;
import java.io.*;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import static org.junit.Assert.*;

public class VoiceBubbleRuntimeTest {
    @org.junit.Before public void friendsVariantOnly(){
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName().endsWith(".friends"));
    }
    @Test public void voiceBubblePlaybackPauseSeekAndRender() throws Exception {
        var ins=InstrumentationRegistry.getInstrumentation();var c=ins.getTargetContext();
        try(android.os.ParcelFileDescriptor command=ins.getUiAutomation().executeShellCommand("am start -W -n "+c.getPackageName()+"/com.familyconnect.app.FriendsActivity")){
            try(InputStream input=new FileInputStream(command.getFileDescriptor())){while(input.read()!=-1){}}
        }
        AtomicReference<Activity> activity=new AtomicReference<>();
        long until=SystemClock.elapsedRealtime()+10000;
        while(activity.get()==null&&SystemClock.elapsedRealtime()<until){
            ins.runOnMainSync(()->{for(Activity a:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED))activity.set(a);});
            if(activity.get()==null)SystemClock.sleep(100);
        }
        assertNotNull(activity.get());
        byte[] sample;
        try(InputStream in=ins.getContext().getAssets().open("voice-tone.opus");ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buffer=new byte[4096];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);sample=out.toByteArray();
        }
        ChatAudio audio=new ChatAudio(c);AtomicReference<ChatThreadView> view=new AtomicReference<>();
        try {
            ins.runOnMainSync(()->{
                try {
                    audio.playMessage("preview",sample,()->{});assertTrue(audio.selected("preview"));
                    audio.toggle("preview");assertFalse(audio.playing("preview"));audio.seek("preview",.4f);
                    LinearLayout root=new LinearLayout(c);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(24,36,24,24);root.setBackgroundColor(TerminalUi.BACKGROUND);
                    TerminalUi.label(root,"Голосовые сообщения",22,TerminalUi.TEXT);
                    ChatThreadView chat=new ChatThreadView(c,"",v->{},v->{});chat.audio=audio;view.set(chat);
                    root.addView(chat,new LinearLayout.LayoutParams(-1,0,1));activity.get().setContentView(root);
                    JsonObject history=new JsonObject();history.addProperty("offset",0);history.add("next_offset",JsonNull.INSTANCE);JsonArray messages=new JsonArray();
                    for(int i=0;i<2;i++){JsonObject m=new JsonObject();m.addProperty("id",i==0?"received-preview":"preview");m.addProperty("kind","audio");m.addProperty("duration_ms",i==0?18000:1000);m.addProperty("outgoing",i==1);m.addProperty("timestamp",1789992000);m.addProperty("status","relayed");messages.add(m);}
                    history.add("messages",messages);chat.show(history,()->{},()->{});
                }catch(Exception e){throw new AssertionError(e);}
            });
            ins.waitForIdleSync();SystemClock.sleep(500);
            ins.runOnMainSync(()->{assertTrue(view.get().getWidth()>0);assertTrue(view.get().getHeight()>0);});
            // The real app keeps FLAG_SECURE. Render only this synthetic view.
            AtomicReference<Bitmap> rendered=new AtomicReference<>();
            ins.runOnMainSync(()->{
                android.view.View root=(android.view.View)view.get().getParent();
                Bitmap bitmap=Bitmap.createBitmap(root.getWidth(),root.getHeight(),Bitmap.Config.ARGB_8888);
                root.draw(new android.graphics.Canvas(bitmap));rendered.set(bitmap);
            });
            Bitmap screenshot=rendered.get();assertNotNull(screenshot);
            try(ByteArrayOutputStream out=new ByteArrayOutputStream()){
                assertTrue(screenshot.compress(Bitmap.CompressFormat.PNG,100,out));
                android.os.Bundle result=new android.os.Bundle();
                result.putString("fc_synthetic_render",android.util.Base64.encodeToString(out.toByteArray(),android.util.Base64.NO_WRAP));
                ins.sendStatus(0,result);
            }
            screenshot.recycle();
        }finally{ins.runOnMainSync(audio::close);}
    }
}
