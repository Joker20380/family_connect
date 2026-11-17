"""Fetch fixed official GitHub assets; never execute unverified cache/downloads."""
import argparse
from dataclasses import dataclass
import hashlib
import http.client
import json
import os
from pathlib import Path
import ssl
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


@dataclass(frozen=True)
class Asset:
    name: str
    repository: str
    asset_id: int
    sha256: str
    size: int
    executable: bool = False

    @property
    def url(self):
        return f'https://api.github.com/repos/{self.repository}/releases/assets/{self.asset_id}'


ASSETS = (
    Asset('appimage-tool', 'AppImage/appimagetool', 715388534,
          'e8c1169c4af66c3184d7ee110713d4be04befe671fa358e2c1591ee840553b03', 15133176, True),
    Asset('appimage-runtime', 'AppImage/type2-runtime', 657374641,
          '617aa77314d57c8b8e4fae9c3f0b35af7b30d5529cb69e98f64f92510ed98a46', 944632),
)
CDN_HOSTS = {'release-assets.githubusercontent.com', 'objects.githubusercontent.com',
             'github-releases.githubusercontent.com'}


class DownloadError(Exception):
    def __init__(self, reason, retryable=False, delay=0):
        super().__init__(reason)
        self.retryable = retryable
        self.delay = delay


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        return None


def open_response(url, headers, timeout):
    opener = urllib.request.build_opener(NoRedirect())
    try:
        return opener.open(urllib.request.Request(url, headers=headers), timeout=timeout)
    except urllib.error.HTTPError as response:
        return response


def validated_host(url, initial):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443)
            or parsed.fragment or (url != initial and parsed.hostname not in CDN_HOSTS)):
        raise DownloadError('unapproved redirect origin')
    return parsed.hostname


def verified(path, asset):
    if path.is_symlink() or not path.is_file() or path.stat().st_size != asset.size:
        return False
    with path.open('rb') as source:
        if source.read(4) != b'\x7fELF':
            return False
        source.seek(0)
        return hashlib.file_digest(source, 'sha256').hexdigest() == asset.sha256


def download_attempt(asset, destination, token, emit, *, transport, clock, budget):
    deadline = clock() + budget
    url = asset.url
    for hop in range(6):
        remaining = deadline - clock()
        if remaining <= 0:
            raise DownloadError('attempt deadline', True)
        host = validated_host(url, asset.url)
        stage = 'api' if url == asset.url else 'asset'
        headers = {'Accept': 'application/octet-stream', 'User-Agent': 'FamilyConnect-pinned-build',
                   'X-GitHub-Api-Version': '2022-11-28', 'Cache-Control': 'no-cache'}
        if token and url == asset.url:
            headers['Authorization'] = f'Bearer {token}'
        with transport(url, headers, min(10, remaining)) as response:
            status = response.status
            emit(stage=stage, host=host, status=status, hop=hop)
            if status in (301, 302, 303, 307, 308):
                location = response.headers.get('Location')
                if not location:
                    raise DownloadError('redirect missing location')
                url = urllib.parse.urljoin(url, location)
                validated_host(url, asset.url)
                continue
            if status != 200:
                limited = status == 403 and response.headers.get('X-RateLimit-Remaining') == '0'
                retryable = status in (408, 429, 500, 502, 503, 504) or limited
                retry_after = response.headers.get('Retry-After', '')
                delay = min(30, int(retry_after)) if retry_after.isdecimal() else 0
                raise DownloadError(f'{stage} HTTP {status}' + (' rate-limited' if limited else ''), retryable, delay)
            content_type = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
            if content_type in ('text/html', 'application/json', 'text/plain'):
                raise DownloadError('non-binary response')
            length = response.headers.get('Content-Length')
            if length is not None and length != str(asset.size):
                raise DownloadError('unexpected content length')
            received = 0
            with destination.open('wb') as output:
                while True:
                    if clock() >= deadline:
                        raise DownloadError('attempt deadline', True)
                    chunk = response.read1(65536)
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > asset.size:
                        raise DownloadError('oversized response')
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            if received != asset.size:
                raise DownloadError('truncated response', True)
            if not verified(destination, asset):
                raise DownloadError('ELF/digest mismatch')
            return
    raise DownloadError('redirect limit')


def fetch(asset, directory, *, token='', transport=open_response, sleep=time.sleep,
          clock=time.monotonic, attempts=3, budget=60, log=print):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / asset.name
    events = []
    def emit(**event):
        event.update(asset=asset.asset_id)
        events.append(event)
        log(json.dumps(event, sort_keys=True))
    if destination.exists() or destination.is_symlink():
        if not destination.is_symlink():
            destination.chmod(0o600)
        if verified(destination, asset):
            destination.chmod(0o755 if asset.executable else 0o644)
            emit(result='verified-cache', sha256=asset.sha256, size=asset.size)
            return events
        destination.unlink()
        emit(result='discarded-invalid-cache')
    for attempt in range(1, attempts + 1):
        descriptor, temporary = tempfile.mkstemp(prefix=f'.{asset.name}-', dir=directory)
        os.close(descriptor)
        temporary = Path(temporary)
        try:
            emit(attempt=attempt)
            try:
                download_attempt(asset, temporary, token, emit, transport=transport, clock=clock, budget=budget)
            except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as error:
                reason = error.reason if isinstance(error, urllib.error.URLError) else error
                raise DownloadError('network ' + type(reason).__name__, not isinstance(reason, ssl.SSLCertVerificationError)) from None
            os.replace(temporary, destination)
            destination.chmod(0o755 if asset.executable else 0o644)
            emit(result='verified-download', sha256=asset.sha256, size=asset.size)
            return events
        except DownloadError as error:
            emit(result='rejected', reason=str(error), retryable=error.retryable)
            if not error.retryable or attempt == attempts:
                raise
            sleep(max(error.delay, attempt))
        finally:
            temporary.unlink(missing_ok=True)
    raise DownloadError('attempt limit')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    try:
        for asset in ASSETS:
            fetch(asset, args.directory, token=os.environ.get('APPIMAGE_GITHUB_TOKEN', ''))
    except (DownloadError, OSError, ValueError) as error:
        reason = str(error) if isinstance(error, DownloadError) else type(error).__name__
        parser.exit(1, f'pinned asset unavailable: {reason}\n')


if __name__ == '__main__':
    main()
