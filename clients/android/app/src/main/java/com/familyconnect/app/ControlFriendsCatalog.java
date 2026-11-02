package com.familyconnect.app;

import com.google.gson.*;
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static com.familyconnect.app.ControlJson.*;

/** Signed tester gateway templates, without device credentials. Separate from managed config intake. */
final class ControlFriendsCatalog {
    static final List<String> GATEWAYS=List.of("nl-amsterdam-1","nl-amsterdam-2");
    static boolean explicit(String target){return GATEWAYS.contains(target);}
    static ControlFriendsCatalog verifySelection(JsonObject reply,byte[] anchor,String device,String target,long floor,String previousHash)throws Exception{
        require(explicit(target));fields(reply,"device country address tcp_id catalog gateway_id");
        require(text(reply.get("device")).equals(device)&&text(reply.get("country")).equals("nl")&&text(reply.get("gateway_id")).equals(target));
        var verified=verify(reply.getAsJsonObject("catalog").toString().getBytes(StandardCharsets.UTF_8),anchor,floor,3);
        if(previousHash!=null)require(verified.sequence!=floor||verified.digest.equals(previousHash));
        return verified;
    }
    static final byte[] DOMAIN="family-connect/invited-test/v1\0".getBytes(StandardCharsets.US_ASCII);
    final long sequence;
    final String digest;
    final Map<String,String> profiles;
    final Map<String,String> awgProfiles;
    private ControlFriendsCatalog(long sequence,String digest,Map<String,String> profiles,Map<String,String> awgProfiles){this.sequence=sequence;this.digest=digest;this.profiles=Collections.unmodifiableMap(profiles);this.awgProfiles=Collections.unmodifiableMap(awgProfiles);}
    static ControlFriendsCatalog verify(byte[] raw,byte[] anchor,long floor)throws Exception{
        return verify(raw,anchor,floor,2);
    }
    static ControlFriendsCatalog verify(byte[] raw,byte[] anchor,long floor,int schema)throws Exception{
        require(raw.length>0&&raw.length<=16384&&anchor.length==32);
        JsonObject envelope=parse(raw).getAsJsonObject();fields(envelope,"payload signature");
        byte[] payload=ControlProtocol.base64(text(envelope.get("payload")),true);
        byte[] signature=ControlProtocol.base64(text(envelope.get("signature")),true);require(payload.length<=8192&&signature.length==64);
        Ed25519Signer verifier=new Ed25519Signer();verifier.init(false,new Ed25519PublicKeyParameters(anchor,0));
        verifier.update(DOMAIN,0,DOMAIN.length);verifier.update(payload,0,payload.length);require(verifier.verifySignature(signature));
        JsonObject value=parse(payload).getAsJsonObject();fields(value,"schema sequence access gateways");
        require((schema==2||schema==3)&&integer(value.get("schema"),1)==schema&&text(value.get("access")).equals("invite-test"));
        long sequence=integer(value.get("sequence"),1);require(sequence>=floor);
        Map<String,String> profiles=new LinkedHashMap<>(),awgProfiles=new LinkedHashMap<>();JsonArray gateways=value.getAsJsonArray("gateways");require(gateways.size()==2);
        for(JsonElement item:gateways){
            JsonObject gateway=item.getAsJsonObject();fields(gateway,"country tcp awg"+(schema==3?" gateway_id":""));String country=text(gateway.get("country"));
            require(country.equals("ru")||country.equals("nl"));
            String target=schema==3?text(gateway.get("gateway_id")):country;
            require(!profiles.containsKey(target)&&(schema!=3||(country.equals("nl")&&explicit(target))));
            JsonObject tcp=gateway.getAsJsonObject("tcp").deepCopy();require(text(tcp.get("type")).equals("vless-reality-v1"));require(text(tcp.get("id")).equals("DEVICE_CREDENTIAL"));
            tcp.addProperty("id","11111111-1111-4111-8111-111111111111");TcpProfile.validate(tcp.toString());
            if(schema==3)for(String existing:profiles.values())require(!parse(existing.getBytes(StandardCharsets.UTF_8)).getAsJsonObject().get("server").equals(tcp.get("server")));
            profiles.put(target,gateway.getAsJsonObject("tcp").toString());
            String template=text(gateway.get("awg"));
            require(java.util.regex.Pattern.compile("(?m)^PrivateKey = LOCAL_DEVICE_KEY$").matcher(template).find()&&java.util.regex.Pattern.compile("(?m)^Address = ASSIGNED_ADDRESS$").matcher(template).find());
            require(template.contains("HeaderProtectionKey = ")&&template.contains("ContentPaddingAddition = "));
            require(template.split("LOCAL_DEVICE_KEY",-1).length==2&&template.split("ASSIGNED_ADDRESS",-1).length==2);
            byte[] sample=new byte[32];Arrays.fill(sample,(byte)1);
            ProfileValidator.validate(template.replace("LOCAL_DEVICE_KEY",Base64.getEncoder().encodeToString(sample)).replace("ASSIGNED_ADDRESS","10.83.0.2/32"),Transport.AWG);
            if(schema==3){
                var endpoint=java.util.regex.Pattern.compile("(?m)^Endpoint = ([0-9.]+):[0-9]+$").matcher(template);
                require(endpoint.find()&&endpoint.group(1).equals(text(tcp.get("server")))&&!endpoint.find());
            }
            awgProfiles.put(target,template);
        }
        require(profiles.size()==2);return new ControlFriendsCatalog(sequence,ControlProtocol.hash(payload),profiles,awgProfiles);
    }
}
