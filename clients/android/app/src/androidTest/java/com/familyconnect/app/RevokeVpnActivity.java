package com.familyconnect.app;
import android.app.Activity;
import android.content.Intent;
import android.net.VpnService;
import android.os.Bundle;
/** Disposable test-APK activity: asks Android to transfer VPN permission. */
public final class RevokeVpnActivity extends Activity {
 @Override public void onCreate(Bundle saved){super.onCreate(saved);android.util.Log.i("FCConsent","activity_create");getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);Intent permission=VpnService.prepare(this);android.util.Log.i("FCConsent","prepare_requires_confirmation="+(permission!=null));if(permission==null)finish();else{android.util.Log.i("FCConsent","request_confirmation");startActivityForResult(permission,1);}}
 @Override protected void onResume(){super.onResume();android.util.Log.i("FCConsent","activity_resume");}
 @Override protected void onPause(){android.util.Log.i("FCConsent","activity_pause");super.onPause();}
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);android.util.Log.i("FCConsent","activity_result request="+request+" result="+result);finish();}
}
