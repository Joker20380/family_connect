package android.os;
public class ParcelFileDescriptor implements AutoCloseable {
    public static java.io.IOException failure;
    public static ParcelFileDescriptor fromFd(int descriptor)throws java.io.IOException{if(failure!=null)throw failure;return new ParcelFileDescriptor();}
    public java.io.FileDescriptor getFileDescriptor(){return new java.io.FileDescriptor();}
    public void close(){}
}
