import hashlib
import json
import uuid

from django import forms
from django.core import signing
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST, require_safe

from .models import AuditRecord, SystemMessage
from .views import staff


KINDS = [('information', 'Информация'), ('maintenance', 'Технические работы'),
         ('server_change', 'Изменение серверов'), ('update', 'Обновление')]
PLATFORMS = [('android', 'Android'), ('windows', 'Windows'), ('linux', 'Linux')]


class MessageForm(forms.Form):
    title = forms.CharField(label='Заголовок', max_length=160)
    body = forms.CharField(label='Текст', max_length=4000, widget=forms.Textarea)
    kind = forms.ChoiceField(label='Тип', choices=KINDS, initial='information')
    platforms = forms.MultipleChoiceField(label='Платформы', choices=PLATFORMS,
                                         initial=['android', 'windows', 'linux'],
                                         widget=forms.CheckboxSelectMultiple)
    days = forms.IntegerField(label='Срок в ленте, дней', min_value=1, max_value=365, initial=30)

    def clean(self):
        values = super().clean()
        platforms = values.get('platforms', [])
        if len(set(platforms)) != len(platforms):
            self.add_error('platforms', 'Платформы не должны повторяться.')
        for field, limit in [('title', 160), ('body', 4000)]:
            text = values.get(field, '')
            try:
                invalid = len(text.encode('utf-16-le')) // 2 > limit
            except UnicodeError:
                invalid = True
            if invalid or any(ord(char) < 32 and char not in '\n\t' for char in text):
                self.add_error(field, 'Недопустимый текст или превышена длина.')
        return values


def payload(message):
    return dict(id=message.pk.hex, title=message.title, body=message.body,
                kind=message.kind, platforms=message.platforms, days=message.days)


def digest(message):
    return hashlib.sha256(json.dumps(payload(message), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def audit(message, action):
    AuditRecord.objects.create(actor=message.created_by, action='system.' + action,
                               target=message.pk.hex, details=dict(digest=digest(message)))


@staff('view_system_messages')
@require_safe
def index(request):
    return render(request, 'console/system_messages.html', dict(
        production_page=True, section='system_messages',
        records=SystemMessage.objects.select_related('created_by').order_by('-created_at')[:100]))


@staff('send_system_message')
@staff('view_system_messages')
@require_safe
def compose(request):
    token = signing.dumps(dict(id=uuid.uuid4().hex, actor=request.user.pk), salt='system-draft')
    return render(request, 'console/system_message_form.html', dict(
        production_page=True, section='system_messages', form=MessageForm(), token=token))


@staff('send_system_message')
@staff('view_system_messages')
@require_POST
@sensitive_post_parameters('body', 'title', 'token')
def preview(request):
    token = request.POST.get('token', '')
    try:
        values = signing.loads(token, salt='system-draft', max_age=1800)
        if values['actor'] != request.user.pk:
            raise signing.BadSignature
        ident = uuid.UUID(hex=values['id'])
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return HttpResponseBadRequest('Форма устарела. Откройте новую форму.')
    form = MessageForm(request.POST)
    if not form.is_valid():
        return render(request, 'console/system_message_form.html', dict(
            production_page=True, section='system_messages', form=form, token=token), status=400)
    with transaction.atomic():
        message, created = SystemMessage.objects.get_or_create(pk=ident, defaults=dict(
            created_by=request.user, **form.cleaned_data))
        if message.created_by_id != request.user.pk or any(
                getattr(message, field) != value for field, value in form.cleaned_data.items()):
            return HttpResponseBadRequest('Этот ID уже закреплён за другим текстом. Откройте новую форму.')
        if created:
            audit(message, 'preview')
    return redirect('console:system_message', ident=message.pk)


@staff('view_system_messages')
@require_safe
def detail(request, ident):
    message = get_object_or_404(SystemMessage, pk=ident)
    token = signing.dumps(dict(id=message.pk.hex, actor=request.user.pk, digest=digest(message)), salt='system-send')
    return render(request, 'console/system_message.html', dict(
        production_page=True, section='system_messages', message=message, token=token,
        can_send=message.created_by_id == request.user.pk and message.status in ('draft', 'unknown', 'refused')))


@staff('send_system_message')
@staff('view_system_messages')
@require_POST
def send(request, ident):
    with transaction.atomic():
        message = get_object_or_404(SystemMessage.objects.select_for_update(), pk=ident)
        try:
            values = signing.loads(request.POST.get('token', ''), salt='system-send', max_age=1800)
            if (values != dict(id=message.pk.hex, actor=request.user.pk, digest=digest(message))
                    or message.created_by_id != request.user.pk or request.POST.get('confirm') != 'public'):
                raise signing.BadSignature
        except (signing.BadSignature, TypeError, ValueError):
            return HttpResponseBadRequest('Нужно подтвердить предпросмотр под исходным аккаунтом.')
        if message.status in ('draft', 'unknown', 'refused'):
            message.status = 'queued'
            message.save(update_fields=['status', 'updated_at'])
            audit(message, 'queued')
    return redirect('console:system_message', ident=message.pk)
