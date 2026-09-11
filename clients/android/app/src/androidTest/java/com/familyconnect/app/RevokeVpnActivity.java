package com.familyconnect.app;
import android.app.Activity;
import android.content.Intent;
import android.net.VpnService;
import android.os.Bundle;
/** Disposable test-APK activity: asks Android to transfer VPN permission. */
public final class RevokeVpnActivity extends Activity {
 @Override public void onCreate(Bundle saved){super.onCreate(saved);Intent permission=VpnService.prepare(this);if(permission==null)finish();else startActivityForResult(permission,1);}
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);finish();}
}
