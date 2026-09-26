"""Administrator-authenticated notices. Grant/revoke is an operator-only CLI."""
import re
from pathlib import Path
from scripts.service_notices import Notices

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
