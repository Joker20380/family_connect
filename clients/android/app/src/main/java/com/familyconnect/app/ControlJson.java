package com.familyconnect.app;

import com.google.gson.*;
import com.google.gson.stream.*;
import java.io.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.*;
import java.util.*;

/** Strict UTF-8/JSON reader with recursive duplicate rejection and bounded depth. */
final class ControlJson {
    static void require(boolean ok) { if(!ok) throw new IllegalArgumentException("invalid control data"); }
    static String text(JsonElement value) {
        require(value!=null && value.isJsonPrimitive() && value.getAsJsonPrimitive().isString()); return value.getAsString();
    }
    static long integer(JsonElement value,long minimum) {
        require(value!=null && value.isJsonPrimitive() && value.getAsJsonPrimitive().isNumber());
        String raw=value.getAsString(); require(raw.matches("-?[0-9]+"));
        BigInteger exact=new BigInteger(raw);require(exact.bitLength()<=63);
        long number=exact.longValue();require(number>=minimum);return number;
    }
    static void fields(JsonElement value,String names) {
        require(value!=null && value.isJsonObject());
        require(value.getAsJsonObject().keySet().equals(new HashSet<>(Arrays.asList(names.split(" ")))));
    }
    static JsonElement parse(byte[] raw)throws IOException {
        String s=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        try(JsonReader reader=new JsonReader(new StringReader(s))) {
            reader.setStrictness(Strictness.STRICT); JsonElement value=read(reader,0);
            require(reader.peek()==JsonToken.END_DOCUMENT);return value;
        }
    }
    private static JsonElement read(JsonReader r,int depth)throws IOException {
        require(depth<=64);
        switch(r.peek()) {
            case BEGIN_OBJECT:
                JsonObject object=new JsonObject();r.beginObject();
                while(r.hasNext()){String name=unicode(r.nextName());require(!object.has(name));object.add(name,read(r,depth+1));}
                r.endObject();return object;
            case BEGIN_ARRAY:
                JsonArray array=new JsonArray();r.beginArray();while(r.hasNext())array.add(read(r,depth+1));r.endArray();return array;
            case STRING: return new JsonPrimitive(unicode(r.nextString()));
            case NUMBER:
                // Preserve the token, including exponent/decimal form, for strict integer checks.
                String number=r.nextString();return new JsonPrimitive(new TokenNumber(number));
            case BOOLEAN:return new JsonPrimitive(r.nextBoolean());
            case NULL:r.nextNull();return JsonNull.INSTANCE;
            default:throw new IllegalArgumentException("invalid control JSON");
        }
    }
    private static String unicode(String value) {
        for(int i=0;i<value.length();i++) {
            char c=value.charAt(i);
            if(Character.isHighSurrogate(c)){require(i+1<value.length()&&Character.isLowSurrogate(value.charAt(i+1)));i++;}
            else require(!Character.isLowSurrogate(c));
        }
        return value;
    }
    private static final class TokenNumber extends Number {
        private final String token;TokenNumber(String token){this.token=token;}
        public int intValue(){return new java.math.BigDecimal(token).intValue();}
        public long longValue(){return new java.math.BigDecimal(token).longValue();}
        public float floatValue(){return Float.parseFloat(token);}
        public double doubleValue(){return Double.parseDouble(token);}
        public String toString(){return token;}
    }
    // ACK fields are validated as ASCII before canonical serialization.
    static byte[] canonical(JsonObject body,boolean omitId)throws IOException {
        StringWriter result=new StringWriter();
        try(JsonWriter writer=new JsonWriter(result)) {
            writer.setHtmlSafe(false);writer.beginObject();
            for(String key:new TreeSet<>(body.keySet())) {
                if(omitId && key.equals("ack_id"))continue;writer.name(key);JsonElement value=body.get(key);
                if(value.isJsonNull())writer.nullValue();
                else if(value.isJsonPrimitive() && value.getAsJsonPrimitive().isNumber())writer.value(integer(value,0));
                else writer.value(text(value));
            }
            writer.endObject();
        }
        return result.toString().getBytes(StandardCharsets.UTF_8);
    }
}
