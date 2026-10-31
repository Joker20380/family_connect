package com.familyconnect.app;

import android.content.Context;
import android.widget.*;

final class RadioSettings {
    static android.content.SharedPreferences preferences(Context context){return context.getSharedPreferences("exit-voice",Context.MODE_PRIVATE);}
    static int mode(Context context){int selected=preferences(context).getInt("mode",16);return selected==7||selected==8||selected==9?selected:16;}
    static void attach(LinearLayout parent){
        Context context=parent.getContext();LinearLayout panel=TerminalUi.section(parent,context.getString(R.string.radio_title));
        Spinner picker=new Spinner(context);int[] modes={16,7,8,9};
        TerminalUi.picker(picker,new String[]{context.getString(R.string.radio_normal),"Codec2 · 1600 bit/s","Codec2 · 2400 bit/s","Codec2 · 3200 bit/s"});
        for(int index=0;index<modes.length;index++)if(modes[index]==mode(context))picker.setSelection(index);
        panel.addView(picker,new LinearLayout.LayoutParams(-1,-2));
        picker.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onNothingSelected(AdapterView<?> parent){}public void onItemSelected(AdapterView<?> parent,android.view.View view,int position,long id){preferences(context).edit().putInt("mode",modes[position]).apply();}});
        TerminalUi.label(panel,context.getString(R.string.radio_notice),14,TerminalUi.MUTED);
    }
}
