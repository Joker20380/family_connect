package com.familyconnect.app;

import android.content.Context;
import android.graphics.*;
import android.net.*;
import android.os.*;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.Spinner;
import java.util.Locale;

/** Read-only Android telemetry. UID traffic includes all app traffic, not only VPN. */
final class LiveNetworkPanel extends FrameLayout {
    private final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path line=new Path();
    private final float[] samples=new float[48];
    private int count,batteryLevel=-1;
    private long lastTime,lastRx=-1,lastTx=-1;
    private String country="—",protocol="—",connectionState="—";
    private String network="—",battery="—",signal="—",rate="—";
    private Spinner countries,transports;
    LiveNetworkPanel(Context c){super(c);setWillNotDraw(false);setBackground(TerminalUi.frame(c,TerminalUi.SURFACE,TerminalUi.FRAME));}
    void selectors(Spinner country,Spinner transport){
        countries=country;transports=transport;
        addView(country,new FrameLayout.LayoutParams(1,TerminalUi.dp(getContext(),26)));
        addView(transport,new FrameLayout.LayoutParams(1,TerminalUi.dp(getContext(),26)));
    }
    @Override protected void onMeasure(int widthSpec,int heightSpec){
        int w=View.MeasureSpec.getSize(widthSpec);
        if(countries==null){super.onMeasure(widthSpec,heightSpec);return;}
        int left=w/2+TerminalUi.dp(getContext(),12),width=w-left-TerminalUi.dp(getContext(),12);
        int index=0;
        for(Spinner picker:new Spinner[]{countries,transports}){
            FrameLayout.LayoutParams params=(FrameLayout.LayoutParams)picker.getLayoutParams();
            params.width=Math.max(1,width);params.leftMargin=left;params.topMargin=TerminalUi.dp(getContext(),index++==0?84:110);
        }
        super.onMeasure(widthSpec,heightSpec);
    }
    void connection(String country,String protocol,String state){
        if(this.country.equals(country)&&this.protocol.equals(protocol)&&connectionState.equals(state))return;
        this.country=country;this.protocol=protocol;connectionState=state;invalidate();
    }
    void sample(){
        Context c=getContext();
        ConnectivityManager manager=c.getSystemService(ConnectivityManager.class);
        NetworkCapabilities cap=manager.getNetworkCapabilities(manager.getActiveNetwork());
        network=cap==null?c.getString(R.string.live_offline):cap.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?"Wi-Fi":cap.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)?c.getString(R.string.live_mobile):c.getString(R.string.live_network);
        int strength=Build.VERSION.SDK_INT>=29&&cap!=null&&cap.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?cap.getSignalStrength():Integer.MIN_VALUE;
        signal=strength==Integer.MIN_VALUE?c.getString(R.string.live_unavailable):strength+" dBm";
        int level=c.getSystemService(BatteryManager.class).getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
        batteryLevel=level;battery=level>=0&&level<=100?level+"%":"—";
        long now=SystemClock.elapsedRealtime(),rx=TrafficStats.getUidRxBytes(android.os.Process.myUid()),tx=TrafficStats.getUidTxBytes(android.os.Process.myUid());
        if(lastTime>0&&now-lastTime<900)return;
        if(lastTime>0&&rx>=lastRx&&tx>=lastTx&&lastRx>=0&&lastTx>=0){
            float down=(rx-lastRx)*1000f/(now-lastTime)/1024,up=(tx-lastTx)*1000f/(now-lastTime)/1024;
            rate=String.format(Locale.getDefault(),"↓ %.1f  ↑ %.1f KiB/s",down,up);
            if(count==samples.length){System.arraycopy(samples,1,samples,0,samples.length-1);count--;}
            samples[count++]=down+up;
        }else {count=0;rate="—";}
        lastTime=now;lastRx=rx;lastTx=tx;
        setContentDescription(network+", "+c.getString(R.string.live_battery)+" "+battery+", "+c.getString(R.string.live_signal,signal)+", "+c.getString(R.string.live_traffic)+" "+rate+", "+country+", "+protocol+", "+connectionState);invalidate();
    }
    void pause(){lastTime=0;lastRx=lastTx=-1;count=0;}
    private void text(Canvas c,String value,float x,float y,int size,int color){p.setStyle(Paint.Style.FILL);p.setColor(color);p.setTextSize(TerminalUi.dp(getContext(),size));c.drawText(value,x,y,p);}
    private void fitText(Canvas c,String value,float x,float y,float width,int size,int color){
        p.setStyle(Paint.Style.FILL);p.setColor(color);p.setTextSize(TerminalUi.dp(getContext(),size));
        p.setTextSize(Math.min(p.getTextSize(),p.getTextSize()*width/Math.max(1,p.measureText(value))));c.drawText(value,x,y,p);
    }
    @Override protected void onDraw(Canvas c){
        float d=getResources().getDisplayMetrics().density,w=getWidth(),h=getHeight();p.setTypeface(Typeface.MONOSPACE);
        text(c,getContext().getString(R.string.live_network),12*d,18*d,10,TerminalUi.MUTED);
        text(c,getContext().getString(R.string.live_battery),w*.62f,18*d,10,TerminalUi.MUTED);
        text(c,network,12*d,40*d,16,TerminalUi.MINT);text(c,battery,w*.62f,40*d,16,TerminalUi.AMBER);
        text(c,getContext().getString(R.string.live_signal,signal),12*d,58*d,10,TerminalUi.MUTED);
        if(batteryLevel>=0&&batteryLevel<=100){p.setColor(TerminalUi.FRAME);c.drawRect(w*.62f,50*d,w-12*d,54*d,p);p.setColor(TerminalUi.AMBER);c.drawRect(w*.62f,50*d,w*.62f+(w*.38f-12*d)*batteryLevel/100,54*d,p);}
        float split=w*.50f,left=12*d,right=split-10*d,column=split+12*d;
        fitText(c,getContext().getString(R.string.live_traffic),left,80*d,right-left,10,TerminalUi.MUTED);
        fitText(c,rate,left,99*d,right-left,11,TerminalUi.TEXT);
        fitText(c,getContext().getString(R.string.live_connection),column,80*d,w-column-12*d,10,TerminalUi.MUTED);
        if(countries==null){
            fitText(c,country,column,102*d,w-column-12*d,12,TerminalUi.MINT);
            fitText(c,protocol,column,121*d,w-column-12*d,11,TerminalUi.TEXT);
        }
        fitText(c,connectionState,column,147*d,w-column-12*d,10,TerminalUi.MUTED);
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(d);p.setColor(TerminalUi.FRAME);
        c.drawLine(split,70*d,split,h-10*d,p);
        float top=109*d,bottom=h-8*d,max=1;for(int i=0;i<count;i++)max=Math.max(max,samples[i]);
        for(int i=0;i<4;i++){float y=top+(bottom-top)*i/3;c.drawLine(left,y,right,y,p);}
        if(count>0){line.reset();for(int i=0;i<count;i++){float x=right-(count-1-i)*(right-left)/(samples.length-1),y=bottom-samples[i]/max*(bottom-top);if(i==0)line.moveTo(x,y);else line.lineTo(x,y);}p.setColor(TerminalUi.MINT);p.setStrokeWidth(1.5f*d);c.drawPath(line,p);}
    }
}
