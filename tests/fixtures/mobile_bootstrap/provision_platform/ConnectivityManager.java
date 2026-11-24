package android.net;
public class ConnectivityManager {
    private final Network network=new Network();
    public Network getActiveNetwork(){return network;}
    public Network[] getAllNetworks(){return new Network[]{network};}
    public NetworkCapabilities getNetworkCapabilities(Network network){return new NetworkCapabilities();}
    public LinkProperties getLinkProperties(Network network){return new LinkProperties();}
}
