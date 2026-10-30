"""Bounded recovery projection over the exact retained canonical publisher source."""
import hashlib

DIRECTORY_SHA256 = '79ab44cd607742080b53a78d46f8a0732dc201af9db15407aa2092731e110de5'
MEMBERS = ('bootstrap/recovery_linux.go', 'bootstrap/recovery_linux_test.go',
           'cmd/publisher-recovery/main_linux.go', 'cmd/publisher-recovery/binding_linux.go',
           'cmd/publisher-recovery/binding_linux_test.go', 'cmd/publisher-recovery/stage_linux_test.go')


def directory_projection(raw):
    if hashlib.sha256(raw).hexdigest() != DIRECTORY_SHA256:
        raise ValueError('Accepted publisher atomic-store source mismatch')
    before = b'\tdefer lock.Close()\n\tdirectory, err := ParseDirectory(raw, cache.Family, cache.Gateway, now)'
    after = (b'\tdefer lock.Close()\n\treturn cache.store(raw, now)\n}\n\n'
             b'func (cache *Cache) store(raw []byte, now time.Time) error {\n'
             b'\tdirectory, err := ParseDirectory(raw, cache.Family, cache.Gateway, now)')
    if raw.count(before) != 1:
        raise ValueError('Accepted publisher atomic-store projection mismatch')
    return raw.replace(before, after)


def project(source, committed):
    directory = source / 'bootstrap/directory.go'
    updates = {'bootstrap/directory.go': directory_projection(directory.read_bytes())}
    for name in MEMBERS:
        updates[name] = committed('carrier/' + name)
    for name, raw in updates.items():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in updates.items()}
