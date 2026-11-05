import json
from pathlib import Path
import sys


def main():
    if len(sys.argv) != 4 or sys.argv[1] != 'show':
        raise SystemExit(1)
    values = json.loads(Path('/run/fc-online-service-state.json').read_bytes())
    for name, value in values[sys.argv[2]].items():
        print(name+'='+value)


if __name__ == '__main__':
    main()
