"""Local acceptance of the invitation page across platform User-Agents; synthetic tokens."""
from pathlib import Path
import base64, hashlib, json, re, subprocess, tempfile, threading
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'artifacts/invitation'
OUTPUT.mkdir(parents=True, exist_ok=True)
source = (ROOT / 'deploy/friends/invite/index.html').read_text()

def digest(tag):
    return base64.b64encode(hashlib.sha256(re.search('<'+tag+'>(.*?)</'+tag+'>', source, re.S).group(1).encode()).digest()).decode()

csp = ("default-src 'none'; script-src 'sha256-" + digest('script') + "'; style-src 'sha256-" + digest('style') + "'; "
       "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")


class Probe(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = {}; self.text = {}; self.stack = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs); iid = d.get('id')
        if iid is not None:
            self.ids[iid] = d; self.text.setdefault(iid, ''); self.stack.append(iid)
        else:
            self.stack.append(None)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs); self.handle_endtag(tag)
    def handle_endtag(self, tag):
        if self.stack: self.stack.pop()
    def handle_data(self, data):
        for iid in self.stack:
            if iid is not None: self.text[iid] = self.text.get(iid, '') + data


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        raw = source.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Security-Policy', csp)
        self.end_headers(); self.wfile.write(raw)


server = HTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'

UAS = {
    'android': 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
    'windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'linux':   'Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0',
    'unknown': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
}


def chromium(name, fragment, ua, screenshot):
    profile = tempfile.mkdtemp(prefix='fc-invite-')
    cmd = ['chromium', '--headless=new', '--no-sandbox', '--disable-gpu', '--window-size=390,1100',
           '--user-agent=' + ua, '--virtual-time-budget=3000']
    cmd += ['--screenshot=' + str(OUTPUT / f'page-{name}.png')] if screenshot else ['--dump-dom']
    cmd += [base + '#' + fragment]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=45)
    return p.stdout.decode('utf-8', 'replace')


def probe(name, fragment, ua):
    dom = chromium(name, fragment, ua, screenshot=False)
    chromium(name, fragment, ua, screenshot=True)
    p = Probe(); p.feed(dom)
    return p


def check(cond, msg):
    if not cond: raise AssertionError(msg)


passed = []
try:
    tok = 'a' * 64
    # Android + valid
    p = probe('android-valid', tok, UAS['android'])
    check(p.text.get('invitation-label') == 'Приглашение готово', 'android label')
    check(p.text.get('primary') == 'Скачать для Android', 'android primary label')
    check(p.ids.get('primary', {}).get('href', '').startswith('/downloads/FamilyConnect-Test-'), 'android apk href')
    check('hidden' not in p.ids.get('open', {}), 'android open visible')
    check(p.ids.get('open-link', {}).get('href') == 'familyconnect://invite/' + tok, 'android open uri')
    check('Windows' in p.text.get('others', '') and 'Linux' in p.text.get('others', '') and 'Android' not in p.text.get('others', ''), 'android others')
    check('hidden' in p.ids.get('all', {}), 'android all hidden')
    check('hidden' in p.ids.get('compat', {}), 'android compat hidden')
    passed.append('android-valid')

    # Windows + valid
    p = probe('windows-valid', tok, UAS['windows'])
    check(p.text.get('primary') == 'Скачать для Windows', 'windows primary label')
    check(p.ids.get('primary', {}).get('href') == '/downloads/FamilyConnect-Setup-0.2.15-pilot-unsigned.exe', 'windows primary 0.2.15 href')
    check('hidden' not in p.ids.get('open', {}), 'windows open visible')
    check(p.ids.get('open-link', {}).get('href') == 'familyconnect://invite/' + tok, 'windows open uri')
    check('Android' in p.text.get('others', '') and 'Linux' in p.text.get('others', '') and 'Windows' not in p.text.get('others', ''), 'windows others')
    check('hidden' not in p.ids.get('compat', {}), 'windows compat visible')
    check(p.ids.get('compat-link', {}).get('href') == '/downloads/FamilyConnect-Setup-0.2.14-pilot-unsigned.exe', 'windows compat 0.2.14 href')
    check('0.2.14' in p.text.get('compat', ''), 'windows compat mentions 0.2.14')
    check('старой Windows 10' in p.text.get('compat', ''), 'windows compat explains old Win10')
    passed.append('windows-valid')

    # Linux + valid: no deep-link/open claim
    p = probe('linux-valid', tok, UAS['linux'])
    check(p.text.get('primary') == 'Скачать для Linux', 'linux primary label')
    check(p.ids.get('primary', {}).get('href') == '/downloads/FamilyConnect-0.2.11-x86_64.AppImage', 'linux AppImage href')
    check('hidden' in p.ids.get('open', {}), 'linux open hidden')
    check('Android' in p.text.get('others', '') and 'Windows' in p.text.get('others', '') and 'Linux' not in p.text.get('others', ''), 'linux others')
    check('hidden' in p.ids.get('compat', {}), 'linux compat hidden')
    passed.append('linux-valid')

    # Unknown + valid: neutral three-button choice
    p = probe('unknown-valid', tok, UAS['unknown'])
    check('hidden' in p.ids.get('primary', {}), 'unknown primary hidden')
    check('hidden' in p.ids.get('open', {}), 'unknown open hidden')
    check('hidden' not in p.ids.get('all', {}), 'unknown all visible')
    all_text = p.text.get('all', '')
    check('Скачать Family Connect' in all_text, 'unknown subhead')
    for name in ('Android', 'Windows', 'Linux'):
        check(name in all_text, 'unknown has ' + name)
    check('0.2.14' in all_text, 'unknown windows compat available')
    check('Совместимость со старой Windows 10' in all_text, 'unknown compat label')
    passed.append('unknown-valid')

    # Linux + missing token
    p = probe('linux-missing', '', UAS['linux'])
    check(p.text.get('invitation-label') == 'Нужна ссылка приглашения', 'missing label')
    check('hidden' in p.ids.get('open', {}), 'missing open hidden')
    check('полную ссылку' in p.text.get('hint', ''), 'missing hint')
    check(p.text.get('primary') == 'Скачать для Linux', 'missing still shows linux download')
    passed.append('linux-missing')

    # Linux + invalid token
    p = probe('linux-invalid', 'BAD', UAS['linux'])
    check(p.text.get('invitation-label') == 'Нужна ссылка приглашения', 'invalid label')
    check('hidden' in p.ids.get('open', {}), 'invalid open hidden')
    check('полную ссылку' in p.text.get('hint', ''), 'invalid hint')
    passed.append('linux-invalid')

    for name in passed:
        print(name, 'passed', flush=True)
    print('OK', len(passed), 'scenarios', flush=True)
finally:
    server.shutdown()
