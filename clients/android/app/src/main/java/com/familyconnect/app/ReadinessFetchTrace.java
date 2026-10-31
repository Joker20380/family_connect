package com.familyconnect.app;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;

final class ReadinessFetchTrace {
    enum Operation { CHALLENGE, FETCH, UNKNOWN }
    enum Stage { LOCAL, OPEN_NETWORK, CONNECT_TLS_WRITE, HTTP_STATUS, READ_BODY, PARSE, BINDING, RELAY_OPEN, RELAY_REQUEST, COMPLETE }
    enum Route { HTTPS_UNDERLAY, HTTPS_VPN, RNS }
    enum Error { NONE, DNS, CONNECT, SOCKET, TIMEOUT, TLS, AUTHORIZATION, HTTP, UNAVAILABLE, IO, PROTOCOL, SECURITY, INTERNAL }
    private final JsonObject value=new JsonObject();
    private final JsonArray failures=new JsonArray();
    private Operation operation=Operation.UNKNOWN;
    private Stage stage=Stage.LOCAL;
    private Route route=Route.HTTPS_UNDERLAY;
    private int httpStatus;
    private final long startedNanos=System.nanoTime();
    ReadinessFetchTrace(OwnerPrewarmReceipt receipt,String connection,long started){
        value.addProperty("attempt_id",receipt.challengeId);value.addProperty("fetch_id",receipt.fetchId);
        value.addProperty("started_connection_id",connection);value.addProperty("started_at",started);
    }
    void request(String path,Route selected){
        operation=path.endsWith("/challenge")?Operation.CHALLENGE:path.equals("/friends/restricted-readiness")?Operation.FETCH:Operation.UNKNOWN;
        route=selected;httpStatus=0;stage=Stage.LOCAL;
    }
    void stage(Stage selected){stage=selected;}
    void status(int status){httpStatus=status>=100&&status<=599?status:0;stage=Stage.HTTP_STATUS;}
    void network(String type,long generation){
        value.addProperty("network_type",java.util.Arrays.asList("WIFI","CELLULAR","ETHERNET","NONE","OTHER").contains(type)?type:"OTHER");
        value.addProperty("network_generation",Math.max(0,generation));
    }
    static Error classify(Throwable failure){
        if(failure instanceof FriendsReadinessProtocol.ChallengeFailure){
            FriendsReadinessProtocol.ChallengeFailure challenge=(FriendsReadinessProtocol.ChallengeFailure)failure;
            if(challenge.code==FriendsReadinessProtocol.ChallengeCode.CHALLENGE_UNAUTHORIZED)return Error.AUTHORIZATION;
            if(challenge.availabilityFailure)return Error.UNAVAILABLE;
        }
        if(failure instanceof javax.net.ssl.SSLException)return Error.TLS;
        if(failure instanceof java.net.UnknownHostException)return Error.DNS;
        if(failure instanceof java.net.ConnectException)return Error.CONNECT;
        if(failure instanceof java.net.SocketTimeoutException)return Error.TIMEOUT;
        if(failure instanceof java.net.SocketException)return Error.SOCKET;
        if(failure instanceof FriendsReadinessProtocol.AuthorizationFailure)return Error.AUTHORIZATION;
        if(failure instanceof FriendsReadinessProtocol.Unavailable)return Error.UNAVAILABLE;
        if(failure instanceof java.io.IOException)return Error.IO;
        if(failure instanceof SecurityException)return Error.SECURITY;
        if(failure instanceof IllegalArgumentException)return Error.PROTOCOL;
        return Error.INTERNAL;
    }
    void failed(Throwable failure){
        JsonObject entry=new JsonObject();entry.addProperty("operation",operation.name());entry.addProperty("stage",stage.name());
        entry.addProperty("route",route.name());entry.addProperty("error_class",classify(failure).name());
        entry.addProperty("http_status",httpStatus);
        if(value.has("network_type"))entry.add("network_type",value.get("network_type"));
        if(value.has("network_generation"))entry.add("network_generation",value.get("network_generation"));
        if(failures.size()==4)failures.remove(0);failures.add(entry);
    }
    void cache(JsonObject cache){value.add("cache",cache);}
    void complete(ReadinessImportResult.Code result,boolean selected,boolean refreshed,long finished){
        value.addProperty("refresh_result",result.name());value.addProperty("selected_source",selected?(refreshed?"REFRESH":"CACHE"):"NONE");
        value.addProperty("finished_at",finished);value.addProperty("operation",operation.name());value.addProperty("stage",stage.name());
        value.addProperty("duration_ms",Math.max(0,(System.nanoTime()-startedNanos)/1000000));
    }
    JsonObject json(){JsonObject copy=value.deepCopy();copy.add("failures",failures.deepCopy());return copy;}
}
