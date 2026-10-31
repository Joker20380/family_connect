package com.familyconnect.app;

import android.content.Context;
import android.graphics.Typeface;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

final class ConnectionTerminalView extends LinearLayout {
    private final ConnectionTerminal model;
    private final boolean chat;
    private final Button title,cancel;
    private final TextView output;
    private final ScrollView scroll;
    private boolean expanded;
    private final boolean embedded;
    private long attempt;
    ConnectionTerminalView(Context context,ConnectionTerminal model,boolean chat,Runnable cancelAction){
        this(context,model,chat,cancelAction,false);
    }
    ConnectionTerminalView(Context context,ConnectionTerminal model,boolean chat,Runnable cancelAction,boolean embedded){
        super(context);this.model=model;this.chat=chat;this.embedded=embedded;setOrientation(VERTICAL);setBackground(TerminalUi.frame(context,TerminalUi.BACKGROUND,TerminalUi.FRAME));
        title=new Button(context);TerminalUi.actionStyle(title);addView(title,new LayoutParams(-1,-2));title.setOnClickListener(view->{expanded=!expanded;refresh();});
        scroll=new ScrollView(context){@Override protected void onMeasure(int width,int height){if(embedded)super.onMeasure(width,height);else super.onMeasure(width,MeasureSpec.makeMeasureSpec(Math.max(TerminalUi.dp(context,72),getResources().getDisplayMetrics().heightPixels/5),MeasureSpec.AT_MOST));}};
        output=new TextView(context);TerminalUi.textStyle(output,13,TerminalUi.MINT);output.setTypeface(Typeface.MONOSPACE);int padding=TerminalUi.dp(context,8);output.setPadding(padding,padding,padding,padding);output.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_NONE);
        if(embedded){title.setVisibility(GONE);output.setIncludeFontPadding(false);output.setPadding(padding,TerminalUi.dp(context,2),padding,TerminalUi.dp(context,2));addView(output,new LayoutParams(-1,0,1));output.setGravity(android.view.Gravity.BOTTOM);output.setOnClickListener(view->{StringBuilder history=new StringBuilder();ConnectionTerminal.Snapshot current=model.snapshot();for(ConnectionTerminal.Stage stage:current.lines){if(history.length()>0)history.append('\n');history.append(getResources().getStringArray(R.array.connection_terminal_stages)[stage.ordinal()]);}android.app.AlertDialog.Builder dialog=new android.app.AlertDialog.Builder(context).setTitle(chat?R.string.connection_terminal_chat:R.string.connection_terminal_vpn).setMessage(history).setPositiveButton(android.R.string.ok,null);if(chat&&!current.finished)dialog.setNeutralButton(android.R.string.cancel,(ignored,which)->{if(model.snapshot().attempt==current.attempt)cancelAction.run();});dialog.show();});}
        else{scroll.addView(output);addView(scroll,new LayoutParams(-1,-2));}
        cancel=new Button(context);TerminalUi.actionStyle(cancel);cancel.setText(android.R.string.cancel);cancel.setOnClickListener(view->cancelAction.run());addView(cancel,new LayoutParams(-1,-2));refresh();
    }
    void refresh(){
        ConnectionTerminal.Snapshot snapshot=model.snapshot();if(!embedded)setVisibility(snapshot.attempt==0?GONE:VISIBLE);if(snapshot.attempt==0)return;
        if(attempt!=snapshot.attempt){attempt=snapshot.attempt;expanded=false;}
        String heading=getContext().getString(chat?R.string.connection_terminal_chat:R.string.connection_terminal_vpn)+" #"+attempt;
        title.setText(heading+(snapshot.finished?" · "+line(snapshot.lines.get(snapshot.lines.size()-1)):" · …"));
        StringBuilder text=new StringBuilder();
        int capacity=embedded?Math.max(1,(output.getHeight()-output.getPaddingTop()-output.getPaddingBottom())/Math.max(1,output.getLineHeight())):12;
        java.util.List<ConnectionTerminal.Stage> lines=snapshot.lines;
        if(embedded&&snapshot.finished&&!snapshot.success&&!lines.contains(ConnectionTerminal.Stage.CANCELLED)){
            ConnectionTerminal.Stage last=ConnectionTerminal.Stage.PREPARING,cause=ConnectionTerminal.Stage.FAILED;
            for(ConnectionTerminal.Stage stage:lines){if(stage==ConnectionTerminal.Stage.UNAVAILABLE||stage==ConnectionTerminal.Stage.AUTH)cause=stage;else if(stage!=ConnectionTerminal.Stage.FAILED)last=stage;}
            lines=java.util.List.of(last,cause);
        }
        int start=Math.max(0,lines.size()-capacity);
        for(int index=start;index<lines.size();index++){
            if(text.length()>0)text.append('\n');String value=line(lines.get(index));
            if(embedded)value=android.text.TextUtils.ellipsize(value,output.getPaint(),Math.max(1,output.getWidth()-output.getPaddingLeft()-output.getPaddingRight()),android.text.TextUtils.TruncateAt.END).toString();
            text.append(value);
        }
        if(!text.toString().contentEquals(output.getText())){output.setText(text);if(!embedded)scroll.post(()->{if(isShown())scroll.fullScroll(FOCUS_DOWN);});}
        scroll.setVisibility(!snapshot.finished||!snapshot.success||expanded?VISIBLE:GONE);output.setTextColor(snapshot.finished&&!snapshot.success?TerminalUi.AMBER:TerminalUi.MINT);cancel.setVisibility(embedded||snapshot.finished?GONE:VISIBLE);
    }
    @Override protected void onSizeChanged(int width,int height,int oldWidth,int oldHeight){super.onSizeChanged(width,height,oldWidth,oldHeight);if(embedded)post(this::refresh);}
    private String line(ConnectionTerminal.Stage stage){return getResources().getStringArray(embedded?R.array.connection_terminal_compact:R.array.connection_terminal_stages)[stage.ordinal()];}
}
