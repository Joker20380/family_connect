import json
from types import SimpleNamespace
import pytest

from control.friends import transport_policy as policy
from test_subscription_http import runtime, post, proof, read, payment


def test_configuration_guard_does_not_block_own_status_or_subscription(runtime, monkeypatch):
    root = runtime.module.ROOT
    path = root/'transport-enforcement.json'
    path.write_text(json.dumps(dict(schema=1, profile=policy.PROFILE, enabled=True,
        hosts={'192.0.2.1': 'gateway-ru', '192.0.2.2': 'nl-amsterdam-1', '192.0.2.3': 'nl-amsterdam-2'})))
    path.chmod(0o600)
    monkeypatch.setattr(runtime.module, 'configuration_catalog', lambda country, device: ({'fixture': True}, '192.0.2.1'))
    captured = []
    def run(command, *, input, **kwargs):
        record = json.loads(input)
        captured.append(record)
        return SimpleNamespace(returncode=0, stdout=json.dumps(dict(public_key=record['public_key'],
            transport='amneziawg-3.1', address='10.0.0.2/32')).encode())
    monkeypatch.setattr(runtime.module, 'subprocess', SimpleNamespace(run=run))
    assert post(runtime.server, '/friends/configuration/ru', proof(runtime, purpose='ru'))[0] == 200
    assert captured[-1]['paid']['decisions'][0]['state'] == 'noncohort'
    payment(runtime)
    assert post(runtime.server, '/friends/configuration/ru', proof(runtime, purpose='ru'))[0] == 200
    assert captured[-1]['paid']['decisions'][0]['state'] == 'active'
    runtime.now[0] += 3600
    assert post(runtime.server, '/friends/configuration/ru', proof(runtime, purpose='ru'))[0] == 403
    assert len(captured) == 2
    status, raw, headers = read(runtime)
    assert status == 200 and json.loads(raw)['subscription']['effective_state'] == 'expired'
    assert headers['Cache-Control'] == 'no-store'
    status, raw, _ = post(runtime.server, '/friends/device/status', proof(runtime, purpose='status'))
    assert status == 200 and json.loads(raw)['active'] is True
    assert post(runtime.server, '/friends/configuration/ru', proof(runtime, index=1, purpose='ru'))[0] == 200


def test_disabled_is_compatible_but_malformed_opt_in_is_not_silent_allow(runtime, monkeypatch):
    record = dict(device=runtime.devices[0].reference, public_key=runtime.devices[0].wireguard_public_key, tcp_id='unused')
    assert policy.configuration_decision(runtime.access, runtime.module.ROOT, 'gateway-ru', record) == record
    (runtime.module.ROOT/'transport-enforcement.json').write_text('{}')
    (runtime.module.ROOT/'transport-enforcement.json').chmod(0o600)
    with pytest.raises(ValueError, match='INVALID_TRANSPORT_CONFIGURATION'):
        policy.configuration_decision(runtime.access, runtime.module.ROOT, 'gateway-ru', record)


def test_real_https_control_remains_readable_after_paid_expiry(runtime, tmp_path):
    from datetime import datetime, timedelta, timezone
    import http.client
    import ssl
    import threading
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
            .not_valid_after(now+timedelta(hours=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]),False)
            .sign(key, hashes.SHA256()))
    certificate, private = tmp_path/'isolated.crt', tmp_path/'isolated.key'
    certificate.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    private.chmod(0o600)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificate,private)
    trust = ssl.create_default_context(cafile=str(certificate))
    server = runtime.module.ThreadingHTTPServer(('127.0.0.1',0),runtime.module.Handler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever,kwargs=dict(poll_interval=.01))
    thread.start()
    def secure_post(path, body):
        channel = http.client.HTTPSConnection('localhost',server.server_port,context=trust,timeout=4)
        try:
            channel.request('POST',path,json.dumps(body),{'Content-Type':'application/json'})
            response=channel.getresponse()
            return response.status,json.loads(response.read()),response.getheader('Cache-Control')
        finally:
            channel.close()
    try:
        payment(runtime)
        runtime.now[0] += 3600
        for purpose,path in [('subscription','/friends/device/subscription'),('status','/friends/device/status')]:
            device=runtime.devices[0]
            status,challenge,_=secure_post('/friends/challenge',dict(public_identity=device.public_identity,
                wireguard_public_key=device.wireguard_public_key,purpose=purpose,invitation=''))
            assert status==200
            status,body,cache=secure_post(path,device.prove_transport_key(challenge['challenge']))
            assert status==200
            if purpose=='subscription':
                assert body['subscription']['effective_state']=='expired' and cache=='no-store'
            else:
                assert body['active'] is True
        with pytest.raises(ssl.SSLCertVerificationError):
            channel=http.client.HTTPSConnection('127.0.0.1',server.server_port,context=trust,timeout=4)
            try:
                channel.request('POST','/friends/device/status','{}')
            finally:
                channel.close()
    finally:
        server.shutdown();server.server_close();thread.join(2)
        assert not thread.is_alive()
