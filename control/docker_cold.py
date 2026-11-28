"""Durable cold-generation interlock; not a fleet capture lease or a host installer."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets

from control.capture_native import encoded, require


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def boot():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def publish(path, value):
    raw = encoded(value)
    if path.exists():
        require(path.read_bytes() == raw, 'COLD_RECORD_CHANGED')
        return
    temporary = path.with_name('.' + secrets.token_hex(16))
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            require(path.read_bytes() == raw, 'COLD_RECORD_CHANGED')
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


class Transition:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        self.plan = json.loads((self.root / 'plan.json').read_bytes())
        require(self.plan['schema'] == 1 and re.fullmatch('[a-f0-9]{32}', self.plan['operation']), 'COLD_PLAN')
        require(self.plan['old_root'] != self.plan['new_root'], 'COLD_OLD_RUNTIME_REUSE')
        require(not Path(self.plan['new_root']).is_relative_to(self.plan['old_root']), 'COLD_ROOT_OVERLAP')
        require(not Path(self.plan['old_root']).is_relative_to(self.plan['new_root']), 'COLD_ROOT_OVERLAP')
        self.lock = None

    def __enter__(self):
        self.lock = (self.root / 'controller.lock').open('a+b')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self.lock.close()
            raise
        return self

    def __exit__(self, *args):
        self.lock.close()
        self.lock = None

    def refuse(self, reason):
        path = self.root / 'failed.json'
        if not path.exists():
            publish(path, dict(schema=1, operation=self.plan['operation'], reason=reason, boot=boot()))
        raise ValueError(json.loads(path.read_bytes())['reason'])

    def check_sources(self):
        for name, expected in self.plan['sources'].items():
            require(digest(name) == expected, 'COLD_SOURCE_CHANGED')
        require(digest(self.plan['engine']) == self.plan['engine_sha256'], 'COLD_ENGINE_CHANGED')
        require(digest(self.plan['configuration']) == self.plan['configuration_sha256'], 'COLD_CONFIG_CHANGED')
        config = json.loads(Path(self.plan['configuration']).read_bytes())
        require(config['data-root'] == self.plan['new_root'] and
                config['authorization-plugins'] == [self.plan['plugin']] and
                config.get('live-restore') is False, 'COLD_RUNTIME_BINDING')

    def guard(self):
        if (self.root / 'failed.json').exists():
            self.refuse('COLD_ALREADY_FAILED')
        try:
            self.check_sources()
        except (ValueError, OSError, KeyError) as error:
            self.refuse(str(error) if isinstance(error, ValueError) and str(error).startswith('COLD_') else 'COLD_BINDING_UNREADABLE')
        require(boot() != self.plan['old_boot'], 'COLD_NEW_KERNEL_REQUIRED')
        receipt = dict(schema=1, operation=self.plan['operation'], old_boot=self.plan['old_boot'],
                       boot=boot(), plan_sha256=digest(self.root / 'plan.json'), capture_lease=None)
        path = self.root / 'kernel.json'
        if path.exists() and json.loads(path.read_bytes()) != receipt:
            self.refuse('COLD_NEW_OPERATION_REQUIRED')
        publish(path, receipt)
        return receipt

    def step(self, name, observe, execute):
        require(self.lock is not None, 'COLD_CONTROLLER_LOCK_REQUIRED')
        require(re.fullmatch('[a-z][a-z0-9-]{0,63}', name), 'COLD_STEP_NAME')
        self.guard()
        completed = self.root / (name + '-complete.json')
        intent = self.root / (name + '-intent.json')
        if completed.exists():
            expected = json.loads(completed.read_bytes())
            if observe() != expected['observed']:
                self.refuse('COLD_COMPLETED_EFFECT_CHANGED')
            return expected
        if intent.exists():
            try:
                observed = observe()
            except (ValueError, OSError, KeyError) as error:
                self.refuse(str(error) if isinstance(error, ValueError) else 'COLD_EFFECT_READBACK_FAILED')
            if observed is None:
                self.refuse('COLD_EFFECT_OUTCOME_UNKNOWN')
        else:
            publish(intent, dict(operation=self.plan['operation'], boot=boot(), step=name))
            try:
                execute()
            except BaseException as error:
                try:
                    publish(self.root / (name + '-error.json'), dict(step=name, category=type(error).__name__,
                            outcome='REQUIRES_READ_ONLY_RECONCILIATION'))
                except Exception as failure:
                    error.add_note('COLD_ERROR_RECORD_' + type(failure).__name__)
                raise
            try:
                observed = observe()
            except (ValueError, OSError, KeyError) as error:
                self.refuse(str(error) if isinstance(error, ValueError) else 'COLD_EFFECT_READBACK_FAILED')
            if observed is None:
                self.refuse('COLD_EFFECT_NOT_CONFIRMED')
        receipt = dict(operation=self.plan['operation'], boot=boot(), step=name, observed=observed)
        publish(completed, receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--exec-engine', action='store_true')
    args = parser.parse_args()
    transition = Transition(args.root)
    require(os.geteuid() == 0, 'COLD_ROOT_REQUIRED')
    transition.guard()
    if args.exec_engine:
        plan = transition.plan
        os.execv(plan['engine'], [plan['engine'], '--config-file', plan['configuration']])
    print('COLD_KERNEL_INTERLOCK_PASS_NO_CAPTURE_LEASE')


if __name__ == '__main__':
    main()
