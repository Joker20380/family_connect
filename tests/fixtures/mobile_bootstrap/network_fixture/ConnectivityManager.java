package android.net;
public class ConnectivityManager {
    public Network[] networks=new Network[0];
    public Network dnsNetwork;
    public Network[] getAllNetworks(){return networks;}
    public NetworkCapabilities getNetworkCapabilities(Network network){return network.alive?network.caps:null;}
    public LinkProperties getLinkProperties(Network network){dnsNetwork=network;return new LinkProperties();}
}
