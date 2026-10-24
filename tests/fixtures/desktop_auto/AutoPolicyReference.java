package com.familyconnect.app;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class AutoPolicyReference implements ConnectivityOrchestrator.Host {
    long time;
    boolean guard, offline, deadlines, cancelOpen, closeFailure;
    int releases;
    List<String> configured = Arrays.asList("awg", "tcp");
    List<String> attempts = new ArrayList<>(), remembered = new ArrayList<>();
    Map<String, ConnectivityOrchestrator.Rejected> failures = new HashMap<>();
    String active;
    ConnectivityOrchestrator.Failure configurationFailure;
    final ConnectivityOrchestrator core = new ConnectivityOrchestrator(this);
    public long now() { return time; }
    public boolean networkAvailable() { return !offline; }
    public List<String> configure(List<String> ignored, long deadline) throws Exception {
        guard = true;
        if (configurationFailure != null) throw new ConnectivityOrchestrator.Rejected(configurationFailure);
        return configured;
    }
    public void pause(long millis) { time += millis; }
    public void open(String candidate, long deadline) throws Exception {
        if (!guard || active != null) throw new IllegalStateException("guard or concurrent path");
        active = candidate;
        attempts.add(candidate);
        if (cancelOpen) core.interrupt(ConnectivityOrchestrator.Failure.CANCELLED);
        if (deadlines) time = deadline;
        if (failures.containsKey(candidate)) throw failures.get(candidate);
    }
    public void closeCandidate() {
        if (closeFailure && active != null) throw new IllegalStateException("synthetic cleanup failure");
        active = null;
    }
    public void release() { releases++; guard = false; }
    public void remember(String candidate) { remembered.add(candidate); }
    public void event(ConnectivityOrchestrator.Event event) {}
    void fail(String candidate, ConnectivityOrchestrator.Failure reason) {
        failures.put(candidate, new ConnectivityOrchestrator.Rejected(reason));
    }
    static String text(Object value) { return value == null ? "" : value.toString(); }
    void scenario(String name) {
        ConnectivityOrchestrator.Failure network = ConnectivityOrchestrator.Failure.NETWORK;
        if (name.equals("normal-fallback") || name.equals("mesh-fallback") || name.equals("cleanup")) fail("awg", network);
        if (name.equals("mesh-fallback")) fail("tcp", network);
        if (name.equals("auth")) fail("awg", ConnectivityOrchestrator.Failure.AUTH);
        if (name.equals("configuration")) fail("awg", ConnectivityOrchestrator.Failure.CONFIGURATION);
        if (name.equals("internal")) fail("awg", ConnectivityOrchestrator.Failure.INTERNAL);
        if (name.equals("configure-denied")) configurationFailure = ConnectivityOrchestrator.Failure.AUTH;
        if (name.equals("mesh-only") || name.startsWith("bootstrap-") || name.equals("cancel-wait")) configured = new ArrayList<>();
        if (name.startsWith("bootstrap-")) failures.put("restricted", new ConnectivityOrchestrator.Rejected(
            ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE, name.equals("bootstrap-temporary")));
        if (name.equals("cancel-wait")) fail("restricted", network);
        offline = name.equals("offline");
        deadlines = name.equals("deadlines");
        cancelOpen = name.equals("cancel-open");
        closeFailure = name.equals("cleanup");
        core.connect(configured, "awg", null);
        if (name.equals("bootstrap-temporary")) {
            for (long delay : new long[]{30000, 60000, 300000}) { time += delay; core.retryIfDue(); }
        }
        if (name.equals("cancel-wait")) { core.interrupt(ConnectivityOrchestrator.Failure.CANCELLED); time += 120000; core.retryIfDue(); }
        if (name.equals("restoration")) { fail("awg", network); core.lost(network); core.lost(network); time += 30000; core.retryIfDue(); }
        if (name.equals("stable")) { core.lost(network); core.trafficHealthy(true); time += 120000; core.trafficHealthy(true); core.lost(network); }
        for (ConnectivityOrchestrator.Event event : core.events()) {
            System.out.println("AUTO_EVENT|" + name + "|" + event.name + "|" + text(event.candidate) + "|" + text(event.failure) + "|" + event.state + "|" + event.elapsedMs);
        }
        System.out.println("AUTO_STATE|" + name + "|" + core.state() + "|" + text(core.selected()) + "|" +
            String.join(",", attempts) + "|" + String.join(",", remembered) + "|" + releases + "|" + guard + "|" + time);
    }
    public static void main(String[] args) {
        for (String name : new String[]{"normal", "normal-fallback", "mesh-fallback", "auth", "configuration", "internal",
            "offline", "mesh-only", "bootstrap-permanent", "bootstrap-temporary", "deadlines", "cancel-open", "cancel-wait",
            "restoration", "stable", "cleanup", "configure-denied"}) new AutoPolicyReference().scenario(name);
    }
}
