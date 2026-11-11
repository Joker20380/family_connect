package com.familyconnect.app;

import android.app.Activity;
import android.app.Notification;
import android.app.NotificationManager;
import android.content.Context;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewGroup;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.runner.lifecycle.ActivityLifecycleMonitorRegistry;
import androidx.test.runner.lifecycle.Stage;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.ByteArrayInputStream;
import java.security.KeyStore;
import java.security.cert.CertificateFactory;
import java.util.Base64;
import java.util.concurrent.TimeUnit;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManagerFactory;
import org.junit.Test;
import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;

public class SupportChatRuntimeTest {
    private Context context;
    private Bundle arguments;

    private JsonObject data(String... pairs) {
        JsonObject result = new JsonObject();
        for (int index = 0; index < pairs.length; index += 2) result.addProperty(pairs[index], pairs[index + 1]);
        return result;
    }

    private void report(JsonObject result) {
        Bundle status = new Bundle();
        status.putString("stream", "SUPPORT_RESULT=" + result + "\n");
        InstrumentationRegistry.getInstrumentation().sendStatus(0, status);
    }

    private JsonArray history(ChatLocalAndroid chat, String address) throws Exception {
        JsonObject request = data("address", address);
        request.addProperty("offset", 0);
        request.addProperty("limit", 50);
        return chat.call("history", request).getAsJsonObject().getAsJsonArray("messages");
    }

    private JsonArray awaitHistory(String address, int expected, boolean outgoingAccepted) throws Exception {
        long until = SystemClock.elapsedRealtime() + 100000;
        while (SystemClock.elapsedRealtime() < until) {
            JsonObject observation = ChatRuntime.WORKER.submit(() -> {
                ChatLocalAndroid chat = ChatRuntime.open(context, false);
                JsonObject value = new JsonObject();
                value.add("messages", history(chat, address));
                value.add("delivery", chat.call("delivery_state", new JsonObject()));
                return value;
            }).get(30, TimeUnit.SECONDS);
            JsonArray messages = observation.getAsJsonArray("messages");
            JsonObject state = observation.getAsJsonObject("delivery");
            boolean accepted = !outgoingAccepted;
            if (messages.size() == expected && outgoingAccepted) {
                String status = messages.get(expected - 1).getAsJsonObject().get("status").getAsString();
                accepted = "relayed".equals(status) || "recipient_stored".equals(status);
            }
            if (messages.size() == expected && accepted && state.get("attempts").getAsInt() > 0
                    && !state.get("running").getAsBoolean() && !state.get("pending").getAsBoolean()
                    && state.get("error").isJsonNull()) return messages;
            SystemClock.sleep(300);
        }
        throw new AssertionError("Ordinary Android worker/mailbox deadline");
    }

    private SSLSocketFactory trustFixture() throws Exception {
        KeyStore roots = KeyStore.getInstance(KeyStore.getDefaultType());
        roots.load(null);
        byte[] certificate = Base64.getDecoder().decode(arguments.getString("ca"));
        roots.setCertificateEntry("isolated-support", CertificateFactory.getInstance("X.509")
                .generateCertificate(new ByteArrayInputStream(certificate)));
        TrustManagerFactory trust = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        trust.init(roots);
        SSLContext tls = SSLContext.getInstance("TLS");
        tls.init(null, trust.getTrustManagers(), null);
        SSLSocketFactory previous = HttpsURLConnection.getDefaultSSLSocketFactory();
        HttpsURLConnection.setDefaultSSLSocketFactory(tls.getSocketFactory());
        return previous;
    }

