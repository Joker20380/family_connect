package com.familyconnect.app;

import com.google.gson.JsonObject;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public final class ActualDirectoryGate {
    public static void main(String[] args) throws Exception {
        JsonObject template = ControlJson.parse(Files.readAllBytes(Path.of(args[0])))
                .getAsJsonArray().get(0).getAsJsonObject();
        JsonObject production = ControlJson.parse(Files.readAllBytes(Path.of(args[1]))).getAsJsonObject();
        JsonObject canary = ControlJson.parse(Files.readAllBytes(Path.of(args[2]))).getAsJsonObject();
        FloorRoundtrip.Memory memory = new FloorRoundtrip.Memory();
        RestrictedCache cache = new RestrictedCache(memory, raw -> true);
        template.add("directory", production);
        cache.accept(template.toString().getBytes(StandardCharsets.UTF_8));
        template.add("directory", canary);
        cache.accept(template.toString().getBytes(StandardCharsets.UTF_8));
        byte[] retained = memory.read();
        template.add("directory", production);
        boolean rejected = false;
        try { cache.accept(template.toString().getBytes(StandardCharsets.UTF_8)); }
        catch (IllegalArgumentException expected) { rejected = true; }
        if (!rejected || !Arrays.equals(retained, memory.read())) {
            throw new AssertionError("Return gate did not preserve the accepted floor");
        }
        System.out.println("Actual P -> C accepted; actual C -> P rejected; floor preserved. Directory-floor fixture only, not native cryptographic or physical acceptance.");
    }
}
