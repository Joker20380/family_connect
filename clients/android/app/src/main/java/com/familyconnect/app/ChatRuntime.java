package com.familyconnect.app;

import android.content.Context;
import com.google.gson.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import javax.net.ssl.HttpsURLConnection;

/** One process owner and serialized queue shared by UI and background delivery. */
final class ChatRuntime {
    static final ScheduledExecutorService WORKER=Executors.newSingleThreadScheduledExecutor();
    private static ChatLocalAndroid owner;
    private static volatile boolean attached;
    private static volatile ChatCarrier carrier;
    private static long enrollmentExpires;
    private static long retryEnrollment,nextEvents,nextMailbox;
    private static ScheduledFuture<?> task;
    static volatile String visiblePeer;
    static volatile boolean uiVisible;
    static volatile int unread;
    static volatile long eventsRevision;
    static volatile boolean eventsUnavailable;
    private static String subscriptionMarker;
    static final SubscriptionRefreshGate SUBSCRIPTION_REFRESH=new SubscriptionRefreshGate();
    static String configuredRoute(){ChatCarrier current=carrier;return attached&&current!=null?current.route():"—";}
    static ChatLocalAndroid open(Context context,boolean create)throws Exception{
        if(owner==null)owner=ChatLocalAndroid.open(context,create);
        return owner;
    }
    static JsonObject enroll(Context context,ChatLocalAndroid chat)throws Exception{
        if(attached&&System.currentTimeMillis()/1000<enrollmentExpires-20){JsonObject value=new JsonObject();value.addProperty("status","active");return value;}
        if(carrier==null)carrier=new ChatCarrier(context);
        long terminal=ConnectionTerminal.CHAT.begin(ConnectionTerminal.Stage.CHAT_ENROLL);
        JsonObject result;
        try{result=new FriendsAccessAndroid(context,carrier).registerChat(chat);}
        catch(FriendsAccessAndroid.Denied|FriendsAccessAndroid.Conflict rejected){ConnectionTerminal.CHAT.end(terminal,ConnectionTerminal.Stage.AUTH,false);enrollmentExpires=0;chat.deliveryUpdate(false,false);carrier.close();carrier=null;throw rejected;}
        catch(Exception|LinkageError unavailable){ConnectionTerminal.CHAT.end(terminal,ConnectionTerminal.Stage.FAILED,false);throw unavailable;}
        if("active".equals(result.get("status").getAsString())){
            ConnectionTerminal.CHAT.add(terminal,"SERVICE_ONLY".equals(carrier.route())?ConnectionTerminal.Stage.CHAT_SERVICE:"EXISTING_EXIT".equals(carrier.route())?ConnectionTerminal.Stage.CHAT_EXISTING:ConnectionTerminal.Stage.CHAT_DIRECT);
            JsonObject node=result.getAsJsonObject("node");
            enrollmentExpires=node.get("expires_at").getAsLong();
            try{chat.configureDelivery(node.get("host").getAsString(),node.get("port").getAsInt(),node.get("public_key").getAsString(),carrier,enrollmentExpires);attached=true;ConnectionTerminal.CHAT.end(terminal,ConnectionTerminal.Stage.CHAT_READY,true);}
            catch(Exception|LinkageError unavailable){ConnectionTerminal.CHAT.end(terminal,ConnectionTerminal.Stage.FAILED,false);throw unavailable;}
        }
        else ConnectionTerminal.CHAT.end(terminal,ConnectionTerminal.Stage.FAILED,false);
        return result;
    }
    static void start(Context context){
        Context app=context.getApplicationContext();
        WORKER.execute(()->{if(task==null)task=WORKER.scheduleWithFixedDelay(()->tick(app),0,6,TimeUnit.SECONDS);});
    }
    static void stop(){SUBSCRIPTION_REFRESH.cancel();ChatCarrier active=carrier;if(active!=null&&!uiVisible)active.close();WORKER.execute(()->{if(task!=null){task.cancel(false);task=null;}if(owner!=null&&!uiVisible)try{owner.close();owner=null;attached=false;carrier=null;}catch(Exception ignored){}});}
    private static void tick(Context context){
        try{
            // An existing identity must never be replaced on a failed resume.
            ChatLocalAndroid chat=open(context,!ChatLocalAndroid.hasState(context));
            boolean online=new ChatNetworkAndroid(context).available();
            long now=android.os.SystemClock.elapsedRealtime();
            if((!attached||System.currentTimeMillis()/1000>=enrollmentExpires-20)&&online&&now>=retryEnrollment){retryEnrollment=now+60000;try{enroll(context,chat);}catch(Exception ignored){}}
            if(attached){
                chat.deliveryUpdate(online&&System.currentTimeMillis()/1000<enrollmentExpires,true);
                JsonObject state=chat.call("delivery_state",new JsonObject()).getAsJsonObject();
                if(online&&!state.get("running").getAsBoolean()&&!state.get("pending").getAsBoolean()&&now>=nextMailbox){nextMailbox=now+(state.get("error").isJsonNull()?15000:60000);chat.call("request_sync",new JsonObject());}
            }
            syncEvents(context,chat,false);
            deliverNotifications(context,chat);
        }catch(Exception ignored){/* Keep history/identity intact; retry on the next tick. */}
    }
    /** Worker-only: foreground and background share one bounded polling deadline. */
    static void syncEvents(Context context,ChatLocalAndroid chat,boolean force){
        long now=android.os.SystemClock.elapsedRealtime();
        if(!force&&now<nextEvents)return;
        nextEvents=now+30000;
        try{
            String before=chat.call("service_events",new JsonObject()).toString();
            fetchEvents(context,chat);
            if(!before.equals(chat.call("service_events",new JsonObject()).toString()))eventsRevision++;
            eventsUnavailable=false;
        }catch(Exception unavailable){eventsUnavailable=true;}
    }
    private static void fetchEvents(Context context,ChatLocalAndroid chat)throws Exception{
        HttpsURLConnection connection=new ChatNetworkAndroid(context).openHttps("https://185.251.89.19:8443/downloads/family-connect-events-v2.json");
        connection.setConnectTimeout(8000);connection.setReadTimeout(8000);connection.setInstanceFollowRedirects(false);connection.setUseCaches(false);
        try{
            if(connection.getResponseCode()!=200)throw new java.io.IOException("Events unavailable");
            byte[] data;try(var input=connection.getInputStream();var output=new java.io.ByteArrayOutputStream()){byte[] buffer=new byte[8192];int n;while((n=input.read(buffer))!=-1){if(output.size()+n>1048576)throw new java.io.IOException("Events too large");output.write(buffer,0,n);}data=output.toByteArray();}
            if(data.length>1048576)return;
            JsonObject args=new JsonObject();args.add("feed",JsonParser.parseString(new String(data,StandardCharsets.UTF_8)));
            chat.call("import_events",args);
        }finally{connection.disconnect();}
    }
    static void mark(ChatLocalAndroid chat,String operation,JsonArray ids,String flag)throws Exception{
        JsonObject args=new JsonObject();args.add("ids",ids);args.addProperty("flag",flag);chat.call(operation,args);
    }
    static JsonObject subscription(Context context,ChatLocalAndroid chat)throws Exception{
        try(ControlIdentity identity=new FriendsIdentityVault(context).load()){
            JsonObject args=new JsonObject();args.addProperty("device",identity.reference());
            return chat.call("subscription_status",args).getAsJsonObject();
        }
    }
    static void refreshSubscription(Context context,SubscriptionRefreshGate.Request request,java.util.function.Consumer<JsonObject> completion){
        Context app=context.getApplicationContext();
        WORKER.execute(()->{
            JsonObject result=new JsonObject();String outcome="unavailable";
            try(ControlIdentity identity=new FriendsIdentityVault(app).load()){
                if(request.cancelled())throw new SubscriptionRefreshGate.Cancelled();
                ChatLocalAndroid expected=open(app,!ChatLocalAndroid.hasState(app));
                result=subscription(app,expected);
                if(!request.bind(expected,identity.reference())){result=new JsonObject();throw new SubscriptionRefreshGate.Cancelled();}
                if(!new ChatNetworkAndroid(app).available())outcome="offline";
                else{
                    JsonObject response=new FriendsAccessAndroid(app,android.os.SystemClock.elapsedRealtime()+20000).subscription(identity);
                    JsonObject[] saved=new JsonObject[1];
                    try(ControlIdentity current=new FriendsIdentityVault(app).load()){
                        if(!request.commit(owner,current.reference(),()->saved[0]=expected.acceptSubscription(response,identity.reference()))){result=new JsonObject();throw new SubscriptionRefreshGate.Cancelled();}
                    }
                    result=saved[0].getAsJsonObject("view");
                    outcome=saved[0].get("accepted").getAsBoolean()?"current":"stale";
                    eventsRevision++;
                }
            }catch(SubscriptionRefreshGate.Cancelled cancelled){outcome="cancelled";}
            catch(SubscriptionRequest.Unsupported unsupported){outcome="unsupported";}
            catch(SubscriptionRequest.IdentityRejected rejected){outcome="identity_rejected";}
            catch(SubscriptionRequest.InvalidResponse invalid){outcome="invalid";}
            catch(ChatLocalAndroid.ChatException invalid){outcome="invalid_subscription".equals(invalid.code)?"invalid":"unavailable";}
            catch(Exception unavailable){outcome="unavailable";}
            finally{SUBSCRIPTION_REFRESH.finish(request);}
            result.addProperty("refresh_status",outcome);completion.accept(result);
            if("current".equals(outcome)||"stale".equals(outcome))new android.os.Handler(android.os.Looper.getMainLooper()).post(()->deliverSavedNotifications(app));
        });
    }
    static void deliverSavedNotifications(Context context){
        Context app=context.getApplicationContext();
        WORKER.execute(()->{
            try{if(ChatLocalAndroid.hasState(app))deliverNotifications(app,open(app,false));}catch(Exception|LinkageError unavailable){}
        });
    }
    static JsonArray serviceEvents(Context context,ChatLocalAndroid chat)throws Exception{
        JsonArray events=chat.call("service_events",new JsonObject()).getAsJsonArray();
        try{
            JsonObject view=subscription(context,chat);
            String marker=view.get("notice").toString();
            if(!marker.equals(subscriptionMarker)){subscriptionMarker=marker;eventsRevision++;}
            if(!view.get("notice").isJsonNull())events.add(view.get("notice"));
        }catch(Exception unavailable){}
        return events;
    }
    static void deliverNotifications(Context context,ChatLocalAndroid chat)throws Exception{
        int count=0;java.util.Map<String,String> names=new java.util.HashMap<>();
        for(JsonElement item:chat.call("contacts",new JsonObject()).getAsJsonArray()){
            JsonObject card=item.getAsJsonObject();
            if(card.has("official_support")&&card.get("official_support").getAsBoolean())names.put(card.get("address").getAsString(),context.getString(R.string.chat_official_support));
            else if(card.has("name"))names.put(card.get("address").getAsString(),card.get("name").getAsString());
        }
        for(String operation:new String[]{"inbox","service_events"}){
            boolean service=operation.equals("service_events");
            JsonArray posted=new JsonArray();
            java.util.Map<String,java.util.List<JsonObject>> conversations=new java.util.LinkedHashMap<>();
            for(JsonElement item:service?serviceEvents(context,chat):chat.call(operation,new JsonObject()).getAsJsonArray()){
                JsonObject message=item.getAsJsonObject();if(message.get("read").getAsBoolean())continue;
                String peer=service?(message.has("subscription_event")?"subscription":"service"):message.get("peer").getAsString();
                conversations.computeIfAbsent(peer,ignored->new java.util.ArrayList<>()).add(message);count++;
            }
            for(var entry:conversations.entrySet()){
                String peer=entry.getKey();var messages=entry.getValue();
                if(peer.equals(visiblePeer)||(peer.equals("subscription")&&("service".equals(visiblePeer)||SubscriptionUi.visible()))){ChatNotifications.cancel(context,peer);continue;}
                boolean fresh=false;for(JsonObject message:messages)fresh|=!message.get("notified").getAsBoolean()&&!(message.has("notification_suppressed")&&message.get("notification_suppressed").getAsBoolean());
                if(!fresh)continue;
                JsonObject latest=messages.get(messages.size()-1);latest.addProperty("unread",messages.size());
                if(ChatNotifications.message(context,peer,latest,service,names.get(peer)))for(JsonObject message:messages)posted.add(message.get("id"));
            }
            if(!posted.isEmpty())mark(chat,service?"mark_events":"mark_inbox",posted,"notified");
        }
        unread=count;
    }
}
