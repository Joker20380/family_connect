package com.familyconnect.app;

import android.content.*;
import android.media.*;
import android.os.*;
import java.io.*;
import java.nio.*;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

final class ChatAudio implements AutoCloseable {
    static final int MAX_BYTES=131072,MAX_MILLIS=60000;
    private static final ExecutorService CODECS=Executors.newSingleThreadExecutor();
    private final Context context;
    private final Handler main=new Handler(Looper.getMainLooper());
    private File recording,playback;
    private MediaRecorder recorder;
    private MediaPlayer player;
    private PcmCapture capture;
    private String messageId;
    private int generation,mode=16;
    private AudioFocusRequest focus;
    private boolean receiverRegistered;
    private final BroadcastReceiver noisy=new BroadcastReceiver(){public void onReceive(Context c,Intent i){stopPlayback();}};
    ChatAudio(Context context){this.context=context;}
    int mode(){return mode;}
    void start(Runnable limit)throws Exception {start(16,limit);}
    void start(int selected,Runnable limit)throws Exception {
        stopPlayback();discardRecording();mode=selected;
        if(selected!=16){capture=new PcmCapture(()->main.post(limit));capture.start();return;}
        if(Build.VERSION.SDK_INT<29)throw new IOException("opus_capture_unavailable");
        recording=File.createTempFile("voice-",".ogg",context.getCacheDir());recorder=new MediaRecorder();
        try{
            recorder.setAudioSource(MediaRecorder.AudioSource.VOICE_RECOGNITION);
            recorder.setOutputFormat(MediaRecorder.OutputFormat.OGG);recorder.setAudioEncoder(MediaRecorder.AudioEncoder.OPUS);
            recorder.setAudioChannels(1);recorder.setAudioSamplingRate(16000);recorder.setAudioEncodingBitRate(12000);
            recorder.setMaxDuration(MAX_MILLIS);recorder.setMaxFileSize(MAX_BYTES);recorder.setOutputFile(recording.getAbsolutePath());
            recorder.setOnInfoListener((r,what,extra)->{if(what==MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED||what==MediaRecorder.MEDIA_RECORDER_INFO_MAX_FILESIZE_REACHED)limit.run();});
            recorder.prepare();recorder.start();
        }catch(Exception failure){discardRecording();throw failure;}
    }
    void finishAsync(Consumer<byte[]> ready,Runnable failed){
        int expected=++generation,selected=mode;
        PcmCapture pending=capture;capture=null;MediaRecorder compressed=recorder;recorder=null;File file=recording;recording=null;
        CODECS.execute(()->{
            byte[] result=null;
            try{
                if(pending!=null){short[] pcm=pending.finish();try{result=RadioCodec.encode(pcm,selected);}finally{Arrays.fill(pcm,(short)0);}}
                else if(compressed!=null){compressed.stop();if(file.length()<64||file.length()>MAX_BYTES)throw new IOException();result=Files.readAllBytes(file.toPath());}
            }catch(Exception|LinkageError failure){}finally{if(compressed!=null)compressed.release();if(file!=null)file.delete();}
            byte[] value=result;main.post(()->{if(generation!=expected){if(value!=null)Arrays.fill(value,(byte)0);return;}if(value==null)failed.run();else ready.accept(value);});
        });
    }
    void play(byte[] data,Runnable done)throws Exception {playMessage("preview",data,mode,done);}
    void playMessage(String id,byte[] data,Runnable done)throws Exception {playMessage(id,data,16,done);}
    void playMessage(String id,byte[] data,int selected,Runnable done)throws Exception {
        stopPlayback();if(data.length<1||data.length>MAX_BYTES)throw new IOException("audio_limit");
        final int expected=generation;byte[] copy=data.clone();
        CODECS.execute(()->{
            byte[] playable=null;
            try{if(selected==16)playable=copy.clone();else{short[] pcm=RadioCodec.decode(copy,selected);try{playable=wav(pcm);}finally{Arrays.fill(pcm,(short)0);}}}
            catch(Exception|LinkageError failure){}finally{Arrays.fill(copy,(byte)0);}
            byte[] value=playable;
            main.post(()->{
                if(expected!=generation){if(value!=null)Arrays.fill(value,(byte)0);return;}if(value==null){done.run();return;}
                try{
                    AudioAttributes attributes=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build();
                    focus=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT).setAudioAttributes(attributes).setWillPauseWhenDucked(true).setOnAudioFocusChangeListener(change->{if(change!=AudioManager.AUDIOFOCUS_GAIN)stopPlayback();},main).build();
                    if(context.getSystemService(AudioManager.class).requestAudioFocus(focus)!=AudioManager.AUDIOFOCUS_REQUEST_GRANTED)throw new IOException("audio_focus_denied");
                    IntentFilter filter=new IntentFilter(AudioManager.ACTION_AUDIO_BECOMING_NOISY);
                    if(Build.VERSION.SDK_INT>=33)context.registerReceiver(noisy,filter,Context.RECEIVER_NOT_EXPORTED);else context.registerReceiver(noisy,filter);receiverRegistered=true;
                    playback=File.createTempFile("voice-play-",selected==16?".ogg":".wav",context.getCacheDir());Files.write(playback.toPath(),value);
                    player=new MediaPlayer();player.setAudioAttributes(attributes);player.setDataSource(playback.getAbsolutePath());
                    player.setOnPreparedListener(prepared->{if(expected!=generation)return;if(prepared.getDuration()<=0||prepared.getDuration()>61000){stopPlayback();done.run();return;}messageId=id;prepared.start();});
                    player.setOnCompletionListener(prepared->{stopPlayback();done.run();});player.setOnErrorListener((prepared,what,extra)->{stopPlayback();done.run();return true;});player.prepareAsync();
                }catch(Exception failure){stopPlayback();done.run();}finally{Arrays.fill(value,(byte)0);}
            });
        });
    }
    static byte[] wav(short[] pcm){
        ByteBuffer buffer=ByteBuffer.allocate(44+pcm.length*2).order(ByteOrder.LITTLE_ENDIAN);
        buffer.put(new byte[]{82,73,70,70}).putInt(36+pcm.length*2).put(new byte[]{87,65,86,69,102,109,116,32}).putInt(16).putShort((short)1).putShort((short)1).putInt(8000).putInt(16000).putShort((short)2).putShort((short)16).put(new byte[]{100,97,116,97}).putInt(pcm.length*2);
        for(short sample:pcm)buffer.putShort(sample);return buffer.array();
    }
    boolean selected(String id){return player!=null&&id.equals(messageId);}
    boolean playing(String id){return selected(id)&&player.isPlaying();}
    int position(String id){return selected(id)?player.getCurrentPosition():0;}
    void toggle(String id){if(selected(id)){if(player.isPlaying())player.pause();else player.start();}}
    void seek(String id,float fraction){if(selected(id))player.seekTo(Math.round(Math.max(0,Math.min(1,fraction))*player.getDuration()));}
    void stopPlayback(){generation++;messageId=null;if(player!=null){player.release();player=null;}if(playback!=null){playback.delete();playback=null;}if(focus!=null){context.getSystemService(AudioManager.class).abandonAudioFocusRequest(focus);focus=null;}if(receiverRegistered){context.unregisterReceiver(noisy);receiverRegistered=false;}}
    void discardRecording(){generation++;if(recorder!=null){try{recorder.stop();}catch(Exception ignored){}recorder.release();recorder=null;}if(recording!=null){recording.delete();recording=null;}if(capture!=null){PcmCapture pending=capture;capture=null;pending.stop();CODECS.execute(()->{try{short[] pcm=pending.finish();Arrays.fill(pcm,(short)0);}catch(Exception ignored){}});}}
    @Override public void close(){discardRecording();stopPlayback();}
    static void cleanOld(Context context){File[] files=context.getCacheDir().listFiles();if(files!=null)for(File file:files)if(file.getName().startsWith("voice-")&&(file.getName().endsWith(".ogg")||file.getName().endsWith(".wav")))file.delete();}
    private static final class PcmCapture {
        private final AudioRecord input;
        private final short[] samples=new short[480000];
        private final Runnable limit;
        private volatile boolean running;
        private int count;
        private boolean failed;
        private Thread thread;
        PcmCapture(Runnable limit)throws IOException{
            this.limit=limit;int size=AudioRecord.getMinBufferSize(8000,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT);
            if(size<=0)throw new IOException("pcm_capture_unavailable");
            try{input=new AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION,8000,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT,Math.max(size,3200));}
            catch(SecurityException denied){throw new IOException("pcm_capture_permission_denied",denied);}
            if(input.getState()!=AudioRecord.STATE_INITIALIZED){input.release();throw new IOException("pcm_capture_unavailable");}
        }
        void start(){input.startRecording();running=true;thread=new Thread(()->{while(running&&count<samples.length){int read=input.read(samples,count,Math.min(160,samples.length-count));if(read<=0){if(running)failed=true;break;}count+=read;}if(running){running=false;limit.run();}},"exit-voice-capture");thread.start();}
        void stop(){running=false;try{input.stop();}catch(Exception ignored){}}
        short[] finish()throws Exception{stop();try{thread.join(1500);if(thread.isAlive())throw new IOException("capture_deadline");if(failed||count==0)throw new IOException("capture_failed");return Arrays.copyOf(samples,count);}finally{input.release();Arrays.fill(samples,(short)0);}}
    }
}
