package com.familyconnect.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.NetworkRequest;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.*;
import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.text.DateFormat;
import java.util.Date;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

/** Native local chat UI. No bootstrap is inferred from contacts or invitation codes. */
public final class ChatActivity extends LocalizedActivity {
    // FIFO across Activity recreation: previous close finishes before the next open.
    private static final ExecutorService WORKER = ChatRuntime.WORKER;
    private volatile int generation;
    private volatile boolean visible;
    private ChatLocalAndroid chat; // Worker only.
    private LinearLayout content;
    private TextView notice;
    private LinearLayout page;
    private ChatThreadView thread;
    private String screen="loading";
    private JsonObject peer;
    private String draft = "";
    private java.util.Map<String,String> drafts=new java.util.HashMap<>();
    private static final class DraftCommit { volatile String text; }
    private static final class Retained {
        final JsonObject peer; final String draft; final int offset; final DraftCommit commit; final java.util.Map<String,String> drafts;
        Retained(JsonObject peer, String draft, int offset, DraftCommit commit,java.util.Map<String,String> drafts) {
            this.drafts=drafts;
            this.peer = peer; this.draft = draft; this.offset = offset; this.commit = commit;
        }
    }
    private DraftCommit committed = new DraftCommit();
    private int offset;
    private int observedHistoryTotal=-1;
    private String observedHistoryPeer;
    private boolean revealLatestMessage;
    private boolean busy;
    private volatile boolean deliveryAttached;
    private volatile int deliveryLabel = R.string.chat_local_notice;
    private ConnectivityManager connectivity;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private ChatAudio audio;
    private byte[] voiceDraft;
    private boolean recordingVoice,voiceSending;
    private Runnable voiceSendTimer;
    private long recordingStarted;
    private Runnable voiceTimer;
    private int renderedAttempt;
    private long renderedEventsRevision;
    private volatile int serviceUnread;
    private ChatPollPolicy polling=new ChatPollPolicy();
    private final ConnectivityManager.NetworkCallback networks = new ConnectivityManager.NetworkCallback() {
        @Override public void onAvailable(Network network) { updateNetwork(); }
        @Override public void onLost(Network network) { updateNetwork(); }
        @Override public void onCapabilitiesChanged(Network network, NetworkCapabilities caps) { updateNetwork(); }
    };
    private void updateNetwork() {
        final int expected = generation;
        if (!visible) return;
        WORKER.execute(() -> {
            if (chat != null && deliveryAttached && visible && generation == expected) {
                try { chat.deliveryUpdate(new ChatNetworkAndroid(this).available(), true); }
                catch (Exception ignored) { /* Local history remains available. */ }
            }
        });
    }
    private JsonObject activateDelivery() throws Exception {
        JsonObject result = ChatRuntime.enroll(this,chat);
        if (result.get("status").getAsString().equals("active")) {
            deliveryAttached=true;
            chat.deliveryUpdate(new ChatNetworkAndroid(this).available(), true);
            deliveryLabel=R.string.chat_delivery_ready;
        } else deliveryLabel=R.string.chat_registered_pending;
        return result;
    }
    private final Runnable deliveryTick = new Runnable() {
        public void run() {
            if (!visible) return;
            handler.postDelayed(this, 2000);
            if(!busy&&chat!=null&&getIntent().hasExtra("chat_peer")){openNotification();return;}
            if (busy || chat==null) return;
            final int expected = generation;
            WORKER.execute(() -> {
                try {
                    if (chat == null || !visible || generation != expected) return;
                    ChatRuntime.syncEvents(ChatActivity.this,chat,false);
                    JsonObject state = chat.call("delivery_state", args()).getAsJsonObject();
                    ChatRuntime.deliverNotifications(ChatActivity.this,chat);
                    if(deliveryAttached&&polling.poll(android.os.SystemClock.elapsedRealtime(),visible&&generation==expected,
                            state.get("online").getAsBoolean(),state.get("running").getAsBoolean(),
                            state.get("pending").getAsBoolean(),state.get("error").isJsonNull()))
                        chat.call("request_sync",args());
                    runOnUiThread(() -> {
                        if (!visible || generation != expected || busy) return;
                        boolean running = state.get("running").getAsBoolean();
                        deliveryLabel = !state.get("online").getAsBoolean() ? R.string.chat_network_wait
                            : running ? R.string.chat_exchanging : !state.get("error").isJsonNull()
                            ? R.string.chat_exchange_error : R.string.chat_delivery_ready;
                        if(screen.equals("contacts")||screen.equals("conversation"))notice.setText(deliveryLabel);
                        if(renderedEventsRevision!=ChatRuntime.eventsRevision){
                            renderedEventsRevision=ChatRuntime.eventsRevision;
                            if(screen.equals("events")){serviceEvents(false);return;}
                            if(screen.equals("contacts")){refreshContacts();return;}
                        }
                        int attempts = state.get("attempts").getAsInt();
                        if (!running && attempts != renderedAttempt) {
                            renderedAttempt = attempts;
                            if (screen.equals("conversation")) conversation(); else if(screen.equals("contacts")) refreshContacts(); else if(screen.equals("events"))serviceEvents(false);
                        }
                    });
                } catch (Exception ignored) { }
            });
        }
    };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        ChatAudio.cleanOld(this);audio=new ChatAudio(this);
        Object previous = getLastNonConfigurationInstance();
        if (previous instanceof Retained) {
            Retained retained = (Retained) previous;
            peer = retained.peer; draft = retained.draft; offset = retained.offset; committed = retained.commit; drafts=retained.drafts;
        }
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        shell();
    }
    @Override public Object onRetainNonConfigurationInstance() {
        // Rotation retains only UI data in RAM; process death does not persist a draft.
        return new Retained(peer, draft, offset, committed,drafts);
    }
    @Override protected void onStart() {
        super.onStart(); ChatNotifications.request(this); visible = true;ChatRuntime.uiVisible=true; generation++; busy = false;
        connectivity = getSystemService(ConnectivityManager.class);
        if (connectivity != null) connectivity.registerNetworkCallback(new NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .addCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN).build(), networks);
        handler.post(deliveryTick);
        job(() -> {
            chat = null;
            deliveryAttached = false; renderedAttempt = 0; polling=new ChatPollPolicy();
            if (!ChatLocalAndroid.hasState(this)) return JsonNull.INSTANCE;
            chat = ChatRuntime.open(this, false);
            {
                try { activateDelivery(); }
                catch (Exception unavailable) { deliveryLabel = R.string.chat_enrollment_unavailable; }
            }
            return chat.call("profile", args());
        }, result -> {
            if (draft.equals(committed.text)) draft = "";
            committed.text = null;
            if (result.isJsonNull()) welcome(); else {
                ChatDeliveryService.start(this);
                if(getIntent().hasExtra("chat_peer"))openNotification();else if (peer != null) conversation(); else contacts();
            }
        });
    }
    @Override protected void onStop() {
        clearVoice();
        visible = false; generation++;
        handler.removeCallbacks(deliveryTick);
        if (connectivity != null) { connectivity.unregisterNetworkCallback(networks); connectivity = null; }
        ChatRuntime.visiblePeer=null;ChatRuntime.uiVisible=false;
        WORKER.execute(()->{if(!ChatRuntime.uiVisible&&!ChatDeliveryService.enabled(this)&&chat!=null)try{chat.deliveryUpdate(false,false);}catch(Exception ignored){}});
        if(thread!=null)thread.setForeground(false);
        super.onStop();
    }
    private void shell() { shell(getString(R.string.chat_title),null,null); }
    private void shell(String title,Runnable back,Runnable menu) {
        if(recordingVoice||voiceDraft!=null)clearVoice();
        ChatRuntime.visiblePeer=null;
        if(thread!=null)thread.setForeground(false);thread=null;
        page=TerminalUi.dashboard(this);TerminalUi.dashboardHeader(page);
        LinearLayout toolbar=new LinearLayout(this);toolbar.setGravity(Gravity.CENTER_VERTICAL);
        if(back!=null){Button button=ChatThreadView.small(this,"‹",getString(R.string.chat_dialogs));button.setOnClickListener(v->back.run());toolbar.addView(button,new LinearLayout.LayoutParams(TerminalUi.dp(this,48),TerminalUi.dp(this,48)));}
        TextView heading=new TextView(this);TerminalUi.textStyle(heading,20,TerminalUi.TEXT);heading.setText(title);heading.setSingleLine(true);heading.setEllipsize(android.text.TextUtils.TruncateAt.END);toolbar.addView(heading,new LinearLayout.LayoutParams(0,TerminalUi.dp(this,48),1));heading.setGravity(Gravity.CENTER_VERTICAL);
        if(menu!=null){Button button=ChatThreadView.small(this,"⋮",getString(R.string.chat_menu));button.setOnClickListener(v->menu.run());toolbar.addView(button,new LinearLayout.LayoutParams(TerminalUi.dp(this,48),TerminalUi.dp(this,48)));}
        page.addView(toolbar);notice=TerminalUi.label(page,getString(deliveryLabel),11,TerminalUi.MUTED);notice.setMaxLines(2);
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);scroll.addView(content);page.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        if(getPackageName().endsWith(".friends"))TerminalUi.tabs(page,this,1);
    }
    private void chatMenu(){
        if(busy)return;
        new AlertDialog.Builder(this).setItems(new String[]{getString(R.string.chat_add),getString(R.string.chat_profile),getString(R.string.chat_register),getString(R.string.chat_background)},(d,which)->{if(which==0)addContact();else if(which==1)profile();else if(which==2)registerDelivery();else notificationSettings();}).show();
    }
    private void notificationSettings(){
        screen="notifications";ChatRuntime.visiblePeer=null;shell(getString(R.string.chat_notifications),this::contacts,null);
        Switch enabled=new Switch(this);enabled.setText(R.string.chat_background_hint);enabled.setChecked(ChatDeliveryService.enabled(this));
        content.addView(enabled);enabled.setOnCheckedChangeListener((button,value)->{getSharedPreferences("chat-notifications",MODE_PRIVATE).edit().putBoolean("background",value).apply();if(value)ChatDeliveryService.start(this);else stopService(new android.content.Intent(this,ChatDeliveryService.class));});
        TerminalUi.button(content,R.string.chat_enable_notifications,()->startActivity(new android.content.Intent(android.provider.Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(android.provider.Settings.EXTRA_APP_PACKAGE,getPackageName())));
    }
    private void registerDelivery(){job(()->{
        try{return activateDelivery();}catch(FriendsAccessAndroid.Denied failure){throw new ChatLocalAndroid.ChatException("invitation_required");}
        catch(Exception failure){throw new ChatLocalAndroid.ChatException("enrollment_unavailable");}
    },result->{if(result.getAsJsonObject().get("status").getAsString().equals("active"))getPreferences(MODE_PRIVATE).edit().putBoolean("chat_registered",true).apply();notice.setText(deliveryLabel);});}
    private void welcome() {
        screen="welcome";shell();
        TerminalUi.label(content, getString(R.string.chat_welcome), 15, TerminalUi.TEXT);
        TerminalUi.button(content, R.string.chat_create, () -> job(() -> {
            chat = ChatRuntime.open(this, true);
            try { JsonObject registration=activateDelivery();if(registration.get("status").getAsString().equals("active"))getPreferences(MODE_PRIVATE).edit().putBoolean("chat_registered",true).apply(); }
            catch(Exception unavailable){deliveryLabel=R.string.chat_enrollment_unavailable;}
            return chat.call("profile", args());
        }, result -> {ChatDeliveryService.start(this);contacts();}));
    }
    private void contacts() {
        if(busy)return;
        if(peer!=null)drafts.put(peer.get("address").getAsString(),draft);
        ChatRuntime.visiblePeer=null;peer=null;draft="";offset=0;screen="contacts";
        shell(getString(R.string.chat_dialogs),null,this::chatMenu);
        TerminalUi.button(content,R.string.chat_add,this::addContact);
        refreshContacts();
    }
    private void refreshContacts(){
        job(()->{
            JsonArray cards=chat.call("contacts",args()).getAsJsonArray();
            JsonArray inbox=chat.call("inbox",args()).getAsJsonArray();
            serviceUnread=0;for(JsonElement entry:chat.call("service_events",args()).getAsJsonArray())if(!entry.getAsJsonObject().get("read").getAsBoolean())serviceUnread++;
            for(JsonElement item:cards){JsonObject card=item.getAsJsonObject();int unread=0;for(JsonElement entry:inbox){JsonObject message=entry.getAsJsonObject();if(!message.get("read").getAsBoolean()&&message.get("peer").equals(card.get("address")))unread++;}card.addProperty("unread",unread);}
            for(JsonElement entry:cards){JsonObject card=entry.getAsJsonObject();JsonObject request=args("address",card.get("address").getAsString());request.addProperty("offset",0);request.addProperty("limit",1);
                JsonObject h=chat.call("history",request).getAsJsonObject();int total=h.get("total").getAsInt();
                if(total>1){request.addProperty("offset",total-1);h=chat.call("history",request).getAsJsonObject();}
                if(!h.getAsJsonArray("messages").isEmpty())card.add("last",h.getAsJsonArray("messages").get(0));
            }return cards;
        },result->{
            if(!screen.equals("contacts"))return;content.removeAllViews();
            TerminalUi.button(content,R.string.chat_add,this::addContact);
            Button events=TerminalUi.button(content,R.string.service_events,this::serviceEvents);if(serviceUnread>0)events.setText(getString(R.string.service_events)+" · "+serviceUnread);
            if(!getSystemService(android.app.NotificationManager.class).areNotificationsEnabled())TerminalUi.button(content,R.string.chat_enable_notifications,()->startActivity(new android.content.Intent(android.provider.Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(android.provider.Settings.EXTRA_APP_PACKAGE,getPackageName())));
            if(!deliveryAttached)TerminalUi.button(content,R.string.chat_enable_delivery,this::registerDelivery);
            if(result.getAsJsonArray().isEmpty())TerminalUi.label(content,getString(R.string.chat_empty_simple),15,TerminalUi.MUTED);
            java.util.List<JsonObject> cards=new java.util.ArrayList<>();for(JsonElement item:result.getAsJsonArray())cards.add(item.getAsJsonObject());
            cards.sort((a,b)->Double.compare(b.has("last")?b.getAsJsonObject("last").get("timestamp").getAsDouble():0,a.has("last")?a.getAsJsonObject("last").get("timestamp").getAsDouble():0));
            for(JsonObject card:cards){
                LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);int pad=TerminalUi.dp(this,12);row.setPadding(pad,pad,pad,pad);row.setMinimumHeight(TerminalUi.dp(this,80));row.setBackground(TerminalUi.frame(this,TerminalUi.SURFACE,TerminalUi.FRAME));
                TextView avatar=new TextView(this);TerminalUi.textStyle(avatar,22,TerminalUi.AMBER);avatar.setText(card.get("address").getAsString().substring(0,2).toUpperCase(java.util.Locale.ROOT));row.addView(avatar,new LinearLayout.LayoutParams(TerminalUi.dp(this,48),-2));
                LinearLayout text=new LinearLayout(this);text.setOrientation(LinearLayout.VERTICAL);row.addView(text,new LinearLayout.LayoutParams(0,-2,1));
                TextView title=TerminalUi.label(text,contactTitle(card)+(card.get("unread").getAsInt()>0?" · "+card.get("unread").getAsInt():""),16,TerminalUi.TEXT);title.setGravity(Gravity.START);
                TextView preview=TerminalUi.label(text,card.has("last")?card.getAsJsonObject("last").get("text").getAsString():getString(R.string.chat_no_messages),13,TerminalUi.MUTED);preview.setGravity(Gravity.START);preview.setMaxLines(1);preview.setEllipsize(android.text.TextUtils.TruncateAt.END);
                row.setFocusable(true);row.setContentDescription(contactTitle(card));row.setOnClickListener(v->{if(busy)return;peer=card;offset=-1;draft=drafts.getOrDefault(card.get("address").getAsString(),"");screen="opening";conversation();});content.addView(row,new LinearLayout.LayoutParams(-1,-2));
            }
        });
    }
    private String contactTitle(JsonObject card){return card.has("name")&&!card.get("name").getAsString().isEmpty()?card.get("name").getAsString():getString(R.string.chat_contact)+" "+card.get("address").getAsString().substring(0,8);}
    private void profile() {
        if(busy)return;
        screen="profile";
        job(() -> chat.call("profile", args()), result -> {
            shell(getString(R.string.chat_profile),this::contacts,null);
            LinearLayout panel = TerminalUi.section(content, null);
            JsonObject card = result.getAsJsonObject();
            showCard(panel, card);
            TerminalUi.button(panel, R.string.chat_copy_key, () -> {
                ClipboardManager clipboard = getSystemService(ClipboardManager.class);
                clipboard.setPrimaryClip(ClipData.newPlainText(getString(R.string.chat_public_key), card.get("public").getAsString()));
                notice.setText(R.string.chat_copied);
            });
            TerminalUi.button(panel, R.string.chat_contacts, this::contacts);
        });
    }
    private void showCard(LinearLayout panel, JsonObject card) {
        selectable(panel, getString(R.string.chat_address), card.get("address").getAsString());
        selectable(panel, getString(R.string.chat_fingerprint), groups(card.get("fingerprint").getAsString()));
        selectable(panel, getString(R.string.chat_public_key), card.get("public").getAsString());
    }
    private void selectable(LinearLayout panel, String title, String value) {
        TerminalUi.label(panel, title, 12, TerminalUi.MUTED);
        TextView text = TerminalUi.label(panel, value, 13, TerminalUi.TEXT);
        text.setTextIsSelectable(true); text.setGravity(Gravity.START);
    }
    private void addContact() {
        if(busy)return;
        screen="add";shell(getString(R.string.chat_add),this::contacts,null);
        LinearLayout panel = TerminalUi.section(content, getString(R.string.chat_add));
        EditText key = input(panel, R.string.chat_key_hint, false);
        TerminalUi.button(panel, R.string.chat_preview, () -> {
            String value = key.getText().toString().trim().toLowerCase(java.util.Locale.ROOT);
            job(() -> chat.call("preview_contact", args("public", value)), result -> verifyContact(result.getAsJsonObject()));
        });
        TerminalUi.button(panel, R.string.chat_contacts, this::contacts);
    }
    private void verifyContact(JsonObject card) {
        screen="verify";shell(getString(R.string.chat_verify),this::contacts,null);
        LinearLayout panel = TerminalUi.section(content, getString(R.string.chat_verify));
        showCard(panel, card);
        TerminalUi.label(panel, getString(R.string.chat_verify_hint), 14, TerminalUi.AMBER);
        CheckBox checked = new CheckBox(this);
        checked.setText(R.string.chat_verified); TerminalUi.textStyle(checked, 14, TerminalUi.TEXT);
        checked.setMinHeight(TerminalUi.dp(this, 48)); panel.addView(checked);
        Button save = TerminalUi.button(panel, R.string.chat_save_contact, () -> {
            if (!checked.isChecked()) return;
            job(() -> chat.call("trust_contact", args("public", card.get("public").getAsString(),
                "fingerprint", card.get("fingerprint").getAsString())), result -> {
                    peer = result.getAsJsonObject(); offset = -1; conversation();
                });
        });
        save.setEnabled(false);
        checked.setOnCheckedChangeListener((button, yes) -> save.setEnabled(yes && !busy));
        TerminalUi.button(panel, R.string.chat_contacts, this::contacts);
    }
    private void conversation() {
        if (peer == null) { contacts(); return; }
        String address = peer.get("address").getAsString();
        JsonObject request = args("address", address);
        request.addProperty("offset", Math.max(0, offset)); request.addProperty("limit", 50);
        job(() -> chat.call("history", request), result -> {
            JsonObject history = result.getAsJsonObject();
            int total=history.get("total").getAsInt();
            boolean appended=address.equals(observedHistoryPeer)&&total>observedHistoryTotal;
            observedHistoryPeer=address;observedHistoryTotal=total;
            if(offset<0||appended){
                revealLatestMessage=true;offset=Math.max(0,(total-1)/50*50);
                if(request.get("offset").getAsInt()!=offset){conversation();return;}
            }
            history.addProperty("offset",offset);
            if(thread==null||!screen.equals("conversation")){
                screen="conversation";
                shell(contactTitle(peer),this::contacts,()->new AlertDialog.Builder(this).setItems(new String[]{getString(R.string.chat_verify),getString(R.string.chat_refresh_history),getString(R.string.chat_rename)},(d,which)->{
                    if(which==0)new AlertDialog.Builder(this).setTitle(R.string.chat_fingerprint).setMessage(groups(peer.get("fingerprint").getAsString())).setPositiveButton(android.R.string.ok,null).show();
                    else if(which==2)renameContact();
                    else if(deliveryAttached)job(()->chat.call("request_sync",args()),ignored->conversation());else conversation();
                }).show());
                View scroll=(View)content.getParent();int index=page.indexOfChild(scroll);page.removeView(scroll);
                thread=new ChatThreadView(this,draft,value->draft=value,text->sendMessage(address,text));
                thread.editMessage=this::editChatMessage;thread.voice.listener=new VoiceHoldButton.Listener(){
                    public boolean start(){return startVoice();}
                    public void lock(){if(recordingVoice&&thread!=null)thread.recordingState(VoiceHoldButton.LOCKED);}
                    public void release(){stopVoice(true);}
                    public void cancel(){clearVoice();}
                    public void send(){if(recordingVoice)stopVoice(true);else sendVoiceDraft();}
                };thread.playAudio=this::playVoice;thread.audio=audio;
                page.addView(thread,index,new LinearLayout.LayoutParams(-1,0,1));
            }
            ChatRuntime.visiblePeer=address;ChatNotifications.cancel(this,address);
            JsonArray readIds=new JsonArray();for(JsonElement item:history.getAsJsonArray("messages")){JsonObject message=item.getAsJsonObject();if(!message.get("outgoing").getAsBoolean())readIds.add(message.get("id"));}
            WORKER.execute(()->{try{ChatRuntime.mark(chat,"mark_inbox",readIds,"read");ChatRuntime.deliverNotifications(ChatActivity.this,chat);}catch(Exception ignored){}});
            if(revealLatestMessage){thread.revealLatest();revealLatestMessage=false;}
            thread.setForeground(visible);thread.show(history,()->{offset=Math.max(0,offset-50);conversation();},()->{offset=history.get("next_offset").getAsInt();conversation();});
        });
    }
    @Override protected void onNewIntent(android.content.Intent intent){super.onNewIntent(intent);setIntent(intent);if(visible&&chat!=null&&!busy)openNotification();}
    private void openNotification(){
        String address=getIntent().getStringExtra("chat_peer");getIntent().removeExtra("chat_peer");
        if("service".equals(address)){serviceEvents();return;}
        job(()->chat.call("contacts",args()),result->{
            for(JsonElement item:result.getAsJsonArray())if(item.getAsJsonObject().get("address").getAsString().equals(address)){peer=item.getAsJsonObject();offset=-1;conversation();return;}
            contacts();
        });
    }
    private void serviceEvents(){serviceEvents(true);}
    private void serviceEvents(boolean refresh){
        if(busy)return;
        screen="events";
        job(()->{if(refresh)ChatRuntime.syncEvents(this,chat,true);return chat.call("service_events",args());},result->{
            shell(getString(R.string.service_events),this::contacts,this::noticeAdmin);ChatRuntime.visiblePeer="service";
            renderedEventsRevision=ChatRuntime.eventsRevision;
            if(ChatRuntime.eventsUnavailable)notice.setText(R.string.service_events_unavailable);
            JsonArray events=result.getAsJsonArray(),ids=new JsonArray();
            if(events.isEmpty())TerminalUi.label(content,getString(R.string.service_events_empty),15,TerminalUi.MUTED);
            for(int i=events.size()-1;i>=0;i--){JsonObject event=events.get(i).getAsJsonObject();ids.add(event.get("id"));
                LinearLayout card=TerminalUi.section(content,null);
                TerminalUi.label(card,event.get("title").getAsString(),18,TerminalUi.MINT);
                TerminalUi.label(card,event.get("body").getAsString(),15,TerminalUi.TEXT);
                if(event.has("revision")&&event.get("revision").getAsInt()>1)TerminalUi.label(card,getString(R.string.notice_edited),11,TerminalUi.MUTED);
                TerminalUi.label(card,event.get("author").getAsString()+" · "+DateFormat.getDateTimeInstance().format(new Date(event.get("created").getAsLong()*1000)),11,TerminalUi.MUTED);
            }
            ChatNotifications.cancel(this,"service");
            WORKER.execute(()->{try{ChatRuntime.mark(chat,"mark_events",ids,"read");}catch(Exception ignored){}});
        });
    }
    private String announcementTitle="",announcementBody="";
    private void noticeAdmin(){noticeList(0);}
    private void noticeList(int offset){
        if(busy)return;
        screen="notice-admin";ChatRuntime.visiblePeer=null;
        shell(getString(R.string.notice_admin),this::serviceEvents,null);
        notice.setText(R.string.notice_role_check);
        noticeJob(()->new FriendsAccessAndroid(this,true).listNotices(offset),result->{
            notice.setText(R.string.notice_admin_active);
            TerminalUi.button(content,R.string.notice_new,()->{announcementTitle="";announcementBody="";noticeCompose(null);});
            TerminalUi.label(content,getString(R.string.notice_published_list),16,TerminalUi.AMBER);
            JsonObject page=result.getAsJsonObject();JsonArray events=page.getAsJsonArray("events");
            if(events.isEmpty())TerminalUi.label(content,getString(R.string.service_events_empty),14,TerminalUi.MUTED);
            for(JsonElement item:events){JsonObject event=item.getAsJsonObject();
                LinearLayout card=TerminalUi.section(content,null);
                Button open=TerminalUi.button(card,R.string.notice_edit,()->{announcementTitle=event.get("title").getAsString();announcementBody=event.get("body").getAsString();noticeCompose(event);});
                open.setText(event.get("title").getAsString());
                TerminalUi.label(card,event.get("author").getAsString()+" · "+DateFormat.getDateTimeInstance().format(new Date(event.get("created").getAsLong()*1000)),12,TerminalUi.MUTED);
                if(event.get("expires").getAsLong()<=System.currentTimeMillis()/1000)TerminalUi.label(card,getString(R.string.notice_expired),12,TerminalUi.MUTED);
            }
            if(offset>0)TerminalUi.button(content,R.string.notice_recent,()->noticeList(0));
            if(!page.get("next_offset").isJsonNull())TerminalUi.button(content,R.string.notice_older,()->noticeList(page.get("next_offset").getAsInt()));
        });
    }
    private void noticeCompose(JsonObject original){
        screen="notice-compose";shell(getString(original==null?R.string.notice_new:R.string.notice_edit),this::noticeAdmin,null);
        if(original!=null)TerminalUi.label(content,getString(R.string.notice_revision,original.get("revision").getAsInt()),12,TerminalUi.MUTED);
        EditText title=input(content,R.string.notice_title,false);title.setSingleLine(true);title.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(160)});title.setText(announcementTitle);
        EditText body=input(content,R.string.notice_body,true);body.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(4000)});body.setText(announcementBody);
        TerminalUi.label(content,getString(original==null?R.string.notice_audience:R.string.notice_edit_hint),13,TerminalUi.MUTED);
        TerminalUi.button(content,R.string.notice_preview,()->{
            announcementTitle=title.getText().toString().trim();announcementBody=body.getText().toString().trim();
            if(announcementTitle.isEmpty()||announcementBody.isEmpty()){notice.setText(R.string.notice_required);return;}
            JsonObject value=args("title",announcementTitle,"body",announcementBody);
            if(original==null){
                value.addProperty("id",java.util.UUID.randomUUID().toString().replace("-",""));value.addProperty("kind","information");
                JsonArray platforms=new JsonArray();for(String platform:new String[]{"android","windows","linux"})platforms.add(platform);value.add("platforms",platforms);value.addProperty("days",30);
            }else{
                value.add("id",original.get("id"));value.add("revision",original.get("revision"));value.addProperty("request_id",java.util.UUID.randomUUID().toString().replace("-",""));
            }
            noticePreview(value,original);
        });
    }
    private void noticePreview(JsonObject value,JsonObject original){
        screen="notice-preview";shell(getString(R.string.notice_preview),()->noticeCompose(original),null);
        TerminalUi.label(content,value.get("title").getAsString(),18,TerminalUi.MINT);
        TerminalUi.label(content,value.get("body").getAsString(),15,TerminalUi.TEXT);
        TerminalUi.label(content,getString(original==null?R.string.notice_audience:R.string.notice_edit_hint),13,TerminalUi.AMBER);
        TerminalUi.button(content,original==null?R.string.notice_publish:R.string.notice_save_edit,()->noticeJob(()->{
            FriendsAccessAndroid api=new FriendsAccessAndroid(this,true);
            JsonObject result=original==null?api.publishNotice(value):api.editNotice(value);
            ChatRuntime.syncEvents(this,chat,true);return result;
        },result->{announcementTitle="";announcementBody="";noticeAdmin();}));
    }
    private void noticeJob(Work work,Consumer<JsonElement> success){
        job(()->{
            JsonObject result=new JsonObject();
            try{result.add("value",work.run());}
            catch(FriendsAccessAndroid.Conflict conflict){result.addProperty("failure","conflict");}
            catch(FriendsAccessAndroid.Denied denied){result.addProperty("failure","denied");}
            catch(Exception unavailable){result.addProperty("failure","unavailable");}
            return result;
        },result->{JsonObject reply=result.getAsJsonObject();if(reply.has("failure"))notice.setText(reply.get("failure").getAsString().equals("conflict")?R.string.notice_conflict:reply.get("failure").getAsString().equals("denied")?R.string.notice_denied:R.string.notice_unavailable);else success.accept(reply.get("value"));});
    }
    private void renameContact(){
        if(busy||peer==null)return;
        screen="rename";ChatRuntime.visiblePeer=null;
        shell(getString(R.string.chat_rename),this::conversation,null);
        EditText name=input(content,R.string.chat_name,false);name.setSingleLine(true);
        name.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(80)});
        name.setText(peer.has("name")?peer.get("name").getAsString():"");
        TerminalUi.label(content,getString(R.string.chat_name_hint),13,TerminalUi.MUTED);
        TerminalUi.button(content,R.string.chat_save_name,()->{String value=name.getText().toString(),address=peer.get("address").getAsString();job(()->chat.call("rename_contact",args("address",address,"name",value)),result->{peer=result.getAsJsonObject();conversation();});});
    }
    private void editChatMessage(JsonObject message){
        if(busy||peer==null||!message.get("outgoing").getAsBoolean())return;
        screen="message-edit";shell(getString(R.string.chat_edit_message),this::conversation,null);
        EditText text=input(content,R.string.chat_message_hint,true);text.setText(message.get("text").getAsString());
        TerminalUi.button(content,R.string.notice_save_edit,()->{
            String value=text.getText().toString();if(value.trim().isEmpty()||value.getBytes(StandardCharsets.UTF_8).length>4096){notice.setText(R.string.chat_invalid_message);return;}
            job(()->chat.call("edit_message",args("address",peer.get("address").getAsString(),"message_id",message.get("id").getAsString(),"text",value)),result->conversation());
        });
    }
    private void clearVoice(){
        if(voiceTimer!=null)handler.removeCallbacks(voiceTimer);voiceTimer=null;
        if(voiceSendTimer!=null)handler.removeCallbacks(voiceSendTimer);voiceSendTimer=null;
        recordingVoice=false;voiceSending=false;
        if(audio!=null)audio.close();if(voiceDraft!=null){java.util.Arrays.fill(voiceDraft,(byte)0);voiceDraft=null;}
        if(thread!=null)thread.recordingState(VoiceHoldButton.IDLE);
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }
    private boolean startVoice(){
        if(!visible||busy||peer==null||thread==null||!screen.equals("conversation")||recordingVoice||voiceSending)return false;
        if(android.os.Build.VERSION.SDK_INT<29){notice.setText(R.string.chat_voice_unsupported);return false;}
        if(checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)!=android.content.pm.PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO},81);return false;}
        clearVoice();
        try{
            audio.start(()->stopVoice(false));recordingVoice=true;recordingStarted=android.os.SystemClock.elapsedRealtime();
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
            thread.recordingElapsed(0);thread.recordingState(VoiceHoldButton.HOLDING);
            voiceTimer=new Runnable(){public void run(){if(!recordingVoice||thread==null)return;thread.recordingElapsed(android.os.SystemClock.elapsedRealtime()-recordingStarted);handler.postDelayed(this,200);}};handler.post(voiceTimer);
            return true;
        }catch(Exception error){clearVoice();notice.setText(R.string.chat_voice_failed);return false;}
    }
    private void stopVoice(boolean send){
        if(!recordingVoice)return;recordingVoice=false;
        if(voiceTimer!=null)handler.removeCallbacks(voiceTimer);voiceTimer=null;
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        long elapsed=android.os.SystemClock.elapsedRealtime()-recordingStarted;
        if(elapsed<400){clearVoice();notice.setText(R.string.chat_voice_hold);return;}
        try{
            voiceDraft=audio.finish();
            if(thread!=null){thread.recordingState(VoiceHoldButton.READY);thread.recordingElapsed(Math.min(elapsed,ChatAudio.MAX_MILLIS));}
            if(send)sendVoiceDraft();
        }catch(Exception error){clearVoice();notice.setText(R.string.chat_voice_failed);}
    }
    private void sendVoiceDraft(){
        if(!visible||!screen.equals("conversation")||voiceDraft==null||voiceSending||peer==null)return;
        if(thread!=null)thread.recordingState(VoiceHoldButton.SENDING);
        if(busy){if(voiceSendTimer==null){voiceSendTimer=()->{voiceSendTimer=null;sendVoiceDraft();};handler.postDelayed(voiceSendTimer,100);}return;}
        busy=true;voiceSending=true;final int expected=generation;
        final String encoded=java.util.Base64.getEncoder().encodeToString(voiceDraft),address=peer.get("address").getAsString();
        WORKER.execute(()->{
            String error=null;
            try{chat.call("queue_audio",args("address",address,"audio",encoded));}
            catch(ChatLocalAndroid.ChatException failure){error=failure.code.equals("invalid_input")?"invalid_audio":failure.code;}
            catch(Exception failure){error="store_unavailable";}
            final String code=error;
            runOnUiThread(()->{
                if(!visible||generation!=expected||isDestroyed())return;
                busy=false;voiceSending=false;
                if(code==null){clearVoice();offset=-1;conversation();}
                else{if(thread!=null)thread.recordingState(VoiceHoldButton.READY);notice.setText(errorText(code));}
            });
        });
    }
    private void playVoice(JsonObject message){
        if(busy||recordingVoice||voiceDraft!=null)return;
        String id=message.get("id").getAsString();
        if(audio.selected(id)){audio.toggle(id);return;}
        job(()->chat.call("audio",args("message_id",message.get("id").getAsString())),result->{
            byte[] bytes=java.util.Base64.getDecoder().decode(result.getAsJsonObject().get("audio").getAsString());
            try{audio.playMessage(id,bytes,()->{});}catch(Exception error){notice.setText(R.string.chat_voice_failed);}finally{java.util.Arrays.fill(bytes,(byte)0);}
        });
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results){
        super.onRequestPermissionsResult(request,permissions,results);
        if(request==81&&visible&&screen.equals("conversation")){notice.setText(results.length>0&&results[0]==android.content.pm.PackageManager.PERMISSION_GRANTED?R.string.chat_voice_hold:R.string.chat_voice_permission);}
    }
    private void sendMessage(String address,String text){
        if(text.trim().isEmpty()||text.getBytes(StandardCharsets.UTF_8).length>4096){notice.setText(R.string.chat_invalid_message);return;}
        job(()->{JsonElement result=chat.call("queue",args("address",address,"text",text));committed.text=text;return result;},saved->{
            if(draft.equals(text)){draft="";if(thread!=null)thread.composer.setText("");}committed.text=null;offset=-1;conversation();
        });
    }
    @Override public void onBackPressed(){clearVoice();if(!screen.equals("contacts")&&!screen.equals("welcome"))contacts();else super.onBackPressed();}
    private EditText input(LinearLayout parent, int hint, boolean multiline) {
        EditText edit = new EditText(this); TerminalUi.textStyle(edit, 16, TerminalUi.TEXT);
        edit.setHint(hint); edit.setHintTextColor(TerminalUi.MUTED);
        edit.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS |
            (multiline ? InputType.TYPE_TEXT_FLAG_MULTI_LINE : InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD));
        edit.setMinLines(multiline ? 3 : 2); edit.setMaxLines(6);
        edit.setSaveEnabled(false); // Never put drafts/public cards in Activity saved-state.
        if (android.os.Build.VERSION.SDK_INT >= 26) edit.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO);
        parent.addView(edit, new LinearLayout.LayoutParams(-1, -2)); return edit;
    }
    private interface Work { JsonElement run() throws Exception; }
    private void job(Work work, Consumer<JsonElement> success) {
        if (!visible || busy) return;
        busy = true;
        final int expected = generation;
        WORKER.execute(() -> {
            JsonElement value = null; String error = null;
            try { value = work.run(); }
            catch (ChatLocalAndroid.ChatException failure) { error = failure.code; }
            catch (Exception failure) { error = "store_unavailable"; }
            final JsonElement result = value; final String code = error;
            runOnUiThread(() -> {
                if (!visible || generation != expected || isDestroyed()) return;
                busy = false;
                if (code == null) success.accept(result);
                else {
                    notice.setText(errorText(code));
                    if (code.equals("store_unavailable") || code.equals("busy"))
                        TerminalUi.button(content, R.string.chat_reopen, this::recreate);
                }
            });
        });
    }
    private static void enable(View view, boolean enabled) {
        view.setEnabled(enabled);
        if (view instanceof ViewGroup) for (int i=0; i<((ViewGroup)view).getChildCount(); i++) enable(((ViewGroup)view).getChildAt(i), enabled);
    }
    private static JsonObject args(String... pairs) {
        JsonObject result = new JsonObject();
        for (int i=0; i<pairs.length; i+=2) result.addProperty(pairs[i], pairs[i+1]); return result;
    }
    private static String shortAddress(String address) { return address.substring(0,8) + "…" + address.substring(address.length()-8); }
    private static String groups(String value) { return value.replaceAll("(.{4})(?!$)", "$1 "); }
    static int status(String value) {
        switch (value) {
            case "queued": return R.string.chat_queued;
            case "sending": return R.string.chat_sending;
            case "relayed": return R.string.chat_relayed;
            case "delivered": return R.string.chat_delivered;
            case "received": return R.string.chat_received;
            default: return R.string.chat_unknown;
        }
    }
    private static int errorText(String code) {
        switch (code) {
            case "invitation_required": return R.string.chat_invitation_required;
            case "enrollment_unavailable": return R.string.chat_enrollment_unavailable;
            case "invalid_input": return R.string.chat_invalid_input;
            case "invalid_audio": return R.string.chat_voice_invalid;
            case "own_contact": return R.string.chat_own_contact;
            case "message_not_saved": return R.string.chat_not_saved;
            case "contact_not_saved": return R.string.chat_contact_not_saved;
            default: return R.string.chat_storage_error;
        }
    }
}
