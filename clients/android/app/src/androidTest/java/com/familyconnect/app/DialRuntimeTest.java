package com.familyconnect.app;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.view.MotionEvent;
import android.os.SystemClock;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.File;
import java.io.FileOutputStream;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class DialRuntimeTest {
    private void touch(TerminalUi.Dial dial,float x,float y){
        long now=SystemClock.uptimeMillis();
        MotionEvent down=MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,x,y,0);
        MotionEvent up=MotionEvent.obtain(now,now+30,MotionEvent.ACTION_UP,x,y,0);
        dial.dispatchTouchEvent(down);dial.dispatchTouchEvent(up);down.recycle();up.recycle();
    }
    private void draw(TerminalUi.Dial dial,Bitmap image){Canvas canvas=new Canvas(image);canvas.drawColor(TerminalUi.BACKGROUND);dial.draw(canvas);}
    @Test public void dialDrawsRealStatesAndDispatchesOnlyEnabledCenterClicks(){
        InstrumentationRegistry.getInstrumentation().runOnMainSync(()->{
            Context c=InstrumentationRegistry.getInstrumentation().getTargetContext();
            TerminalUi.Dial dial=new TerminalUi.Dial(c);dial.setMotion(false);dial.layout(0,0,720,720);
            AtomicInteger calls=new AtomicInteger();dial.setOnClickListener(v->calls.incrementAndGet());
            assertEquals(android.widget.Button.class.getName(),dial.getAccessibilityClassName());
            assertTrue(dial.performClick());assertEquals(1,calls.get());
            touch(dial,1,1);assertEquals("Corners must not toggle VPN",1,calls.get());
            dial.setEnabled(false);touch(dial,360,360);assertEquals("Disabled dial cannot connect",1,calls.get());dial.setEnabled(true);
            Bitmap off=Bitmap.createBitmap(720,720,Bitmap.Config.ARGB_8888);draw(dial,off);
            dial.update("on","ok");assertEquals(c.getString(R.string.disconnect),dial.getContentDescription());
            Bitmap on=Bitmap.createBitmap(720,720,Bitmap.Config.ARGB_8888);draw(dial,on);assertFalse(off.sameAs(on));
            Bitmap repeat=Bitmap.createBitmap(720,720,Bitmap.Config.ARGB_8888);draw(dial,repeat);assertTrue("Disabled motion stays still",on.sameAs(repeat));
            File folder=c.getExternalFilesDir("ui-acceptance");assertNotNull(folder);
            try(FileOutputStream a=new FileOutputStream(new File(folder,"dial-reference-on.png"));FileOutputStream b=new FileOutputStream(new File(folder,"dial-reference-off.png"))){on.compress(Bitmap.CompressFormat.PNG,100,a);off.compress(Bitmap.CompressFormat.PNG,100,b);}
            catch(Exception e){throw new AssertionError(e);}
            finally{off.recycle();on.recycle();repeat.recycle();}
        });
    }
}
