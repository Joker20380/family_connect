package com.familyconnect.app;
import android.app.Application;
import android.content.Context;
public final class FamilyApplication extends Application {
    @Override protected void attachBaseContext(Context base){super.attachBaseContext(AppLanguage.wrap(base));}
}
