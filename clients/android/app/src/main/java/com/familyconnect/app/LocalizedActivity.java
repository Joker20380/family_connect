package com.familyconnect.app;
import android.app.Activity;
import android.content.Context;
/** Refresh every screen when the user changes the shared app language. */
public abstract class LocalizedActivity extends Activity {
    private String language;
    @Override protected void attachBaseContext(Context base){language=AppLanguage.selected(base);super.attachBaseContext(AppLanguage.wrap(base));}
    @Override protected void onResume(){super.onResume();if(!AppLanguage.selected(this).equals(language))recreate();}
}
