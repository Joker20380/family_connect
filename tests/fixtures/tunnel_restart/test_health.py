"""Exercise exact VpnHealth logic with Android stubs and only loopback DNS."""

from pathlib import Path
import subprocess
import shutil
import pytest

from scripts.ci_android_fixture import source as accepted_source


@pytest.mark.parametrize('historical', [True, False])
def test_health_fixture(tmp_path, historical):
    source = accepted_source('health89') if historical else Path(__file__).resolve().parents[3]/'clients/android/app/src/main/java/com/familyconnect/app/VpnHealth.java'
    text = source.read_text()
    assert text.count('new String[]{"1.1.1.1","9.9.9.9"}') == 1
    assert text.count('InetAddress.getByName(target),53') == 1
    text = text.replace('new String[]{"1.1.1.1","9.9.9.9"}', 'new String[]{"127.0.0.1","127.0.0.1"}').replace(
        'InetAddress.getByName(target),53', 'InetAddress.getByName(target),HealthHarness.port')
    stubs = {
        'android/content/Context.java': 'package android.content; public class Context { final Object manager; public Context(Object value){manager=value;} public <T> T getSystemService(Class<T> type){return type.cast(manager);} }',
        'android/os/SystemClock.java': 'package android.os; public class SystemClock { public static long elapsedRealtime(){return System.nanoTime()/1000000;} }',
        'android/util/Base64.java': 'package android.util; public class Base64 { public static final int NO_WRAP=2; public static String encodeToString(byte[] value,int flags){return java.util.Base64.getEncoder().encodeToString(value);} public static byte[] decode(String value,int flags){return java.util.Base64.getDecoder().decode(value);} }',
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
    javac, java = shutil.which('javac'), shutil.which('java')
    assert javac and java, 'Accepted health fixture requires a JDK on PATH'
    subprocess.run([javac, '-d', str(tmp_path / 'classes'), *files], check=True, capture_output=True, timeout=30)
    result = subprocess.run([java, '-cp', str(tmp_path / 'classes'), 'com.familyconnect.app.HealthHarness'], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'PASS_HEALTH_10_SCENARIOS' in result.stdout
