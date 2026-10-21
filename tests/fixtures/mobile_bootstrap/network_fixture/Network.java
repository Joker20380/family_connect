package android.net;
public class Network {
    public final NetworkCapabilities caps=new NetworkCapabilities();
    public boolean alive=true;
    public int opened,bound;
    public final long generation;
    public Runnable beforeOpen=()->{};
    public Network(long generation){this.generation=generation;}
    public long getNetworkHandle(){return generation;}
    public java.net.URLConnection openConnection(java.net.URL url)throws java.io.IOException{
        beforeOpen.run();
        if(!alive)throw new java.net.ConnectException("lost network");
        opened++;
        return url.openConnection();
    }
    public void bindSocket(java.io.FileDescriptor descriptor)throws java.io.IOException{
        if(!alive)throw new java.io.IOException("lost network");bound++;
    }
}
