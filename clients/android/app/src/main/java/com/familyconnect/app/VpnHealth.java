package com.familyconnect.app;
import android.content.Context;
import android.net.*;
import java.net.*;
import java.security.SecureRandom;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
/** DNS reachability through this VPN only; never falls back to a physical network. */
final class VpnHealth {
    private final ConnectivityManager manager;
    private volatile DatagramSocket active;
    private volatile boolean cancelled;
    VpnHealth(Context context){manager=context.getSystemService(ConnectivityManager.class);}
    synchronized void cancel(){cancelled=true;if(active!=null)active.close();}
    private synchronized boolean own(DatagramSocket socket){if(cancelled){socket.close();return false;}active=socket;return true;}
    static byte[] query(int id,String label){
        byte[] name=(label+".example.com").getBytes(StandardCharsets.US_ASCII);
        java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
        byte[] header={(byte)(id>>8),(byte)id,1,0,0,1,0,0,0,0,0,0};out.write(header,0,12);
        for(String part:new String(name,StandardCharsets.US_ASCII).split("\\.")){byte[] b=part.getBytes(StandardCharsets.US_ASCII);out.write(b.length);out.write(b,0,b.length);}
        out.write(0);out.write(0);out.write(1);out.write(0);out.write(1);return out.toByteArray();
    }
    static boolean valid(byte[] query,byte[] reply,int length){
        if(length<query.length||length>reply.length||reply[0]!=query[0]||reply[1]!=query[1])return false;
        int flags=(reply[2]&255)*256+(reply[3]&255),rcode=flags&15;
        if((flags&0xfa00)!=0x8000||(rcode!=0&&rcode!=3)||reply[4]!=0||reply[5]!=1)return false;
        return Arrays.equals(Arrays.copyOfRange(query,12,query.length),Arrays.copyOfRange(reply,12,query.length));
    }
    Network find(String source){
        for(Network n:manager.getAllNetworks()){
            NetworkCapabilities c=manager.getNetworkCapabilities(n);LinkProperties p=manager.getLinkProperties(n);
            if(c==null||!c.hasTransport(NetworkCapabilities.TRANSPORT_VPN)||p==null)continue;
            for(LinkAddress a:p.getLinkAddresses())if(a.getAddress().getHostAddress().equals(source))return n;
        }return null;
    }
    boolean check(String source){
        Network network=find(source);if(network==null||cancelled)return false;
        for(String target:new String[]{"1.1.1.1","9.9.9.9"}){
            if(cancelled)return false;
            try(DatagramSocket socket=new DatagramSocket(null)){
                if(!own(socket))return false;
                network.bindSocket(socket);socket.bind(new InetSocketAddress(InetAddress.getByName(source),0));
                socket.connect(InetAddress.getByName(target),53);socket.setSoTimeout(2500);
                byte[] q=query(new SecureRandom().nextInt(65536),"fc-"+java.util.UUID.randomUUID().toString().replace("-",""));
                socket.send(new DatagramPacket(q,q.length));byte[] bytes=new byte[1232];DatagramPacket reply=new DatagramPacket(bytes,bytes.length);socket.receive(reply);
                if(valid(q,bytes,reply.getLength())&&!cancelled&&network.equals(find(source)))return true;
            }catch(Exception ignored){}finally{active=null;}
        }return false;
    }
}
