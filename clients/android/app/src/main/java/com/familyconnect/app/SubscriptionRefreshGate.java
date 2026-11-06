package com.familyconnect.app;

final class SubscriptionRefreshGate {
    static final class Cancelled extends Exception {}
    interface Commit { void run()throws Exception; }
    private Request active;
    synchronized Request begin(){if(active!=null)return null;active=new Request();return active;}
    synchronized void finish(Request request){request.cancel();if(active==request)active=null;}
    synchronized void cancel(){if(active!=null)active.cancel();}

    static final class Request {
        private Object owner;
        private String device;
        private boolean cancelled,used;
        synchronized boolean cancelled(){return cancelled;}
        synchronized boolean bind(Object owner,String device){
            if(cancelled||this.owner!=null||owner==null||device==null)return false;
            this.owner=owner;this.device=device;return true;
        }
        synchronized boolean commit(Object currentOwner,String currentDevice,Commit commit)throws Exception {
            if(cancelled||used||owner==null||owner!=currentOwner||!device.equals(currentDevice))return false;
            used=true;commit.run();return true;
        }
        synchronized void cancel(){cancelled=true;}
    }
}
