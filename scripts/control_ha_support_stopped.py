"""Capture a cleanly stopped accepted support component, preserving unsettled history."""
import argparse
import base64
from contextlib import ExitStack, contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time

from control.capture_gate import Gate, MARKER
from scripts import control_ha_handoff as handoff
from scripts import control_ha_support_replace as replace
from scripts import control_ha_support_resume as resume
from scripts.control_ha_installed_inventory import Reader, stamp
from scripts.control_ha_mailbox_startup import encoded, owned, unique

PURPOSE = 'family-connect/stopped-support-component/v1/not-fleet-capture'
LIMIT = 32 * 1024 * 1024
require = replace.require


def document(path):
    return json.loads(owned(path, os.geteuid()), object_pairs_hook=unique)


def roots(plan, operation=None):
    arguments = plan['new_argv']
    values = {}
    for name, option in (('store', '--store'), ('runtime', '--runtime'), ('key', '--key')):
        require(arguments.count(option) == 1, 'SUPPORT_ARGUMENT_SHAPE')
        values[name] = arguments[arguments.index(option) + 1]
    values.update(gate=plan['gate'], recovery=plan['root'], authority=plan['start_authority'])
    if operation is not None:
        for name in ('operation', 'pending-before', 'reclosure', 'stop-intent', 'stopped'):
            values['stop-' + name] = str(Path(operation) / (name + '.json'))
    paths = [Path(value) for value in values.values()]
    require(all(path.is_absolute() and '..' not in path.parts for path in paths) and
            len(set(paths)) == len(paths) and not any(left in right.parents for left in paths
                for right in paths if left != right), 'SUPPORT_SOURCE_OVERLAP')
    return values


def closed(response, ticket):
    require(response.get('unit_verified') is True and response.get('restart_guard_verified') is True and
            response.get('controller_uid') == os.geteuid(), 'INDEPENDENT_MAILBOX_REQUIRED')
    value = response['observed']
    require(value['ticket'] == ticket and value['capture_permitted'] is False and
            value['fence']['new_link_admission'] == 'CLOSED' and
            value['fence']['in_process_drained'] is True and
            value['fence']['opening_invalidated'] is True and
            value['fence']['accepted_target_work'] == 0, 'STOPPED_MAILBOX_NOT_CLOSED')
    return response


def live_writer_fds(paths, proc=Path('/proc')):
    identities = {(info.st_dev, info.st_ino) for value in paths for info in [Path(value).stat()]}
    inspected = 0
    for process in proc.iterdir():
        if not process.name.isdecimal() or int(process.name) == os.getpid():
            continue
        try:
            descriptors = list((process / 'fd').iterdir())
        except FileNotFoundError:
            continue
        try:
            mappings = (process / 'maps').read_text()
        except FileNotFoundError:
            continue
        require(len(mappings) <= 4 * 1024 * 1024, 'WRITER_MAPS_LIMIT')
        for row in mappings.splitlines():
            fields = row.split(None, 5)
            require(len(fields) >= 5, 'WRITER_MAPS_SHAPE')
            if fields[1][1] == 'w' and fields[1][3] == 's':
                major, minor = fields[3].split(':')
                require((os.makedev(int(major, 16), int(minor, 16)), int(fields[4])) not in identities,
                        'UNMANAGED_WRITABLE_MAPPING')
        for descriptor in descriptors:
            inspected += 1
            require(inspected <= 131072, 'WRITER_CENSUS_LIMIT')
            try:
                information = descriptor.stat()
                if (information.st_dev, information.st_ino) not in identities:
                    continue
                fields = dict(line.split(':', 1) for line in
                              (process / 'fdinfo' / descriptor.name).read_text().splitlines() if ':' in line)
                flags = int(fields['flags'].strip(), 8)
                require(flags & os.O_ACCMODE == os.O_RDONLY, 'UNMANAGED_WRITABLE_DESCRIPTOR')
            except FileNotFoundError:
                continue
    return dict(descriptors_checked=inspected, census_atomic=False, privileged_future_writers_fenced=False)


