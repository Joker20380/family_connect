package com.familyconnect.app;

import com.google.gson.*;
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static com.familyconnect.app.ControlJson.*;

/** Signed tester gateway templates, without device credentials. Separate from managed config intake. */
final class ControlFriendsCatalog {
    static final byte[] DOMAIN="family-connect/invited-test/v1\0".getBytes(StandardCharsets.US_ASCII);
    final long sequence;
    final Map<String,String> profiles;
    final Map<String,String> awgProfiles;
    private ControlFriendsCatalog(long sequence,Map<String,String> profiles,Map<String,String> awgProfiles){this.sequence=sequence;this.profiles=Collections.unmodifiableMap(profiles);this.awgProfiles=Collections.unmodifiableMap(awgProfiles);}
    static ControlFriendsCatalog verify(byte[] raw,byte[] anchor,long floor)throws Exception{
        require(raw.length>0&&raw.length<=16384&&anchor.length==32);
        JsonObject envelope=parse(raw).getAsJsonObject();fields(envelope,"payload signature");
        byte[] payload=ControlProtocol.base64(text(envelope.get("payload")),true);
        byte[] signature=ControlProtocol.base64(text(envelope.get("signature")),true);require(payload.length<=8192&&signature.length==64);
        Ed25519Signer verifier=new Ed25519Signer();verifier.init(false,new Ed25519PublicKeyParameters(anchor,0));
        verifier.update(DOMAIN,0,DOMAIN.length);verifier.update(payload,0,payload.length);require(verifier.verifySignature(signature));
        JsonObject value=parse(payload).getAsJsonObject();fields(value,"schema sequence access gateways");
        require(integer(value.get("schema"),1)==2&&text(value.get("access")).equals("invite-test"));
        long sequence=integer(value.get("sequence"),1);require(sequence>=floor);
        Map<String,String> profiles=new LinkedHashMap<>(),awgProfiles=new LinkedHashMap<>();JsonArray gateways=value.getAsJsonArray("gateways");require(gateways.size()==2);
        for(JsonElement item:gateways){
            JsonObject gateway=item.getAsJsonObject();fields(gateway,"country tcp awg");String country=text(gateway.get("country"));
            require(country.equals("ru")||country.equals("nl"));require(!profiles.containsKey(country));
            JsonObject tcp=gateway.getAsJsonObject("tcp").deepCopy();require(text(tcp.get("id")).equals("DEVICE_CREDENTIAL"));
            tcp.addProperty("id","11111111-1111-4111-8111-111111111111");TcpProfile.validate(tcp.toString());
            profiles.put(country,gateway.getAsJsonObject("tcp").toString());
            String template=text(gateway.get("awg"));
            require(java.util.regex.Pattern.compile("(?m)^PrivateKey = LOCAL_DEVICE_KEY$").matcher(template).find()&&java.util.regex.Pattern.compile("(?m)^Address = ASSIGNED_ADDRESS$").matcher(template).find());
            require(template.contains("HeaderProtectionKey = ")&&template.contains("ContentPaddingAddition = "));
            require(template.split("LOCAL_DEVICE_KEY",-1).length==2&&template.split("ASSIGNED_ADDRESS",-1).length==2);
            byte[] sample=new byte[32];Arrays.fill(sample,(byte)1);
            ProfileValidator.validate(template.replace("LOCAL_DEVICE_KEY",Base64.getEncoder().encodeToString(sample)).replace("ASSIGNED_ADDRESS","10.83.0.2/32"),Transport.AWG);
            awgProfiles.put(country,template);
        }
        require(profiles.size()==2);return new ControlFriendsCatalog(sequence,profiles,awgProfiles);
    }
}
