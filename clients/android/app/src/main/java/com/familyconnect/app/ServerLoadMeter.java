package com.familyconnect.app;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;

final class ServerLoadMeter extends View {
    static final int GREEN=0xff59d69d,ORANGE=0xffffa34d;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final ServerLoadPresentation load;

    ServerLoadMeter(Context context){this(context,ServerLoadPresentation.from(null,"",0,false));}
    ServerLoadMeter(Context context,ServerLoadPresentation load){
        super(context);this.load=load;setTag("server_load_meter");
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
    }
    static int color(ServerLoadPresentation load){return load.percent==null?TerminalUi.MUTED:load.warning()?ORANGE:GREEN;}
    @Override protected void onMeasure(int width,int height){
        setMeasuredDimension(resolveSize(TerminalUi.dp(getContext(),78),width),resolveSize(TerminalUi.dp(getContext(),8),height));
    }
    @Override protected void onDraw(Canvas canvas){
        float gap=TerminalUi.dp(getContext(),2),side=Math.max(0,Math.min(getHeight(),(getWidth()-9*gap)/10f));
        float top=(getHeight()-side)/2f;
        for(int index=0;index<10;index++){
            paint.setColor(index<load.filledSegments()?color(load):TerminalUi.FRAME);
            float left=index*(side+gap);
            canvas.drawRoundRect(left,top,left+side,top+side,1,1,paint);
        }
    }
}
