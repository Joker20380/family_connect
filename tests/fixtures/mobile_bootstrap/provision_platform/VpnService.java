package android.net;
import android.content.*;
import android.os.ParcelFileDescriptor;
public class VpnService extends Context {
    public static Intent prepare(Context context){return null;}
    public boolean protect(int descriptor){return true;}
    public class Builder {
        public Builder setSession(String value){return this;}public Builder setMtu(int value){return this;}
        public Builder addAddress(String address,int prefix){return this;}public Builder addRoute(String address,int prefix){return this;}
        public Builder addDnsServer(String value){return this;}public Builder setBlocking(boolean value){return this;}
        public ParcelFileDescriptor establish(){return new ParcelFileDescriptor();}
    }
}
