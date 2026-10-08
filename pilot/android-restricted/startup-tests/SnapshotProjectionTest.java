import java.lang.reflect.Method;
import org.json.JSONArray;
import org.json.JSONObject;

public final class SnapshotProjectionTest {
    public static void main(String[] arguments) throws Exception {
        Method project = Class.forName("com.familyconnect.bootstraplocalize.BootstrapSnapshot").getDeclaredMethod("safe", JSONObject.class);
        project.setAccessible(true);
        JSONObject input = new JSONObject().put("device_support_id", "PRIVATE_ID").put("private_key", "PRIVATE_KEY");
        JSONObject event = new JSONObject().put("timestamp", 1791452205720L).put("component", "SESSION").put("reason_code", "STARTUP_FAILED").put("connection_id", "PRIVATE_ID").put("event", "cleanup_completed");
        input.put("events", new JSONArray().put(event));
        input.put("counters", new JSONObject().put("protect_denied", 0).put("url", "https://private"));
        input.put("restricted_history", new JSONArray().put(new JSONObject().put("lifecycle", new JSONObject().put("trace", new JSONArray().put(new JSONObject().put("stage", "FAMILY_TLS").put("reason", "FAMILY_TLS_ERROR").put("payload", "PRIVATE_PAYLOAD"))))));
        JSONObject filtered = (JSONObject)project.invoke(null, input);
        if (filtered.getJSONArray("events").length() != 1 || filtered.getJSONArray("events").getJSONObject(0).getLong("timestamp") != 1791452205720L || !filtered.has("restricted_history") || filtered.getJSONObject("counters").getInt("protect_denied") != 0) throw new AssertionError("Missing safe evidence");
        if (filtered.toString().contains("PRIVATE") || filtered.toString().contains("https://")) throw new AssertionError("Private evidence leaked");
        for (int index = 0; index < 150; index++) input.getJSONArray("events").put(event);
        filtered = (JSONObject)project.invoke(null, input);
        if (filtered.getJSONArray("events").length() != 128) throw new AssertionError("Event bound");
        if (!filtered.getString("events_collection").equals("BOUNDED") || filtered.getInt("events_projection_dropped") != 23) throw new AssertionError("Bound silently treated as absence");
        Method parse = Class.forName("com.familyconnect.bootstraplocalize.BootstrapSnapshot").getDeclaredMethod("project", String.class);
        parse.setAccessible(true);
        JSONObject invalid = (JSONObject)parse.invoke(null, "invalid PRIVATE token");
        if (!invalid.getString("collection").equals("COLLECTION_ERROR") || invalid.toString().contains("PRIVATE")) throw new AssertionError("Parse failure became absence or leaked");
        JSONObject unsupported = (JSONObject)parse.invoke(null, "{\"events\":42}");
        if (!unsupported.getString("events_collection").equals("UNSUPPORTED_FORMAT")) throw new AssertionError("Unknown schema discarded");
        JSONObject absent = (JSONObject)parse.invoke(null, "{}");
        JSONObject empty = (JSONObject)parse.invoke(null, "{\"events\":[]}");
        if (!absent.getString("events_collection").equals("ABSENT_FIELD") || !empty.getString("events_collection").equals("COMPLETE") || !empty.getString("events_history").equals("EVICTION_OR_RESET_UNKNOWN")) throw new AssertionError("Absent/current empty/history conflated");
        System.out.println("PASS: ring object events/history preserved; private fields excluded; events bounded");
    }
}
