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
        wave=new Wave(context);body.addView(wave,new LayoutParams(-1,dp(32)));
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
        if(wave.progress!=progress){wave.progress=progress;wave.invalidate();}
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();post(tick);}
    @Override protected void onDetachedFromWindow(){removeCallbacks(tick);super.onDetachedFromWindow();}
    private final class Transport extends View {
        final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);boolean playing;
        Transport(Context c){super(c);setFocusable(true);setClickable(true);setContentDescription(c.getString(R.string.chat_voice_play));}
        @Override protected void onDraw(Canvas c){
            float x=getWidth()/2f,y=getHeight()/2f;paint.setColor(TerminalUi.MINT);c.drawCircle(x,y,dp(22),paint);paint.setColor(0xff153d30);
            if(playing){c.drawRoundRect(x-dp(7),y-dp(9),x-dp(2),y+dp(9),dp(1),dp(1),paint);c.drawRoundRect(x+dp(2),y-dp(9),x+dp(7),y+dp(9),dp(1),dp(1),paint);}
            else{Path p=new Path();p.moveTo(x-dp(5),y-dp(10));p.lineTo(x+dp(10),y);p.lineTo(x-dp(5),y+dp(10));p.close();c.drawPath(p,paint);}
        }
    }
    private final class Wave extends View {
        final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);float progress;
        // A neutral voice motif, not a claimed amplitude analysis of private audio.
        final int[] heights={7,12,19,10,24,28,16,9,20,13,27,18,11,23,15,8,19,29,17,12,25,16,9,21};
        Wave(Context c){super(c);setContentDescription(c.getString(R.string.chat_voice_progress));}
        @Override protected void onDraw(Canvas c){
            int count=Math.max(1,getWidth()/dp(5));float step=(float)getWidth()/count;
            for(int i=0;i<count;i++){float h=dp(heights[i%heights.length]),x=i*step;
                paint.setColor((i+.5f)/count<=progress?TerminalUi.MINT:0xff568775);
                c.drawRoundRect(x,(getHeight()-h)/2,x+dp(3),(getHeight()+h)/2,dp(2),dp(2),paint);
            }
        }
        @Override public boolean onTouchEvent(MotionEvent event){
            if(audio==null||!audio.selected(id))return false;
            if(event.getAction()==MotionEvent.ACTION_DOWN){getParent().requestDisallowInterceptTouchEvent(true);return true;}
            if(event.getAction()==MotionEvent.ACTION_MOVE||event.getAction()==MotionEvent.ACTION_UP){audio.seek(id,event.getX()/Math.max(1,getWidth()));refresh();if(event.getAction()==MotionEvent.ACTION_UP)performClick();return true;}
            return super.onTouchEvent(event);
        }
        @Override public boolean performClick(){super.performClick();return true;}
    }
}
