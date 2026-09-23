package com.familyconnect.app;

import android.app.Activity;
import android.graphics.*;
import android.os.*;
import android.view.MotionEvent;
import android.widget.LinearLayout;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.*;
import java.io.*;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import static org.junit.Assert.*;

/** Native gesture/lifecycle UI acceptance with a fake recorder: never records or sends. */
public class VoiceHoldRuntimeTest {
    @org.junit.Before public void friendsVariantOnly(){
        org.junit.Assume.assumeTrue(InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName().endsWith(".friends"));
    }
    private final android.app.Instrumentation ins=InstrumentationRegistry.getInstrumentation();
    private ChatThreadView thread;
    private int starts,sends,cancels;
    private long down;
    private void event(int action,float x,float y){ins.runOnMainSync(()->{
        if(action==MotionEvent.ACTION_DOWN)down=SystemClock.uptimeMillis();
        MotionEvent e=MotionEvent.obtain(down,SystemClock.uptimeMillis(),action,x,y,0);
        thread.voice.dispatchTouchEvent(e);e.recycle();
    });}
    private void hold(){event(MotionEvent.ACTION_DOWN,26,26);SystemClock.sleep(300);}
    @Test public void holdReleaseLockCancelAndInlineRender()throws Exception{
        var context=ins.getTargetContext();
        try(ParcelFileDescriptor cmd=ins.getUiAutomation().executeShellCommand("am start -W -n "+context.getPackageName()+"/com.familyconnect.app.FriendsActivity")){
            try(InputStream in=new FileInputStream(cmd.getFileDescriptor())){while(in.read()!=-1){}}
        }
        AtomicReference<Activity> activity=new AtomicReference<>();
        ins.runOnMainSync(()->{for(Activity a:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED))activity.set(a);});
        assertNotNull(activity.get());
        ins.runOnMainSync(()->{
            LinearLayout root=new LinearLayout(context);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(24,36,24,24);root.setBackgroundColor(TerminalUi.BACKGROUND);
            TerminalUi.label(root,"Запись в чате",22,TerminalUi.TEXT);
            thread=new ChatThreadView(context,"",v->{},v->{});root.addView(thread,new LinearLayout.LayoutParams(-1,0,1));activity.get().setContentView(root);
            thread.voice.listener=new VoiceHoldButton.Listener(){
                public boolean start(){starts++;thread.recordingState(VoiceHoldButton.HOLDING);return true;}
                public void lock(){thread.recordingState(VoiceHoldButton.LOCKED);}
                public void release(){sends++;thread.recordingState(VoiceHoldButton.IDLE);}
                public void cancel(){cancels++;thread.recordingState(VoiceHoldButton.IDLE);}
                public void send(){sends++;thread.recordingState(VoiceHoldButton.IDLE);}
            };
        });
        event(MotionEvent.ACTION_DOWN,26,26);event(MotionEvent.ACTION_UP,26,26);SystemClock.sleep(250);assertEquals(0,starts);
        hold();assertEquals(1,starts);event(MotionEvent.ACTION_UP,26,26);assertEquals(1,sends);
        float density=context.getResources().getDisplayMetrics().density;
        hold();event(MotionEvent.ACTION_MOVE,26,26-90*density);event(MotionEvent.ACTION_UP,26,26-90*density);
        assertEquals(VoiceHoldButton.LOCKED,thread.voice.state());assertEquals(1,sends);
        ins.runOnMainSync(()->{assertEquals(android.view.View.GONE,thread.composer.getVisibility());thread.recordingElapsed(12000);});
        AtomicReference<Bitmap> render=new AtomicReference<>();
        ins.runOnMainSync(()->{android.view.View root=(android.view.View)thread.getParent();Bitmap bitmap=Bitmap.createBitmap(root.getWidth(),root.getHeight(),Bitmap.Config.ARGB_8888);root.draw(new Canvas(bitmap));render.set(bitmap);});
        try(ByteArrayOutputStream out=new ByteArrayOutputStream()){render.get().compress(Bitmap.CompressFormat.PNG,100,out);Bundle result=new Bundle();result.putString("fc_synthetic_render",android.util.Base64.encodeToString(out.toByteArray(),android.util.Base64.NO_WRAP));ins.sendStatus(0,result);}finally{render.get().recycle();}
        event(MotionEvent.ACTION_DOWN,26,26);event(MotionEvent.ACTION_UP,26,26);assertEquals(2,sends);
        hold();event(MotionEvent.ACTION_MOVE,26-100*density,26);event(MotionEvent.ACTION_UP,26-100*density,26);assertEquals(1,cancels);assertEquals(2,sends);
        hold();event(MotionEvent.ACTION_CANCEL,26,26);assertEquals(2,cancels);assertEquals(2,sends);
        ins.runOnMainSync(()->{thread.voice.performClick();assertEquals(VoiceHoldButton.LOCKED,thread.voice.state());thread.voice.performClick();assertEquals(3,sends);assertEquals(android.view.View.VISIBLE,thread.composer.getVisibility());});
    }
}
