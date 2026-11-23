"""Three pinned etcd children on loopback with disposable mTLS and synthetic data."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import ssl
import subprocess
import tempfile
import time

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from control.friends import control_shadow, paid_beta
from control.friends.access import Access
from control.friends.control_quorum import QuorumUnavailable, ShadowQuorum, tls_context

ROOT = Path(__file__).resolve().parents[1]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def private_file(path, raw):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as output:
        output.write(raw)


def certificates(root):
    now = datetime.now(timezone.utc)
    authority = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Disposable HA rehearsal CA')])
    ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
          .public_key(authority.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(hours=1))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(authority.public_key()), False)
          .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(authority.public_key()), False)
          .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
              key_encipherment=False, data_encipherment=False, key_agreement=False,
              key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False), True)
          .sign(authority, hashes.SHA256()))
    private_file(root / 'ca.pem', ca.public_bytes(serialization.Encoding.PEM))
    for label in ('client', 'node0', 'node1', 'node2'):
        key = ec.generate_private_key(ec.SECP256R1())
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'rehearsal-' + label)])
        certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(hours=1))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(authority.public_key()), False)
            .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False,
                key_encipherment=False, data_encipherment=False, key_agreement=False,
                key_cert_sign=False, crl_sign=False, encipher_only=False, decipher_only=False), True)
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH]), False)
            .sign(authority, hashes.SHA256()))
        private_file(root / (label + '.pem'), certificate.public_bytes(serialization.Encoding.PEM))
        private_file(root / (label + '.key'), key.private_bytes(serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))


def eventually(action, *, timeout=20):
    deadline = time.monotonic() + timeout
    while True:
        try:
            return action()
        except (QuorumUnavailable, ConnectionError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.2)


class Rehearsal:
    def __init__(self, binary, root):
        self.binary, self.root = Path(binary), Path(root)
        manifest = json.loads((ROOT / 'deploy/control-ha/rehearsal-etcd.json').read_text())
        require(hashlib.sha256(self.binary.read_bytes()).hexdigest() == manifest['binary_sha256'], 'ETCD_PIN_MISMATCH')
        require(not any(parent.is_symlink() for parent in (self.root, *self.root.parents)), 'REHEARSAL_SYMLINK')
        require(self.root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()), 'TEMPORARY_REHEARSAL_ONLY')
        self.root.mkdir(mode=0o700)
        self.processes, self.reservations, self.commands = {}, [], []
        self.manifest = manifest

    def __enter__(self):
        try:
            certificates(self.root)
            for _ in range(6):
                reservation = socket.socket()
                reservation.bind(('127.0.0.1', 0))
                self.reservations.append(reservation)
            urls = ['https://127.0.0.1:' + str(item.getsockname()[1]) for item in self.reservations]
            self.endpoints, peers = urls[:3], urls[3:]
            cluster = ','.join('node' + str(index) + '=' + peer for index, peer in enumerate(peers))
            token = secrets.token_hex(16)
            for index in range(3):
                name = 'node' + str(index)
                self.commands.append([str(self.binary), '--name', name,
                    '--data-dir', str(self.root / (name + '-data')),
                    '--listen-client-urls', self.endpoints[index], '--advertise-client-urls', self.endpoints[index],
                    '--listen-peer-urls', peers[index], '--initial-advertise-peer-urls', peers[index],
                    '--initial-cluster', cluster, '--initial-cluster-token', token,
                    '--initial-cluster-state', 'new', '--client-cert-auth', '--peer-client-cert-auth',
                    '--trusted-ca-file', str(self.root / 'ca.pem'), '--peer-trusted-ca-file', str(self.root / 'ca.pem'),
                    '--cert-file', str(self.root / (name + '.pem')), '--key-file', str(self.root / (name + '.key')),
                    '--peer-cert-file', str(self.root / (name + '.pem')), '--peer-key-file', str(self.root / (name + '.key')),
                    '--log-level', 'warn'])
            for reservation in self.reservations:
                reservation.close()
            for index in range(3):
                self.start(index)
            self.context = tls_context(self.root / 'ca.pem', self.root / 'client.pem', self.root / 'client.key')
            eventually(lambda: self.client().read())
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def start(self, index):
        require(index not in self.processes or self.processes[index].poll() is not None, 'CHILD_ALREADY_RUNNING')
        logfile = self.root / ('node' + str(index) + '.log')
        descriptor = os.open(logfile, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, 'wb') as output:
            self.processes[index] = subprocess.Popen(self.commands[index], stdin=subprocess.DEVNULL,
                stdout=output, stderr=output, env={'PATH': os.defpath, 'HOME': str(self.root)})

    def stop(self, index):
        process = self.processes[index]
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)

    def client(self, first=0, context=None):
        return ShadowQuorum(self.endpoints[first:] + self.endpoints[:first], context or self.context, timeout=3)

    def __exit__(self, *_):
        for reservation in self.reservations:
            reservation.close()
        for process in self.processes.values():
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def run(binary, root):
    with Rehearsal(binary, root) as cluster:
        access = Access(cluster.root / 'synthetic.db')
        access.initialize()
        with paid_beta.connection(access.path, write=True) as database:
            paid_beta.migrate(database)
            database.execute('CREATE TABLE synthetic_payload(value BLOB)')
            database.execute('INSERT INTO synthetic_payload VALUES (?)', (b'synthetic-private-payload',))
        key, observed = secrets.token_bytes(32), int(time.time())
        first = control_shadow.capture(access.path, key, observed_at=observed)
        require(cluster.client().publish(first, key) == 'published', 'INITIAL_PUBLICATION')
        for index in range(3):
            require(eventually(lambda index=index: cluster.client(index).read(first_only=True))[0] == first,
                    'INITIAL_READBACK')
        anonymous = ssl.create_default_context(cafile=cluster.root / 'ca.pem')
        try:
            cluster.client(context=anonymous).read()
        except QuorumUnavailable:
            pass
        else:
            raise ValueError('MTLS_CLIENT_AUTH_NOT_ENFORCED')
        statuses = [cluster.client(index).request('/v3/maintenance/status', {}, first_only=True) for index in range(3)]
        require(len({status['header']['member_id'] for status in statuses}) == 3, 'DISTINCT_MEMBERS_REQUIRED')
        require(len({status['header']['cluster_id'] for status in statuses}) == 1, 'ONE_CLUSTER_REQUIRED')
        leaders = [index for index, status in enumerate(statuses) if status['header']['member_id'] == status['leader']]
        require(len(leaders) == 1, 'ONE_LEADER_REQUIRED')
        leader = leaders[0]
        cluster.stop(leader)
        started = time.monotonic()
        second = control_shadow.capture(access.path, key, observed_at=observed + 1)
        eventually(lambda: cluster.client().publish(second, key))
        failover_seconds = round(time.monotonic() - started, 3)
        require(cluster.client().read()[0] == second, 'MAJORITY_READBACK')
        stopped = next(index for index in range(3) if index != leader)
        cluster.stop(stopped)
        candidate = control_shadow.capture(access.path, key, observed_at=observed + 2)
        for operation in (lambda: cluster.client().read(), lambda: cluster.client().publish(candidate, key)):
            try:
                operation()
            except QuorumUnavailable:
                pass
            else:
                raise ValueError('MINORITY_ACKNOWLEDGED_OPERATION')
        cluster.start(stopped)
        require(eventually(lambda: cluster.client().read())[0] == second, 'CONFIRMED_STATE_LOST')
        cluster.start(leader)
        for index in range(3):
            require(eventually(lambda index=index: cluster.client(index).read(first_only=True))[0] == second,
                    'RECOVERY_DIVERGED')
        _, revision = cluster.client().read()
        require(not cluster.client().replace(candidate, revision - 1), 'STALE_CAS_ACCEPTED')
        receipt = dict(schema=1, result='ISOLATED_SHADOW_QUORUM_PASS', etcd_version=cluster.manifest['version'],
            binary_sha256=cluster.manifest['binary_sha256'], members=3, mtls='PASS', leader_loss='PASS',
            no_quorum_read='REFUSED', no_quorum_publish='REFUSED_BEFORE_WRITE', recovery='PASS',
            stale_cas='REFUSED', failover_seconds=failover_seconds, synthetic_only=True,
            production_writes=0, production_ha='NOT_IMPLEMENTED')
        private_file(cluster.root / 'receipt.json', control_shadow.encode(receipt) + b'\n')
    require(all(process.poll() is not None for process in cluster.processes.values()), 'CHILD_CLEANUP_FAILED')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--etcd', type=Path, required=True)
    parser.add_argument('--workdir', type=Path, required=True)
    arguments = parser.parse_args()
    def terminate(signum, frame):
        raise SystemExit(128 + signum)
    previous = signal.signal(signal.SIGTERM, terminate)
    try:
        print(json.dumps(run(arguments.etcd, arguments.workdir), sort_keys=True))
    except Exception as error:
        print(json.dumps(dict(result='REHEARSAL_FAILED', error_type=type(error).__name__, production_writes=0)))
        raise SystemExit(1) from None
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == '__main__':
    main()
