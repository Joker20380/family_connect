package android.net;
import java.net.*;
import java.util.*;
public class LinkProperties { public List<InetAddress> getDnsServers(){try{return List.of(InetAddress.getByName("127.0.0.1"));}catch(Exception error){throw new AssertionError(error);}} }
