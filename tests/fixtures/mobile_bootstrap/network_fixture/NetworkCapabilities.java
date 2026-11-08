package android.net;
public class NetworkCapabilities {
    public static final int NET_CAPABILITY_NOT_VPN=15,NET_CAPABILITY_INTERNET=12,NET_CAPABILITY_NOT_RESTRICTED=13,NET_CAPABILITY_FOREGROUND=19;
    public static final int TRANSPORT_CELLULAR=3,TRANSPORT_WIFI=4,TRANSPORT_ETHERNET=5;
    public boolean notVpn=true,internet=true,notRestricted=true,foreground=true;
    public int transport=TRANSPORT_WIFI;
    public boolean hasCapability(int capability){return capability==15?notVpn:capability==12?internet:capability==13?notRestricted:capability==(android.os.Build.VERSION.SDK_INT==27?18:19)&&foreground;}
    public boolean hasTransport(int wanted){return transport==wanted;}
}
