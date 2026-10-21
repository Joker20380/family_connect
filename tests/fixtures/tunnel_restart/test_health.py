"""Exercise exact VpnHealth logic with Android stubs and only loopback DNS."""

import os
from pathlib import Path
import subprocess

from preserve import ROOT, WORK, digest


def test_health_fixture(tmp_path):
    parent = ROOT / 'state-client-build/beta87-product-fix-20261019/android88-source'
    relative = Path('clients/android/app/src/main/java/com/familyconnect/app/VpnHealth.java')
    source = WORK / 'android-source' / relative
    assert digest(source) == digest(parent / relative)
    text = source.read_text()
    assert text.count('new String[]{"1.1.1.1","9.9.9.9"}') == 1
    assert text.count('InetAddress.getByName(target),53') == 1
    text = text.replace('new String[]{"1.1.1.1","9.9.9.9"}', 'new String[]{"127.0.0.1","127.0.0.1"}').replace(
        'InetAddress.getByName(target),53', 'InetAddress.getByName(target),HealthHarness.port')
    stubs = {
        'android/content/Context.java': 'package android.content; public class Context { final Object manager; public Context(Object value){manager=value;} public <T> T getSystemService(Class<T> type){return type.cast(manager);} }',
        'android/os/SystemClock.java': 'package android.os; public class SystemClock { public static long elapsedRealtime(){return System.nanoTime()/1000000;} }',
        'android/net/Network.java': 'package android.net; public class Network { public void bindSocket(java.net.DatagramSocket socket){ConnectivityManager.bindings.incrementAndGet();} }',
        'android/net/NetworkCapabilities.java': 'package android.net; public class NetworkCapabilities { public static final int TRANSPORT_VPN=4; public boolean hasTransport(int transport){return transport==TRANSPORT_VPN;} }',
        'android/net/LinkAddress.java': 'package android.net; public class LinkAddress { public java.net.InetAddress getAddress(){return java.net.InetAddress.getLoopbackAddress();} }',
        'android/net/LinkProperties.java': 'package android.net; public class LinkProperties { public java.util.List<LinkAddress> getLinkAddresses(){return java.util.List.of(new LinkAddress());} }',
        'android/net/ConnectivityManager.java': 'package android.net; public class ConnectivityManager { public volatile Network current=new Network(); public static final java.util.concurrent.atomic.AtomicInteger bindings=new java.util.concurrent.atomic.AtomicInteger(); public Network[] getAllNetworks(){Network value=current;return value==null?new Network[]{}:new Network[]{value};} public NetworkCapabilities getNetworkCapabilities(Network network){return new NetworkCapabilities();} public LinkProperties getLinkProperties(Network network){return new LinkProperties();} }',
        'com/familyconnect/app/VpnHealth.java': text,
        'com/familyconnect/app/HealthHarness.java': Path(__file__).with_name('HealthHarness.java').read_text(),
    }
    files = []
    for name, value in stubs.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)
        files.append(str(target))
    tools = ROOT / 'state-client-build/field65-export16/diag-source-freeze-1/resume-tools/jdk/bin'
    subprocess.run([str(tools / 'javac'), '-d', str(tmp_path / 'classes'), *files], check=True, capture_output=True, timeout=30)
    result = subprocess.run([str(tools / 'java'), '-cp', str(tmp_path / 'classes'), 'com.familyconnect.app.HealthHarness'], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'PASS_HEALTH_10_SCENARIOS' in result.stdout
