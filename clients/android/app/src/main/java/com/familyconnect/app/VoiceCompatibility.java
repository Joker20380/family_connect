package com.familyconnect.app;

final class VoiceCompatibility {
    static int mode(int stored,int sdk){
        if(stored==7||stored==8||stored==9)return stored;
        return sdk>=29?16:9;
    }
    static int[] modes(int sdk){return sdk>=29?new int[]{16,7,8,9}:new int[]{7,8,9};}
    private VoiceCompatibility(){}
}
