package com.familyconnect.app;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.location.*;
import android.os.*;
import java.util.function.Consumer;

/** Approximate, foreground-only location. No coordinates are logged or persisted. */
final class RouteLocation implements LocationListener {
    private final Context context;private final LocationManager manager;
    private final Consumer<Location> result;private final Consumer<Integer> status;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private boolean received,active;
    private int generation;
    private final java.util.List<CancellationSignal> requests=new java.util.ArrayList<>();
    private final Runnable timeout=this::expire;
    private void expire(){if(!received){status.accept(R.string.route_location_unavailable);stop();}}
    RouteLocation(Context context,Consumer<Location> result,Consumer<Integer> status){this.context=context;this.result=result;this.status=status;manager=context.getSystemService(LocationManager.class);}
    boolean permitted(){return context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;}
    @android.annotation.SuppressLint("MissingPermission") // Checked immediately before querying and subscribing.
    void start(){
        stop();received=false;if(!permitted()){status.accept(R.string.route_location_permission);return;}
        status.accept(R.string.route_location_wait);active=true;
        try{
            java.util.List<String> providers=manager.getProviders(true);
            Location newest=null;boolean subscribed=false;final int attempt=generation;
            for(String provider:new String[]{"fused",LocationManager.NETWORK_PROVIDER}){
                if(!providers.contains(provider))continue;
                try{
                    Location last=manager.getLastKnownLocation(provider);
                    if(fresh(last)&&(newest==null||last.getElapsedRealtimeNanos()>newest.getElapsedRealtimeNanos()))newest=last;
                    manager.requestLocationUpdates(provider,5000,0,this,Looper.getMainLooper());subscribed=true;
                    if(Build.VERSION.SDK_INT>=30){
                        CancellationSignal request=new CancellationSignal();requests.add(request);
                        manager.getCurrentLocation(provider,request,context.getMainExecutor(),location->{if(active&&generation==attempt&&location!=null)onLocationChanged(location);});
                    }
                }catch(IllegalArgumentException ignored){/* Another enabled provider can still answer. */}
            }
            if(newest!=null)onLocationChanged(newest);
            if(!subscribed){status.accept(R.string.route_location_unavailable);stop();return;}
            if(!received)handler.postDelayed(timeout,25000);
        }catch(SecurityException|IllegalArgumentException error){status.accept(R.string.route_location_unavailable);stop();}
    }
    private boolean fresh(Location location){if(location==null)return false;long age=SystemClock.elapsedRealtimeNanos()-location.getElapsedRealtimeNanos();return age>=0&&age<600_000_000_000L;}
    @Override public void onLocationChanged(Location location){if(!active||!fresh(location))return;received=true;handler.removeCallbacks(timeout);result.accept(location);status.accept(R.string.route_location_ready);}
    @Override public void onProviderDisabled(String provider){status.accept(R.string.route_location_unavailable);}
    @Override public void onProviderEnabled(String provider){}
    @Override public void onStatusChanged(String provider,int state,Bundle extras){}
    void stop(){active=false;generation++;handler.removeCallbacks(timeout);for(CancellationSignal request:requests)request.cancel();requests.clear();try{manager.removeUpdates(this);}catch(SecurityException ignored){}}
}
