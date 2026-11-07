package android.net;
public class NetworkCapabilities {
    public static final int NET_CAPABILITY_NOT_VPN=1,NET_CAPABILITY_INTERNET=2,NET_CAPABILITY_NOT_RESTRICTED=6,NET_CAPABILITY_FOREGROUND=7;
    public static final int TRANSPORT_CELLULAR=3,TRANSPORT_WIFI=4,TRANSPORT_ETHERNET=5;
    public boolean notVpn=true,internet=true,notRestricted=true,foreground=true;
    public int transport=TRANSPORT_WIFI;
    public boolean hasCapability(int capability){return capability==1?notVpn:capability==2?internet:capability==6?notRestricted:capability==7&&foreground;}
    public boolean hasTransport(int wanted){return transport==wanted;}
}
