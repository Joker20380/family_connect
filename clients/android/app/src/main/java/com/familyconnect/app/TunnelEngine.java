package com.familyconnect.app;
import android.content.Context;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
interface TunnelEngine {
    void up(String profile)throws Exception;
    void down()throws Exception;
    static TunnelEngine create(Context context,Transport type,java.util.function.Consumer<Boolean> state){
        if(type==Transport.WG)return new TunnelEngine(){
            final com.wireguard.android.backend.GoBackend backend=new com.wireguard.android.backend.GoBackend(context);
            final com.wireguard.android.backend.Tunnel tunnel=new com.wireguard.android.backend.Tunnel(){
                public String getName(){return "fc-android";}
                public void onStateChange(State s){state.accept(s==State.UP);}
            };
            public void up(String profile)throws Exception{backend.setState(tunnel,com.wireguard.android.backend.Tunnel.State.UP,com.wireguard.config.Config.parse(new ByteArrayInputStream(profile.getBytes(StandardCharsets.UTF_8))));}
            public void down()throws Exception{backend.setState(tunnel,com.wireguard.android.backend.Tunnel.State.DOWN,null);}
        };
        return new TunnelEngine(){
            final org.amnezia.awg.backend.GoBackend backend=new org.amnezia.awg.backend.GoBackend(context);
            final org.amnezia.awg.backend.Tunnel tunnel=new org.amnezia.awg.backend.Tunnel(){
                public String getName(){return "fc-android-awg";}
                public void onStateChange(State s){state.accept(s==State.UP);}
            };
            public void up(String profile)throws Exception{backend.setState(tunnel,org.amnezia.awg.backend.Tunnel.State.UP,org.amnezia.awg.config.Config.parse(new ByteArrayInputStream(profile.getBytes(StandardCharsets.UTF_8))));}
            public void down()throws Exception{backend.setState(tunnel,org.amnezia.awg.backend.Tunnel.State.DOWN,null);}
        };
    }
}
