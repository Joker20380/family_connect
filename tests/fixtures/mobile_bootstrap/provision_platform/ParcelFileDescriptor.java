package android.os;
public class ParcelFileDescriptor implements AutoCloseable { private boolean closed;public int getFd(){if(closed)throw new AssertionError();return 100;}public void close(){closed=true;} }
