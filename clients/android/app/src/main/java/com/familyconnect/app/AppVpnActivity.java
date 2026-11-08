package com.familyconnect.app;

import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.*;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class AppVpnActivity extends LocalizedActivity {
    private final ExecutorService loader=Executors.newSingleThreadExecutor();
    private final List<Entry> entries=new ArrayList<>(),visible=new ArrayList<>();
    private final Set<String> included=new HashSet<>(),excluded=new HashSet<>();
    private AppVpnPolicy.Mode mode=AppVpnPolicy.Mode.ALL;
    private AppVpnStore store;
    private TextView summary;
    private EditText search;
    private CheckBox selected;
    private Spinner category;
    private Rows rows;
    private boolean loaded;

    private static final class Entry {
        final String name,label;
        final ApplicationInfo info;
        Entry(String name,String label,ApplicationInfo info){this.name=name;this.label=label;this.info=info;}
        boolean system(){return info!=null&&(info.flags&ApplicationInfo.FLAG_SYSTEM)!=0;}
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        store=new AppVpnStore(this);
        boolean invalid=false;
        try{
            AppVpnPolicy saved=state==null?store.read():AppVpnStore.decode(state.getString("draft"));
            mode=saved.mode;included.addAll(saved.included);excluded.addAll(saved.excluded);
        }catch(IllegalArgumentException damaged){invalid=true;}
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(TerminalUi.BACKGROUND);
        int padding=TerminalUi.dp(this,16);root.setPadding(padding,padding,padding,padding);
        LinearLayout header=new LinearLayout(this);header.setOrientation(LinearLayout.VERTICAL);
        TerminalUi.label(header,getString(R.string.app_vpn_title),22,TerminalUi.TEXT);
        TerminalUi.label(header,getString(R.string.app_vpn_warning),13,TerminalUi.MUTED);
        Spinner modes=new Spinner(this);modes.setTag("app_vpn_modes");
        modes.setAdapter(choices(R.array.app_vpn_modes));
        modes.setSelection(mode.ordinal());header.addView(modes,new LinearLayout.LayoutParams(-1,-2));
        summary=TerminalUi.label(header,getString(invalid?R.string.app_vpn_invalid:R.string.app_vpn_loading),13,TerminalUi.AMBER);summary.setTag("app_vpn_summary");
        search=new EditText(this);search.setTag("app_vpn_search");search.setSingleLine();search.setHint(R.string.app_vpn_search);search.setTextColor(TerminalUi.TEXT);search.setHintTextColor(TerminalUi.MUTED);
        header.addView(search,new LinearLayout.LayoutParams(-1,-2));
        selected=new CheckBox(this);selected.setTag("app_vpn_selected");selected.setText(R.string.app_vpn_selected);selected.setTextColor(TerminalUi.TEXT);header.addView(selected);
        category=new Spinner(this);category.setAdapter(choices(R.array.app_vpn_categories));header.addView(category);
        ListView list=new ListView(this);list.setTag("app_vpn_list");list.addHeaderView(header,null,false);rows=new Rows();list.setAdapter(rows);list.setDividerHeight(1);
        root.addView(list,new LinearLayout.LayoutParams(-1,0,1));
        TextView scope=TerminalUi.label(root,getString(R.string.app_vpn_details),13,TerminalUi.MINT);
        scope.setMinHeight(TerminalUi.dp(this,48));scope.setFocusable(true);scope.setPaintFlags(scope.getPaintFlags()|android.graphics.Paint.UNDERLINE_TEXT_FLAG);
        scope.setOnClickListener(view->new android.app.AlertDialog.Builder(this).setMessage(R.string.app_vpn_scope).setPositiveButton(android.R.string.ok,null).show());
        TerminalUi.button(root,R.string.app_vpn_save,()->{
            try{store.save(draft());updateSummary();Toast.makeText(this,R.string.app_vpn_saved,Toast.LENGTH_SHORT).show();}
            catch(IllegalArgumentException|IllegalStateException failed){summary.setText(R.string.app_vpn_invalid);}
        }).setTag("app_vpn_save");
        TerminalUi.button(root,R.string.app_vpn_back,this::finish).setTag("app_vpn_back");
        modes.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onItemSelected(AdapterView<?> parent,View view,int position,long id){mode=AppVpnPolicy.Mode.values()[position];filter();updateSummary();}
            public void onNothingSelected(AdapterView<?> parent){}
        });
        category.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onItemSelected(AdapterView<?> parent,View view,int position,long id){filter();}
            public void onNothingSelected(AdapterView<?> parent){}
        });
        selected.setOnCheckedChangeListener((button,checked)->filter());
        search.addTextChangedListener(new TextWatcher(){
            public void beforeTextChanged(CharSequence text,int start,int count,int after){}
            public void onTextChanged(CharSequence text,int start,int before,int count){filter();}
            public void afterTextChanged(Editable text){}
        });
        if(state!=null){search.setText(state.getString("search",""));selected.setChecked(state.getBoolean("selected"));category.setSelection(state.getInt("category"));}
        TerminalUi.install(this,root);
        loader.execute(()->{
            List<Entry> found=new ArrayList<>();PackageManager manager=getPackageManager();
            for(ApplicationInfo info:manager.getInstalledApplications(0))found.add(new Entry(info.packageName,manager.getApplicationLabel(info).toString(),info));
            found.sort(Comparator.comparing((Entry entry)->entry.label.toLowerCase(Locale.ROOT)).thenComparing(entry->entry.name));
            runOnUiThread(()->{
                if(isFinishing()||isDestroyed())return;
                entries.addAll(found);Set<String> missing=new HashSet<>(included);missing.addAll(excluded);
                for(Entry entry:entries)missing.remove(entry.name);
                for(String name:missing)entries.add(new Entry(name,name,null));
                loaded=true;filter();updateSummary();
            });
        });
    }
    private ArrayAdapter<String> choices(int resource){
        return new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,getResources().getStringArray(resource)){
            @Override public View getView(int position,View convert,ViewGroup parent){
                TextView view=(TextView)super.getView(position,convert,parent);view.setSingleLine(false);view.setMaxLines(3);view.setTextSize(16);return view;
            }
        };
    }
    private AppVpnPolicy draft(){return new AppVpnPolicy(mode,included,excluded);}
    private Set<String> selection(){return mode==AppVpnPolicy.Mode.INCLUDE?included:excluded;}
    private void updateSummary(){
        if(summary==null||!loaded)return;
        AppVpnPolicy policy=draft();
        try{if(!policy.equals(store.read())){summary.setText(R.string.app_vpn_unsaved);return;}}
        catch(IllegalArgumentException invalid){summary.setText(R.string.app_vpn_unsaved);return;}
        boolean pending=ConnectionService.activeApplications!=null&&!policy.equals(ConnectionService.activeApplications);
        try{new AppVpnAndroid(this,policy);summary.setText(getString(pending?R.string.app_vpn_pending:R.string.app_vpn_next)+(policy.mode==AppVpnPolicy.Mode.ALL?"":" · "+policy.selected().size()));}
        catch(IllegalArgumentException invalid){summary.setText(getString(R.string.app_vpn_invalid)+(pending?"\n"+getString(R.string.app_vpn_pending):""));}
    }
    private void filter(){
        if(rows==null)return;
        String query=search.getText().toString().trim().toLowerCase(Locale.ROOT);int kind=category.getSelectedItemPosition();visible.clear();
        for(Entry entry:entries){
            if(kind==1&&entry.system()||kind==2&&!entry.system())continue;
            if(selected.isChecked()&&(mode==AppVpnPolicy.Mode.ALL||!selection().contains(entry.name)))continue;
            if(!entry.label.toLowerCase(Locale.ROOT).contains(query)&&!entry.name.toLowerCase(Locale.ROOT).contains(query))continue;
            visible.add(entry);
        }
        rows.notifyDataSetChanged();
    }
    @Override protected void onSaveInstanceState(Bundle state){
        super.onSaveInstanceState(state);state.putString("draft",AppVpnStore.encode(draft()));state.putString("search",search.getText().toString());state.putBoolean("selected",selected.isChecked());state.putInt("category",category.getSelectedItemPosition());
    }
    @Override protected void onDestroy(){loader.shutdownNow();super.onDestroy();}
    private final class Rows extends BaseAdapter {
        public int getCount(){return visible.size();}
        public Entry getItem(int position){return visible.get(position);}
        public long getItemId(int position){return position;}
        public View getView(int position,View convert,ViewGroup parent){
            Entry entry=getItem(position);
            LinearLayout row=new LinearLayout(AppVpnActivity.this);row.setGravity(android.view.Gravity.CENTER_VERTICAL);int padding=TerminalUi.dp(AppVpnActivity.this,8);row.setPadding(0,padding,0,padding);
            ImageView icon=new ImageView(AppVpnActivity.this);if(entry.info!=null)icon.setImageDrawable(getPackageManager().getApplicationIcon(entry.info));
            row.addView(icon,new LinearLayout.LayoutParams(padding*5,padding*5));
            LinearLayout text=new LinearLayout(AppVpnActivity.this);text.setOrientation(LinearLayout.VERTICAL);text.setPadding(padding,0,padding,0);
            TerminalUi.label(text,entry.label,16,TerminalUi.TEXT);
            TerminalUi.label(text,entry.name,12,TerminalUi.MUTED);
            if(entry.info==null)TerminalUi.label(text,getString(R.string.app_vpn_missing),12,TerminalUi.AMBER);
            else if(entry.system())TerminalUi.label(text,getString(R.string.app_vpn_system),12,TerminalUi.MUTED);
            String[] group=entry.info==null?null:getPackageManager().getPackagesForUid(entry.info.uid);
            if(group!=null&&group.length>1)TerminalUi.label(text,getString(R.string.app_vpn_shared),12,TerminalUi.AMBER);
            row.addView(text,new LinearLayout.LayoutParams(0,-2,1));
            CheckBox check=new CheckBox(AppVpnActivity.this);check.setContentDescription(entry.label+" · "+entry.name);check.setEnabled(mode!=AppVpnPolicy.Mode.ALL);check.setChecked(mode!=AppVpnPolicy.Mode.ALL&&selection().contains(entry.name));row.addView(check);
            check.setOnCheckedChangeListener((button,checked)->{
                Set<String> names=selection();String[] related=group==null?new String[]{entry.name}:group;
                for(String name:related){if(checked)names.add(name);else names.remove(name);}filter();updateSummary();
            });
            row.setOnClickListener(view->{if(check.isEnabled())check.setChecked(!check.isChecked());});return row;
        }
    }
}
