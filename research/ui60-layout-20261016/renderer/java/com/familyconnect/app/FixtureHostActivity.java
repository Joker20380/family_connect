package com.familyconnect.app;

public final class FixtureHostActivity extends android.app.Activity {
    @Override public void onCreate(android.os.Bundle state){
        super.onCreate(state);
        getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);
        getWindow().setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        setContentView(new android.widget.LinearLayout(this));
    }
}
