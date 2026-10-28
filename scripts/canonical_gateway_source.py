"""Apply the narrow canonical reader delta to the exact accepted gateway source."""
import hashlib

MAIN_SHA256 = 'aff554747a2c1a2f50e68c6a94b5299ede76c18442462e0dd7ae0f4436d34552'
CHAT_SHA256 = 'ead66b41320f2975874d26c7d9baadfba61e89844ceda8ed6dd05bc125399aa7'
TEMPLATE_ROOT = 'deploy/friends/restricted/canonical-profile/'
READER_MEMBERS = ('roombroker/control.go', 'roombroker/canonical_profile_linux.go',
                  'roombroker/canonical_profile_other.go', 'roombroker/canonical_profile_linux_test.go')


def main_projection(raw):
    if hashlib.sha256(raw).hexdigest() != MAIN_SHA256:
        raise ValueError('Accepted gateway startup source mismatch')
    replacements = (
        (b'\tflag.Parse()\n', b'\tchatAPITarget := flag.String("chat-api-target", "", "fixed Friends API endpoint; required with chat-services")\n'
            b'\tflag.Parse()\n\tservices, err := pinnedChatServices(*chatServices, *chatAPITarget)\n'
            b'\tif err != nil {\n\t\treturn err\n\t}\n'),
        (b'Services: pinnedChatServices(*chatServices)', b'Services: services'),
    )
    for before, after in replacements:
        if raw.count(before) != 1:
            raise ValueError('Accepted gateway startup projection mismatch')
        raw = raw.replace(before, after)
    return raw


def project(source, committed):
    main = source / 'cmd/bootstrap-broker/main.go'
    chat = source / 'cmd/bootstrap-broker/chat_services.go'
    projected = main_projection(main.read_bytes())
    if hashlib.sha256(chat.read_bytes()).hexdigest() != CHAT_SHA256:
        raise ValueError('Accepted gateway service source mismatch')
    updates = {'cmd/bootstrap-broker/main.go': projected}
    for name in ('chat_services.go', 'chat_services_test.go'):
        updates['cmd/bootstrap-broker/' + name] = committed(TEMPLATE_ROOT + name)
    for name in READER_MEMBERS:
        updates[name] = committed('carrier/' + name)
    for name, raw in updates.items():
        (source / name).write_bytes(raw)
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in updates.items()}
