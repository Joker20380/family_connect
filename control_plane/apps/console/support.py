import json
import socket
import uuid

from django.conf import settings
from django.core import signing
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST, require_safe

from .models import AuditRecord, InventoryDevice, SubscriptionSnapshot, SubscriptionEventObservation
from .views import staff


ERRORS = {
    'unconfirmed': 'Связь устройства и chat identity не подтверждена.',
    'unregistered': 'Чат устройства не зарегистрирован.',
    'support_not_enrolled': 'Клиент не подтвердил протокол официальной поддержки. Нужен совместимый клиент и регистрация чата.',
    'revoked': 'Identity отозвана. Отправка запрещена.',
    'identity_changed': 'Identity изменилась. Старая очередь не переназначается.',
    'binding_expired': 'Истёк срок подтверждения адресата. Отправка заблокирована.',
    'binding_unavailable': 'Нет актуального подтверждения адресата от registry.',
    'recipient_mismatch': 'Адресат изменился. Отправка заблокирована.',
    'request_conflict': 'Этот ID уже использован для другого сообщения. Откройте карточку заново.',
    'invalid_message': 'Нужен непустой текст до 4096 байт UTF-8.',
    'history_full': 'Достигнут лимит защищённой истории. Сообщение не принято.',
    'support_unavailable': 'Исполнитель поддержки недоступен. Результат неизвестен; повторите с тем же ID.',
    'invalid_form': 'Форма истекла или изменена. Откройте карточку заново.',
}
STATUSES = {'queued': 'Принято локально · в очереди', 'sending': 'Попытка передачи',
            'relayed': 'Принято mailbox · ждём ACK клиента', 'delivered': 'Подтверждено транспортом',
            'recipient_stored': 'Сохранено клиентом · подписанный ACK', 'received': 'Ответ сохранён поддержкой',
            'expired': 'Срок доставки истёк'}


class SupportUnavailable(Exception):
    pass


def known_device(pseudonym):
    if (len(pseudonym) != 64 or any(char not in '0123456789abcdef' for char in pseudonym)
            or not (InventoryDevice.objects.filter(pseudonym=pseudonym, snapshot__scope='production',
                        snapshot__source='gateway-ru').exists()
                    or SubscriptionSnapshot.objects.filter(status='ok', devices__contains=[dict(pseudonym=pseudonym)]).exists()
                    or SubscriptionEventObservation.objects.filter(pseudonym=pseudonym).exists())):
        raise Http404


def invoke(operation, **arguments):
    path = getattr(settings, 'SUPPORT_SOCKET', '')
    if not path:
        raise SupportUnavailable('support_unavailable')
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(5)
            connection.connect(path)
            connection.sendall(json.dumps(dict(operation=operation, arguments=arguments), ensure_ascii=False).encode() + b'\n')
            with connection.makefile('rb') as stream:
                raw = stream.readline(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024 or not raw.endswith(b'\n'):
                raise ValueError
            response = json.loads(raw)
        if not response['ok']:
            raise SupportUnavailable(response['error'] if response['error'] in ERRORS else 'support_unavailable')
        return response['result']
    except (OSError, ValueError, KeyError, TypeError):
        raise SupportUnavailable('support_unavailable') from None


def conversation(request, pseudonym, *, error=None, token=None, text=''):
    known_device(pseudonym)
    data = dict(production_page=True, section='messages', pseudonym=pseudonym, error=ERRORS.get(error), text=text)
    try:
        history = invoke('history', pseudonym=pseudonym)
        for message in history['messages']:
            message['status_label'] = STATUSES.get(message['status'], 'Неизвестный статус')
        binding = history['binding']
        data.update(history=history, blocked=ERRORS.get(binding['state']), ready=binding['state'] == 'verified')
        if token is None and data['ready']:
            token = signing.dumps(dict(pseudonym=pseudonym, address=binding['address'],
                                       actor=str(request.user.pk), request_id=str(uuid.uuid4())), salt='support-send')
    except SupportUnavailable as failure:
        data['error'] = ERRORS[str(failure)]
    data['token'] = token
    return render(request, 'console/support_conversation.html', data, status=400 if error else 200)


@staff('view_support_messages')
@require_safe
def history(request, pseudonym):
    return conversation(request, pseudonym)


@staff('send_support_message')
@staff('view_support_messages')
@require_POST
@sensitive_post_parameters('text', 'token')
def send(request, pseudonym):
    known_device(pseudonym)
    token, text = request.POST.get('token', ''), request.POST.get('text', '')
    try:
        values = signing.loads(token, salt='support-send', max_age=1800)
        if values['pseudonym'] != pseudonym or values['actor'] != str(request.user.pk):
            raise signing.BadSignature
    except (signing.BadSignature, KeyError, TypeError):
        return conversation(request, pseudonym, error='invalid_form')
    if not text.strip() or len(text.encode('utf-8')) > 4096:
        return conversation(request, pseudonym, error='invalid_message', token=token, text=text)
    AuditRecord.objects.get_or_create(actor=request.user, action='support.request', target=values['request_id'],
                                     defaults=dict(details=dict(pseudonym=pseudonym)))
    try:
        result = invoke('send', **values, text=text)
    except SupportUnavailable as failure:
        AuditRecord.objects.create(actor=request.user, action='support.result_unknown' if str(failure) == 'support_unavailable'
                                   else 'support.refused', target=values['request_id'],
                                   details=dict(pseudonym=pseudonym, error=str(failure)))
        return conversation(request, pseudonym, error=str(failure), token=token, text=text)
    AuditRecord.objects.get_or_create(actor=request.user, action='support.accepted', target=values['request_id'],
                                     defaults=dict(details=dict(pseudonym=pseudonym, message_id=result['id'])))
    return redirect('console:support_history', pseudonym=pseudonym)


@staff('view_support_messages')
@require_safe
def inbox(request):
    data = dict(production_page=True, section='messages')
    try:
        data['threads'] = invoke('inbox')
    except SupportUnavailable as failure:
        data['error'] = ERRORS[str(failure)]
    return render(request, 'console/support_inbox.html', data)
