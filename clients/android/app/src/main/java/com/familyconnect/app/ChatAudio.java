package com.familyconnect.app;

import android.content.Context;
import android.media.*;
import android.os.Build;
import java.io.*;
import java.nio.file.Files;
import java.util.Arrays;

/** Private temporary capture; only compressed bytes enter the encrypted chat store. */
final class ChatAudio implements AutoCloseable {
    static final int MAX_BYTES=131072,MAX_MILLIS=60000;
    private final Context context;
    private File recording,playback;
    private MediaRecorder recorder;
    private MediaPlayer player;
    private String messageId;
    ChatAudio(Context context){this.context=context;}
    void start(Runnable limit)throws Exception {
        if(Build.VERSION.SDK_INT<29)throw new IOException("Opus recording requires Android 10");
        stopPlayback();discardRecording();
        recording=File.createTempFile("voice-",".ogg",context.getCacheDir());
        recorder=new MediaRecorder();
        try{
            recorder.setAudioSource(MediaRecorder.AudioSource.VOICE_RECOGNITION);
            recorder.setOutputFormat(MediaRecorder.OutputFormat.OGG);recorder.setAudioEncoder(MediaRecorder.AudioEncoder.OPUS);
            recorder.setAudioChannels(1);recorder.setAudioSamplingRate(16000);recorder.setAudioEncodingBitRate(12000);
            recorder.setMaxDuration(MAX_MILLIS);recorder.setMaxFileSize(MAX_BYTES);recorder.setOutputFile(recording.getAbsolutePath());
            recorder.setOnInfoListener((r,what,extra)->{if(what==MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED||what==MediaRecorder.MEDIA_RECORDER_INFO_MAX_FILESIZE_REACHED)limit.run();});
            recorder.prepare();recorder.start();
        }catch(Exception failure){discardRecording();throw failure;}
    }
    byte[] finish()throws Exception {
        if(recorder==null)throw new IOException();
        try{
            recorder.stop();recorder.release();recorder=null;
            if(recording.length()<64||recording.length()>MAX_BYTES)throw new IOException();
            return Files.readAllBytes(recording.toPath());
        }finally{discardRecording();}
    }
    void play(byte[] data,Runnable done)throws Exception {
        stopPlayback();if(data.length<64||data.length>MAX_BYTES)throw new IOException();
        playback=File.createTempFile("voice-play-",".ogg",context.getCacheDir());
        try{
            Files.write(playback.toPath(),data);player=new MediaPlayer();player.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build());
            player.setDataSource(playback.getAbsolutePath());player.prepare();
            if(player.getDuration()<=0||player.getDuration()>61000)throw new IOException();
            player.setOnCompletionListener(p->{stopPlayback();done.run();});player.setOnErrorListener((p,a,b)->{stopPlayback();done.run();return true;});player.start();
        }catch(Exception failure){stopPlayback();throw failure;}
    }
    void playMessage(String id,byte[] data,Runnable done)throws Exception {play(data,done);messageId=id;}
    boolean selected(String id){return player!=null&&id.equals(messageId);}
    boolean playing(String id){return selected(id)&&player.isPlaying();}
    int position(String id){return selected(id)?player.getCurrentPosition():0;}
    void toggle(String id){if(selected(id)){if(player.isPlaying())player.pause();else player.start();}}
    void seek(String id,float fraction){if(selected(id))player.seekTo(Math.round(Math.max(0,Math.min(1,fraction))*player.getDuration()));}
    void stopPlayback(){messageId=null;if(player!=null){player.release();player=null;}if(playback!=null){playback.delete();playback=null;}}
    void discardRecording(){if(recorder!=null){try{recorder.stop();}catch(Exception ignored){}recorder.release();recorder=null;}if(recording!=null){recording.delete();recording=null;}}
    @Override public void close(){discardRecording();stopPlayback();}
    static void cleanOld(Context context){File[] files=context.getCacheDir().listFiles();if(files!=null)for(File file:files)if(file.getName().startsWith("voice-")&&file.getName().endsWith(".ogg"))file.delete();}
}
