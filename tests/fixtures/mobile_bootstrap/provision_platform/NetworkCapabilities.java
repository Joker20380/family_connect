package android.net;
public class NetworkCapabilities {
    public static final int NET_CAPABILITY_NOT_VPN=15,NET_CAPABILITY_INTERNET=12,TRANSPORT_VPN=4;
    public boolean hasCapability(int value){return true;}
    public boolean hasTransport(int value){return false;}
}
