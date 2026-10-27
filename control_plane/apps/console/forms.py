from datetime import datetime, timezone
import re

from django import forms

from control.friends import paid_beta, support_ids
from .models import DeviceProjection, OperationRequest, PaymentRecord


class LookupForm(forms.Form):
    selector = forms.CharField(max_length=64, label='Synthetic Support ID or canonical device', strip=True)


class UTCInstant(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(required=False, max_length=20, help_text='UTC seconds only: YYYY-MM-DDTHH:MM:SSZ', **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if not value:
            return None
        try:
            return datetime.fromtimestamp(paid_beta.parse_utc(value), timezone.utc)
        except paid_beta.PaidBetaError:
            raise forms.ValidationError('Use an exact UTC instant ending in Z.') from None


class PaymentForm(forms.Form):
    device = forms.ModelChoiceField(queryset=DeviceProjection.objects.all())
    amount_minor = forms.IntegerField(min_value=1, max_value=100_000_000, label='Synthetic amount (minor units)')
    currency = forms.ChoiceField(choices=PaymentRecord._meta.get_field('currency').choices)
    reference = forms.CharField(min_length=8, max_length=128, help_text='Opaque synthetic reference only; stored only as SHA256. No payer/bank/Support ID.')

    def clean_reference(self):
        value = self.cleaned_data['reference']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', value) or re.search(support_ids.PATTERN, value.upper()):
            raise forms.ValidationError('Use an opaque synthetic reference, without an identity alias.')
        return value


class OperationForm(forms.Form):
    device = forms.ModelChoiceField(queryset=DeviceProjection.objects.all())
    action = forms.ChoiceField(choices=OperationRequest.ACTIONS)
    payment = forms.ModelChoiceField(queryset=PaymentRecord.objects.filter(confirmed_at__isnull=False, operationrequest__isnull=True), required=False)
    period_start = UTCInstant()
    paid_until = UTCInstant()
    grace_until = UTCInstant()
    attest_exact_apk = forms.BooleanField(required=False, label='I verified the exact accepted signed106 handoff (synthetic attestation)')

    def clean(self):
        values = super().clean()
        action = values.get('action')
        if action == 'activate':
            if not all(values.get(name) for name in ('payment', 'period_start', 'paid_until', 'attest_exact_apk')) or values.get('grace_until'):
                raise forms.ValidationError('Activate requires payment, start/end and exact APK attestation only.')
            if values['payment'].device_id != getattr(values.get('device'), 'pk', None):
                raise forms.ValidationError('Payment must belong to this device.')
        elif action == 'grace':
            if not values.get('grace_until') or any(values.get(name) for name in ('payment', 'period_start', 'paid_until', 'attest_exact_apk')):
                raise forms.ValidationError('Grace requires only a grace boundary.')
        elif action in ('expire', 'revoke'):
            if any(values.get(name) for name in ('payment', 'period_start', 'paid_until', 'grace_until', 'attest_exact_apk')):
                raise forms.ValidationError('Expire/revoke must not include payment or period fields.')
        return values


class ConfirmForm(forms.Form):
    confirmed = forms.BooleanField(label='I reviewed this synthetic operation; no real payment or device is involved.')
    token = forms.CharField(widget=forms.HiddenInput, required=False, max_length=1024)
