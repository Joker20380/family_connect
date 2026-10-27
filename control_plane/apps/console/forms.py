from datetime import datetime, timezone
import re

from django import forms
from django.core.exceptions import ValidationError

from control.friends import paid_beta, support_ids
from .models import DeviceProjection, OperationRequest, PaymentRecord


class LookupForm(forms.Form):
    selector = forms.CharField(max_length=64, label='Support ID или идентификатор демо-устройства', strip=True)


class UTCInstant(forms.CharField):
    def __init__(self, **kwargs):
        super().__init__(required=False, max_length=20, help_text='Точное время UTC: ГГГГ-ММ-ДДTЧЧ:ММ:ССZ', **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if not value:
            return None
        try:
            return datetime.fromtimestamp(paid_beta.parse_utc(value), timezone.utc)
        except paid_beta.PaidBetaError:
            raise forms.ValidationError('Введите точное время UTC с окончанием Z.') from None


class PaymentForm(forms.Form):
    device = forms.ModelChoiceField(label='Устройство', queryset=DeviceProjection.objects.all())
    purpose = forms.ChoiceField(label='Назначение', choices=PaymentRecord.Purpose.choices,
        initial=PaymentRecord.Purpose.CUSTOMER_PAYMENT, required=False,
        help_text='Назначение неизменно после создания. Canary — служебная проверка, не оплата и не выручка.')
    amount_minor = forms.IntegerField(min_value=0, max_value=100_000_000, label='Демо-сумма в минимальных единицах валюты')
    currency = forms.ChoiceField(label='Валюта', choices=PaymentRecord._meta.get_field('currency').choices)
    reference = forms.CharField(label='Основание', min_length=8, max_length=128, help_text='Непрозрачное демо-основание: сохраняется только SHA256. Без данных плательщика, банка и Support ID.')

    def clean_reference(self):
        value = self.cleaned_data['reference']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', value) or re.search(support_ids.PATTERN, value.upper()):
            raise forms.ValidationError('Используйте непрозрачное демо-основание без идентификаторов пользователя.')
        return value

    def clean_purpose(self):
        return self.cleaned_data['purpose'] or PaymentRecord.Purpose.CUSTOMER_PAYMENT

    def clean(self):
        values = super().clean()
        try:
            PaymentRecord(purpose=values.get('purpose'), amount_minor=values.get('amount_minor')).clean()
        except ValidationError as error:
            self.add_error(None, error)
        return values


class OperationForm(forms.Form):
    device = forms.ModelChoiceField(label='Устройство', queryset=DeviceProjection.objects.all())
    action = forms.ChoiceField(label='Действие', choices=OperationRequest.ACTIONS)
    payment = forms.ModelChoiceField(label='Подтверждённая запись (оплата или canary)', queryset=PaymentRecord.objects.filter(confirmed_at__isnull=False, operationrequest__isnull=True), required=False)
    period_start = UTCInstant(label='Начало периода')
    paid_until = UTCInstant(label='Оплачено до')
    grace_until = UTCInstant(label='Льготный период до')
    attest_exact_apk = forms.BooleanField(required=False, label='Я проверил передачу точного подписанного APK106 (демо-подтверждение)')

    def clean(self):
        values = super().clean()
        action = values.get('action')
        if action == 'activate':
            if not all(values.get(name) for name in ('payment', 'period_start', 'paid_until', 'attest_exact_apk')) or values.get('grace_until'):
                raise forms.ValidationError('Для активации нужны только подтверждённая запись, начало/конец периода и подтверждение APK.')
            if values['payment'].device_id != getattr(values.get('device'), 'pk', None):
                raise forms.ValidationError('Подтверждённая запись должна относиться к этому устройству.')
        elif action == 'grace':
            if not values.get('grace_until') or any(values.get(name) for name in ('payment', 'period_start', 'paid_until', 'attest_exact_apk')):
                raise forms.ValidationError('Для льготного периода нужна только дата его окончания.')
        elif action in ('expire', 'revoke'):
            if any(values.get(name) for name in ('payment', 'period_start', 'paid_until', 'grace_until', 'attest_exact_apk')):
                raise forms.ValidationError('Завершение/отзыв не должны включать оплату или даты периода.')
        return values


class ConfirmForm(forms.Form):
    confirmed = forms.BooleanField(label='Я проверил демо-операцию: реальные оплаты и устройства не затрагиваются.')
    token = forms.CharField(widget=forms.HiddenInput, required=False, max_length=1024)
