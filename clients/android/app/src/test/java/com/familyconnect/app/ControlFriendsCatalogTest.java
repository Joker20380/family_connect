package com.familyconnect.app;
import com.google.gson.*;
import java.util.*;
import java.nio.charset.StandardCharsets;
import org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import org.junit.Test;
import static org.junit.Assert.*;

public class ControlFriendsCatalogTest {
    final Ed25519PrivateKeyParameters key=new Ed25519PrivateKeyParameters(new byte[32],0);
    JsonObject payload()throws Exception{
        try(var harness=new ControlTransactionTest.Harness()){
            var verified=harness.journal.verify(ControlTransactionTest.resource("valid-tcp.envelope"),1000);
            JsonObject profile=ControlJson.parse(verified.state().getAsJsonArray("transport_profiles").get(0).getAsJsonObject().get("config").getAsString().getBytes(StandardCharsets.UTF_8)).getAsJsonObject();
            profile.addProperty("id","DEVICE_CREDENTIAL");
            JsonObject value=new JsonObject();value.addProperty("schema",2);value.addProperty("sequence",2);value.addProperty("access","invite-test");JsonArray gateways=new JsonArray();
            for(String country:new String[]{"ru","nl"}){JsonObject item=new JsonObject();item.addProperty("country",country);item.add("tcp",profile.deepCopy());
                String sample=Base64.getEncoder().encodeToString(new byte[]{1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1});
                item.addProperty("awg","[Interface]\nPrivateKey = LOCAL_DEVICE_KEY\nAddress = ASSIGNED_ADDRESS\nDNS = 1.1.1.1\nMTU = 1280\nJc = 4\nJmin = 40\nJmax = 100\nS1 = 16\nS2 = 16\nS3 = 16\nS4 = 16\nH1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\nHeaderProtectionKey = "+sample+"\nContentPaddingAddition = 0-32\n[Peer]\nPublicKey = "+sample+"\nEndpoint = 186.246.45.246:51823\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n");gateways.add(item);}value.add("gateways",gateways);return value;
        }
    }
    byte[] signed(JsonObject value){
        byte[] raw=value.toString().getBytes(StandardCharsets.UTF_8);Ed25519Signer signer=new Ed25519Signer();signer.init(true,key);signer.update(ControlFriendsCatalog.DOMAIN,0,ControlFriendsCatalog.DOMAIN.length);signer.update(raw,0,raw.length);
        JsonObject out=new JsonObject();out.addProperty("payload",Base64.getEncoder().encodeToString(raw));out.addProperty("signature",Base64.getEncoder().encodeToString(signer.generateSignature()));return out.toString().getBytes(StandardCharsets.UTF_8);
    }
    @Test public void acceptsBothCountriesAndRefusesReplayOrTampering()throws Exception{
        byte[] raw=signed(payload());byte[] anchor=key.generatePublicKey().getEncoded();
        assertEquals(2,ControlFriendsCatalog.verify(raw,anchor,2).profiles.size());
        assertThrows(Exception.class,()->ControlFriendsCatalog.verify(raw,anchor,3));
        byte[] wrong=anchor.clone();wrong[0]^=1;assertThrows(Exception.class,()->ControlFriendsCatalog.verify(raw,wrong,0));
        JsonObject envelope=ControlJson.parse(raw).getAsJsonObject();JsonObject modified=payload();modified.addProperty("sequence",3);
        envelope.addProperty("payload",Base64.getEncoder().encodeToString(modified.toString().getBytes(StandardCharsets.UTF_8)));
        assertThrows(Exception.class,()->ControlFriendsCatalog.verify(envelope.toString().getBytes(StandardCharsets.UTF_8),anchor,0));
    }
    @Test public void rejectsDuplicateCountriesUnknownSchemaAndArbitraryXray()throws Exception{
        byte[] anchor=key.generatePublicKey().getEncoded();JsonObject value=payload();value.getAsJsonArray("gateways").get(1).getAsJsonObject().addProperty("country","ru");
        assertThrows(Exception.class,()->ControlFriendsCatalog.verify(signed(value),anchor,0));
        JsonObject unknown=payload();unknown.addProperty("schema",3);assertThrows(Exception.class,()->ControlFriendsCatalog.verify(signed(unknown),anchor,0));
        JsonObject arbitrary=payload();arbitrary.getAsJsonArray("gateways").get(0).getAsJsonObject().getAsJsonObject("tcp").add("outbounds",new JsonArray());
        assertThrows(Exception.class,()->ControlFriendsCatalog.verify(signed(arbitrary),anchor,0));
    }
}
