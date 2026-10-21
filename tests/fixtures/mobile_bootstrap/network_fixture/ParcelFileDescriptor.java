package android.os;
public class ParcelFileDescriptor implements AutoCloseable {
    public static ParcelFileDescriptor fromFd(int descriptor)throws java.io.IOException{return new ParcelFileDescriptor();}
    public java.io.FileDescriptor getFileDescriptor(){return new java.io.FileDescriptor();}
    public void close(){}
}
