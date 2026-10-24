package com.familyconnect.app;

final class ReadinessStop {
    static String reason(boolean cancelled,long now,long deadline){
        if(cancelled)return "CANCELLED";
        return now>=deadline?"TIMEOUT":"NONE";
    }
    static void check(boolean cancelled,long now,long deadline)throws java.io.IOException{
        String reason=reason(cancelled,now,deadline);
        if(reason.equals("CANCELLED"))throw new java.io.InterruptedIOException("RNS cancelled");
        if(reason.equals("TIMEOUT"))throw new java.net.SocketTimeoutException("RNS deadline");
    }
}
