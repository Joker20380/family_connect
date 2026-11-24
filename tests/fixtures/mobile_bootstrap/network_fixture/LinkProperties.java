package android.net;
public class LinkProperties {
    public java.util.List<java.net.InetAddress> getDnsServers(){try{return java.util.List.of(java.net.InetAddress.getByName("192.0.2.53"));}catch(Exception failure){throw new AssertionError(failure);}}
}
