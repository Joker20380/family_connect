"""Read actual bpftrace LLVM helper sizes, not a textual-format size estimate."""

import argparse
import hashlib
import json
from pathlib import Path
import re


def inspect(text):
    result = {}
    for function in re.split(r'(?=^define )', text, flags=re.MULTILINE)[1:]:
        kind = None
        field = None
        for line in function.splitlines():
            match = re.search(r'(%\S+) = getelementptr %printf_args_t[^,]*,.*i32 0, i32 3$', line)
            if match:
                field = match[1]
                kind = None
            if field:
                match = re.search(r'store i\d+ (\d+), ptr ' + re.escape(field) + ',', line)
                if match:
                    kind = int(match[1])
            match = re.search(r'inttoptr \(i64 130 to ptr\)\(ptr @ringbuf, ptr ([^,]+), i64 (\d+)', line)
            if match and kind is not None and 'runtime_error' not in match[1]:
                size = int(match[2])
                if kind in result and result[kind]['payload'] != size:
                    raise ValueError('inconsistent_compiled_size')
                result[kind] = dict(payload=size, occupied=(size + 15) & ~7)
                kind = None
    required = set(range(1, 20)) | {23, 24, 25, 26, 27, 28}
    if set(result) != required:
        raise ValueError('missing_or_unexpected_compiled_kind')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('llvm', type=Path)
    arguments = parser.parse_args()
    if arguments.llvm.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('layout_file_limit')
    raw = arguments.llvm.read_bytes()
    print(json.dumps(dict(sha256=hashlib.sha256(raw).hexdigest(), sizes=inspect(raw.decode())), indent=2))


if __name__ == '__main__':
    main()
