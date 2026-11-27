"""Add only the existing HA entry to a closed working vault; no whole-vault replacement."""
import argparse
import hmac
import json
import os
from pathlib import Path
import resource
import re
import subprocess
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
    result = {}
    for group in document.findall('./Root/Group'):
        for nested in group.iter('Group'):
            for entry in nested.findall('Entry'):
                identifier = entry.findtext('UUID')
                key.require(identifier and identifier not in result, 'HA_ENTRY_IDENTITY')
                entry.tail = None
                result[identifier] = ET.tostring(entry)
    return result


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
        key.require(set(before_entries) < set(after_entries) and len(after_entries) == len(before_entries) + 1 and
                    all(after_entries[name] == raw for name, raw in before_entries.items()),
                    'HA_OTHER_ENTRIES_CHANGED')
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
    args = parser.parse_args()
    try:
        print(json.dumps(activate(args.candidate, args.working, args.journal), sort_keys=True))
    except Exception:
        parser.exit(1, 'HA_ACTIVATION_REFUSED; no admission closed; preserve private phase evidence\n')


if __name__ == '__main__':
    main()
