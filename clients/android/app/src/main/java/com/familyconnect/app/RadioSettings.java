package com.familyconnect.app;

import android.content.Context;
import android.widget.*;

final class RadioSettings {
    static android.content.SharedPreferences preferences(Context context){return context.getSharedPreferences("exit-voice",Context.MODE_PRIVATE);}
    static int mode(Context context){return VoiceCompatibility.mode(preferences(context).getInt("mode",16),android.os.Build.VERSION.SDK_INT);}
    static void attach(LinearLayout parent){
        Context context=parent.getContext();LinearLayout panel=TerminalUi.section(parent,context.getString(R.string.radio_title));
        Spinner picker=new Spinner(context);int[] modes=VoiceCompatibility.modes(android.os.Build.VERSION.SDK_INT);
        TerminalUi.picker(picker,android.os.Build.VERSION.SDK_INT>=29?new String[]{context.getString(R.string.radio_normal),"Codec2 · 1600 bit/s","Codec2 · 2400 bit/s","Codec2 · 3200 bit/s"}:new String[]{"Codec2 · 1600 bit/s","Codec2 · 2400 bit/s","Codec2 · 3200 bit/s"});
        for(int index=0;index<modes.length;index++)if(modes[index]==mode(context))picker.setSelection(index);
        panel.addView(picker,new LinearLayout.LayoutParams(-1,-2));
        picker.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onNothingSelected(AdapterView<?> parent){}public void onItemSelected(AdapterView<?> parent,android.view.View view,int position,long id){preferences(context).edit().putInt("mode",modes[position]).apply();}});
        TerminalUi.label(panel,context.getString(android.os.Build.VERSION.SDK_INT>=29?R.string.radio_notice:R.string.radio_legacy_notice),14,TerminalUi.MUTED);
    }
}
