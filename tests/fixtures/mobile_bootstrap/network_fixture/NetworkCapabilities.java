package android.net;
public class NetworkCapabilities {
    public static final int NET_CAPABILITY_NOT_VPN=1,NET_CAPABILITY_INTERNET=2;
    public static final int TRANSPORT_CELLULAR=3,TRANSPORT_WIFI=4,TRANSPORT_ETHERNET=5;
    public boolean notVpn=true,internet=true;
    public int transport=TRANSPORT_WIFI;
    public boolean hasCapability(int capability){return capability==1?notVpn:internet;}
    public boolean hasTransport(int wanted){return transport==wanted;}
}
