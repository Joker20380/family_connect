package com.familyconnect.app;

import android.content.Context;
import android.graphics.*;
import android.view.*;

/** One microphone target stays attached and in place for the entire gesture. */
final class VoiceHoldButton extends View {
    static final int IDLE=0,HOLDING=1,LOCKED=2,READY=3,SENDING=4;
    interface Listener {
        boolean start();
        void lock();
        void release();
        void cancel();
        void send();
    }
    Listener listener;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path iconPath=new Path();
    private final VoiceGesture gesture=new VoiceGesture();
    private int state=IDLE,pointer=-1,initialState;
    private float x,y;
    private boolean touching,suppressClick;
    private final Runnable begin=()->{
        if(touching&&state==IDLE&&listener!=null&&listener.start()){
            gesture.start();setState(HOLDING);performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
        }
    };
    VoiceHoldButton(Context context){super(context);setClickable(true);setFocusable(true);setState(IDLE);}
    void setState(int value){state=value;if(value==IDLE||value==READY||value==SENDING){gesture.reset();removeCallbacks(begin);}setEnabled(value!=SENDING);
        setContentDescription(getContext().getString(value==LOCKED||value==READY?R.string.chat_send:value==HOLDING?R.string.chat_voice_hold_hint:R.string.chat_voice_hold));invalidate();}
    int state(){return state;}
    @Override public boolean onTouchEvent(MotionEvent event){
        if(!isEnabled())return false;
        switch(event.getActionMasked()){
            case MotionEvent.ACTION_DOWN:
                initialState=state;pointer=event.getPointerId(0);x=event.getRawX();y=event.getRawY();touching=true;
                getParent().requestDisallowInterceptTouchEvent(true);
                if(state==IDLE)postDelayed(begin,180);
                return true;
            case MotionEvent.ACTION_POINTER_DOWN:
                removeCallbacks(begin);touching=false;dispatch(gesture.cancel());return true;
            case MotionEvent.ACTION_MOVE:
                if(!touching||event.findPointerIndex(pointer)<0)return true;
                float density=getResources().getDisplayMetrics().density;
                if(initialState==LOCKED||initialState==READY){
                    if(Math.abs(event.getRawX()-x)>24*density||Math.abs(event.getRawY()-y)>24*density)touching=false;
                    return true;
                }
                if(state==IDLE&&(Math.abs(event.getRawX()-x)>24*density||Math.abs(event.getRawY()-y)>24*density)){removeCallbacks(begin);touching=false;return true;}
                dispatch(gesture.move((event.getRawX()-x)/density,(event.getRawY()-y)/density));return true;
            case MotionEvent.ACTION_UP:
                removeCallbacks(begin);getParent().requestDisallowInterceptTouchEvent(false);
                if(touching){
                    if(initialState==LOCKED||initialState==READY){if(listener!=null)listener.send();}
                    else dispatch(gesture.release());
                    suppressClick=true;performClick();suppressClick=false;
                }
                touching=false;pointer=-1;return true;
            case MotionEvent.ACTION_CANCEL:
                removeCallbacks(begin);touching=false;pointer=-1;dispatch(gesture.cancel());return true;
            default:return true;
        }
    }
    private void dispatch(VoiceGesture.Action action){
        if(listener==null)return;
        if(action==VoiceGesture.Action.LOCK){setState(LOCKED);listener.lock();performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);}
        else if(action==VoiceGesture.Action.CANCEL){touching=false;setState(IDLE);listener.cancel();}
        else if(action==VoiceGesture.Action.SEND)listener.release();
    }
    @Override public boolean performClick(){
        super.performClick();if(suppressClick||listener==null)return true;
        // TalkBack/keyboard click starts locked recording; the next click sends.
        if(state==IDLE&&listener.start()){setState(LOCKED);listener.lock();}
        else if(state==LOCKED||state==READY)listener.send();return true;
    }
    @Override protected void onDetachedFromWindow(){removeCallbacks(begin);touching=false;super.onDetachedFromWindow();}
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);float d=getResources().getDisplayMetrics().density,cx=getWidth()/2f,cy=getHeight()/2f;
        paint.setStyle(Paint.Style.FILL);paint.setColor(state==HOLDING?0xffe78c80:TerminalUi.MINT);canvas.drawCircle(cx,cy,22*d,paint);
        paint.setColor(0xff153d30);
        if(state==LOCKED||state==READY){iconPath.reset();iconPath.moveTo(cx-7*d,cy-10*d);iconPath.lineTo(cx+12*d,cy);iconPath.lineTo(cx-7*d,cy+10*d);iconPath.lineTo(cx-3*d,cy);iconPath.close();canvas.drawPath(iconPath,paint);}
        else if(state==HOLDING||state==SENDING)canvas.drawRoundRect(cx-7*d,cy-7*d,cx+7*d,cy+7*d,2*d,2*d,paint);
        else{
            canvas.drawRoundRect(cx-4*d,cy-12*d,cx+4*d,cy+4*d,4*d,4*d,paint);
            paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(2*d);paint.setStrokeCap(Paint.Cap.ROUND);
            canvas.drawArc(cx-8*d,cy-5*d,cx+8*d,cy+9*d,0,180,false,paint);
            canvas.drawLine(cx,cy+9*d,cx,cy+13*d,paint);canvas.drawLine(cx-5*d,cy+13*d,cx+5*d,cy+13*d,paint);
        }
    }
}
