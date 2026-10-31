package com.familyconnect.app;

import android.content.Context;
import android.graphics.*;
import android.net.*;
import android.os.*;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.util.Locale;

/** Read-only Android telemetry. UID traffic includes all app traffic, not only VPN. */
final class LiveNetworkPanel extends ViewGroup {
    private final android.text.TextPaint paint=new android.text.TextPaint(Paint.ANTI_ALIAS_FLAG);
    private final Path line=new Path();
    private final float[] samples=new float[48];
    private final TextView[] fields=new TextView[7];
    private android.widget.Spinner countries,transports;
    private TextView delivery,connectionHeading;
    private int count,rowHeight,choicesTop,graphTop,selectorTop,batteryBarTop,verticalCompression;
    private long lastTime,lastRx=-1,lastTx=-1;
    private String country="—",protocol="—",connectionState="—";
    private String network="—",battery="—",signal="—",rate="—";
    LiveNetworkPanel(Context context){
        super(context);setWillNotDraw(false);setBackground(TerminalUi.frame(context,TerminalUi.SURFACE,TerminalUi.FRAME));
        String[] names={"network","battery","signal","country","traffic","protocol","state"};
        for(int index=0;index<fields.length;index++){
            TextView field=new TextView(context);TerminalUi.textStyle(field,12,TerminalUi.TEXT);field.setIncludeFontPadding(false);
            field.setPadding(0,0,0,0);field.setMaxLines(4);field.setHorizontallyScrolling(false);field.setTag("metric_"+names[index]);
            fields[index]=field;addView(field);
        }
        connectionHeading=new TextView(context);TerminalUi.textStyle(connectionHeading,10,TerminalUi.MUTED);
        connectionHeading.setIncludeFontPadding(false);connectionHeading.setText(R.string.live_connection);
        connectionHeading.setVisibility(GONE);addView(connectionHeading);
        setOnClickListener(view->new android.app.AlertDialog.Builder(context).setTitle(R.string.live_traffic).setMessage(getContentDescription()).setPositiveButton(android.R.string.ok,null).show());
        display();
    }
    private static int rowHeight(Context context){
        TextView text=new TextView(context);text.setTextSize(12);
        return 2*(int)Math.ceil(text.getPaint().getFontMetrics().bottom-text.getPaint().getFontMetrics().top)+TerminalUi.dp(context,2);
    }
    static int minimumHeight(Context context){int row=rowHeight(context);return Math.max(row*7/2+2*Math.max(TerminalUi.dp(context,48),row)+TerminalUi.dp(context,16),row*5+TerminalUi.dp(context,48));}
    void selectors(android.widget.Spinner countries,android.widget.Spinner transports,TextView delivery){
        this.countries=countries;this.transports=transports;this.delivery=delivery;
        for(View child:new View[]{countries,transports})addView(child);
        fields[3].setVisibility(GONE);fields[5].setVisibility(GONE);
        connectionHeading.setVisibility(VISIBLE);
        display();
    }
    int requiredHeight(int width,int compression){verticalCompression=Math.max(0,Math.min(compression,TerminalUi.dp(getContext(),20)));forceLayout();measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));return getMeasuredHeight();}
    @Override protected void onMeasure(int widthSpec,int heightSpec){
        int width=MeasureSpec.getSize(widthSpec),height=MeasureSpec.getSize(heightSpec),padding=TerminalUi.dp(getContext(),12);
        rowHeight=rowHeight(getContext());
        if(countries!=null){
            int column=width/2-2*padding,batteryLeft=Math.round(width*.62f);
            for(int index=0;index<fields.length;index++){
                int fieldWidth=index==0||index==2?batteryLeft-2*padding:index==1?width-batteryLeft-padding:column;
                fields[index].measure(MeasureSpec.makeMeasureSpec(fieldWidth,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
            }
            connectionHeading.measure(MeasureSpec.makeMeasureSpec(column,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
            for(View picker:new View[]{countries,transports})picker.measure(MeasureSpec.makeMeasureSpec(column,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
            batteryBarTop=padding+fields[1].getMeasuredHeight()+TerminalUi.dp(getContext(),6);
            choicesTop=Math.max(TerminalUi.dp(getContext(),70)-verticalCompression,padding+Math.max(fields[0].getMeasuredHeight()+fields[2].getMeasuredHeight()+TerminalUi.dp(getContext(),2),fields[1].getMeasuredHeight()+TerminalUi.dp(getContext(),10))+TerminalUi.dp(getContext(),8));
            graphTop=choicesTop+fields[4].getMeasuredHeight()+TerminalUi.dp(getContext(),8);
            selectorTop=choicesTop+connectionHeading.getMeasuredHeight()+TerminalUi.dp(getContext(),4);
            int required=padding+Math.max(selectorTop+countries.getMeasuredHeight()+transports.getMeasuredHeight()+fields[6].getMeasuredHeight(),graphTop+TerminalUi.dp(getContext(),40));
            setMeasuredDimension(width,Math.max(height,required));return;
        }
        for(int index=0;index<fields.length;index++)fields[index].measure(MeasureSpec.makeMeasureSpec(index==4?width-2*padding:(width-3*padding)/2,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(rowHeight+(index>=5?rowHeight/2:0),MeasureSpec.EXACTLY));
        setMeasuredDimension(width,height);
    }
    @Override protected void onLayout(boolean changed,int left,int top,int right,int bottom){
        int padding=TerminalUi.dp(getContext(),12),column=(right-left-3*padding)/2;
        if(countries!=null){
            place(fields[0],padding,padding);place(fields[1],Math.round((right-left)*.62f),padding);
            place(fields[2],padding,padding+fields[0].getMeasuredHeight()+TerminalUi.dp(getContext(),2));place(fields[4],padding,choicesTop);
            int start=(right-left)/2+padding;
            place(connectionHeading,start,choicesTop);
            place(countries,start,selectorTop);place(transports,start,selectorTop+countries.getMeasuredHeight());
            place(fields[6],start,selectorTop+countries.getMeasuredHeight()+transports.getMeasuredHeight());return;
        }
        for(int index=0;index<fields.length;index++){
            int row=index<4?index/2:index==4?2:3;
            int start=padding+(index==1||index==3||index==6?column+padding:0);
            fields[index].layout(start,padding+row*rowHeight,start+fields[index].getMeasuredWidth(),padding+row*rowHeight+fields[index].getMeasuredHeight());
        }
    }
    private static void place(View view,int left,int top){view.layout(left,top,left+view.getMeasuredWidth(),top+view.getMeasuredHeight());}
    void connection(String country,String protocol,String state){
        if(this.country.equals(country)&&this.protocol.equals(protocol)&&connectionState.equals(state))return;
        this.country=country;this.protocol=protocol;connectionState=state;display();
    }
    void deviceBattery(int level){String value=level>=0&&level<=100?level+"%":"—";if(!battery.equals(value)){battery=value;display();}}
    void sample(){
        Context context=getContext();ConnectivityManager manager=context.getSystemService(ConnectivityManager.class);
        NetworkCapabilities capabilities=manager.getNetworkCapabilities(manager.getActiveNetwork());
        String observedNetwork=capabilities==null?context.getString(R.string.live_offline):capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?"Wi-Fi":capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)?context.getString(R.string.live_mobile):context.getString(R.string.live_network);
        int strength=Build.VERSION.SDK_INT>=29&&capabilities!=null&&capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?capabilities.getSignalStrength():Integer.MIN_VALUE;
        int level=context.getSystemService(BatteryManager.class).getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
        acceptSample(observedNetwork,strength,level,SystemClock.elapsedRealtime(),TrafficStats.getUidRxBytes(android.os.Process.myUid()),TrafficStats.getUidTxBytes(android.os.Process.myUid()));
    }
    void acceptSample(String observedNetwork,int strength,int level,long now,long rx,long tx){
        if(lastTime>0&&now-lastTime<900)return;
        network=observedNetwork;signal=strength==Integer.MIN_VALUE?"—":strength+" dBm";battery=level>=0&&level<=100?level+"%":"—";
        if(lastTime>0&&rx>=lastRx&&tx>=lastTx&&lastRx>=0&&lastTx>=0){
            float down=(rx-lastRx)*1000f/(now-lastTime)/1024,up=(tx-lastTx)*1000f/(now-lastTime)/1024;
            rate=String.format(Locale.getDefault(),"↓ %.1f  ↑ %.1f KiB/s",down,up);
            if(count==samples.length){System.arraycopy(samples,1,samples,0,samples.length-1);count--;}
            samples[count++]=down+up;
        }else{count=0;rate="—";}
        lastTime=now;lastRx=rx;lastTx=tx;display();
    }
    void pause(){lastTime=0;lastRx=lastTx=-1;count=0;rate=network=battery=signal="—";display();}
    private void display(){
        Context context=getContext();
        String[] labels={context.getString(R.string.live_network),context.getString(R.string.live_battery),context.getString(R.string.live_signal,"").replace(":","").trim(),context.getString(R.string.terminal_country),context.getString(R.string.live_traffic),context.getString(R.string.terminal_transport),context.getString(R.string.live_connection)};
        String[] values={network,battery,signal,country,rate,protocol,countries==null?connectionState:protocol+" · "+connectionState};
        StringBuilder description=new StringBuilder();
        for(int index=0;index<fields.length;index++){
            String label=labels[index],value=values[index];
            boolean signalField=index==2,stateField=countries!=null&&index==6;
            String content=signalField?context.getString(R.string.live_signal,value):stateField?value:label+"\n"+value;
            android.text.SpannableString text=new android.text.SpannableString(content);
            int valueStart=signalField||stateField?0:label.length()+1;
            text.setSpan(new android.text.style.RelativeSizeSpan(10f/12),0,text.length(),0);
            text.setSpan(new android.text.style.ForegroundColorSpan(TerminalUi.MUTED),0,text.length(),0);
            text.setSpan(new android.text.style.RelativeSizeSpan((index<2?16f:index==4?11f:10f)/10),valueStart,text.length(),0);
            text.setSpan(new android.text.style.ForegroundColorSpan(index==0?TerminalUi.MINT:index==1?TerminalUi.AMBER:index==4?TerminalUi.TEXT:TerminalUi.MUTED),valueStart,text.length(),0);
            fields[index].setText(text);description.append(labels[index]).append(": ").append(values[index]).append("; ");
        }
        if(delivery!=null)description.append(delivery.getText());
        setContentDescription(description);invalidate();
    }
    @Override protected void onDraw(Canvas canvas){
        float density=getResources().getDisplayMetrics().density,left=12*density,right=countries==null?getWidth()-12*density:getWidth()/2f-10*density,top=countries==null?12*density+4.5f*rowHeight:graphTop,bottom=getHeight()-8*density,maximum=1;
        float batteryFraction=Ui60Presentation.batteryFraction(battery);
        if(countries!=null&&batteryFraction>=0){
            float batteryLeft=getWidth()*.62f,batteryRight=getWidth()-12*density;
            paint.setStyle(Paint.Style.FILL);paint.setColor(TerminalUi.FRAME);canvas.drawRect(batteryLeft,batteryBarTop,batteryRight,batteryBarTop+4*density,paint);
            paint.setColor(TerminalUi.AMBER);canvas.drawRect(batteryLeft,batteryBarTop,batteryLeft+(batteryRight-batteryLeft)*batteryFraction,batteryBarTop+4*density,paint);
        }
        paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(TerminalUi.stroke(getContext(),TerminalUi.STROKE_FINE));paint.setColor(TerminalUi.FRAME);
        if(countries!=null)canvas.drawLine(getWidth()/2f,choicesTop,getWidth()/2f,getHeight()-8*density,paint);
        if(bottom>top)for(int index=0;index<4;index++){float position=top+(bottom-top)*index/3;canvas.drawLine(left,position,right,position,paint);}
        for(int index=0;index<count;index++)maximum=Math.max(maximum,samples[index]);
        if(count>0&&bottom>top){line.reset();for(int index=0;index<count;index++){float x=right-(count-1-index)*(right-left)/(samples.length-1),y=bottom-samples[index]/maximum*(bottom-top);if(index==0)line.moveTo(x,y);else line.lineTo(x,y);}paint.setColor(TerminalUi.MINT);paint.setStrokeWidth(TerminalUi.stroke(getContext(),TerminalUi.STROKE_DETAIL));canvas.drawPath(line,paint);}
    }
}
