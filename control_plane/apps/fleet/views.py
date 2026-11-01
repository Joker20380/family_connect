from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django import forms
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import GatewayInstance, DeploymentOperation
from .workflow import create_intent
from .rehearsal import summary


class IntentForm(forms.Form):
    instance = forms.ModelChoiceField(label='Физический экземпляр',queryset=GatewayInstance.objects.all())
    action = forms.ChoiceField(label='Локальная операция',choices=DeploymentOperation._meta.get_field('action').choices)


@login_required
@permission_required('fleet_console.view_gatewayinstance',raise_exception=True)
@require_http_methods(['GET','POST'])
def console(request):
    form=IntentForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        try:
            create_intent(request.user,form.cleaned_data['instance'].pk,form.cleaned_data['action'])
            return redirect('fleet-console')
        except ValidationError as error:
            form.add_error(None,error)
    instances=GatewayInstance.objects.select_related('logical_gateway','desired_bundle','actual_bundle').prefetch_related('health_checks')
    return render(request,'fleet/console.html',dict(instances=instances,operations=DeploymentOperation.objects.all()[:50],form=form,
                                                   rehearsals=summary()))