    private View find(View view, Class<?> type, String description) {
        if (type.isInstance(view) && (description == null || description.contentEquals(
                view.getContentDescription() == null ? "" : view.getContentDescription()))) return view;
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int index = 0; index < group.getChildCount(); index++) {
                View child = find(group.getChildAt(index), type, description);
                if (child != null) return child;
            }
        }
        return null;
    }

    private void notificationAndReply(String address) throws Exception {
        Notification notification = null;
        long notificationDeadline = SystemClock.elapsedRealtime() + 20000;
        while (notification == null && SystemClock.elapsedRealtime() < notificationDeadline) {
            for (var active : context.getSystemService(NotificationManager.class).getActiveNotifications()) {
                if (("chat:" + address).equals(active.getTag())) notification = active.getNotification();
            }
            if (notification == null) SystemClock.sleep(200);
        }
        assertNotNull("Real received message must post a notification", notification);
        assertEquals(context.getString(R.string.chat_official_support), notification.extras.getString(Notification.EXTRA_TITLE));
        assertEquals(Notification.VISIBILITY_PRIVATE, notification.visibility);
        assertNotNull(notification.publicVersion);
        notification.contentIntent.send();
        long until = SystemClock.elapsedRealtime() + 30000;
        boolean[] sent = {false};
        while (!sent[0] && SystemClock.elapsedRealtime() < until) {
            InstrumentationRegistry.getInstrumentation().runOnMainSync(() -> {
                for (Activity activity : ActivityLifecycleMonitorRegistry.getInstance().getActivitiesInStage(Stage.RESUMED)) {
                    if (!(activity instanceof ChatActivity) || !address.equals(ChatRuntime.visiblePeer)) continue;
                    ChatThreadView thread = (ChatThreadView) find(activity.getWindow().getDecorView(), ChatThreadView.class, null);
                    if (thread == null) continue;
                    thread.composer.setText("support synthetic Android reply");
                    View send = find(thread, android.widget.Button.class, activity.getString(R.string.chat_send));
                    assertNotNull(send);
                    assertTrue(send.performClick());
                    sent[0] = true;
                }
            });
            SystemClock.sleep(200);
        }
        assertTrue("Notification must open the addressed conversation and permit a UI reply", sent[0]);
    }

    @Test public void addressedSupport() throws Exception {
        arguments = InstrumentationRegistry.getArguments();
        context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        assumeTrue("Explicit isolated support acceptance required", "true".equals(arguments.getString("fcSupportAcceptance")));
        assertTrue(BuildConfig.DEBUG);
        assertTrue(context.getPackageName().equals("com.familyconnect.app.pilot")
                || context.getPackageName().equals("com.familyconnect.app.orchestrator"));
        assertTrue(Build.HARDWARE.contains("ranchu") || Build.HARDWARE.contains("goldfish"));
        assertEquals("off", ConnectionService.status);
        String phase = arguments.getString("phase");
        SSLSocketFactory previous = trustFixture();
        try {
            JsonObject result = ChatRuntime.WORKER.submit(() -> {
                boolean prepare = "prepare".equals(phase);
                if (prepare) {
                    assertFalse("Fresh isolated package required", ChatLocalAndroid.hasState(context));
                    new FriendsAccessAndroid(context, true).activate(arguments.getString("invitation"));
                }
                ChatLocalAndroid chat = ChatRuntime.open(context, prepare);
                JsonObject enrollment = ChatRuntime.enroll(context, chat);
                assertEquals("active", enrollment.get("status").getAsString());
                assertTrue("Role must arrive from authenticated HTTPS enrollment", enrollment.has("support_configuration"));
                JsonObject value = new JsonObject();
                value.add("profile", chat.call("profile", new JsonObject()));
                value.addProperty("device", enrollment.get("device").getAsString());
                value.add("contacts", chat.call("contacts", new JsonObject()));
                return value;
            }).get(90, TimeUnit.SECONDS);
            ChatRuntime.start(context);
            String address = arguments.getString("address");
            if (!"prepare".equals(phase)) {
                JsonArray messages = awaitHistory(address, Integer.parseInt(arguments.getString("expected")), false);
                if (arguments.containsKey("message")) assertEquals(arguments.getString("message"), messages.get(0).getAsJsonObject().get("id").getAsString());
                result.addProperty("count", messages.size());
            }
            if ("reply".equals(phase)) {
                notificationAndReply(address);
                JsonArray messages = awaitHistory(address, 2, true);
                result.addProperty("reply_id", messages.get(1).getAsJsonObject().get("id").getAsString());
            }
            report(result);
        } finally {
            ChatRuntime.uiVisible = false;
            ChatRuntime.stop();
            ChatRuntime.WORKER.submit(() -> null).get(30, TimeUnit.SECONDS);
            HttpsURLConnection.setDefaultSSLSocketFactory(previous);
        }
    }
}
