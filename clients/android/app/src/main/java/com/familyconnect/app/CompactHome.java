package com.familyconnect.app;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

final class CompactHome extends ViewGroup {
    private final View header,workspace,map,navigation;
    private final Controls controls;
    private int gap,footer,heading,body,controlHeight,networkHeight,controlWidth,mapWidth;
    private boolean columns;

    CompactHome(Context context,View header,View dial,TextView status,TextView delivery,
                View action,View selectors,View workspace,View map,View navigation) {
        super(context);
        this.header=header;this.workspace=workspace;this.map=map;this.navigation=navigation;
        controls=new Controls(context,dial,status,delivery,action,selectors);
        for(View child:new View[]{header,controls,workspace,map,navigation}) attach(this,child);
        setTag("compact_home");controls.setTag("home_connection");workspace.setTag("home_workspace");map.setTag("home_map");
        dial.setTag("home_action");selectors.setTag("home_selectors");status.setTag("home_status");
        controls.setBackground(TerminalUi.frame(context,TerminalUi.SURFACE,TerminalUi.FRAME));
    }

    private static void attach(ViewGroup parent,View child){if(child.getParent()!=null)((ViewGroup)child.getParent()).removeView(child);parent.addView(child);}
    private int dp(int value){return TerminalUi.dp(getContext(),value);}
    private static void exact(View view,int width,int height){view.measure(MeasureSpec.makeMeasureSpec(Math.max(0,width),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(Math.max(0,height),MeasureSpec.EXACTLY));}
    @Override protected void onMeasure(int widthSpec,int heightSpec){
        int width=MeasureSpec.getSize(widthSpec),height=MeasureSpec.getSize(heightSpec);
        gap=dp(4);columns=width>height;
        footer=Math.max(dp(columns?48:58),(int)Math.ceil((columns?12:24)*getResources().getDisplayMetrics().scaledDensity)+dp(columns?12:32));
        ViewGroup buttons=(ViewGroup)navigation;
        for(int index=0;index<buttons.getChildCount();index++){
            TextView item=(TextView)buttons.getChildAt(index);
            android.graphics.drawable.Drawable[] icons=item.getCompoundDrawables();
            android.graphics.drawable.Drawable icon=icons[0]!=null?icons[0]:icons[1];
            item.setCompoundDrawables(columns?icon:null,columns?null:icon,null,null);item.setSingleLine(columns);item.setHorizontallyScrolling(false);item.setMaxLines(columns?1:2);item.setEllipsize(android.text.TextUtils.TruncateAt.END);
        }
        heading=Math.max(dp(28),(int)Math.ceil(28*getResources().getDisplayMetrics().scaledDensity));
        networkHeight=LiveNetworkPanel.minimumHeight(getContext());
        body=height-footer-gap;
        if(columns){
            controlWidth=Math.max(dp(160),width/3);mapWidth=Math.max(dp(96),width/6);
            exact(header,controlWidth,heading);exact(controls,controlWidth,body-heading-gap);
            exact(workspace,width-controlWidth-mapWidth-2*gap,body);exact(map,mapWidth,body);
        }else{
            int available=body-heading-3*gap;
            int minimum=controls.minimumHeight();
            int extra=Math.max(0,available-minimum-networkHeight-dp(88));
            int graph=Math.min(dp(16),extra/4);networkHeight+=graph;extra-=graph;
            controlHeight=minimum+Math.min(dp(24),extra/4);
            exact(header,width,heading);exact(controls,width,controlHeight);exact(workspace,width,networkHeight);
            exact(map,width,available-controlHeight-networkHeight);
        }
        exact(navigation,width,footer);setMeasuredDimension(width,height);
    }
    @Override protected void onLayout(boolean changed,int left,int top,int right,int bottom){
        int width=right-left,height=bottom-top;
        header.layout(0,0,columns?controlWidth:width,heading);
        controls.layout(0,heading+gap,columns?controlWidth:width,columns?body:heading+gap+controlHeight);
        int workspaceTop=columns?0:controls.getBottom()+gap;
        workspace.layout(columns?controlWidth+gap:0,workspaceTop,columns?width-mapWidth-gap:width,columns?body:workspaceTop+networkHeight);
        map.layout(columns?width-mapWidth:0,columns?0:workspace.getBottom()+gap,width,body);
        navigation.layout(0,height-footer,width,height);
    }

    private static final class Controls extends ViewGroup {
        private final View dial,selectors;
        private final TextView status,delivery;
        private int label,route,padding,gap,leftWidth,contentHeight;
        Controls(Context context,View dial,TextView status,TextView delivery,View action,View selectors){
            super(context);this.dial=dial;this.status=status;this.delivery=delivery;this.selectors=selectors;
            for(View child:new View[]{dial,status,delivery,selectors})attach(this,child);
            status.setTextSize(14);status.setMaxLines(2);status.setHorizontallyScrolling(false);
            delivery.setSingleLine(true);delivery.setHorizontallyScrolling(false);delivery.setEllipsize(android.text.TextUtils.TruncateAt.END);
            status.setPadding(0,0,0,0);delivery.setPadding(0,0,0,0);
        }
        private int dp(int value){return TerminalUi.dp(getContext(),value);}
        private int textHeight(TextView text){return (int)Math.ceil(text.getPaint().getFontMetrics().bottom-text.getPaint().getFontMetrics().top)+dp(2);}
        int minimumHeight(){
            padding=dp(4);gap=dp(4);label=2*textHeight(status);route=textHeight(delivery);
            int choiceHeight=2*dp(48)+textHeight(delivery);
            return 2*padding+route+gap+Math.max(choiceHeight,dp(80)+label);
        }
        @Override protected void onMeasure(int widthSpec,int heightSpec){
            int width=MeasureSpec.getSize(widthSpec),height=MeasureSpec.getSize(heightSpec);minimumHeight();
            int inner=width-2*padding;leftWidth=(inner-gap)/2;contentHeight=height-2*padding-route-gap;
            int decoration=Math.min(dp(132),contentHeight-label);
            exact(dial,leftWidth,decoration);exact(status,leftWidth,label);exact(delivery,inner,route);
            ViewGroup choices=(ViewGroup)selectors;
            for(int index=0;index<choices.getChildCount();index++)choices.getChildAt(index).getLayoutParams().height=index<2?dp(48):textHeight(delivery);
            exact(selectors,inner-leftWidth-gap,contentHeight);setMeasuredDimension(width,height);
        }
        @Override protected void onLayout(boolean changed,int left,int top,int right,int bottom){
            int edge=right-left-padding,decoration=dial.getMeasuredHeight();
            dial.layout(padding,padding,padding+leftWidth,padding+decoration);
            status.layout(padding,padding+decoration,padding+leftWidth,padding+decoration+label);
            selectors.layout(padding+leftWidth+gap,padding,edge,padding+contentHeight);
            delivery.layout(padding,padding+contentHeight+gap,edge,padding+contentHeight+gap+route);
        }
    }
}
