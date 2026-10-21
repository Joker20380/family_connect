import json


def complete_records(value):
    if isinstance(value,str):value=value.encode()
    return [json.loads(line) for line in value.splitlines(keepends=True) if line.endswith(b'\n') and line.strip()]


if __name__=='__main__':
    assert complete_records(b'{"ok":1}\n{"unfinished":')==[{'ok':1}]
    assert complete_records(b'{"ok":1}\n{"unicode":"\xd0')==[{'ok':1}]
    assert complete_records(b'{"ok":1}\n{"finished":2}\n')==[{'ok':1},{'finished':2}]
    try:complete_records(b'{bad}\n')
    except json.JSONDecodeError:pass
    else:raise AssertionError('complete corrupt line was hidden')
    print('complete-line parser PASS; incomplete tail waits, corrupt full line fails')
