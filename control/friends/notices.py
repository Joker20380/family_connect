"""Administrator-authenticated notices. Grant/revoke is an operator-only CLI."""
import re
from pathlib import Path
from scripts.service_notices import Notices, refuse_canonical

class NoticeDenied(Exception): pass
class NoticeConflict(Exception): pass


def publish(registry, output, authorization, value):
    if type(authorization) is not str or re.fullmatch(r'Bearer [a-f0-9]{64}', authorization) is None or not Path(registry).exists():
        raise NoticeDenied()
    if type(value) is not dict or set(value) != {'id','kind','title','body','platforms','days'} or type(value['days']) is not int or not 1 <= value['days'] <= 365:
        raise ValueError('Invalid notice request')
    if type(value['id']) is not str or re.fullmatch('[a-f0-9]{32}',value['id']) is None: raise ValueError('Invalid notice id')
    publisher=Notices(registry)
    try:
        try:
            ident=publisher.publish(authorization[7:],ident=value['id'],kind=value['kind'],title=value['title'],body=value['body'],platforms=value['platforms'],lifetime=value['days']*86400)
        except ValueError as error:
            if str(error)=='Publisher access denied': raise NoticeDenied() from None
            raise
        publisher.export_all(output)
        return dict(id=ident,status='published')
    finally: publisher.db.close()


def device_request(access, registry, output, action, value):
    """Fresh device proof; the operator registry alone grants publishing rights."""
    refuse_canonical(access.path)
    refuse_canonical(registry)
    if action not in ('role','publish','list','edit') or type(value) is not dict or set(value) != ({'proof'} if action=='role' else {'proof','offset'} if action=='list' else {'proof','notice'}):
        raise ValueError('Invalid device notice request')
    record=access.complete(value['proof'],'notices-'+action)
    publisher=Notices(registry)
    try:
        if action=='role': return dict(device=record['device'],**publisher.device_role(record['device']))
        if action in ('list','edit'):
            try:result=publisher.list_device(record['device'],value['offset']) if action=='list' else publisher.edit_device(record['device'],value['notice'])
            except ValueError as error:
                if str(error)=='Publisher access denied':raise NoticeDenied() from None
                if str(error)=='Stale notice revision':raise NoticeConflict() from None
                raise
            if action=='edit':publisher.export_all(output)
            return result
        notice=value['notice']
        if type(notice) is not dict or set(notice)!={'id','kind','title','body','platforms','days'} or type(notice['days']) is not int or not 1<=notice['days']<=365:
            raise ValueError('Invalid notice request')
        if type(notice['id']) is not str or re.fullmatch('[a-f0-9]{32}',notice['id']) is None: raise ValueError('Invalid notice id')
        try:
            ident=publisher.publish('',device=record['device'],ident=notice['id'],kind=notice['kind'],title=notice['title'],body=notice['body'],platforms=notice['platforms'],lifetime=notice['days']*86400)
        except ValueError as error:
            if str(error)=='Publisher access denied': raise NoticeDenied() from None
            raise
        publisher.export_all(output)
        return dict(id=ident,status='published')
    finally: publisher.db.close()


def device_request_repository(access, action, value):
    if action not in ('role', 'publish', 'list', 'edit') or type(value) is not dict or set(value) != (
            {'proof'} if action == 'role' else {'proof', 'offset'} if action == 'list' else {'proof', 'notice'}):
        raise ValueError('Invalid device notice request')
    with access.enrollment() as enrollment:
        publisher = enrollment.notices()
        publisher.require_schema()
        record = access.complete(value['proof'], 'notices-' + action, transaction=enrollment)
        invitation = enrollment.device_invitation(record['device'])
        if invitation is None or invitation['revoked']:
            from .access import Rejected
            raise Rejected()
        if action == 'role':
            return dict(device=record['device'], **publisher.device_role(record['device']))
        try:
            if action == 'list':
                return publisher.list_device(record['device'], value['offset'])
            if action == 'edit':
                return publisher.edit_device(record['device'], value['notice'], now=int(access.clock()))
            return publish_value(publisher, '', value['notice'], now=int(access.clock()), device=record['device'])
        except ValueError as error:
            if str(error) == 'Publisher access denied': raise NoticeDenied() from None
            if str(error) == 'Stale notice revision': raise NoticeConflict() from None
            raise


def publish_value(publisher, token, value, *, now, device=None):
    if type(value) is not dict or set(value) != {'id', 'kind', 'title', 'body', 'platforms', 'days'} or type(value['days']) is not int or not 1 <= value['days'] <= 365:
        raise ValueError('Invalid notice request')
    if type(value['id']) is not str or re.fullmatch('[a-f0-9]{32}', value['id']) is None:
        raise ValueError('Invalid notice id')
    ident = publisher.publish(token, device=device, ident=value['id'], kind=value['kind'], title=value['title'],
        body=value['body'], platforms=value['platforms'], lifetime=value['days'] * 86400, now=now)
    return dict(id=ident, status='stored')


def publish_repository(access, authorization, value):
    if type(authorization) is not str or re.fullmatch(r'Bearer [a-f0-9]{64}', authorization) is None:
        raise NoticeDenied()
    with access.enrollment() as enrollment:
        publisher = enrollment.notices()
        publisher.require_schema()
        try:
            return publish_value(publisher, authorization[7:], value, now=int(access.clock()))
        except ValueError as error:
            if str(error) == 'Publisher access denied': raise NoticeDenied() from None
            raise


def grant_device_repository(access, device, name):
    with access.enrollment() as enrollment:
        publisher = enrollment.notices()
        publisher.require_schema()
        record = enrollment.device(device)
        invitation = enrollment.device_invitation(device)
        if record is None or record['revoked'] or invitation is None or invitation['revoked']:
            raise ValueError('Device not active')
        publisher.assign_device(device, name)


def feed_repository(access, version=1):
    with access.read_enrollment() as enrollment:
        publisher = enrollment.notices()
        publisher.require_schema()
        return publisher.feed(now=int(access.clock()), version=version)
