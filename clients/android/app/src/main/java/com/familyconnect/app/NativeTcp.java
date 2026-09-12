package com.familyconnect.app;
import android.net.VpnService;
final class NativeTcp {
    static void load(android.content.Context context){org.amnezia.awg.util.SharedLibraryLoader.loadSharedLibrary(context,"fc-awg");}
    static native long start(int tunFd,String profile,VpnService protector);
    static native boolean stop(long handle);
    static native int connections(long handle);
}
