package com.familyconnect.app;

import android.content.Context;
import com.google.gson.*;
import java.io.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.util.*;
import javax.net.ssl.HttpsURLConnection;
import static com.familyconnect.app.ControlJson.*;

/** One-use invitation activation; later requests prove the persisted device identity. */
final class FriendsAccessAndroid {
    private final Context context;
    private final boolean direct;
    static final class Denied extends Exception {}
    static final class Conflict extends Exception {}
    FriendsAccessAndroid(Context context){this(context,false);}
    FriendsAccessAndroid(Context context,boolean direct){this.context=context;this.direct=direct;}
    private boolean present(String name,String alias)throws Exception{
        File file=new File(context.getNoBackupFilesDir(),name);KeyStore keys=KeyStore.getInstance("AndroidKeyStore");keys.load(null);
        return keys.containsAlias(alias)||file.exists()||new File(file+".bak").exists()||new File(file+".new").exists();
    }
    private ControlIdentity identity(boolean create)throws Exception{
        FriendsIdentityVault vault=new FriendsIdentityVault(context);
        if(present("friends-identity.enc","family-connect-friends-identity-v1"))return vault.load();
        if(!create)throw new Denied();return vault.create();
    }
    private JsonObject post(String path,JsonObject body)throws Exception{
        require(path.matches("/friends/(challenge|activate|configuration/(ru|nl)|chat/(challenge|register)|referral/(issue|claim)|device/status|notices/device/(role|publish|list|edit))"));
        HttpsURLConnection connection=direct?new ChatNetworkAndroid(context).openHttps("https://185.251.89.19:8443"+path):(HttpsURLConnection)new URL("https://185.251.89.19:8443"+path).openConnection();
        try{
            connection.setConnectTimeout(5000);connection.setReadTimeout(15000);connection.setInstanceFollowRedirects(false);connection.setUseCaches(false);connection.setRequestMethod("POST");connection.setDoOutput(true);connection.setRequestProperty("Content-Type","application/json");
            byte[] raw=body.toString().getBytes(StandardCharsets.UTF_8);require(raw.length<=((path.equals("/friends/notices/device/publish")||path.equals("/friends/notices/device/edit"))?32768:8192));connection.setFixedLengthStreamingMode(raw.length);
            try(OutputStream out=connection.getOutputStream()){out.write(raw);}finally{Arrays.fill(raw,(byte)0);}
            int status=connection.getResponseCode();if(status==409)throw new Conflict();if(status==400||status==403)throw new Denied();if(status!=200)throw new IOException("Test access unavailable");
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();long deadline=System.nanoTime()+20_000_000_000L;
            try(InputStream input=connection.getInputStream()){byte[] buffer=new byte[1024];int n;while((n=input.read(buffer))!=-1){if(bytes.size()+n>(path.equals("/friends/notices/device/list")?1048576:16384)||System.nanoTime()>deadline||Thread.currentThread().isInterrupted())throw new IOException();bytes.write(buffer,0,n);}}
            return parse(bytes.toByteArray()).getAsJsonObject();
        }finally{connection.disconnect();}
    }
    private JsonObject proof(ControlIdentity identity,String purpose,String invitation)throws Exception{
        JsonObject request=new JsonObject();request.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));request.addProperty("wireguard_public_key",identity.wireguardPublicKey());request.addProperty("purpose",purpose);request.addProperty("invitation",invitation);
        JsonObject challenge=post("/friends/challenge",request);fields(challenge,"challenge expires_at audience");
        long now=System.currentTimeMillis()/1000,expiry=integer(challenge.get("expires_at"),1);require(expiry>now&&expiry-now<=120&&text(challenge.get("audience")).equals("family-connect/enrollment/v1"));
        return identity.proveTransportKey(text(challenge.get("challenge")));
    }
    void activate(String invitation)throws Exception{
        try(ControlIdentity identity=identity(true)){
            JsonObject result=post("/friends/activate",proof(identity,"activate",invitation));fields(result,"device status");
            require(text(result.get("device")).equals(identity.reference())&&text(result.get("status")).equals("active"));
        }
    }
    String register(String invitationToken) throws Exception {
        try(ControlIdentity identity=identity(true)) {
            String invitation="";
            if(!invitationToken.isEmpty()){
                require(invitationToken.matches("[0-9a-f]{64}"));
                JsonObject request=new JsonObject();request.addProperty("token",invitationToken);request.addProperty("request_id",identity.reference());
                JsonObject claim=post("/friends/referral/claim",request);fields(claim,"invitation status");
                invitation=text(claim.get("invitation"));require(invitation.matches("FC-(?:[A-F0-9]{4}-){7}[A-F0-9]{4}"));
                require(text(claim.get("status")).equals("issued")||text(claim.get("status")).equals("activated"));
            }
            JsonObject result=post("/friends/activate",proof(identity,"activate",invitation));
            fields(result,"device status");
            require(text(result.get("device")).equals(identity.reference())&&text(result.get("status")).equals("active"));
            return identity.reference();
        }
    }
    String deviceStatus() throws Exception {
        try(ControlIdentity identity=identity(false)) {
            JsonObject request=new JsonObject();
            request.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));
            request.addProperty("wireguard_public_key",identity.wireguardPublicKey());
            request.addProperty("purpose","status");
            request.addProperty("invitation","");
            JsonObject challenge=post("/friends/challenge",request);fields(challenge,"challenge expires_at audience");
            long now=System.currentTimeMillis()/1000,expiry=integer(challenge.get("expires_at"),1);
            require(expiry>now&&expiry-now<=120&&text(challenge.get("audience")).equals("family-connect/enrollment/v1"));
            JsonObject result=post("/friends/device/status",identity.proveTransportKey(text(challenge.get("challenge"))));
            fields(result,"device registered revoked active");
            require(text(result.get("device")).equals(identity.reference()));
            require(result.get("registered").isJsonPrimitive()&&result.get("registered").getAsJsonPrimitive().isBoolean());
            require(result.get("revoked").isJsonPrimitive()&&result.get("revoked").getAsJsonPrimitive().isBoolean());
            require(result.get("active").isJsonPrimitive()&&result.get("active").getAsJsonPrimitive().isBoolean());
            return result.get("active").getAsBoolean()?text(result.get("device")):"";
        }
    }
    JsonObject referral() throws Exception {
        try(ControlIdentity identity=identity(false)) {
            JsonObject result=post("/friends/referral/issue",proof(identity,"refer",""));
            fields(result,"url pool_limit remaining");
            require(text(result.get("url")).matches("https://185\\.251\\.89\\.19:8443/(?:invite|i)/#[0-9a-f]{64}"));
            require(integer(result.get("pool_limit"),1)==500&&integer(result.get("remaining"),0)<=500);
            return result;
        }
    }
    JsonObject noticeRole() throws Exception {
        try(ControlIdentity identity=identity(false)) {
            JsonObject request=new JsonObject();request.add("proof",proof(identity,"notices-role",""));
            JsonObject result=post("/friends/notices/device/role",request);fields(result,"device role name");
            require(text(result.get("device")).equals(identity.reference()));
            require(text(result.get("role")).equals("administrator")||text(result.get("role")).equals("member"));
            return result;
        }
    }
    JsonObject publishNotice(JsonObject notice) throws Exception {
        try(ControlIdentity identity=identity(false)) {
            JsonObject request=new JsonObject();request.add("proof",proof(identity,"notices-publish",""));request.add("notice",notice);
            JsonObject result=post("/friends/notices/device/publish",request);fields(result,"id status");
            require(text(result.get("id")).equals(text(notice.get("id")))&&text(result.get("status")).equals("published"));return result;
        }
    }
    JsonObject listNotices(int offset) throws Exception {
        try(ControlIdentity identity=identity(false)) {
            JsonObject request=new JsonObject();request.add("proof",proof(identity,"notices-list",""));request.addProperty("offset",offset);
            JsonObject result=post("/friends/notices/device/list",request);fields(result,"events next_offset");return result;
        }
    }
    JsonObject editNotice(JsonObject notice) throws Exception {
        try(ControlIdentity identity=identity(false)) {
            JsonObject request=new JsonObject();request.add("proof",proof(identity,"notices-edit",""));request.add("notice",notice);
            JsonObject result=post("/friends/notices/device/edit",request);fields(result,"id revision status");
            require(text(result.get("id")).equals(text(notice.get("id")))&&text(result.get("status")).equals("updated"));return result;
        }
    }
    JsonObject registerChat(ChatLocalAndroid chat)throws Exception {
        try(ControlIdentity identity=identity(false)) {
            String publicKey=chat.call("profile",new JsonObject()).getAsJsonObject().get("public").getAsString();
            JsonObject request=new JsonObject();
            request.addProperty("public_identity",Base64.getEncoder().encodeToString(identity.publicIdentity()));
            request.addProperty("wireguard_public_key",identity.wireguardPublicKey());
            request.addProperty("chat_public",publicKey);
            JsonObject challenge=post("/friends/chat/challenge",request);
            fields(challenge,"challenge expires_at audience device chat_public");
            long now=System.currentTimeMillis()/1000,expiry=integer(challenge.get("expires_at"),1);
            require(expiry>now&&expiry-now<=120&&text(challenge.get("audience")).equals("family-connect/enrollment/v1"));
            require(text(challenge.get("device")).equals(identity.reference())&&text(challenge.get("chat_public")).equals(publicKey));
            String nonce=text(challenge.get("challenge"));
            JsonObject body=chat.enrollmentProof(identity.reference(),nonce);
            fields(body,"chat_public chat_signature");require(text(body.get("chat_public")).equals(publicKey));
            body.add("proof",identity.proveTransportKey(nonce));
            JsonObject result=post("/friends/chat/register",body);
            String status=text(result.get("status"));
            fields(result,status.equals("active")?"device chat_public status node":"device chat_public status");
            require(text(result.get("device")).equals(identity.reference())&&text(result.get("chat_public")).equals(publicKey)
                &&(status.equals("pending-node")||status.equals("active")));
            if(status.equals("active")) {
                JsonObject node=result.getAsJsonObject("node");fields(node,"sequence expires_at host port public_key");
                require(integer(node.get("sequence"),1)>0);
                long until=integer(node.get("expires_at"),1),current=System.currentTimeMillis()/1000;
                require(until>current&&until-current<=120);
                require(text(node.get("host")).matches("[0-9]+(\\.[0-9]+){3}")
                    &&integer(node.get("port"),1)<=65535&&text(node.get("public_key")).matches("[0-9a-f]{128}"));
            }
            return result;
        }
    }
    private String materialize(JsonObject reply,ControlIdentity identity,String country,String transport,long floor)throws Exception{
        fields(reply,"device country address tcp_id catalog");require(text(reply.get("device")).equals(identity.reference())&&text(reply.get("country")).equals(country));
        ControlFriendsCatalog catalog=ControlFriendsCatalog.verify(reply.getAsJsonObject("catalog").toString().getBytes(StandardCharsets.UTF_8),ControlTrust.anchor(context),floor);
        String id=text(reply.get("tcp_id"));require(id.matches("[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")&&!id.equals("00000000-0000-0000-0000-000000000000"));
        if(transport.equals("tcp"))return TcpProfile.validate(catalog.profiles.get(country).replace("DEVICE_CREDENTIAL",id));
        require(transport.equals("awg"));String address=text(reply.get("address")),prefix=country.equals("ru")?"10.84.":"10.83.";
        require(address.startsWith(prefix)&&address.matches("10\\.(83|84)\\.[0-9]{1,3}\\.[0-9]{1,3}/32"));
        String[] parts=address.substring(0,address.length()-3).split("\\.");for(String part:parts)require(Integer.parseInt(part)<=255&&Integer.toString(Integer.parseInt(part)).equals(part));
        require(!(parts[2].equals("0")&&(parts[3].equals("0")||parts[3].equals("1")))&&!(parts[2].equals("255")&&parts[3].equals("255")));
        byte[] key=identity.wireguardPrivateKey();try{return ProfileValidator.validate(catalog.awgProfiles.get(country).replace("LOCAL_DEVICE_KEY",Base64.getEncoder().encodeToString(key)).replace("ASSIGNED_ADDRESS",address),Transport.AWG);}finally{Arrays.fill(key,(byte)0);}
    }
    String profile(String country,String transport)throws Exception{
        require(country.equals("ru")||country.equals("nl"));require(transport.equals("awg")||transport.equals("tcp"));
        try(ControlIdentity identity=identity(false)){
            FriendsConfigurationVault vault=new FriendsConfigurationVault(context);boolean exists=present("friends-configuration.enc","family-connect-friends-configuration-v1");
            JsonObject cache=exists?parse(vault.read()).getAsJsonObject():new JsonObject();JsonObject prior=cache.has(country)?cache.getAsJsonObject(country):null;
            long floor=0;
            if(prior!=null){materialize(prior,identity,country,transport,0);floor=ControlFriendsCatalog.verify(prior.getAsJsonObject("catalog").toString().getBytes(StandardCharsets.UTF_8),ControlTrust.anchor(context),0).sequence;}
            JsonObject reply;
            try{reply=post("/friends/configuration/"+country,proof(identity,country,""));}
            catch(IOException unavailable){if(prior!=null)return materialize(prior,identity,country,transport,floor);throw unavailable;}
            String profile=materialize(reply,identity,country,transport,floor);cache.add(country,reply);
            byte[] raw=cache.toString().getBytes(StandardCharsets.UTF_8);try{if(exists)vault.write(raw);else vault.create(raw);}finally{Arrays.fill(raw,(byte)0);}
            return profile;
        }
    }
}
