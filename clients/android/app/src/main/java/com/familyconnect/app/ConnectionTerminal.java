package com.familyconnect.app;

import java.util.ArrayList;
import java.util.List;

final class ConnectionTerminal {
    static final ConnectionTerminal VPN=new ConnectionTerminal(),CHAT=new ConnectionTerminal();
    enum Stage { PREPARING, AWG, TCP, TELEMOST, RESTORING, VPN_READY, CHAT_ENROLL, CHAT_DIRECT, CHAT_SERVICE, CHAT_EXISTING, CHAT_READY, UNAVAILABLE, AUTH, FAILED, CANCELLED, RETRY_WAIT }
    static final class Snapshot {
        final long attempt;
        final List<Stage> lines;
        final boolean finished,success;
        Snapshot(long attempt,List<Stage> lines,boolean finished,boolean success) {
            this.attempt=attempt;this.lines=List.copyOf(lines);this.finished=finished;this.success=success;
        }
    }
    private long attempt;
    private final List<Stage> lines=new ArrayList<>();
    private boolean finished,success;
    synchronized long begin(Stage stage){++attempt;lines.clear();finished=false;success=false;append(stage);return attempt;}
    synchronized void add(long token,Stage stage){if(token==attempt&&!finished)append(stage);}
    synchronized void end(long token,Stage stage,boolean ready){if(token!=attempt||finished)return;append(stage);finished=true;success=ready;}
    private void append(Stage stage){if(!lines.isEmpty()&&lines.get(lines.size()-1)==stage)return;if(lines.size()==12)lines.remove(0);lines.add(stage);}
    synchronized Snapshot snapshot(){return new Snapshot(attempt,lines,finished,success);}
    static int homePane(String vpnState,Snapshot vpn){
        if("on".equals(vpnState))return 0;
        if(!"off".equals(vpnState)&&vpn.attempt>0)return 1;
        return vpn.finished&&!vpn.success&&!vpn.lines.contains(Stage.CANCELLED)?1:0;
    }
    static int pane(String vpnState,Snapshot vpn,Snapshot chat){
        if("on".equals(vpnState))return 0;
        if(!"off".equals(vpnState)&&vpn.attempt>0)return 1;
        if(chat.attempt>0&&!chat.finished)return 2;
        if(vpn.attempt>0&&!vpn.success&&!vpn.lines.contains(Stage.CANCELLED))return 1;
        if(chat.attempt>0&&!chat.success&&!chat.lines.contains(Stage.CANCELLED))return 2;
        return 0;
    }
    void event(long token,ConnectivityOrchestrator.Event event) {
        switch(event.name){
            case "candidate_attempted":add(token,transport(event.candidate));break;
            case "candidate_failed":add(token,event.failure==ConnectivityOrchestrator.Failure.AUTH?Stage.AUTH:Stage.UNAVAILABLE);break;
            case "restoration_attempted":add(token,Stage.RESTORING);break;
            case "recovery_wait":add(token,Stage.RETRY_WAIT);break;
            case "candidate_succeeded":end(token,Stage.VPN_READY,true);break;
            case "restoration_failed":if(event.state==ConnectivityOrchestrator.State.RESTORING){add(token,Stage.UNAVAILABLE);break;}
            case "connect_failed":case "cleanup_failed":end(token,event.failure==ConnectivityOrchestrator.Failure.CANCELLED?Stage.CANCELLED:event.failure==ConnectivityOrchestrator.Failure.AUTH?Stage.AUTH:Stage.FAILED,false);break;
            default:break;
        }
    }
    static Stage transport(String value){if("restricted".equals(value))return Stage.TELEMOST;if("tcp".equals(value))return Stage.TCP;if("awg".equals(value)||"wg".equals(value))return Stage.AWG;return Stage.PREPARING;}
}
