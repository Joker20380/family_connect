"""Bounded SSH binary streaming into inert, receipt-verified staging only."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import queue
import shlex
import subprocess
import threading
import time
import uuid

from scripts.friends_staging_receiver import durable, encoded, hash_file

HOSTS = {'ru': '185.251.89.19', 'nl': '186.246.45.246'}
PYTHON = '/opt/apps/family_connect/friends-access/venv/bin/python'


class TransferFailure(Exception):
    pass


def budgets(size, minimum_rate=262144):
    if not 65536 <= minimum_rate <= 16 * 1024**2:
        raise ValueError('Invalid minimum rate')
    return dict(transfer_seconds=round(5 + 2 * size / minimum_rate, 3), validation_seconds=round(5 + 2 * size / (8 * 1024**2), 3))


def prepare(manifest, role, parent, destination, minimum_rate=262144):
    items = []
    sources = []
    for entry in manifest:
        path = Path(entry['source']).resolve(strict=True)
        if Path(entry['source']).is_symlink() or path.stat().st_size != entry['bytes'] or hash_file(path) != entry['sha256']:
            raise ValueError('Local artifact pin mismatch')
        items.append(dict(artifact_id=entry['artifact_id'], bytes=entry['bytes'], sha256=entry['sha256'], mode=entry.get('mode', 0o600), **budgets(entry['bytes'], minimum_rate)))
        sources.append(path)
    request = dict(version=1, role=role, parent=str(parent), destination=destination, attempt=uuid.uuid4().hex, items=items, commit_seconds=5)
    if len(encoded(request)) > 32768:
        raise ValueError('Oversized manifest')
    return request, sources


def command(role):
    source = Path(__file__).with_name('friends_staging_receiver.py').read_bytes()
    if len(source) > 32768:
        raise ValueError('Receiver source too large')
    loader = 'import base64;exec(compile(base64.b64decode(' + repr(base64.b64encode(source).decode()) + "),'<pinned-staging-receiver>','exec'))"
    return ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'UpdateHostKeys=no', '-o', 'ConnectTimeout=10', '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=2', 'root@' + HOSTS[role], shlex.join([PYTHON, '-I', '-B', '-u', '-c', loader])]


def transfer(request, sources, evidence, transport=None, connect_seconds=15):
    evidence = Path(evidence)
    evidence.mkdir(mode=0o700, parents=True, exist_ok=False)
    started = time.monotonic()
    overall = connect_seconds + 10 + sum(item['transfer_seconds'] + item['validation_seconds'] + request['commit_seconds'] for item in request['items']) + request['commit_seconds']
    if overall > 660:
        raise ValueError('Operation budget exceeded')
    receipt = dict(version=1, role=request['role'], attempt=request['attempt'], state='FAILED', connect_start=time.time(), connect_end=None, final_event=None, timeout_stage=None, exception_class=None, overall_seconds=overall, items=[dict(host_role=request['role'], artifact_id=item['artifact_id'], local_sha256=item['sha256'], expected_bytes=item['bytes'], remote_temp_path_class='inert_parent/unique_quarantine', connect_start=time.time(), connect_end=None, transfer_start=None, transfer_end=None, bytes_transferred=0, remote_sha256_result=False, atomic_promote_result=False, state='FAILED', timeout_stage=None, exception_class=None) for item in request['items']])
    receipt['receiver_sha256'] = hashlib.sha256(Path(__file__).with_name('friends_staging_receiver.py').read_bytes()).hexdigest()
    durable(evidence / 'receipt.json', receipt)
    try:
        process = subprocess.Popen(transport or command(request['role']), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError as error:
        receipt.update(exception_class=type(error).__name__, last_stage='connect', finished=time.time())
        for item in receipt['items']:
            item.update(exception_class=type(error).__name__)
        durable(evidence / 'receipt.json', receipt)
        return receipt
    events = queue.Queue()
    writers = []
    phase = 'connect'
    phase_end = started + connect_seconds
    current = None

    def reader():
        try:
            while line := process.stdout.readline(262145):
                if len(line) > 262144:
                    raise ValueError()
                events.put(json.loads(line))
        except Exception:
            events.put(dict(event='PROTOCOL_ERROR'))
        finally:
            events.put(dict(event='EXIT'))

    def writer(path, remaining):
        try:
            with path.open('rb') as stream:
                while remaining:
                    chunk = stream.read(min(65536, remaining))
                    if not chunk:
                        raise OSError()
                    process.stdin.write(chunk)
                    process.stdin.flush()
                    remaining -= len(chunk)
        except (BrokenPipeError, OSError, ValueError):
            events.put(dict(event='WRITE_FAILED'))

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    try:
        while True:
            remaining = min(phase_end, started + overall) - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            try:
                event = events.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError() from None
            kind = event['event']
            durable(evidence / (str(time.time_ns()) + '.json'), event)
            if kind == 'CONNECTED':
                receipt['connect_end'] = time.time()
                for item in receipt['items']:
                    item['connect_end'] = receipt['connect_end']
                request['connection'] = dict(start=receipt['connect_start'], end=receipt['connect_end'])
                process.stdin.write(encoded(request))
                process.stdin.flush()
                phase = 'inspection'
                phase_end = time.monotonic() + 10 + sum(item['validation_seconds'] for item in request['items'])
            elif kind == 'ITEM':
                index = next(index for index,item in enumerate(request['items']) if item['artifact_id'] == event['artifact_id'])
                current = receipt['items'][index]
                current.update(state='PARTIAL', transfer_start=time.time())
                phase = 'transfer'
                phase_end = time.monotonic() + request['items'][index]['transfer_seconds'] + 2
                worker = threading.Thread(target=writer, args=(sources[index], request['items'][index]['bytes']), daemon=True)
                writers.append(worker)
                worker.start()
            elif kind == 'PROGRESS':
                current['bytes_transferred'] = event['bytes']
            elif kind == 'FSYNCING':
                current['transfer_end'] = time.time()
                phase = 'fsync'
                phase_end = time.monotonic() + request['commit_seconds'] + 2
            elif kind == 'VALIDATING':
                phase = 'validation'
                budget = next(item['validation_seconds'] for item in request['items'] if item['artifact_id'] == event['artifact_id'])
                phase_end = time.monotonic() + budget + 2
            elif kind == 'VERIFIED':
                current['remote_sha256_result'] = True
                phase = 'promotion'
                phase_end = time.monotonic() + request['commit_seconds'] + 2
            elif kind in ('READY', 'INSPECTED'):
                receipt['state'] = 'READY' if kind == 'READY' or event['state'] == 'READY' else 'PARTIAL'
                receipt['final_event'] = event
                if kind == 'READY' or event['state'] == 'READY':
                    for item in receipt['items']:
                        item.update(state='READY', remote_sha256_result=True, atomic_promote_result=True)
                break
            elif kind == 'FAILED':
                receipt.update(final_event=event, timeout_stage=event.get('timeout_stage'), exception_class=event['exception_class'])
                phase = event['stage']
                raise TransferFailure()
            elif kind in ('EXIT', 'WRITE_FAILED', 'PROTOCOL_ERROR'):
                raise TransferFailure()
            else:
                raise TransferFailure()
            durable(evidence / 'receipt.json', receipt)
        process.stdin.close()
        if process.wait(timeout=3) != 0:
            raise TransferFailure()
    except (TimeoutError, TransferFailure, OSError, subprocess.TimeoutExpired) as error:
        receipt.update(state='PARTIAL' if any(item['bytes_transferred'] for item in receipt['items']) else 'FAILED', timeout_stage=receipt['timeout_stage'] or (phase if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)) else None), exception_class=receipt['exception_class'] or type(error).__name__)
        for item in receipt['items']:
            item.update(state=receipt['state'], timeout_stage=receipt['timeout_stage'], exception_class=receipt['exception_class'])
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        for worker in writers:
            worker.join(timeout=1)
        thread.join(timeout=1)
        for stream in (process.stdin, process.stdout):
            try:
                stream.close()
            except OSError:
                pass
        receipt.update(finished=time.time(), elapsed_seconds=round(time.monotonic() - started, 3), last_stage=phase, process_exit=process.returncode)
        durable(evidence / 'receipt.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--role', choices=HOSTS, required=True)
    parser.add_argument('--parent', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--minimum-rate', type=int, default=262144)
    parser.add_argument('--inspect', action='store_true')
    args = parser.parse_args()
    request, sources = prepare(json.loads(args.manifest.read_bytes()), args.role, args.parent, args.destination, args.minimum_rate)
    request['inspect_only'] = args.inspect
    result = transfer(request, sources, args.evidence)
    print(json.dumps(dict(state=result['state'], elapsed_seconds=result['elapsed_seconds'], timeout_stage=result['timeout_stage'], exception_class=result['exception_class'])))
    return 0 if result['state'] == 'READY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
