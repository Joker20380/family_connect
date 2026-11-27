"""Add only the existing HA entry to a closed working vault; no whole-vault replacement."""
import argparse
import base64
import gzip
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import resource
import re
import subprocess
import time
from types import SimpleNamespace
import xml.etree.ElementTree as ET

from scripts import ha_wrapping_key as key
from scripts.signing_key import private_file, vault_archive
from control.capture_fleet import private_write


def record(directory, name, value):
    private_write(directory, name, json.dumps(value, sort_keys=True).encode())


def entries(raw):
    key.require(len(raw) <= 32 * 1024 * 1024 and b'<!DOCTYPE' not in raw, 'HA_VAULT_XML_BOUNDS')
    document = ET.fromstring(raw)
    binaries = {}
    for binary in document.findall('./Meta/Binaries/Binary'):
        identifier = binary.get('ID')
        key.require(identifier is not None and identifier not in binaries, 'HA_BINARY_IDENTITY')
        body = base64.b64decode(binary.text or '', validate=True)
        if binary.get('Compressed') == 'True':
            with gzip.GzipFile(fileobj=io.BytesIO(body)) as stream:
                body = stream.read(32 * 1024 * 1024 + 1)
        key.require(len(body) <= 32 * 1024 * 1024, 'HA_BINARY_BOUNDS')
        binaries[identifier] = hashlib.sha256(body).hexdigest()
    result = {}
    for group in document.findall('./Root/Group'):
        for nested in group.iter('Group'):
            for entry in nested.findall('Entry'):
                identifier = entry.findtext('UUID')
                key.require(identifier and identifier not in result, 'HA_ENTRY_IDENTITY')
                for value in entry.findall('.//Binary/Value'):
                    reference = value.get('Ref')
                    key.require(reference in binaries, 'HA_BINARY_REFERENCE')
                    value.set('Ref', 'sha256:' + binaries[reference])
                entry.tail = None
                result[identifier] = ET.tostring(entry)
    return result


def preserved(before, after):
    key.require(set(before) < set(after) and len(after) == len(before) + 1 and
                all(after[name] == raw for name, raw in before.items()), 'HA_OTHER_ENTRIES_CHANGED')
    added, = set(after) - set(before)
    entry = ET.fromstring(after[added])
    titles = [item.findtext('Value') for item in entry.findall('String') if item.findtext('Key') == 'Title']
    key.require(titles == [key.ENTRY], 'HA_UNEXPECTED_ENTRY_ADDED')


def reconcile(candidate, working, journal):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    candidate, working, journal = Path(candidate), Path(working), Path(journal)
    key.require(candidate.name == working.name == key.DATABASE, 'HA_DATABASE_SELECTION')
    key.require((journal / 'entry-created.json').is_file() and (journal / 'failed.json').is_file(),
                'HA_RECONCILE_PHASE_REQUIRED')
    key.require(not (journal / 'reconciled.json').exists(), 'HA_RECONCILE_ALREADY_RECORDED')
    dialog = subprocess.run(['/usr/bin/zenity', '--password', '--title=Family Connect — read-only HA reconciliation',
        '--text=Только проверка рабочей Family-Connect.kdbx и сохранённой зашифрованной копии. Повторного добавления записи не будет.'],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=600)
    key.require(dialog.returncode == 0, 'HA_LOCAL_UNLOCK_CANCELLED')
    password = dialog.stdout.rstrip(b'\n')
    dialog = None
    key.require(password and b'\n' not in password and b'\r' not in password, 'HA_LOCAL_UNLOCK_INPUT')
    def export(path):
        descriptor = private_file(path)
        try:
            result = subprocess.run(['/usr/bin/keepassxc-cli', 'export', '-q', f'/proc/self/fd/{descriptor}'],
                input=password + b'\n', stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                pass_fds=(descriptor,), timeout=120)
            key.require(result.returncode == 0, 'HA_RECONCILE_NATIVE_READ_REFUSED')
            return entries(result.stdout)
        finally:
            os.close(descriptor)
    try:
        encrypted = working.read_bytes()
        preserved(export(journal / 'working-before.kdbx'), export(working))
        key.require(hmac.compare_digest(key.load(candidate), key.load(working)), 'HA_EXISTING_KEY_MISMATCH')
        key.require(working.read_bytes() == encrypted, 'HA_VAULT_CHANGED_DURING_RECONCILE')
        result = dict(result='EXISTING_HA_ENTRY_ACTIVATED_REAL_CONSUMER_PASS', reconciliation_read_only=True,
            other_entries_unchanged=True, prior_failure_retained=True, new_key_generated=False,
            whole_vault_replaced=False, capture_started=False, external_custody=False)
        record(journal, 'reconciled.json', result)
        return result
    finally:
        password = None


