import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fc_control_plane.settings')

def main(argv=None):
    from control.capture_gate import Busy, GateError
    from fc_control_plane.capture import configured_gate, operation
    from django.core.management import execute_from_command_line
    arguments = sys.argv if argv is None else argv
    try:
        if configured_gate().directory is not None and len(arguments) > 1 and arguments[1] == 'runserver':
            raise GateError('CAPTURE_RUNSERVER_UNSUPPORTED')
        with operation():
            try:
                execute_from_command_line(arguments)
            except SystemExit as error:
                if error.code not in (None, 0):
                    raise
        return 0
    except Busy:
        print('CAPTURE_BUSY', file=sys.stderr)
        return 75
    except GateError:
        print('CAPTURE_UNAVAILABLE', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
