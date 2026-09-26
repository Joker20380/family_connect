package com.familyconnect.app;

import android.content.Context;
import android.graphics.*;
import android.view.*;
import com.google.gson.*;
import java.io.*;
import java.util.function.Consumer;

/** Offline land map plus a logical device-to-region link; never a traceroute/GPS claim. */
@android.annotation.SuppressLint("ViewConstructor") // Constructed in code with an explicit inspection callback.
final class RouteMapView extends View {
    private static final String[] REGIONS={"nl","ru"};
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path land=new Path(),route=new Path();
    private final PathMeasure measure=new PathMeasure();
    private final float[] point=new float[2];
    private final ScaleGestureDetector scaleGesture;
    private final GestureDetector gestures;
    private final Consumer<String> inspect;
    private float zoom=1,panX,panY,phase;
    private double west=-180,east=180,north=85,south=-60;
    private android.location.Location origin;
    private String region="ru",state="off",health="off";
    private boolean motion=true,dotsDirty=true,compact;
    private final float[][] dotBatches=new float[8][];
    private android.animation.ValueAnimator animator;
    RouteMapView(Context context,Consumer<String> inspect){
        super(context);this.inspect=inspect;setBackgroundColor(TerminalUi.BACKGROUND);setClickable(true);
        try(Reader reader=new InputStreamReader(context.getAssets().open("maps/land.json"),java.nio.charset.StandardCharsets.UTF_8)){
            for(JsonElement ring:JsonParser.parseReader(reader).getAsJsonArray()){
                boolean first=true;for(JsonElement vertex:ring.getAsJsonArray()){
                    JsonArray v=vertex.getAsJsonArray();float x=v.get(0).getAsFloat(),y=v.get(1).getAsFloat();
                    if(first){land.moveTo(x,y);first=false;}else land.lineTo(x,y);
                }land.close();
            }
        }catch(IOException failure){throw new IllegalStateException("Bundled map unavailable",failure);}
        scaleGesture=new ScaleGestureDetector(context,new ScaleGestureDetector.SimpleOnScaleGestureListener(){
            @Override public boolean onScale(ScaleGestureDetector detector){float previousZoom=zoom;zoom=Math.max(1,Math.min(3,zoom*detector.getScaleFactor()));
                float ratio=zoom/previousZoom;panX=detector.getFocusX()-(detector.getFocusX()-panX)*ratio;panY=detector.getFocusY()-(detector.getFocusY()-panY)*ratio;
                clamp();dotsDirty=true;invalidate();return true;}
        });
        gestures=new GestureDetector(context,new GestureDetector.SimpleOnGestureListener(){
            @Override public boolean onDown(android.view.MotionEvent e){return true;}
            @Override public boolean onScroll(android.view.MotionEvent a,android.view.MotionEvent b,float dx,float dy){if(scaleGesture.isInProgress())return true;panX-=dx;panY-=dy;clamp();dotsDirty=true;invalidate();return true;}
            @Override public boolean onDoubleTap(android.view.MotionEvent e){zoom=1;panX=panY=0;dotsDirty=true;invalidate();return true;}
            @Override public boolean onSingleTapConfirmed(android.view.MotionEvent e){
                if(e.getY()<0||e.getY()>getHeight()*.78f)return performClick();
                float x=(e.getX()-panX)/zoom/getWidth(),y=(e.getY()-panY)/zoom/(getHeight()*.78f);
                for(String code:REGIONS)if(Math.hypot((x-nodeX(code))*getWidth()*zoom,(y-nodeY(code))*getHeight()*.78f*zoom)<TerminalUi.dp(getContext(),28)){inspect.accept(code);performClick();return true;}
                return performClick();
            }
        });
    }
    void compactPreview(){compact=true;motion=false;setBackground(TerminalUi.frame(getContext(),TerminalUi.SURFACE,TerminalUi.FRAME));setContentDescription(getContext().getString(R.string.dashboard_route));}
    private float longitudeX(double lon){return (float)((lon-west)/(east-west));}
    private float latitudeY(double lat){return (float)((north-lat)/(north-south));}
    private float nodeX(String code){return longitudeX(code.equals("nl")?5:38);}
    private float nodeY(String code){return latitudeY(code.equals("nl")?52:56);}
    void locate(android.location.Location location){
        if(origin==null){north=Math.min(90,Math.max(85,location.getLatitude()+4));south=Math.max(-90,Math.min(-60,location.getLatitude()-4));zoom=1;panX=panY=0;}
        origin=new android.location.Location(location);dotsDirty=true;animateState();postInvalidateOnAnimation();
    }
    private void clamp(){panX=Math.max(getWidth()*(1-zoom),Math.min(0,panX));panY=Math.max(getHeight()*.78f*(1-zoom),Math.min(0,panY));}
    @android.annotation.SuppressLint("ClickableViewAccessibility") // GestureDetector calls performClick for confirmed taps.
    @Override public boolean onTouchEvent(android.view.MotionEvent event){if(compact)return super.onTouchEvent(event);if(getParent()!=null)getParent().requestDisallowInterceptTouchEvent(true);scaleGesture.onTouchEvent(event);gestures.onTouchEvent(event);return true;}
    @Override public boolean performClick(){super.performClick();return true;}
    void update(String region,String state,String health,boolean motion){
        if(this.region.equals(region)&&this.state.equals(state)&&this.health.equals(health)&&this.motion==motion)return;
        this.region=region;this.state=state;this.health=health;this.motion=motion;
        setContentDescription(getContext().getString(R.string.dashboard_route)+": "+region.toUpperCase(java.util.Locale.ROOT)+", "+state);animateState();invalidate();
    }
    private void animateState(){
        boolean run=motion&&isAttachedToWindow()&&getWindowVisibility()==VISIBLE&&isShown()&&android.animation.ValueAnimator.areAnimatorsEnabled();
        if(run&&animator==null){animator=android.animation.ValueAnimator.ofFloat(0,1);animator.setDuration(5200);animator.setRepeatCount(-1);animator.setInterpolator(new android.view.animation.LinearInterpolator());animator.addUpdateListener(a->{phase=(float)a.getAnimatedValue();invalidate();});animator.start();}
        else if(!run&&animator!=null){animator.cancel();animator=null;}
    }
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();animateState();}
    @Override protected void onDetachedFromWindow(){if(animator!=null){animator.cancel();animator=null;}super.onDetachedFromWindow();}
    @Override protected void onWindowVisibilityChanged(int visibility){super.onWindowVisibilityChanged(visibility);animateState();}
    @Override protected void onVisibilityChanged(View changed,int visibility){super.onVisibilityChanged(changed,visibility);animateState();}
    @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){super.onSizeChanged(w,h,oldw,oldh);clamp();dotsDirty=true;}
    private void drawLandDots(Canvas canvas,float w,float mapH,float d){
        if(dotsDirty){
            Path projected=new Path();Matrix projection=new Matrix();
            float sx=(float)(w/(east-west))*zoom,sy=(float)(-mapH/(north-south))*zoom;
            projection.setValues(new float[]{sx,0,(float)-west*sx+panX,0,sy,(float)-north*sy+panY,0,0,1});
            land.transform(projection,projected);
            Region mask=new Region();mask.setPath(projected,new Region(0,0,(int)w,(int)mapH));
            java.util.ArrayList<java.util.ArrayList<Float>> batches=new java.util.ArrayList<>();
            for(int i=0;i<dotBatches.length;i++)batches.add(new java.util.ArrayList<>());
            // Reference-style stippling: clean staggered rows, equal dot coverage.
            float spacing=2.3f*d,rowSpacing=spacing*.8660254f;
            float pixelOffset=(Math.max(1,Math.round(.65f*d))&1)==1?.5f:0;
            for(int row=0;row*rowSpacing<mapH;row++)for(int col=0;col*spacing<w;col++){
                float x=Math.round((col+.5f*(row&1))*spacing-pixelOffset)+pixelOffset;
                float y=Math.round(row*rowSpacing-pixelOffset)+pixelOffset;
                if(x<0||y<0||x>=w||y>=mapH||!mask.contains((int)x,(int)y))continue;
                java.util.ArrayList<Float> batch=batches.get(0);batch.add(x);batch.add(y);
            }
            for(int i=0;i<dotBatches.length;i++){
                java.util.ArrayList<Float> batch=batches.get(i);dotBatches[i]=new float[batch.size()];
                for(int j=0;j<batch.size();j++)dotBatches[i][j]=batch.get(j);
            }
            dotsDirty=false;
        }
        paint.setStyle(Paint.Style.STROKE);paint.setStrokeCap(Paint.Cap.ROUND);paint.setStrokeWidth(Math.max(1,Math.round(.65f*d)));paint.setColor(TerminalUi.MINT);
        // One opacity for all land; pixel-aligned centers give equal raster coverage.
        float shimmer=motion?(float)Math.sin(2*Math.PI*phase):0;
        paint.setAlpha(120+Math.round(6*shimmer));
        for(float[] batch:dotBatches)canvas.drawPoints(batch,paint);
        paint.setAlpha(255);paint.setStrokeCap(Paint.Cap.BUTT);
    }
    @Override protected void onDraw(Canvas c){
        float w=getWidth(),h=getHeight(),mapH=compact?Math.min(h,w*145f/360f):h*.78f,d=getResources().getDisplayMetrics().density;
        if(compact){
            float inset=6*d;w=Math.min(w-2*inset,(h-2*inset)*360f/145f);mapH=w*145f/360f;
            c.translate((getWidth()-w)/2,(h-mapH)/2);
        }
        int viewport=c.save();c.clipRect(0,0,w,mapH);
        try {
        paint.setColor(TerminalUi.FRAME);paint.setAlpha(45);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(.4f*d);
        float grid=16*d;
        for(float x=0;x<w;x+=grid)c.drawLine(x,0,x,mapH,paint);
        for(float y=0;y<mapH;y+=grid)c.drawLine(0,y,w,y,paint);
        paint.setAlpha(255);drawLandDots(c,w,mapH,d);
        c.save();c.translate(panX,panY);c.scale(zoom,zoom);
        paint.setTypeface(Typeface.MONOSPACE);paint.setTextSize(12*d/zoom);
        for(String code:REGIONS){if(compact&&!code.equals(region))continue;float x=nodeX(code)*w,y=nodeY(code)*mapH;paint.setStyle(Paint.Style.FILL);paint.setColor(code.equals(region)?TerminalUi.AMBER:TerminalUi.MINT);c.drawCircle(x,y,4*d/zoom,paint);if(!compact)c.drawText(code.toUpperCase(java.util.Locale.ROOT),x+8*d/zoom,y-8*d/zoom,paint);}
        c.restore();
        if(origin==null)return;
        float targetX=nodeX(region)*w*zoom+panX,targetY=nodeY(region)*mapH*zoom+panY;
        float startX=longitudeX(origin.getLongitude())*w*zoom+panX,startY=latitudeY(origin.getLatitude())*mapH*zoom+panY;
        paint.setColor(state.equals("on")&&health.equals("ok")?TerminalUi.MINT:TerminalUi.AMBER);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(2*d);
        route.reset();route.moveTo(startX,startY);route.cubicTo(startX,Math.min(startY,targetY)-h*.16f,targetX,Math.min(startY,targetY)-h*.16f,targetX,targetY);
        paint.setAlpha(state.equals("off")?150:255);paint.setStyle(Paint.Style.FILL);
        measure.setPath(route,false);float length=measure.getLength(),spacing=10*d;
        for(float distance=phase*spacing;distance<length;distance+=spacing){measure.getPosTan(distance,point,null);c.drawCircle(point[0],point[1],1.6f*d,paint);}
        paint.setAlpha(255);
        paint.setStyle(Paint.Style.FILL);c.drawCircle(startX,startY,4*d,paint);

        } finally {
            c.restoreToCount(viewport);paint.setAlpha(255);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(d);paint.setColor(TerminalUi.FRAME);
            if(!compact)c.drawRect(d/2,d/2,w-d/2,mapH-d/2,paint);
        }
    }
}
