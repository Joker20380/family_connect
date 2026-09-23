package com.familyconnect.app;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.widget.CompoundButton;

/** Capsule switch with native checked/accessibility semantics and bounded motion. */
final class TerminalToggle extends CompoundButton {
    private final android.text.TextPaint paint=new android.text.TextPaint(Paint.ANTI_ALIAS_FLAG);
    private float position;
    private boolean controlled,motion=true,ready,pending;
    private ValueAnimator animator;
    TerminalToggle(Context context){
        super(context);setButtonDrawable(null);setBackground(TerminalUi.frame(context,TerminalUi.SURFACE,TerminalUi.FRAME));
        TerminalUi.textStyle(this,14,TerminalUi.TEXT);setPadding(0,0,0,0);setMinHeight(TerminalUi.dp(context,48));ready=true;
    }
    void setControlled(boolean value){controlled=value;}
    @Override public void toggle(){if(!controlled)super.toggle();}
    void setMotion(boolean value){motion=value;if(!motion)settle();}
    void setPending(boolean value){if(pending!=value){pending=value;invalidate();}}
    @Override public void setChecked(boolean checked){
        boolean changed=checked!=isChecked();super.setChecked(checked);
        if(!ready){position=checked?1:0;return;}
        if(!changed)return;
        if(animator!=null)animator.cancel();
        float target=checked?1:0;
        if(motion&&isAttachedToWindow()&&isShown()&&ValueAnimator.areAnimatorsEnabled()){
            animator=ValueAnimator.ofFloat(position,target);animator.setDuration(180);
            animator.addUpdateListener(a->{position=(float)a.getAnimatedValue();invalidate();});animator.start();
        }else{position=target;invalidate();}
    }
    private void settle(){if(animator!=null){animator.cancel();animator=null;}position=isChecked()?1:0;invalidate();}
    @Override protected void onDetachedFromWindow(){settle();super.onDetachedFromWindow();}
    @Override protected void onWindowVisibilityChanged(int value){super.onWindowVisibilityChanged(value);if(value!=VISIBLE)settle();}
    @Override public CharSequence getAccessibilityClassName(){return android.widget.Switch.class.getName();}
    @Override protected void onDraw(Canvas canvas){
        float d=getResources().getDisplayMetrics().density,w=getWidth(),h=getHeight(),cy=h/2;
        float left=w-63*d,right=w-12*d,radius=15.5f*d;
        int color=pending?TerminalUi.AMBER:blend(TerminalUi.AMBER,TerminalUi.MINT,position);
        paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(d);paint.setColor(color);paint.setAlpha(isEnabled()?210:95);
        paint.setStyle(Paint.Style.FILL);paint.setColor(TerminalUi.TEXT);paint.setAlpha(isEnabled()?255:120);
        paint.setTypeface(getTypeface());paint.setTextSize(getTextSize());paint.setTextAlign(Paint.Align.LEFT);
        canvas.save();canvas.clipRect(10*d,0,left-8*d,h);
        String label=getText().toString();float available=Math.max(1,left-20*d);
        float measured=paint.measureText(label);
        if(measured>available)paint.setTextSize(Math.max(12*getResources().getDisplayMetrics().scaledDensity,getTextSize()*available/measured));
        label=android.text.TextUtils.ellipsize(label,paint,available,android.text.TextUtils.TruncateAt.END).toString();
        canvas.drawText(label,12*d,cy-(paint.ascent()+paint.descent())/2,paint);canvas.restore();
        paint.setColor(color);paint.setAlpha(isEnabled()?35:15);canvas.drawRoundRect(left,cy-radius,right,cy+radius,radius,radius,paint);
        paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(d);paint.setAlpha(isEnabled()?255:90);
        canvas.drawRoundRect(left,cy-radius,right,cy+radius,radius,radius,paint);
        float knob=left+radius+position*(right-left-radius*2);
        paint.setStyle(Paint.Style.FILL);paint.setAlpha(isEnabled()?40:15);canvas.drawCircle(knob,cy,14.5f*d,paint);
        paint.setAlpha(isEnabled()?255:100);canvas.drawCircle(knob,cy,12.5f*d,paint);
        paint.setTextSize(9*d);paint.setTextAlign(Paint.Align.CENTER);
        canvas.drawText(pending?"…":isChecked()?"I":"O",isChecked()?left+9*d:right-9*d,cy-(paint.ascent()+paint.descent())/2,paint);
        paint.setAlpha(255);
    }
    private static int blend(int a,int b,float p){
        return android.graphics.Color.rgb(Math.round(android.graphics.Color.red(a)+(android.graphics.Color.red(b)-android.graphics.Color.red(a))*p),
            Math.round(android.graphics.Color.green(a)+(android.graphics.Color.green(b)-android.graphics.Color.green(a))*p),
            Math.round(android.graphics.Color.blue(a)+(android.graphics.Color.blue(b)-android.graphics.Color.blue(a))*p));
    }
}
