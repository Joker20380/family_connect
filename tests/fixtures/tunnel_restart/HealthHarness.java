package com.familyconnect.app;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.os.SystemClock;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.Arrays;
import java.util.concurrent.atomic.AtomicInteger;

public final class HealthHarness {
    static volatile String mode="OK";
    static volatile boolean running=true;
    static int port;
    static final AtomicInteger requests=new AtomicInteger();
    static final ConnectivityManager manager=new ConnectivityManager();
    static final Context context=new Context(manager);
    static void require(boolean value,String name){if(!value)throw new AssertionError(name);}
    static long deadline(){return SystemClock.elapsedRealtime()+600;}
    public static void main(String[] arguments)throws Exception{
        try(DatagramSocket server=new DatagramSocket(0,InetAddress.getLoopbackAddress())){
            port=server.getLocalPort();server.setSoTimeout(100);
            Thread responder=new Thread(()->{
                while(running){
                    try{
                        byte[] bytes=new byte[1232];DatagramPacket request=new DatagramPacket(bytes,bytes.length);server.receive(request);
                        requests.incrementAndGet();String behavior=mode;
                        if(behavior.equals("BLACKHOLE"))continue;
                        if(behavior.equals("DELAY"))Thread.sleep(120);
                        if(behavior.equals("STALE"))manager.current=new Network();
                        byte[] answer=Arrays.copyOf(bytes,request.getLength());answer[2]=(byte)0x81;answer[3]=(byte)0x83;
                        if(behavior.equals("MALFORMED"))answer[0]^=1;
                        server.send(new DatagramPacket(answer,answer.length,request.getSocketAddress()));
                    }catch(java.net.SocketTimeoutException ignored){}catch(Exception failure){if(running)throw new RuntimeException(failure);}
                }
            });responder.start();
            try{
                VpnHealth health=new VpnHealth(context);
                require(health.check("127.0.0.1",deadline()),"normal VPN-bound DNS projection");
                AtomicInteger progress=new AtomicInteger();
                Thread useful=new Thread(()->{while(running&&!Thread.currentThread().isInterrupted()){progress.incrementAndGet();try{Thread.sleep(1);}catch(InterruptedException done){return;}}});
                useful.start();mode="DELAY";
                require(health.check("127.0.0.1",deadline())&&progress.get()>20,"delayed probe with useful progress");
                useful.interrupt();useful.join(1000);require(!useful.isAlive(),"progress worker closed");
                mode="BLACKHOLE";
                require(!health.check("127.0.0.1",SystemClock.elapsedRealtime()+80),"true blackhole returns false");
                mode="MALFORMED";require(!health.check("127.0.0.1",deadline()),"malformed response rejected");
                mode="STALE";require(!health.check("127.0.0.1",deadline()),"old network generation rejected");
                mode="OK";require(health.check("127.0.0.1",deadline()),"fresh generation found");
                manager.current=null;int prior=requests.get();
                require(!health.check("127.0.0.1",deadline())&&requests.get()==prior,"absent network does not send");
                manager.current=new Network();mode="BLACKHOLE";boolean[] result={true};
                Thread pending=new Thread(()->result[0]=health.check("127.0.0.1",SystemClock.elapsedRealtime()+5000));
                prior=requests.get();pending.start();long stop=deadline();
                while(requests.get()==prior&&SystemClock.elapsedRealtime()<stop)Thread.sleep(1);
                require(requests.get()>prior,"probe entered socket");health.cancel();pending.join(1000);
                require(!pending.isAlive()&&!result[0],"cancel releases probe without success");
                mode="OK";prior=requests.get();
                require(!health.check("127.0.0.1",deadline())&&requests.get()==prior,"cancelled checker never reused");
                VpnHealth next=new VpnHealth(context);require(next.check("127.0.0.1",deadline()),"new checker after cleanup succeeds");next.cancel();
                require(manager.bindings.get()>0,"network binding called");
                System.out.println("PASS_HEALTH_10_SCENARIOS_NO_EXTERNAL_PACKETS");
            }finally{running=false;responder.join(1000);require(!responder.isAlive(),"responder closed");}
        }
    }
}
