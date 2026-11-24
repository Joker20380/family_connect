package android.content;
import java.io.*;
import android.content.res.AssetManager;
public class Context {
    public static final int MODE_APPEND=32768;
    public File getNoBackupFilesDir(){File path=new File(System.getProperty("fixture.client"));path.mkdirs();return path;}
    public File getFilesDir(){return getNoBackupFilesDir();}
    public String getPackageName(){return "com.familyconnect.app.friends";}
    public Context getApplicationContext(){return this;}
    public AssetManager getAssets(){return new AssetManager();}
    public android.content.pm.ApplicationInfo getApplicationInfo(){return new android.content.pm.ApplicationInfo();}
    public <T> T getSystemService(Class<T> type){return type.cast(new android.net.ConnectivityManager());}
    public Object startService(Intent intent){return null;}
    public FileOutputStream openFileOutput(String name,int mode)throws IOException{return new FileOutputStream(new File(getFilesDir(),name),true);}
}
