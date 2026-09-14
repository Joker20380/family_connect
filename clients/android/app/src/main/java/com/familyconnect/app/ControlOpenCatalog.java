package com.familyconnect.app;

import com.google.gson.*;
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import java.nio.charset.StandardCharsets;
import java.util.*;
import static com.familyconnect.app.ControlJson.*;

/** Separate, deliberately public test access. Never accepted by managed config intake. */
final class ControlOpenCatalog {
    static final byte[] DOMAIN="family-connect/open-test/v1\0".getBytes(StandardCharsets.US_ASCII);
    final long sequence;
    final Map<String,String> profiles;
    private ControlOpenCatalog(long sequence,Map<String,String> profiles){this.sequence=sequence;this.profiles=Collections.unmodifiableMap(profiles);}
    static ControlOpenCatalog verify(byte[] raw,byte[] anchor,long floor)throws Exception{
        require(raw.length>0&&raw.length<=16384&&anchor.length==32);
        JsonObject envelope=parse(raw).getAsJsonObject();fields(envelope,"payload signature");
        byte[] payload=ControlProtocol.base64(text(envelope.get("payload")),true);
        byte[] signature=ControlProtocol.base64(text(envelope.get("signature")),true);require(payload.length<=8192&&signature.length==64);
        Ed25519Signer verifier=new Ed25519Signer();verifier.init(false,new Ed25519PublicKeyParameters(anchor,0));
        verifier.update(DOMAIN,0,DOMAIN.length);verifier.update(payload,0,payload.length);require(verifier.verifySignature(signature));
        JsonObject value=parse(payload).getAsJsonObject();fields(value,"schema sequence access gateways");
        require(integer(value.get("schema"),1)==1&&text(value.get("access")).equals("open-test"));
        long sequence=integer(value.get("sequence"),1);require(sequence>=floor);
        Map<String,String> profiles=new LinkedHashMap<>();JsonArray gateways=value.getAsJsonArray("gateways");require(gateways.size()==2);
        for(JsonElement item:gateways){
            JsonObject gateway=item.getAsJsonObject();fields(gateway,"country profile");String country=text(gateway.get("country"));
            require(country.equals("ru")||country.equals("nl"));require(!profiles.containsKey(country));
            profiles.put(country,TcpProfile.validate(gateway.getAsJsonObject("profile").toString()));
        }
        require(profiles.size()==2);return new ControlOpenCatalog(sequence,profiles);
    }
}
