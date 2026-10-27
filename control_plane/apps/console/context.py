from .models import OperationSwitch


def operation_controls(request):
    if request.user.is_authenticated and request.user.is_staff:
        return {'operations_stopped': OperationSwitch.objects.filter(pk=1, stopped=True).exists()}
    return {}
