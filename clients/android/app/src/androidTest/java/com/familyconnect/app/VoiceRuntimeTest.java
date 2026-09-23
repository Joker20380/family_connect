package com.familyconnect.app;
import android.media.*;
import android.os.*;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.io.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;
@RunWith(AndroidJUnit4.class)
public class VoiceRuntimeTest {
 @Test public void opusEncoderAndSilentSyntheticPlayback()throws Exception {
  assumeTrue(Build.VERSION.SDK_INT>=29);
  MediaCodec encoder=MediaCodec.createEncoderByType("audio/opus");
  try{MediaFormat format=MediaFormat.createAudioFormat("audio/opus",16000,1);format.setInteger(MediaFormat.KEY_BIT_RATE,12000);encoder.configure(format,null,null,MediaCodec.CONFIGURE_FLAG_ENCODE);encoder.start();encoder.stop();}finally{encoder.release();}
  android.app.Instrumentation ins=InstrumentationRegistry.getInstrumentation();File file=File.createTempFile("voice-test-",".ogg",ins.getTargetContext().getCacheDir());
  try{
   try(InputStream in=ins.getContext().getAssets().open("voice-tone.opus");OutputStream out=new FileOutputStream(file)){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}
   CountDownLatch done=new CountDownLatch(1);AtomicReference<MediaPlayer> player=new AtomicReference<>();AtomicBoolean failed=new AtomicBoolean();
   ins.runOnMainSync(()->{try{MediaPlayer p=new MediaPlayer();player.set(p);p.setDataSource(file.getAbsolutePath());p.setVolume(0,0);p.prepare();assertTrue(p.getDuration()>0&&p.getDuration()<1500);p.setOnCompletionListener(v->done.countDown());p.setOnErrorListener((v,a,b)->{failed.set(true);done.countDown();return true;});p.start();}catch(Exception e){throw new AssertionError(e);}});
   try{assertTrue(done.await(10,TimeUnit.SECONDS));assertFalse(failed.get());}finally{ins.runOnMainSync(()->player.get().release());}
  }finally{file.delete();}
 }
}
