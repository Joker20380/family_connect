"""Only the disposable Engine fixture delays an already allowed request."""
import time

from control.capture_docker import Admission, main
from control.capture_native import record, require


class DelayedAdmission(Admission):
    def request(self, request):
        result = super().request(request)
        headers = request.get('RequestHeaders') or request.get('RequestHeader') or {}
        if result['Allow'] and any(name.lower() == 'x-fc-native-delay' for name in headers):
            require(self.journal.parent.name.startswith('fc-owner-executor-'), 'DOCKER_LAB_ONLY')
            record(self.journal, 'delay-permitted', dict(allowed=True))
            deadline = time.monotonic() + 8
            while not (self.journal / 'delay-go').exists():
                require(time.monotonic() < deadline, 'DOCKER_LAB_DELAY_TIMEOUT')
                time.sleep(.01)
        return result


if __name__ == '__main__':
    main(DelayedAdmission)
