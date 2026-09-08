"""RU: Отзыв закрывает активную сессию. EN: Revocation closes an active session."""
import json
import subprocess
import time
from pathlib import Path

root = Path.cwd()
artifacts = root / 'artifacts'


def membership(action):
    return subprocess.run(['docker', 'run', '--rm', '--network', 'none',
        '-v', f'{root}/state-v2/control:/state:rw',
        '-v', f'{root}/state-v2/client/cert.der:/client.der:ro',
        '-v', f'{root}/state-v2/trust/ca.der:/ca.der:ro',
        'family-connect-control:auth2', 'python', 'scripts/admin.py', action,
        '--certificate', '/client.der', '--ca', '/ca.der'], check=True, capture_output=True, text=True)


def main():
    artifacts.mkdir(exist_ok=True)
    revoked = False
    try:
        with (artifacts / 'revocation.txt').open('w') as log:
            process = subprocess.Popen(['docker', 'compose', 'run', '--rm', '--no-deps', 'client'],
                                       stdout=log, stderr=log)
            time.sleep(4)
            if process.poll() is not None:
                raise RuntimeError('client ended before revocation')
            response = membership('revoke')
            revoked = True
            started = time.monotonic()
            code = process.wait(timeout=20)
            elapsed = time.monotonic() - started
        if code == 0:
            raise RuntimeError('revoked device completed transfer')
        if 'authorization lease ended' not in (artifacts / 'revocation.txt').read_text():
            raise RuntimeError('client failed for a reason other than revocation')
        result = {'revocation_epoch': json.loads(response.stdout)['epoch'],
                  'closed_within_seconds': elapsed, 'client_exit_code': code}
        (artifacts / 'revocation.json').write_text(json.dumps(result, indent=2)+'\n')
        print('PASS: active session revoked / активная сессия отозвана')
    finally:
        if revoked:
            membership('enroll')  # New epoch; never restore an older signed state.


if __name__ == "__main__":
    main()
