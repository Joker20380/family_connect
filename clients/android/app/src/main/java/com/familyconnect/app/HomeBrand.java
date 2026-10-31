package com.familyconnect.app;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import android.widget.TextView;

final class HomeBrand extends TextView {
    private String connection="off";
    private boolean motion=true;
    private float cursorAlpha=1;
    private ValueAnimator cursor;

    HomeBrand(Context context){
        super(context);TerminalUi.textStyle(this,24,TerminalUi.TEXT);
        setText("EX_IT");setContentDescription("EX_IT");setTag("home_brand");
        setIncludeFontPadding(false);setGravity(android.view.Gravity.CENTER);
        setAccessibilityLiveRegion(ACCESSIBILITY_LIVE_REGION_NONE);
    }
    static float alphaAt(long elapsed){
        long phase=Math.floorMod(elapsed,9200);
        return phase>=1200?1:(float)(.5+.5*Math.cos(2*Math.PI*(phase%600)/600));
    }
    void connection(String state,boolean enabled){
        if(!connection.equals(state)||motion!=enabled){connection=state;motion=enabled;stop();}
        synchronizeAnimation();
    }
    private void stop(){if(cursor!=null){cursor.cancel();cursor.removeAllUpdateListeners();cursor=null;}cursorAlpha=1;invalidate();}
    private void synchronizeAnimation(){
        boolean pending="connecting".equals(connection)||"reconnecting".equals(connection)||"restoring".equals(connection);
        boolean run=pending&&motion&&ValueAnimator.areAnimatorsEnabled()&&isAttachedToWindow()&&isShown()&&getWindowVisibility()==VISIBLE&&hasWindowFocus();
        if(!run){stop();return;}
        if(cursor!=null)return;
        cursor=ValueAnimator.ofInt(0,9200);cursor.setDuration(9200);cursor.setRepeatCount(ValueAnimator.INFINITE);
        cursor.setInterpolator(new android.view.animation.LinearInterpolator());
        cursor.addUpdateListener(value->{cursorAlpha=alphaAt((Integer)value.getAnimatedValue());invalidate();});cursor.start();
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();synchronizeAnimation();}
    @Override protected void onDetachedFromWindow(){stop();super.onDetachedFromWindow();}
    @Override protected void onWindowVisibilityChanged(int visibility){super.onWindowVisibilityChanged(visibility);synchronizeAnimation();}
    @Override protected void onVisibilityChanged(View changed,int visibility){super.onVisibilityChanged(changed,visibility);synchronizeAnimation();}
    @Override public void onWindowFocusChanged(boolean focused){super.onWindowFocusChanged(focused);synchronizeAnimation();}
    @Override protected void onDraw(Canvas canvas){
        Paint paint=getPaint();paint.setColor(getCurrentTextColor());paint.setAlpha(255);
        float start=(getWidth()-paint.measureText("EX_IT"))/2;
        float baseline=(getHeight()-paint.ascent()-paint.descent())/2;
        canvas.drawText("EX",start,baseline,paint);start+=paint.measureText("EX");
        paint.setAlpha(Math.round(255*cursorAlpha));canvas.drawText("_",start,baseline,paint);start+=paint.measureText("_");
        paint.setAlpha(255);canvas.drawText("IT",start,baseline,paint);
    }
}
