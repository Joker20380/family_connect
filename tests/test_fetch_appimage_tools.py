import hashlib
import io
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from scripts.fetch_appimage_tools import ASSETS, Asset, DownloadError, fetch, open_response


BINARY = b'\x7fELF' + b'synthetic-not-executable' * 10
ASSET = Asset('test-tool', 'AppImage/appimagetool', 715388534, hashlib.sha256(BINARY).hexdigest(), len(BINARY), True)
CDN = 'https://release-assets.githubusercontent.com/synthetic?signature=DO-NOT-LOG'


class Response(io.BytesIO):
    def __init__(self, status=200, body=BINARY, headers=None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}


def test_redirect_auth_is_api_only_and_logs_are_safe(tmp_path):
    requests, logs = [], []
    def transport(url, headers, timeout):
        requests.append((url, headers))
        assert 0 < timeout <= 10
        return Response(302, headers={'Location': CDN}) if len(requests) == 1 else Response()
    fetch(ASSET, tmp_path, token='DO-NOT-LOG-TOKEN', transport=transport, log=logs.append)
    assert requests[0][1]['Authorization'] == 'Bearer DO-NOT-LOG-TOKEN'
    assert 'Authorization' not in requests[1][1]
    assert 'DO-NOT-LOG' not in ''.join(logs)
    assert '"stage": "api"' in ''.join(logs) and '"stage": "asset"' in ''.join(logs)
    assert (tmp_path / ASSET.name).read_bytes() == BINARY
    assert os.access(tmp_path / ASSET.name, os.X_OK)
    fetch(ASSET, tmp_path, transport=lambda *_: pytest.fail('verified cache must not download'))
    assert not list(tmp_path.glob('.*'))


@pytest.mark.parametrize('response,reason', [
    (lambda: Response(403), 'api HTTP 403'),
    (lambda: Response(404), 'api HTTP 404'),
    (lambda: Response(body=b'<html>failure</html>', headers={'Content-Type': 'text/html'}), 'non-binary'),
    (lambda: Response(body=b'<html>failure</html>'), 'truncated'),
    (lambda: Response(body=b'\x7fELF' + b'x' * (len(BINARY) - 4)), 'digest mismatch'),
    (lambda: Response(body=b'x' * len(BINARY)), 'ELF/digest'),
    (lambda: Response(body=BINARY[:-1], headers={'Content-Length': str(len(BINARY))}), 'truncated'),
    (lambda: Response(body=BINARY + b'x'), 'oversized'),
    (lambda: Response(headers={'Content-Length': '10000000000'}), 'content length'),
    (lambda: Response(302, headers={'Location': 'https://evil.example/tool?secret=hidden'}), 'unapproved'),
    (lambda: Response(302, headers={'Location': 'http://release-assets.githubusercontent.com/tool'}), 'unapproved'),
    (lambda: Response(302, headers={'Location': CDN}), 'redirect limit'),
])
def test_rejected_download_and_corrupt_executable_cache_leave_no_tool(tmp_path, response, reason):
    target = tmp_path / ASSET.name
    target.write_bytes(b'corrupt executable cache')
    target.chmod(0o755)
    with pytest.raises(DownloadError, match=reason):
        fetch(ASSET, tmp_path, transport=lambda *_: response(), sleep=lambda _: None)
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('failure', ['rate-limit', 'server', 'timeout'])
def test_classified_failures_retry_with_bounds(tmp_path, failure):
    calls, delays = [], []
    def transport(*args):
        calls.append(args)
        if len(calls) == 3:
            return Response()
        if failure == 'timeout':
            raise TimeoutError('https://secret-query must not be logged')
        return Response(503) if failure == 'server' else Response(403, headers={'X-RateLimit-Remaining': '0', 'Retry-After': '9999'})
    logs = []
    fetch(ASSET, tmp_path, transport=transport, sleep=delays.append, log=logs.append)
    assert len(calls) == 3 and len(delays) == 2 and max(delays) <= 30
    assert 'secret-query' not in ''.join(logs)


def test_cdn_error_is_distinguished_and_generic_403_is_not_retried(tmp_path):
    calls, logs = [], []
    def transport(*args):
        calls.append(args)
        return Response(302, headers={'Location': CDN}) if len(calls) == 1 else Response(403)
    with pytest.raises(DownloadError, match='asset HTTP 403'):
        fetch(ASSET, tmp_path, transport=transport, log=logs.append)
    assert len(calls) == 2
    assert 'DO-NOT-LOG' not in ''.join(logs)


def test_deadline_and_attempt_limit(tmp_path):
    ticks = iter(range(100))
    with pytest.raises(DownloadError, match='deadline'):
        fetch(ASSET, tmp_path, transport=lambda *_: Response(), budget=1,
              clock=lambda: next(ticks), sleep=lambda _: None)
    assert list(tmp_path.iterdir()) == []


def test_hash_rechecked_for_same_size_cache_and_symlink_not_followed(tmp_path):
    outside = tmp_path / 'outside'
    outside.write_bytes(BINARY)
    outside.chmod(0o640)
    target = tmp_path / ASSET.name
    target.symlink_to(outside)
    fetch(ASSET, tmp_path, transport=lambda *_: Response())
    assert not target.is_symlink() and outside.stat().st_mode & 0o777 == 0o640
    target.write_bytes(b'\x7fELF' + b'x' * (len(BINARY) - 4))
    with pytest.raises(DownloadError):
        fetch(ASSET, tmp_path, transport=lambda *_: Response(404))
    assert not target.exists()


def test_real_http_redirect_and_truncated_transfer(tmp_path):
    observed = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            observed.append(self.headers.get('Authorization'))
            if self.path == '/api':
                self.send_response(302)
                self.send_header('Location', CDN)
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header('Content-Length', str(len(BINARY)))
                self.end_headers()
                self.wfile.write(BINARY[:10])
                self.wfile.flush()
                self.connection.shutdown(socket.SHUT_WR)
        def log_message(self, *args):
            pass
    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            def transport(url, headers, timeout):
                suffix = '/api' if url == ASSET.url else '/asset'
                return open_response(f'http://127.0.0.1:{server.server_port}{suffix}', headers, timeout)
            with pytest.raises(DownloadError, match='truncated'):
                fetch(ASSET, tmp_path, token='synthetic', transport=transport, sleep=lambda _: None)
        finally:
            server.shutdown()
            thread.join(3)
    assert observed == ['Bearer synthetic', None] * 3
    assert list(tmp_path.iterdir()) == []


def test_pins_are_unchanged():
    assert [(asset.asset_id, asset.sha256) for asset in ASSETS] == [
        (715388534, 'e8c1169c4af66c3184d7ee110713d4be04befe671fa358e2c1591ee840553b03'),
        (657374641, '617aa77314d57c8b8e4fae9c3f0b35af7b30d5529cb69e98f64f92510ed98a46'),
    ]
