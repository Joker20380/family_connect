from django.http import HttpResponse

from control.capture_gate import CURRENT
from .capture import configured_gate, operation


class CaptureAdmission:
    sync_capable = True
    async_capable = False

    def __init__(self, get_response):
        self.get_response = get_response
        self.gate = configured_gate()

    def unavailable(self):
        response = HttpResponse('Management temporarily unavailable.', status=503)
        response['Cache-Control'] = 'no-store'
        response['Retry-After'] = '1'
        return response

    def __call__(self, request):
        if self.gate.directory is None:
            return self.get_response(request)
        try:
            with operation() as admitted:
                response = self.get_response(request)
                if response.streaming:
                    admitted.uncertain()
                    response.close()
                    return self.unavailable()
                if response.status_code >= 500:
                    admitted.uncertain()
                return response
        except OSError:
            return self.unavailable()

    def process_exception(self, request, exception):
        admitted = CURRENT.get()
        if admitted is not None:
            admitted.uncertain()


class LocalConsoleHeaders:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store'
        response['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        return response
