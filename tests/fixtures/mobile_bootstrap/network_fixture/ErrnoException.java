package android.system;
public class ErrnoException extends Exception {
    public final int errno;
    public ErrnoException(String function,int errno){super(function);this.errno=errno;}
}