def activate(candidate, working, journal):
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    candidate, working, journal = Path(candidate), Path(working), Path(journal)
    key.require(candidate.name == working.name == key.DATABASE and candidate != working, 'HA_DATABASE_SELECTION')
    key.require(journal.is_absolute() and not any(path.is_symlink() for path in (journal, *journal.parents)),
                'HA_ACTIVATION_JOURNAL')
    confirmed = subprocess.run(['/usr/bin/zenity', '--question', '--title=Family Connect — активация HA записи',
        '--text=Сохраните и закройте KeePassXC. Будет добавлена только существующая HA custody encryption '
               'из кандидата; остальные записи рабочей базы сохраняются. Целиком база не заменяется. '
               'Не открывайте KeePassXC до завершения. Admission остаётся открыт.',
        '--ok-label=Сохранено и закрыто', '--cancel-label=Отложить'],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    key.require(confirmed.returncode == 0, 'HA_ACTIVATION_NOT_CONFIRMED')
    running = subprocess.run(['/usr/bin/pgrep', '-u', str(os.getuid()), '-x', 'keepassxc'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    key.require(running.returncode == 1, 'HA_GUI_MUST_BE_CLOSED')
    journal.mkdir(mode=0o700, exist_ok=False)
    descriptor = private_file(working)
    memory = None
    password = payload = expected_key = checked_key = before_entries = after_entries = None
    try:
        encrypted = os.read(descriptor, key.LIMIT + 1)
        key.require(len(encrypted) == os.fstat(descriptor).st_size <= key.LIMIT, 'HA_WORKING_VAULT_BOUNDS')
        backup = os.open(journal / 'working-before.kdbx', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(backup, 'wb') as stream:
            stream.write(encrypted)
            stream.flush()
            os.fsync(stream.fileno())
        payload = vault_archive(SimpleNamespace(vault=candidate, vault_entry=key.ENTRY, vault_password_dialog=True,
            vault_purpose='HA activation — existing candidate entry'))
        expected_key = key.decode(payload)
        dialog = subprocess.run(['/usr/bin/zenity', '--password', '--title=Family Connect — рабочий сейф',
            '--text=Разблокируйте рабочую Family-Connect.kdbx для адресного добавления существующей HA записи.'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=600)
        key.require(dialog.returncode == 0, 'HA_LOCAL_UNLOCK_CANCELLED')
        password = dialog.stdout.rstrip(b'\n')
        dialog = None
        key.require(password and b'\n' not in password and b'\r' not in password, 'HA_LOCAL_UNLOCK_INPUT')

        def cli(*arguments, output=False, descriptors=()):
            result = subprocess.run(['/usr/bin/keepassxc-cli', *arguments], input=password + b'\n',
                stdout=subprocess.PIPE if output else subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                pass_fds=descriptors, timeout=120)
            key.require(result.returncode == 0, 'HA_SELECTIVE_NATIVE_COMMAND_REFUSED')
            return result.stdout

        before_entries = entries(cli('export', '-q', str(working), output=True))
        key.require(working.read_bytes() == encrypted, 'HA_WORKING_VAULT_CHANGED_BEFORE_ADD')
        record(journal, 'intent.json', dict(operation='COPY_EXISTING_HA_ENTRY_ONLY', new_key=False,
            database=key.DATABASE, entry=key.ENTRY, purpose=key.PURPOSE, full_vault_replacement=False))
        cli('add', '-q', str(working), key.ENTRY)
        record(journal, 'entry-created.json', dict(result='EMPTY_HA_ENTRY_CREATED_NOT_ACTIVE'))
        memory = os.memfd_create('fc-ha-existing-attachment', os.MFD_CLOEXEC)
        os.write(memory, payload)
        cli('attachment-import', '-q', str(working), key.ENTRY, key.ATTACHMENT,
            f'/proc/self/fd/{memory}', descriptors=(memory,))
        after_entries = entries(cli('export', '-q', str(working), output=True))
        preserved(before_entries, after_entries)
        checked_key = key.load(working)
        key.require(hmac.compare_digest(checked_key, expected_key), 'HA_EXISTING_KEY_MISMATCH')
        result = dict(result='EXISTING_HA_ENTRY_ACTIVATED_REAL_CONSUMER_PASS', new_key_generated=False,
                      other_entries_unchanged=True, whole_vault_replaced=False, encrypted_prestate_retained=True,
                      capture_started=False, external_custody=False)
        record(journal, 'complete.json', result)
        return result
    except BaseException as error:
        cause = str(error) if re.fullmatch('HA_[A-Z_]{1,96}', str(error)) else type(error).__name__
        record(journal, 'failed.json', dict(result='HA_ACTIVATION_REFUSED', cause=cause,
                                           automatic_retry=False, capture_started=False))
        raise ValueError('HA_ACTIVATION_REFUSED_PRESERVE_ENCRYPTED_PRESTATE_AND_PHASE_RECORDS') from None
    finally:
        os.close(descriptor)
        if memory is not None:
            os.close(memory)
        password = payload = expected_key = checked_key = before_entries = after_entries = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--working', type=Path, required=True)
    parser.add_argument('--journal', type=Path, required=True)
    parser.add_argument('--reconcile', action='store_true')
    args = parser.parse_args()
    try:
        action = reconcile if args.reconcile else activate
        print(json.dumps(action(args.candidate, args.working, args.journal), sort_keys=True))
    except Exception as error:
        cause = str(error) if re.fullmatch('HA_[A-Z_]{1,96}', str(error)) else type(error).__name__
        if args.reconcile and args.journal.is_dir():
            try:
                record(args.journal, 'reconcile-refused-' + str(time.time_ns()) + '.json',
                       dict(result='HA_RECONCILIATION_REFUSED', cause=cause, vault_write=False))
            except Exception:
                pass
        parser.exit(1, 'HA_ACTIVATION_REFUSED: ' + cause + '; no admission closed; preserve private phase evidence\n')


if __name__ == '__main__':
    main()
