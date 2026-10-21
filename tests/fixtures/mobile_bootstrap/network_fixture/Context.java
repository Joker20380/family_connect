package android.content;
public class Context {
    public android.net.ConnectivityManager manager;
    public Context getApplicationContext(){return this;}
    public <Value> Value getSystemService(Class<Value> type){return type.cast(manager);}
}
