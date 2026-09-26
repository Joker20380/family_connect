package com.familyconnect.app;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.view.WindowManager;
import android.widget.*;
import com.google.gson.JsonObject;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.EncodeHintType;
import com.google.zxing.qrcode.QRCodeWriter;
import com.google.zxing.common.BitMatrix;
import java.util.Collections;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** The QR contains a referral link, never a batch of invitation codes. */
public final class ReferralActivity extends LocalizedActivity {
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private LinearLayout content;
    private TextView status;
    private Button load;
    private boolean rendered;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        content=TerminalUi.screen(this,getString(R.string.referral_title));
        if(!getPackageName().endsWith(".friends"))TerminalUi.button(content,R.string.chat_connection,this::finish);
        TerminalUi.label(content,getString(R.string.referral_hint),15,TerminalUi.TEXT);
        status=TerminalUi.label(content,"",14,TerminalUi.MUTED);
        load=TerminalUi.button(content,R.string.referral_load,this::load);
        load();
    }
    private void load() {
        if(rendered)return;load.setEnabled(false);status.setText(R.string.referral_loading);
        worker.execute(()->{
            try {
                JsonObject result=new FriendsAccessAndroid(this).referral();
                String url=result.get("url").getAsString();
                BitMatrix matrix=new QRCodeWriter().encode(url,BarcodeFormat.QR_CODE,512,512,
                    Collections.singletonMap(EncodeHintType.MARGIN,4));
                int[] pixels=new int[512*512];
                for(int y=0;y<512;y++)for(int x=0;x<512;x++)pixels[y*512+x]=matrix.get(x,y)?0xff041310:0xffffffff;
                Bitmap bitmap=Bitmap.createBitmap(pixels,512,512,Bitmap.Config.ARGB_8888);
                runOnUiThread(()->{
                    if(isDestroyed())return;rendered=true;load.setVisibility(android.view.View.GONE);
                    status.setText("");
                    status.setVisibility(android.view.View.GONE);
                    ImageView qr=new ImageView(this);qr.setImageBitmap(bitmap);qr.setAdjustViewBounds(true);
                    qr.setContentDescription(getString(R.string.referral_qr));content.addView(qr,new LinearLayout.LayoutParams(-1,-2));
                    TerminalUi.button(content,R.string.referral_copy,()->{
                        getSystemService(ClipboardManager.class).setPrimaryClip(ClipData.newPlainText("Family Connect",url));
                        status.setVisibility(android.view.View.VISIBLE);status.setText(R.string.referral_copied);
                    });
                });
            } catch(Exception failure) {
                runOnUiThread(()->{if(!isDestroyed()){status.setText(R.string.referral_unavailable);load.setEnabled(true);}});
            }
        });
    }
    @Override protected void onDestroy(){worker.shutdownNow();super.onDestroy();}
}