def collect(source_roots):
    reader, entries = Reader(), {}

    def visit(name, path):
        require(len(entries) < 4096 and re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', name) and
                not any(part in ('.', '..') for part in name.split('/')), 'SUPPORT_ENTRY_BOUNDS')
        with reader.opened(path) as descriptor:
            information = os.fstat(descriptor)
            directory = stat.S_ISDIR(information.st_mode)
            require(directory or stat.S_ISREG(information.st_mode), 'SUPPORT_FILE_TYPE')
            entry = dict(path=str(path), stamp=list(stamp(information)), kind='directory' if directory else 'file')
            if directory:
                children = reader.names(path)
                entry['children'] = children
            else:
                raw = reader.raw(path)
                entry.update(body=base64.b64encode(raw).decode(), sha256=hashlib.sha256(raw).hexdigest())
            entries[name] = entry
        if directory:
            for child in children:
                visit(name + '/' + child, path / child)

    for name, path in sorted(source_roots.items()):
        visit(name, Path(path))
    reader.verify()
    return reader, entries


class StoppedSupport:
    def __init__(self, previous, operation, mailbox):
        self.previous = replace.Replacement(previous)
        self.root, self.mailbox = Path(operation).absolute(), mailbox
        require(not any(path.is_symlink() for path in (self.root, *self.root.parents)), 'STOPPED_OPERATION_PATH')
        require(all(self.root != Path(value) and Path(value) not in self.root.parents
                    and self.root not in Path(value).parents
                    for value in roots(self.previous.plan).values()), 'OUTPUT_INSIDE_SOURCE')
        if not self.root.exists():
            self.root.mkdir(mode=0o700)
        info = self.root.stat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid() and
                stat.S_IMODE(info.st_mode) == 0o700, 'PRIVATE_STOPPED_OPERATION')
        names = {path.name for path in self.root.iterdir()}
        allowed = {'controller.lock', 'operation.json', 'pending-before.json', 'reclosure.json',
                   'stop-intent.json', 'stopped.json', 'complete.json'}
        temporary = {name for name in names if re.fullmatch(r'\.receipt-[A-Za-z0-9_-]{8}', name)}
        for name in temporary:
            info = (self.root / name).lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and
                    stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink in (1, 2),
                    'STOPPED_PARTIAL_RECEIPT')
        require(all(name in allowed or re.fullmatch(r'snapshot-[0-9a-f]{64}\.json', name)
                    for name in names - temporary), 'STOPPED_OPERATION_CONTENTS')
        if names - temporary - {'controller.lock'}:
            operation = document(self.root / 'operation.json')
            require(operation['purpose'] == PURPOSE and operation['predecessor'] == str(self.previous.root) and
                    operation['plan_sha256'] == replace.digest(self.previous.root / 'plan.json'),
                    'STOPPED_OPERATION_BINDING')

    def save(self, name, value):
        path = self.root / (name + '.json')
        if not path.exists():
            replace.admission.write(path, value)
        require(document(path) == value, 'STOPPED_OPERATION_CHANGED')

    def binding(self):
        accepted = document(self.previous.root / 'accepted.json')
        require(accepted['archive_sha256'] == replace.CANDIDATE and
                document(self.previous.root / 'handoff-open.json')['candidate_binding'] == accepted['binding'],
                'ACCEPTED_SUPPORT_REQUIRED')
        return accepted['binding']

    def stop(self, seconds=30):
        require(type(seconds) in (int, float) and 0 < seconds <= 60, 'STOP_WAIT_BOUND')
        with replace.controller_lock(self.root), replace.controller_lock(self.previous.root):
            require(not self.previous.terminal_failure(), 'STOPPED_TERMINAL_FAILURE')
            accepted = self.binding()
            self.save('operation', dict(schema=1, purpose=PURPOSE, predecessor=str(self.previous.root),
                plan_sha256=replace.digest(self.previous.root / 'plan.json'), binding=accepted,
                source_sha256=replace.digest(Path(__file__)), history_settled=False))
            state = self.previous.validate()
            ticket = document(self.previous.root / 'handoff-ticket.json')['ticket']
            observed = self.mailbox.call('observe')
            require(observed['observed']['ticket'] == ticket, 'STOPPED_TICKET_CHANGED')
            if state['MainPID'] != '0':
                if (self.root / 'stop-intent.json').exists():
                    require(replace.admission.binding(int(state['MainPID'])) == accepted and
                            replace.argv(int(state['MainPID'])) == self.previous.plan['new_argv'],
                            'STOPPED_PROCESS_CHANGED')
                else:
                    require(self.previous.verify(state) == accepted, 'STOPPED_PROCESS_CHANGED')
                self.mailbox.call('reclose', dict(action='RECLOSE', ticket=ticket))
                observed = closed(self.mailbox.call('observe'), ticket)
                if not (self.root / 'reclosure.json').exists():
                    replace.admission.write(self.root / 'reclosure.json', observed)
                if not (self.root / 'pending-before.json').exists():
                    history_reader, history = collect({'pending': Path(self.previous.plan['gate']) / 'pending'})
                    history_reader.verify()
                    replace.admission.write(self.root / 'pending-before.json', dict(entries=history,
                        history_settled=False, observed_while_process_alive=True, binding=accepted))
                self.save('stop-intent', dict(binding=accepted, signal=int(signal.SIGTERM),
                                             forced=False, data_restored=False))
                descriptor = os.pidfd_open(accepted['pid'])
                try:
                    require(replace.admission.binding(accepted['pid']) == accepted, 'STOPPED_PROCESS_CHANGED')
                    signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                finally:
                    os.close(descriptor)
                deadline = time.monotonic() + seconds
                while self.previous.manager.state()['MainPID'] != '0':
                    if time.monotonic() >= deadline:
                        return 'WAITING_CLEAN_SUPPORT_EXIT'
                    time.sleep(.05)
            else:
                require((self.root / 'stop-intent.json').is_file(), 'STOPPED_INTENT_REQUIRED')
                closed(observed, ticket)
            proof = resume.absence(self.previous)
            require(proof['reason'] == 'CLEAN_UNIT_EXIT' and proof['graceful_exit_proven'] is True and
                    proof['old_binding'] == accepted, 'CLEAN_SAME_BOOT_EXIT_REQUIRED')
            closed(self.mailbox.call('observe'), ticket)
            self.save('stopped', proof)
            return 'SUPPORT_STOPPED_HISTORY_UNSETTLED'

    @contextmanager
    def boundary(self):
        with replace.controller_lock(self.root), replace.controller_lock(self.previous.root), ExitStack() as stack:
            expected = document(self.root / 'stopped.json')
            before = resume.absence(self.previous)
            require(before == expected and before['reason'] == 'CLEAN_UNIT_EXIT', 'STOPPED_ABSENCE_CHANGED')
            ticket = document(self.previous.root / 'handoff-ticket.json')['ticket']
            remote_before = closed(self.mailbox.call('observe'), ticket)
            plan = self.previous.plan
            with replace.effective_user(plan['uid'], plan['gid']):
                gate = Gate(plan['gate'])
                descriptors = stack.enter_context(gate.opened())
                for name in ('admission.lock', 'operations.lock'):
                    try:
                        fcntl.flock(descriptors[name], fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        raise ValueError('STOPPED_GATE_BUSY') from None
            started = time.time_ns()
            boundary = dict(started_at_ns=started, absence=before, mailbox=remote_before,
                            gate_pins=gate.pins, history_settled=False)
            yield boundary
            require(resume.absence(self.previous) == before, 'STOPPED_ABSENCE_CHANGED')
            closed(self.mailbox.call('observe'), ticket)
            require(replace.pins(Path(plan['gate'])) == plan['gate_pins'], 'STOPPED_GATE_REPLACED')
            boundary['finished_at_ns'] = time.time_ns()

    def readback(self, candidate, digest):
        result = subprocess.run([sys.executable, '-I', '-B', str(Path(__file__).with_name(
            'control_ha_support_snapshot_reader.py')), '--snapshot', str(candidate), '--sha256',
            digest, '--plan', str(self.previous.root / 'plan.json')], capture_output=True, timeout=30)
        require(result.returncode == 0, 'INDEPENDENT_SUPPORT_READER_REFUSED')
        verified = json.loads(result.stdout, object_pairs_hook=unique)
        require(verified['sha256'] == digest and
                verified['result'] == 'SUPPORT_COMPONENT_BYTES_VERIFIED_NOT_FLEET_BACKUP',
                'INDEPENDENT_SUPPORT_READER_BINDING')
        return verified

    def capture(self):
        with self.boundary() as boundary:
            source_roots = roots(self.previous.plan, self.root)
            reader, entries = collect(source_roots)
            writer_evidence = live_writer_fds(reader.observed) if not self.previous.plan['user'] else dict(
                laboratory=True, privileged_future_writers_fenced=False)
            complete = self.root / 'complete.json'
            if complete.exists():
                receipt = document(complete)
                require(Path(receipt['snapshot']).parent == self.root, 'COMPLETE_PATH_SCOPE')
                require(self.readback(receipt['snapshot'], receipt['sha256']) == receipt['reader'],
                        'COMPLETE_READER_CHANGED')
                reader.verify()
                if not self.previous.plan['user']:
                    live_writer_fds(reader.observed)
                return receipt
            pending = {name: entry for name, entry in entries.items() if name.startswith('gate/pending/')}
            require(all(base64.b64decode(entry['body'], validate=True) == MARKER for entry in pending.values()),
                    'UNRECOGNIZED_PENDING_HISTORY')
            require({'gate/pending/' + name for name in self.previous.plan['pending']} <= set(pending),
                    'PENDING_HISTORY_LOST')
            snapshot = dict(schema=1, purpose=PURPOSE, source_roots=source_roots, entries=entries,
                boundary=boundary, writer_evidence=writer_evidence,
                plan_sha256=replace.digest(self.previous.root / 'plan.json'),
                pending_history=sorted(pending), history_settled=False, fleet_capture=False,
                recovery_authorized=False, captured_at_ns=time.time_ns())
            raw = encoded(snapshot)
            require(len(raw) <= LIMIT, 'SUPPORT_COMPONENT_LIMIT')
            candidate = self.root / ('snapshot-' + hashlib.sha256(raw).hexdigest() + '.json')
            if not candidate.exists():
                descriptor = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(descriptor, 'wb') as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                replace.sync(self.root)
            require(candidate.read_bytes() == raw, 'PARTIAL_SUPPORT_COMPONENT')
            verified = self.readback(candidate, hashlib.sha256(raw).hexdigest())
            reader.verify()
            if not self.previous.plan['user']:
                live_writer_fds(reader.observed)
        receipt = dict(result='STOPPED_SUPPORT_COMPONENT_CAPTURED', snapshot=str(candidate),
            sha256=hashlib.sha256(raw).hexdigest(), reader=verified, started_at_ns=boundary['started_at_ns'],
            finished_at_ns=boundary['finished_at_ns'], history_settled=False, fleet_capture=False, recovery_authorized=False)
        replace.admission.write(complete, receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--operation', type=Path, required=True)
    parser.add_argument('--mailbox-channel', type=Path, required=True)
    parser.add_argument('--stop', action='store_true')
    args = parser.parse_args()
    controller = StoppedSupport(args.previous, args.operation, handoff.SSHMailbox(args.mailbox_channel))
    value = dict(result=controller.stop(), capture_permitted=False) if args.stop else controller.capture()
    print(encoded(value).decode())


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        reason = str(error)
        print(encoded(dict(result='STOPPED_SUPPORT_REFUSED', reason=reason if re.fullmatch(
            '[A-Z][A-Z0-9_]{1,80}', reason) else type(error).__name__, capture_permitted=False)).decode())
        raise SystemExit(78) from None
