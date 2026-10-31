package com.familyconnect.app;

final class Ui60Presentation {
    static int status(String state,boolean failed){
        if("disconnecting".equals(state))return R.string.ui_disconnecting;
        if("cleanup-required".equals(state))return R.string.ui_cleanup_required;
        if("restoring".equals(state))return R.string.restoring;
        if("failed".equals(state)||("off".equals(state)&&failed))return R.string.unable_connect;
        if("off".equals(state))return R.string.off;
        if("on".equals(state))return R.string.on;
        return R.string.connecting;
    }
    static int mapHeight(int width,int inset,float aspect){return (int)Math.ceil(Math.max(0,width-2*inset)*aspect)+2*inset;}
    static int compactDialHeight(int preferred,int minimum,int deficit){return Math.max(minimum,preferred-Math.max(0,deficit));}
    static float batteryFraction(String value){
        if(value==null||!value.endsWith("%"))return -1;
        try{int level=Integer.parseInt(value.substring(0,value.length()-1));return level>=0&&level<=100?level/100f:-1;}
        catch(NumberFormatException unknown){return -1;}
    }
    static int dialHeight(int width,int height,int minimum){return width>height?minimum:Math.max(minimum,Math.round(width*.60f));}
}
