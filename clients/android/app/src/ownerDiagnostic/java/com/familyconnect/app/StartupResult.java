package com.familyconnect.app;

import java.util.Set;
import java.util.Arrays;
import java.util.HashSet;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

final class StartupResult {
    private static final Set<String> STAGES = values("STARTUP", "PROFILE", "DIRECTORY", "SEED_CREATE", "SEED_CONNECT", "SEED_ADMISSION", "SEED_READ", "FAMILY_AUTH", "HELLO_RECEIVE", "REQUEST_SEND", "DESCRIPTOR_RECEIVE", "DESCRIPTOR_VALIDATE", "BYE_SEND", "BYE_RECEIVE", "DEDICATED_CREATE", "DEDICATED_CONNECT", "DEDICATED_AUTH", "DEDICATED_BIND", "DEDICATED_MUX", "CONTROL_REFRESH", "UNKNOWN");
    private static final Set<String> CAUSES = values("NONE", "CANCELLED", "DEADLINE", "CERTIFICATE_TIME_INVALID", "CERTIFICATE_INVALID", "CERTIFICATE_AUTHORITY", "CERTIFICATE_HOSTNAME", "PROVIDER_API", "CARRIER_CLOSED", "EOF", "PROTOCOL_REJECTED", "CREDENTIALS_REJECTED", "DESCRIPTOR_REJECTED", "DESCRIPTOR_EXPIRED", "EXCHANGE_CLOSED", "UNKNOWN");
    private static final Set<String> STATUSES = values("RUNNING", "SUCCEEDED", "FAILED", "CANCELLED");
    final long attempt;
    final String stage, cause, status;
    final boolean complete;
    final String json;

    StartupResult(String raw) {
        if (raw == null || raw.length() > 4096) throw new IllegalArgumentException("Unsupported startup result");
        JsonObject input = JsonParser.parseString(raw).getAsJsonObject();
        if (input.get("schema").getAsInt() != 1 || input.get("attempt").getAsLong() <= 0) throw new IllegalArgumentException("Unsupported startup result");
        attempt = input.get("attempt").getAsLong();
        stage = allowed(STAGES, input.get("stage").getAsString());
        cause = allowed(CAUSES, input.get("cause").getAsString());
        status = input.get("status").getAsString();
        if (!STATUSES.contains(status)) throw new IllegalArgumentException("Unsupported startup status");
        complete = input.get("complete").getAsBoolean();
        JsonObject safe = new JsonObject();
        safe.addProperty("schema",1);safe.addProperty("attempt",attempt);safe.addProperty("stage",stage);safe.addProperty("cause",cause);safe.addProperty("status",status);safe.addProperty("complete",complete);
        for (String field : new String[]{"started_unix_ms", "observed_ms", "completed_ms"}) {
            long value = input.get(field).getAsLong();
            if (value < -1) throw new IllegalArgumentException("Unsupported startup time");
            safe.addProperty(field, value);
        }
        json = safe.toString();
    }

    private static String allowed(Set<String> values, String value) { return values.contains(value) ? value : "UNKNOWN"; }
    private static Set<String> values(String... input) { return new HashSet<>(Arrays.asList(input)); }

    Throwable failure() {
        return "FAILED".equals(status) || "CANCELLED".equals(status) ? new Failure(this) : null;
    }

    static final class Failure extends Exception {
        final StartupResult result;
        Failure(StartupResult value) { super(value.stage + ":" + value.cause); result = value; }
    }
}
