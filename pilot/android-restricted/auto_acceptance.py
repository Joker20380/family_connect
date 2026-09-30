"""Diagnostic normal exhaustion and strict automatic restricted evidence."""
import base64
import json
import secrets


def normal_profiles():
    private = base64.b64encode(secrets.token_bytes(32)).decode()
    public = base64.b64encode(secrets.token_bytes(32)).decode()
    interface = '[Interface]\nPrivateKey = '+private+'\nAddress = 10.78.0.4/32\nDNS = 1.1.1.1\nMTU = 1280\n'
    peer = '[Peer]\nPublicKey = '+public+'\nEndpoint = 186.246.45.246:18446\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25\n'
    awg = ('Jc = 3\nJmin = 40\nJmax = 80\nS1 = 16\nS2 = 16\nS3 = 16\nS4 = 16\nH1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\n'
           'HeaderProtectionKey = '+base64.b64encode(secrets.token_bytes(32)).decode()+'\n'
           'ContentPaddingAddition = 0-32\nRandomTrailers = true\nDisableCookies = false\n')
    tcp = {'type': 'vless-reality-v1', 'server': '186.246.45.246', 'port': 18445,
           'id': '11111111-2222-4333-8444-555555555555', 'server_name': 'android.test',
           'public_key': base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode(), 'short_id': secrets.token_hex(8)}
    return {'wg': interface+peer, 'awg': interface+awg+peer, 'tcp': json.dumps(tcp)}


def validate_connected(events):
    attempted = [item['candidate'] for item in events if item['event'] == 'candidate_attempted']
    succeeded = [item['candidate'] for item in events if item['event'] == 'candidate_succeeded']
    denied = [item['candidate'] for item in events if item['event'] == 'candidate_failed'
              and item.get('category') == 'TRANSPORT_UNAVAILABLE']
    if attempted != ['awg', 'wg', 'tcp', 'restricted'] or succeeded != ['restricted'] or denied != ['awg', 'wg', 'tcp']:
        raise RuntimeError('automatic normal exhaustion/restricted success absent')
    if len(events) > 128 or events[-1]['state'] != 'CONNECTED' or any(item['state'] == 'RESTORING' for item in events):
        raise RuntimeError('automatic connection flapped or never connected')


def validate_failed(events):
    restore = [item for item in events if item['event'] == 'restoration_attempted']
    if len(restore) != 1 or restore[0]['state'] != 'RESTORING' or events[-1]['state'] != 'FAILED':
        raise RuntimeError('bounded RESTORING/FAILED proof absent')
    if len([item for item in events if item['event'] == 'candidate_attempted']) != 4:
        raise RuntimeError('terminal restricted failure retried')
