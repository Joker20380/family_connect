package com.familyconnect.app;
import android.content.Context;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
interface TunnelEngine {
    void up(String profile)throws Exception;
    void down()throws Exception;
    default String probeDns(String query,int budgetMillis){return null;}
    static TunnelEngine create(Context context,Transport type,java.util.function.Consumer<Boolean> state){
        return create(context,type,state,new AppVpnAndroid(context,AppVpnPolicy.all()));
    }
    static TunnelEngine create(Context context,Transport type,java.util.function.Consumer<Boolean> state,AppVpnAndroid applications){
        if(type==Transport.TCP)return new TcpTunnelEngine(context,state,applications);
        return new TunnelEngine(){
            String source;
            final org.amnezia.awg.backend.GoBackend backend=new org.amnezia.awg.backend.GoBackend(context);
            final org.amnezia.awg.backend.Tunnel tunnel=new org.amnezia.awg.backend.Tunnel(){
                public String getName(){return type==Transport.WG?"fc-android":"fc-android-awg";}
                public void onStateChange(State s){state.accept(s==State.UP);}
            };
            public void up(String profile)throws Exception{
                org.amnezia.awg.config.Config config=applications.awg(org.amnezia.awg.config.Config.parse(new ByteArrayInputStream(profile.getBytes(StandardCharsets.UTF_8))));
                source=config.getInterface().getAddresses().stream().filter(address->address.getAddress() instanceof java.net.Inet4Address).findFirst().orElseThrow().getAddress().getHostAddress();
                backend.setState(tunnel,org.amnezia.awg.backend.Tunnel.State.UP,config);
            }
            public String probeDns(String query,int budgetMillis){
                try{
                    return NativeTcp.awgDns(backend.ownedHandle(),source,query,budgetMillis);
                }catch(Exception unavailable){return null;}
            }
            public void down()throws Exception{backend.setState(tunnel,org.amnezia.awg.backend.Tunnel.State.DOWN,null);backend.awaitShutdown();}
        };
    }
}
