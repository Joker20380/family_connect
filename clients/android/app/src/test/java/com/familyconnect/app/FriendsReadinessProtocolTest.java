package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Base64;
import java.util.ArrayList;
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.bouncycastle.crypto.signers.Ed25519Signer;
import org.junit.Test;
import static org.junit.Assert.*;

public class FriendsReadinessProtocolTest {
    private static class ProductServer implements FriendsReadinessProtocol.Transport {
        final ArrayList<String> paths=new ArrayList<>(),ids=new ArrayList<>();
        final ControlIdentity owner;
        final String challenge=Base64.getEncoder().encodeToString(new byte[32]);
        boolean revoked,nonCanary,invalidSignature,expired,wrongDevice;
        ProductServer(ControlIdentity identity){owner=identity;}
        public JsonObject post(String path,JsonObject body,String requestId)throws Exception{
            paths.add(path);ids.add(requestId);
            assertTrue(requestId.matches("[a-f0-9]{32}"));
            if(revoked||nonCanary)throw new IllegalArgumentException("authorization rejected");
            if(path.endsWith("/challenge")){
                assertEquals(Base64.getEncoder().encodeToString(owner.publicIdentity()),body.get("public_identity").getAsString());
                JsonObject result=new JsonObject();result.addProperty("challenge",challenge);
                result.addProperty("expires_at",System.currentTimeMillis()/1000+(expired?-1:120));
                result.addProperty("audience","family-connect/enrollment/v1");return result;
            }
            assertEquals("/friends/restricted-readiness",path);
            JsonObject unsigned=body.deepCopy();byte[] signature=Base64.getDecoder().decode(unsigned.remove("signature").getAsString());
            if(invalidSignature)signature[0]^=1;
            Ed25519Signer verifier=new Ed25519Signer();verifier.init(false,new Ed25519PublicKeyParameters(Arrays.copyOfRange(owner.publicIdentity(),32,64),0));
            byte[] domain="family-connect/transport-key-binding/v1\0".getBytes(StandardCharsets.US_ASCII),canonical=ControlJson.canonical(unsigned,false);
            verifier.update(domain,0,domain.length);verifier.update(canonical,0,canonical.length);
            if(!verifier.verifySignature(signature))throw new IllegalArgumentException("invalid proof");
            assertEquals(challenge,body.get("challenge").getAsString());
            JsonObject response=new JsonObject();response.addProperty("challenge",challenge);response.addProperty("device",wrongDevice?"wrong":owner.reference());
            response.addProperty("revision",2);response.addProperty("expires_at",System.currentTimeMillis()/1000+600);
            response.addProperty("private_key","secret-sentinel");return response;
        }
    }
    @Test public void actualProductProtocolSignsAndFetchesWithoutOperator()throws Exception{
        try(ControlIdentity identity=ControlIdentity.restore(new byte[96])){
            ProductServer server=new ProductServer(identity);OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
            byte[] response=FriendsReadinessProtocol.fetch(server,identity,receipt);
            assertEquals(Arrays.asList("/friends/restricted-readiness/challenge","/friends/restricted-readiness"),server.paths);
            assertNotEquals(server.ids.get(0),server.ids.get(1));
            assertTrue(receipt.summary().contains("\"authorized\""));
            assertTrue(receipt.summary().contains("\"import_result\":\"not_attempted\""));
            receipt.imported(response);assertTrue(receipt.summary().contains("\"accepted\""));
            assertFalse(receipt.summary().contains("secret"));Arrays.fill(response,(byte)0);
        }
    }
    @Test public void rejectedProofAndMembershipCannotBecomeReadiness()throws Exception{
        for(String failure:Arrays.asList("invalid","revoked","noncanary","expired","wrong-device")){
            try(ControlIdentity identity=ControlIdentity.restore(new byte[96])){
                ProductServer server=new ProductServer(identity);server.invalidSignature=failure.equals("invalid");server.revoked=failure.equals("revoked");server.nonCanary=failure.equals("noncanary");server.expired=failure.equals("expired");server.wrongDevice=failure.equals("wrong-device");
                OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
                try{FriendsReadinessProtocol.fetch(server,identity,receipt);fail();}catch(IllegalArgumentException expected){receipt.failed();}
                assertFalse(receipt.summary().contains("\"authorized\""));assertFalse(receipt.summary().contains("secret"));
            }
        }
    }
    @Test public void appCannotSignFailsClosed()throws Exception{
        ControlIdentity identity=ControlIdentity.restore(new byte[96]);ProductServer server=new ProductServer(identity);identity.close();
        OwnerPrewarmReceipt receipt=new OwnerPrewarmReceipt();
        try{FriendsReadinessProtocol.fetch(server,identity,receipt);fail();}catch(IllegalStateException expected){receipt.failed();}
        assertTrue(server.paths.isEmpty());assertTrue(receipt.summary().contains("\"failed\""));
    }
}
