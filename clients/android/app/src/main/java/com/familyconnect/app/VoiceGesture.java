package com.familyconnect.app;

/** Decisions use displacement from the original press, in density-independent pixels. */
final class VoiceGesture {
    enum Action { NONE, LOCK, CANCEL, SEND }
    private boolean holding,locked;
    void start(){holding=true;locked=false;}
    Action move(float dx,float dy){
        if(!holding||locked)return Action.NONE;
        float left=-dx,up=-dy;
        if(left>=80&&left>=up){reset();return Action.CANCEL;}
        if(up>=64&&up>left){locked=true;return Action.LOCK;}
        return Action.NONE;
    }
    Action release(){if(!holding||locked)return Action.NONE;reset();return Action.SEND;}
    Action cancel(){if(!holding||locked)return Action.NONE;reset();return Action.CANCEL;}
    void reset(){holding=false;locked=false;}
}
