import copy
import json
import os
from pathlib import Path
import socket
import threading

import pytest

from provisioning.support_worker import SupportError, SupportMailbox, SupportServer
from messenger.tests.test_support import support, queued


@pytest.mark.parametrize('mutation', ['same_device', 'same_address', 'sender', 'stale', 'malformed_node', 'boolean_schema'])
def test_snapshot_cannot_rebind_or_ambiguously_join(support, mutation):
    owner, clients, snapshot = support
    queued(owner, clients[0])
    value = copy.deepcopy(snapshot)
    value['sequence'] += 1
    if mutation == 'same_device':
        value['devices'][1]['device'] = value['devices'][0]['device']
    elif mutation == 'same_address':
        value['devices'][1]['public'] = value['devices'][0]['public']
    elif mutation == 'sender':
        value['sender_public'] = clients[0].profile()['public']
    elif mutation == 'stale':
        value['sequence'] = 1
    elif mutation == 'boolean_schema':
        value['schema'] = True
    else:
        value['node'] = None
    if mutation == 'stale':
        value['devices'].pop()
    with pytest.raises((SupportError, ValueError)):
        owner.update(value)
    assert owner.binding('1' * 64)['address'] == clients[0].profile()['address']


def test_expired_lease_blocks_pending_without_rewriting_history(support, monkeypatch):
    owner, clients, snapshot = support
    request, ident = queued(owner, clients[0])
    monkeypatch.setattr('provisioning.support_worker.time.time', lambda: snapshot['expires_at'] + 1)
    assert owner.store.pending_outbox() == []
    assert owner.binding('1' * 64)['state'] == 'binding_expired'
    assert owner.send(**request)['id'] == ident
    assert owner.history('1' * 64)['messages'][0]['status'] == 'queued'


def test_snapshot_file_permissions_and_duplicate_fields(support, tmp_path):
    owner, clients, snapshot = support
    path = tmp_path / 'snapshot.json'
    path.write_text(json.dumps(snapshot))
    path.chmod(0o640)
    mailbox = SupportMailbox(owner, path, None)
    mailbox.refresh()
    path.chmod(0o666)
    with pytest.raises(SupportError):
        mailbox.refresh()
    path.chmod(0o640)
    path.write_text('{"schema":1,"schema":1}')
    with pytest.raises(SupportError):
        mailbox.refresh()
    link = tmp_path / 'link'
    link.symlink_to(path)
    with pytest.raises(OSError):
        SupportMailbox(owner, link, None).refresh()


class IdleDelivery:
    def request_sync(self):
        pass


def test_real_ipc_lost_response_and_abandoned_socket(support, tmp_path):
    owner, clients, snapshot = support
    path = tmp_path / 'lease'
    path.write_text(json.dumps(snapshot))
    path.chmod(0o600)
    mailbox = SupportMailbox(owner, path, None)
    endpoint = tmp_path / 'worker.sock'
    abandoned = socket.socket(socket.AF_UNIX)
    abandoned.bind(str(endpoint))
    abandoned.close()
    request, ident = queued(owner, clients[0])
    packet = json.dumps(dict(operation='send', arguments=request)).encode() + b'\n'
    with SupportServer(endpoint, owner, mailbox, IdleDelivery()) as server:
        thread = threading.Thread(target=lambda: [server.handle_request() for _ in range(2)])
        thread.start()
        with socket.socket(socket.AF_UNIX) as connection:
            connection.connect(str(endpoint))
            connection.sendall(packet)
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(5)
            connection.connect(str(endpoint))
            connection.sendall(packet)
            response = json.loads(connection.makefile('rb').readline())
        thread.join(5)
        assert not thread.is_alive()
        assert response == dict(ok=True, result=dict(id=ident, accepted=True))
    assert len(owner.history('1' * 64)['messages']) == 1


@pytest.mark.parametrize('request_id', ['', 'not-a-uuid', None, 'A' * 36])
def test_invalid_request_id_is_a_bounded_error(support, request_id):
    owner, clients, snapshot = support
    request, ident = queued(owner, clients[0])
    with pytest.raises(SupportError, match='invalid_message'):
        owner.send(**dict(request, request_id=request_id))
