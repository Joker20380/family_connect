"""XHTTP origin renderer. Private output only; deployment and user allocation are separate."""
import argparse
import json
import os
from pathlib import Path

from clients.desktop.profile_config import parse_tcp


def origin_config(profile, port=18080):
    p = parse_tcp(json.dumps(profile))
    if p['type'] != 'vless-xhttp-tls-v1' or type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError('Invalid XHTTP origin')
    return {
        'log': {'loglevel': 'none'},
        'inbounds': [{'tag': 'xhttp', 'listen': '127.0.0.1', 'port': port,
            'protocol': 'vless', 'settings': {'clients': [{'id': p['id']}], 'decryption': 'none'},
            'streamSettings': {'network': 'xhttp', 'security': 'none',
                'xhttpSettings': {'host': p['server_name'], 'path': p['path'], 'mode': 'packet-up'}}}],
        'outbounds': [{'tag': 'internet', 'protocol': 'freedom'}, {'tag': 'blocked', 'protocol': 'blackhole'}],
        'routing': {'domainStrategy': 'IPIfNonMatch', 'rules': [
            {'type': 'field', 'ip': ['0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
                '169.254.0.0/16', '172.16.0.0/12', '192.168.0.0/16', '224.0.0.0/4', '240.0.0.0/4',
                '::/128', '::1/128', 'fc00::/7', 'fe80::/10', 'ff00::/8', '::ffff:0:0/96'],
                'outboundTag': 'blocked'}]}}


def nginx_config(profile, port=18080):
    p = parse_tcp(json.dumps(profile)); origin_config(p, port)
    # All interpolation values are strictly validated; no user-supplied nginx snippets/paths.
    return f'''server {{
    listen 443 ssl;
    http2 on;
    server_name {p['server_name']};
    ssl_certificate /etc/family-connect/xhttp/tls/fullchain.pem;
    ssl_certificate_key /etc/family-connect/xhttp/tls/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    access_log off;
    location ^~ {p['path']} {{
        proxy_pass http://127.0.0.1:{port};
        proxy_http_version 1.1;
        proxy_set_header Host {p['server_name']};
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        client_max_body_size 2m;
    }}
    location / {{ return 404; }}
}}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=18080)
    args = parser.parse_args()
    with args.profile.open('rb') as source:
        raw = source.read(16385)
    profile = parse_tcp(raw.decode('utf-8'))
    outputs = {'origin.json': json.dumps(origin_config(profile, args.port)),
               'nginx.conf': nginx_config(profile, args.port)}
    args.output.mkdir(mode=0o700)  # Refuse existing directory, including symlinks.
    os.chmod(args.output, 0o700)
    for name, data in outputs.items():
        fd = os.open(args.output/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as output:
            output.write(data+'\n'); output.flush(); os.fsync(output.fileno())
    print('Private XHTTP origin files created; not deployed')


if __name__ == '__main__':
    main()
