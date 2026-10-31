package com.familyconnect.app;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.MotionEvent;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.Locale;

/** Compact voice bubble; progress always follows the player, never a timer estimate. */
final class ChatVoiceView extends LinearLayout {
    private final ChatAudio audio;
    private final String id;
    private final int duration;
    private final Transport transport;
    private final Wave wave;
    private final TextView time;
    private final Runnable tick=new Runnable(){public void run(){refresh();postDelayed(this,200);}};
    ChatVoiceView(Context context,String id,int duration,ChatAudio audio,Runnable play){
        super(context);this.id=id;this.duration=duration;this.audio=audio;
        setOrientation(HORIZONTAL);setGravity(android.view.Gravity.CENTER_VERTICAL);
        transport=new Transport(context);transport.setOnClickListener(v->play.run());
        addView(transport,new LayoutParams(dp(48),dp(48)));
        LinearLayout body=new LinearLayout(context);body.setOrientation(VERTICAL);
        LayoutParams space=new LayoutParams(0,-2,1);space.leftMargin=dp(12);addView(body,space);
        wave=new Wave(context);body.addView(wave,new LayoutParams(-1,dp(48)));
        time=new TextView(context);TerminalUi.textStyle(time,12,TerminalUi.MINT);
        body.addView(time,new LayoutParams(-1,-2));refresh();
    }
    private int dp(int value){return TerminalUi.dp(getContext(),value);}
    private static String clock(int millis){int seconds=Math.max(0,millis)/1000;return String.format(Locale.ROOT,"%d:%02d",seconds/60,seconds%60);}
    private void refresh(){
        boolean selected=audio!=null&&audio.selected(id),playing=selected&&audio.playing(id);
        int position=selected?audio.position(id):0;
        String value=selected?clock(position)+" / "+clock(duration):clock(duration);
        if(!value.contentEquals(time.getText()))time.setText(value);
        if(transport.playing!=playing){transport.playing=playing;transport.invalidate();}
        transport.setContentDescription(getContext().getString(playing?R.string.chat_voice_pause:R.string.chat_voice_play));
        float progress=duration>0?Math.min(1,(float)position/duration):0;
        wave.setProgress(Math.round(progress*1000));wave.setEnabled(selected);
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();post(tick);}
    @Override protected void onDetachedFromWindow(){removeCallbacks(tick);super.onDetachedFromWindow();}
    @Override protected void onWindowVisibilityChanged(int visibility){super.onWindowVisibilityChanged(visibility);removeCallbacks(tick);if(visibility==VISIBLE&&isAttachedToWindow())post(tick);}
    private final class Transport extends View {
        final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);boolean playing;
        Transport(Context c){super(c);setFocusable(true);setClickable(true);setContentDescription(c.getString(R.string.chat_voice_play));}
        @Override protected void onDraw(Canvas c){
            float x=getWidth()/2f,y=getHeight()/2f;paint.setColor(TerminalUi.MINT);c.drawRect(x-dp(21),y-dp(21),x+dp(21),y+dp(21),paint);paint.setColor(TerminalUi.BACKGROUND);
            if(playing){c.drawRoundRect(x-dp(7),y-dp(9),x-dp(2),y+dp(9),dp(1),dp(1),paint);c.drawRoundRect(x+dp(2),y-dp(9),x+dp(7),y+dp(9),dp(1),dp(1),paint);}
            else{Path p=new Path();p.moveTo(x-dp(5),y-dp(10));p.lineTo(x+dp(10),y);p.lineTo(x-dp(5),y+dp(10));p.close();c.drawPath(p,paint);}
        }
    }
    private final class Wave extends android.widget.SeekBar {
        Wave(Context context){
            super(context);setMax(1000);setContentDescription(context.getString(R.string.chat_voice_progress));
            setProgressTintList(android.content.res.ColorStateList.valueOf(TerminalUi.MINT));setThumbTintList(android.content.res.ColorStateList.valueOf(TerminalUi.MINT));
            setOnSeekBarChangeListener(new OnSeekBarChangeListener(){
                public void onStartTrackingTouch(android.widget.SeekBar bar){}
                public void onStopTrackingTouch(android.widget.SeekBar bar){}
                public void onProgressChanged(android.widget.SeekBar bar,int value,boolean user){if(user&&audio!=null)audio.seek(id,value/1000f);}
            });
        }
    }
}
