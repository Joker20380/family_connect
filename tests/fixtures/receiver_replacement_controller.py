import os
from pathlib import Path
import signal
import sys

root, phase = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0, str(root))
import controller

original = controller.Replacement.record


def record(self, name, **value):
    original(self, name, **value)
    if name == phase and not (root / 'fault-consumed').exists():
        (root / 'fault-consumed').touch()
        os.kill(os.getpid(), signal.SIGKILL)


controller.Replacement.record = record
sys.argv = [sys.argv[0], '--run', str(root)]
controller.main()
