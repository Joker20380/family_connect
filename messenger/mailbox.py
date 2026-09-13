"""Bounded LXMF mailbox pull; delete only after the chat store committed.

Uses the pinned LXMF 1.1.1 request API, without its eager deletion callback.
The caller supplies an out-of-band trusted node public key and the chat's IN
LXMF delivery destination (including its persisted ratchets).
"""
from dataclasses import dataclass
import threading
import time

from LXMF.LXMPeer import LXMPeer
import RNS

from .codec import identity, MAX_PACKED


class MailboxError(Exception):
    pass


@dataclass(frozen=True)
class SyncResult:
    stored: int
    duplicates: int
    rejected: int
    purged: int


class Mailbox:
    def __init__(self, chat, source, node_public):
        if source.hash != chat.address or source.direction != RNS.Destination.IN:
            raise ValueError('Chat delivery destination required')
        self.chat, self.source = chat, source
        self.node = identity(node_public)
        self._busy = threading.Lock()

    @staticmethod
    def _wait(predicate, deadline, cancel):
        while True:
            if cancel.is_set():raise MailboxError('cancelled')
            remaining=deadline-time.monotonic()
            if remaining<=0:raise MailboxError('timeout')
            if predicate():return
            cancel.wait(min(.02,remaining))

    def _request(self, link, data, deadline, cancel):
        self._wait(lambda:True,deadline,cancel)
        done=threading.Event();response=[]
        def received(receipt):response.append(receipt.response);done.set()
        receipt=link.request(LXMPeer.MESSAGE_GET_PATH,data=data,
            response_callback=received,failed_callback=lambda _:done.set(),
            timeout=max(.001,deadline-time.monotonic()),max_response_size=70000)
        if receipt is None or receipt is False:raise MailboxError('request_failed')
        self._wait(lambda:done.is_set() or link.status==RNS.Link.CLOSED,deadline,cancel)
        if not response:raise MailboxError('request_failed')
        result=response[0]
        if type(result) is not list:
            if result==LXMPeer.ERROR_NO_ACCESS:raise MailboxError('access_denied')
            raise MailboxError('invalid_response')
        return result

    def sync(self, *, delete_after_store=True, timeout=12, cancel=None):
        if type(timeout) not in (int,float) or not 0<timeout<=30:
            raise ValueError('Mailbox timeout must be within (0,30] seconds')
        if type(delete_after_store) is not bool:raise ValueError('Explicit deletion policy required')
        cancel=cancel if cancel is not None else threading.Event()
        if not self._busy.acquire(blocking=False):raise MailboxError('busy')
        link=None
        deadline=time.monotonic()+timeout
        try:
            self._wait(lambda:True,deadline,cancel)
            destination=RNS.Destination(self.node,RNS.Destination.OUT,RNS.Destination.SINGLE,'lxmf','propagation')
            if not RNS.Transport.has_path(destination.hash):RNS.Transport.request_path(destination.hash)
            self._wait(lambda:RNS.Transport.has_path(destination.hash),deadline,cancel)
            ready=threading.Event()
            link=RNS.Link(destination,established_callback=lambda _:ready.set())
            self._wait(lambda:ready.is_set() or link.status==RNS.Link.CLOSED,deadline,cancel)
            if not ready.is_set() or link.status!=RNS.Link.ACTIVE:raise MailboxError('link_failed')
            link.identify(self.chat.identity)
            available=self._request(link,[None,None],deadline,cancel)
            if len(available)>1000 or any(type(x) is not bytes or len(x)!=32 for x in available):
                raise MailboxError('invalid_list')
            wanted=list(dict.fromkeys(available))[:10]
            if not wanted:return SyncResult(0,0,0,0)
            # Ask for a small batch. Remaining messages stay on the node for the
            # next explicit sync; never download an unbounded remote mailbox.
            messages=self._request(link,[wanted,[],48],deadline,cancel)
            if len(messages)>len(wanted):raise MailboxError('invalid_batch')
            stored=duplicates=rejected=0;haves=[]
            for blob in messages:
                self._wait(lambda:True,deadline,cancel)
                if type(blob) is not bytes or not 16<len(blob)<=MAX_PACKED+256:
                    raise MailboxError('invalid_ciphertext')
                transient=RNS.Identity.full_hash(blob)
                if transient not in wanted or transient in haves:raise MailboxError('unexpected_message')
                if blob[:16]!=self.chat.address:
                    rejected+=1;continue
                plaintext=self.source.decrypt(blob[16:])
                if plaintext is None:
                    rejected+=1;continue
                try:
                    added=self.chat.receive(blob[:16]+plaintext)
                except ValueError:
                    # Unknown contact, bad signature, unsupported text or full
                    # history: preserve on node. No plaintext/error detail logs.
                    rejected+=1;continue
                # Other storage errors propagate before ANY purge request.
                if added:stored+=1
                else:duplicates+=1
                haves.append(transient)
            if delete_after_store and haves:
                if self._request(link,[None,haves],deadline,cancel):
                    raise MailboxError('invalid_purge_response')
            return SyncResult(stored,duplicates,rejected,len(haves) if delete_after_store else 0)
        finally:
            try:
                if link is not None:link.teardown()
            finally:self._busy.release()
