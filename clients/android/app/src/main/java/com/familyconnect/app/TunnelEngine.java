package com.familyconnect.app;
import android.content.Context;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
interface TunnelEngine {
    void up(String profile)throws Exception;
    void down()throws Exception;
    static TunnelEngine create(Context context,Transport type,java.util.function.Consumer<Boolean> state){
        return new TunnelEngine(){
            final org.amnezia.awg.backend.GoBackend backend=new org.amnezia.awg.backend.GoBackend(context);
            final org.amnezia.awg.backend.Tunnel tunnel=new org.amnezia.awg.backend.Tunnel(){
                public String getName(){return type==Transport.WG?"fc-android":"fc-android-awg";}
                public void onStateChange(State s){state.accept(s==State.UP);}
            };
            public void up(String profile)throws Exception{backend.setState(tunnel,org.amnezia.awg.backend.Tunnel.State.UP,org.amnezia.awg.config.Config.parse(new ByteArrayInputStream(profile.getBytes(StandardCharsets.UTF_8))));}
            public void down()throws Exception{backend.setState(tunnel,org.amnezia.awg.backend.Tunnel.State.DOWN,null);}
        };
    }
}
