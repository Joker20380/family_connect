package com.familyconnect.app;

import android.content.*;
import android.content.res.*;
import android.os.LocaleList;
import java.util.Locale;

final class AppLanguage {
    static String selected(Context context){String value=context.getSharedPreferences("appearance",Context.MODE_PRIVATE).getString("language","system");return value.equals("ru")||value.equals("en")?value:"system";}
    private static Locale locale(String value){return value.equals("system")?Resources.getSystem().getConfiguration().getLocales().get(0):Locale.forLanguageTag(value);}
    static Context wrap(Context context){Configuration config=new Configuration(context.getResources().getConfiguration());config.setLocales(new LocaleList(locale(selected(context))));return context.createConfigurationContext(config);}
    static void select(Context context,String value){
        if(!value.equals("system")&&!value.equals("ru")&&!value.equals("en"))throw new IllegalArgumentException();
        context.getSharedPreferences("appearance",Context.MODE_PRIVATE).edit().putString("language",value).apply();
        Locale chosen=locale(value);Locale.setDefault(chosen);Context app=context.getApplicationContext();Configuration config=new Configuration(app.getResources().getConfiguration());config.setLocales(new LocaleList(chosen));app.getResources().updateConfiguration(config,app.getResources().getDisplayMetrics());
    }
}
