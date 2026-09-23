package com.familyconnect.app;

import android.app.Activity;
import android.graphics.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.*;
import com.google.gson.*;
import java.io.*;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import static org.junit.Assert.*;

/** Long synthetic history: no real contacts, messages or microphone. */
public class ChatScrollRuntimeTest {
    @org.junit.Before public void friendsVariantOnly(){
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName().endsWith(".friends"));
    }
    private JsonObject page(int count,String status){
        JsonObject page=new JsonObject();page.addProperty("offset",0);page.add("next_offset",JsonNull.INSTANCE);
        JsonArray messages=new JsonArray();
        for(int i=0;i<count;i++){JsonObject m=new JsonObject();m.addProperty("id","synthetic-"+i);m.addProperty("text","Сообщение "+i+"\nПроверка прокрутки истории");m.addProperty("outgoing",true);m.addProperty("timestamp",1789992000);m.addProperty("status",status);messages.add(m);}
        page.add("messages",messages);return page;
    }
    private Button submit(View view,String label){if(view instanceof Button&&label.equals(view.getContentDescription()))return (Button)view;
        if(view instanceof ViewGroup)for(int i=0;i<((ViewGroup)view).getChildCount();i++){Button button=submit(((ViewGroup)view).getChildAt(i),label);if(button!=null)return button;}return null;}
    @Test public void newMessageScrollsAfterLayoutAndStatusPreservesPosition()throws Exception{
        var ins=InstrumentationRegistry.getInstrumentation();var context=ins.getTargetContext();
        try(ParcelFileDescriptor cmd=ins.getUiAutomation().executeShellCommand("am start -W -n "+context.getPackageName()+"/com.familyconnect.app.FriendsActivity")){
            try(InputStream in=new FileInputStream(cmd.getFileDescriptor())){while(in.read()!=-1){}}
        }
        AtomicReference<Activity> activity=new AtomicReference<>();AtomicReference<ChatThreadView> view=new AtomicReference<>();
        ins.runOnMainSync(()->{for(Activity a:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED))activity.set(a);});assertNotNull(activity.get());
        ins.runOnMainSync(()->{
            LinearLayout root=new LinearLayout(context);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(24,36,24,24);root.setBackgroundColor(TerminalUi.BACKGROUND);
            ChatThreadView thread=new ChatThreadView(context,"",v->{},v->{});view.set(thread);root.addView(thread,new LinearLayout.LayoutParams(-1,-1));activity.get().setContentView(root);
            Button send=submit(thread,context.getString(R.string.chat_send));assertNotNull(send);assertEquals(View.VISIBLE,send.getVisibility());assertFalse(send.isEnabled());
            thread.composer.setText("Текст");assertTrue(send.isEnabled());assertEquals(View.VISIBLE,thread.voice.getVisibility());thread.composer.setText("");assertEquals(View.VISIBLE,send.getVisibility());
            thread.show(page(30,"queued"),()->{},()->{});
        });
        ins.waitForIdleSync();SystemClock.sleep(150);
        ins.runOnMainSync(()->{assertFalse(view.get().history.canScrollVertically(1));view.get().history.scrollTo(0,0);assertTrue(view.get().history.canScrollVertically(1));view.get().revealLatest();view.get().show(page(31,"queued"),()->{},()->{});});
        ins.waitForIdleSync();SystemClock.sleep(150);
        ins.runOnMainSync(()->{assertFalse("New message must be visible after layout",view.get().history.canScrollVertically(1));view.get().history.scrollTo(0,80);view.get().show(page(31,"relayed"),()->{},()->{});});
        ins.waitForIdleSync();SystemClock.sleep(150);
        ins.runOnMainSync(()->{assertEquals("Delivery status must preserve reading position",80,view.get().history.getScrollY());view.get().revealLatest();view.get().show(page(31,"relayed"),()->{},()->{});});
        ins.waitForIdleSync();SystemClock.sleep(150);
        ins.runOnMainSync(()->{assertFalse("Explicit reveal also works without data changes",view.get().history.canScrollVertically(1));});
        AtomicReference<Bitmap> render=new AtomicReference<>();
        ins.runOnMainSync(()->{View root=(View)view.get().getParent();Bitmap bitmap=Bitmap.createBitmap(root.getWidth(),root.getHeight(),Bitmap.Config.ARGB_8888);root.draw(new Canvas(bitmap));render.set(bitmap);});
        try(ByteArrayOutputStream out=new ByteArrayOutputStream()){render.get().compress(Bitmap.CompressFormat.PNG,100,out);Bundle result=new Bundle();result.putString("fc_synthetic_render",android.util.Base64.encodeToString(out.toByteArray(),android.util.Base64.NO_WRAP));ins.sendStatus(0,result);}finally{render.get().recycle();}
    }
}
