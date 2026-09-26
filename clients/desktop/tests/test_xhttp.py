"""Synthetic profiles only; native network acceptance is scripts/check_xhttp.py."""
import json
import pytest
from clients.desktop.profile_config import parse_tcp, tcp_config
from scripts.xhttp_gateway_config import origin_config, nginx_config

PROFILE = dict(type='vless-xhttp-tls-v1', server='192.0.2.1', port=443,
    id='00000000-0000-4000-8000-000000000001', server_name='edge.example.com',
    path='/fc_test_only_path_1234/', mode='packet-up')


def test_client_tls_and_route_are_bound():
    p = parse_tcp(json.dumps(PROFILE))
    c = tcp_config(p, 'fctcp12345678')
    assert len(c['outbounds']) == 1
    outbound = c['outbounds'][0]
    assert outbound['settings']['vnext'][0]['users'] == [{'id': p['id'], 'encryption': 'none'}]
    stream = outbound['streamSettings']
    assert stream['security'] == 'tls' and stream['network'] == 'xhttp'
    assert stream['tlsSettings'] == dict(serverName=p['server_name'], fingerprint='chrome', alpn=['h2'])
    assert stream['xhttpSettings'] == dict(host=p['server_name'], path=p['path'], mode='packet-up')
    assert stream['sockopt']['mark'] == 64630


@pytest.mark.parametrize('field,value', [
    ('path','/'), ('path','/short/'), ('path','/../0123456789abcdef/'),
    ('path','/0123456789abcdef/?x=1'), ('path','/0123456789abcdef%2f/'),
    ('path','/0123456789abcdef/\n'), ('path','/'+'a'*129+'/'),
    ('mode','auto'), ('mode','stream-one'), ('server_name','x.example;return 200'),
    ('server','127.0.0.1'), ('server','0.0.0.0'), ('server','224.0.0.1'),
    ('server','edge.example.com'), ('port',True), ('port',443.0),
    ('id','00000000-0000-0000-0000-000000000000'), ('allowInsecure',True),
    ('extra',{}), ('downloadSettings',{}), ('public_key','a'*43), ('short_id','abcd'),
])
def test_invalid_or_unbounded_options_rejected(field,value):
    with pytest.raises(ValueError): parse_tcp(json.dumps({**PROFILE,field:value}))


def test_duplicate_rejected():
    with pytest.raises(ValueError): parse_tcp(json.dumps(PROFILE)[:-1]+',"mode":"packet-up"}')


def test_origin_not_a_public_plaintext_listener():
    c = origin_config(PROFILE)
    inbound = c['inbounds'][0]
    assert inbound['listen'] == '127.0.0.1'
    assert inbound['settings']['clients'] == [{'id': PROFILE['id']}]
    assert c['routing']['rules'][0]['outboundTag'] == 'blocked'
    nginx = nginx_config(PROFILE)
    assert 'proxy_buffering off;' in nginx and 'access_log off;' in nginx
    assert 'location ^~ '+PROFILE['path'] in nginx
    for port in [True, 0, 80, 65536]:
        with pytest.raises(ValueError): origin_config(PROFILE, port)


def test_renderer_creates_private_files_and_refuses_overwrite(tmp_path):
    import os
    import stat
    import subprocess
    import sys
    source=tmp_path/'profile.json'; source.write_text(json.dumps(PROFILE)); source.chmod(0o600)
    output=tmp_path/'origin'
    command=[sys.executable,'-m','scripts.xhttp_gateway_config','--profile',str(source),'--output',str(output)]
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode==0 and PROFILE['id'] not in result.stdout+result.stderr
    assert stat.S_IMODE(output.stat().st_mode)==0o700
    for name in ('origin.json','nginx.conf'):
        assert stat.S_IMODE((output/name).stat().st_mode)==0o600
    before=(output/'origin.json').read_bytes()
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode!=0 and (output/'origin.json').read_bytes()==before
