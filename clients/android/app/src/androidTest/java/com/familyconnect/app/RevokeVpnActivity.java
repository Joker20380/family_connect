package com.familyconnect.app;
import android.app.Activity;
import android.content.Intent;
import android.net.VpnService;
import android.os.Bundle;
/** Disposable test-APK activity: asks Android to transfer VPN permission. */
public final class RevokeVpnActivity extends Activity {
 private int permissionResult=RESULT_CANCELED;
 private void record(String phase){
  android.util.Log.i("FC-VPN-HANDOVER","activity="+phase+" uid="+android.os.Process.myUid()+" package="+getPackageName()+" finishing="+isFinishing());
  String target=getIntent().getStringExtra("handover_target");
  String nonce=getIntent().getStringExtra("handover_nonce");
  if(target!=null&&(target+".test").equals(getPackageName())&&nonce!=null)
   sendBroadcast(new Intent("com.familyconnect.app.TEST_VPN_HANDOVER").setPackage(target).putExtra("nonce",nonce).putExtra("phase",phase).putExtra("result",permissionResult));
 }
 @Override public void onCreate(Bundle saved){super.onCreate(saved);record("create");getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);Intent permission=VpnService.prepare(this);record(permission==null?"prepare-null":"prepare-intent");if(permission==null)finish();else startActivityForResult(permission,1);}
 @Override protected void onResume(){super.onResume();record("resume");}
 @Override protected void onPause(){record("pause");super.onPause();}
 @Override protected void onDestroy(){record("destroy");super.onDestroy();}
 @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);permissionResult=result;record("result");finish();}
}
