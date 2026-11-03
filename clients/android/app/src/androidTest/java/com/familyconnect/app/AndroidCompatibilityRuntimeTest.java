package com.familyconnect.app;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.media.MediaPlayer;
import android.os.Build;
import android.os.ParcelFileDescriptor;
import android.os.SystemClock;
import android.widget.LinearLayout;
import android.widget.Spinner;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry;
import androidx.test.runner.lifecycle.Stage;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;

public class AndroidCompatibilityRuntimeTest {
    private final android.app.Instrumentation instrumentation=InstrumentationRegistry.getInstrumentation();
    private Context context(){return instrumentation.getTargetContext();}
    @Before public void disposableFriendsOnly(){
        org.junit.Assume.assumeTrue(context().getPackageName().endsWith(".friends"));
        assertTrue("Disposable emulator only",Build.FINGERPRINT.contains("generic")||Build.MODEL.contains("sdk"));
    }
    private void shell(String command)throws Exception{
        try(ParcelFileDescriptor result=instrumentation.getUiAutomation().executeShellCommand(command);FileInputStream input=new FileInputStream(result.getFileDescriptor())){while(input.read()!=-1){}}
    }
    @Test public void nativeRadioRoundTripAndPlayback()throws Exception{
        short[] samples=new short[8000];
        for(int index=0;index<samples.length;index++)samples[index]=(short)(4000*Math.sin(index*2*Math.PI*440/8000));
        for(int mode:new int[]{7,8,9}){
            byte[] encoded=RadioCodec.encode(samples,mode);assertTrue(encoded.length>0&&encoded.length<=ChatAudio.MAX_BYTES);
            short[] decoded=RadioCodec.decode(encoded,mode);assertTrue(decoded.length>=samples.length&&decoded.length<samples.length+320);
            File file=File.createTempFile("compatibility-voice-",".wav",context().getCacheDir());
            MediaPlayer player=new MediaPlayer();CountDownLatch finished=new CountDownLatch(1);AtomicBoolean failed=new AtomicBoolean();
            try{
                Files.write(file.toPath(),ChatAudio.wav(decoded));player.setDataSource(file.getAbsolutePath());player.setVolume(0,0);player.prepare();
                assertTrue(player.getDuration()>=900&&player.getDuration()<=1100);
                player.setOnCompletionListener(value->finished.countDown());player.setOnErrorListener((value,what,extra)->{failed.set(true);finished.countDown();return true;});player.start();
                assertTrue(finished.await(10,TimeUnit.SECONDS));assertFalse(failed.get());
            }finally{player.release();file.delete();Arrays.fill(decoded,(short)0);Arrays.fill(encoded,(byte)0);}
        }
        Arrays.fill(samples,(short)0);
    }
    @Test public void radioRecordingCanFinishWithoutOpusEncoder()throws Exception{
        shell("pm grant "+context().getPackageName()+" android.permission.RECORD_AUDIO");
        AtomicReference<ChatAudio> audio=new AtomicReference<>();AtomicReference<byte[]> recorded=new AtomicReference<>();CountDownLatch finished=new CountDownLatch(1);
        instrumentation.runOnMainSync(()->{ChatAudio value=new ChatAudio(context());audio.set(value);try{value.start(9,()->{});}catch(Exception failure){throw new AssertionError(failure);}});
        try{
            SystemClock.sleep(1200);
            instrumentation.runOnMainSync(()->audio.get().finishAsync(bytes->{recorded.set(bytes);finished.countDown();},finished::countDown));
            assertTrue(finished.await(15,TimeUnit.SECONDS));assertNotNull("Codec2 capture failed",recorded.get());
            assertTrue(RadioCodec.decode(recorded.get(),9).length>0);
        }finally{instrumentation.runOnMainSync(()->audio.get().close());if(recorded.get()!=null)Arrays.fill(recorded.get(),(byte)0);}
    }
    @Test public void voiceSettingsOnlyOfferSupportedRecordingModes()throws Exception{
        RadioSettings.preferences(context()).edit().putInt("mode",16).commit();
        context().getSharedPreferences("app-updates",Context.MODE_PRIVATE).edit().putLong("checked_at",System.currentTimeMillis()).commit();
        shell("am start -W -n "+context().getPackageName()+"/com.familyconnect.app.FriendsActivity");
        AtomicReference<Activity> activity=new AtomicReference<>();AtomicReference<LinearLayout> panel=new AtomicReference<>();
        instrumentation.runOnMainSync(()->{
            for(Activity value:ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED))activity.set(value);
            assertNotNull(activity.get());LinearLayout root=new LinearLayout(activity.get());root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(TerminalUi.BACKGROUND);root.setPadding(24,40,24,24);
            RadioSettings.attach(root);activity.get().setContentView(root);panel.set(root);
            assertEquals(Build.VERSION.SDK_INT<29?9:16,RadioSettings.mode(context()));
            LinearLayout section=(LinearLayout)root.getChildAt(0);Spinner picker=null;
            for(int index=0;index<section.getChildCount();index++)if(section.getChildAt(index) instanceof Spinner)picker=(Spinner)section.getChildAt(index);
            assertNotNull(picker);assertEquals(Build.VERSION.SDK_INT<29?3:4,picker.getCount());
        });
        SystemClock.sleep(300);
        instrumentation.runOnMainSync(()->{
            Bitmap image=Bitmap.createBitmap(panel.get().getWidth(),panel.get().getHeight(),Bitmap.Config.ARGB_8888);panel.get().draw(new Canvas(image));
            File directory=context().getExternalFilesDir("ui-acceptance");
            try(FileOutputStream output=new FileOutputStream(new File(directory,"android-compatibility-voice.png"))){image.compress(Bitmap.CompressFormat.PNG,100,output);}catch(Exception failure){throw new AssertionError(failure);}finally{image.recycle();}
        });
        RadioSettings.preferences(context()).edit().remove("mode").commit();
    }
}
