package com.familyconnect.app;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public final class FloorRoundtrip {
    static final class Memory implements RestrictedCache.Storage {
        byte[] value;
        public byte[] read() { return value == null ? null : value.clone(); }
        public void write(byte[] raw) { value = raw.clone(); }
    }
    static byte[] encode(JsonObject value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    public static void main(String[] args) throws Exception {
        JsonArray values = ControlJson.parse(Files.readAllBytes(Path.of(args[0]))).getAsJsonArray();
        Memory memory = new Memory();
        RestrictedCache cache = new RestrictedCache(memory, raw -> true);
        cache.accept(encode(values.get(0).getAsJsonObject()));
        cache.accept(encode(values.get(1).getAsJsonObject()));
        boolean rejected = false;
        try { cache.accept(encode(values.get(0).getAsJsonObject())); }
        catch (IllegalArgumentException expected) { rejected = true; }
        if (!rejected) throw new AssertionError("old production accepted");
        cache = new RestrictedCache(memory, raw -> true);
        cache.accept(encode(values.get(2).getAsJsonObject()));
        cache = new RestrictedCache(memory, raw -> true);
        cache.accept(encode(values.get(2).getAsJsonObject()));
        System.out.println("old-return rejected; preserved-floor forward-return and repeated common import accepted");
    }
}
