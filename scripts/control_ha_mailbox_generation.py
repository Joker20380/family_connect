"""Forward-only support generation transition; reclosure never becomes an opening lease."""
import hashlib
import json
from pathlib import Path
import re

from scripts import control_ha_legacy_support as admission
from scripts import control_ha_mailbox_startup as mailbox
from scripts import control_ha_mailbox_control as control
from scripts.control_ha_mailbox_control import MailboxControl, sha
from scripts.control_ha_mailbox_startup import encoded, owned, unique, fixture_scope


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def closed(startup):
    startup.unchanged()
    startup.check_seal()
    observed = startup.observe()
    fence = observed['fence']
    admission.require(fence['new_link_admission'] == 'CLOSED' and fence['opening_invalidated'] is True,
                      'PREDECESSOR_NOT_INVALIDATED')
    admission.require(fence['in_process_drained'] is True and fence['accepted_target_work'] == 0,
                      'PREDECESSOR_WORK_BUSY')
    return observed


def advance(startup, request):
    value = json.loads(owned(request, startup.owner_uid), object_pairs_hook=unique)
    admission.require(type(value) is dict and set(value) == {'action', 'ticket', 'manifest', 'manifest_sha256'} and
                      value['action'] == 'ADVANCE_CLOSED_GENERATION', 'GENERATION_REQUEST')
    destination = Path(value['manifest'])
    admission.require(destination.is_absolute() and '..' not in destination.parts and destination != startup.path,
                      'NEW_MANIFEST_REQUIRED')
    fresh = mailbox.Startup(destination, owner_uid=startup.owner_uid, control_ready=startup.control_ready)
    admission.require(fresh.digest == value['manifest_sha256'] and
                      fresh.manifest['generation'] != startup.manifest['generation'] and
                      fresh.manifest['support_public'] == startup.manifest['support_public'] and
                      fresh.manifest['replacement_plan_sha256'] != startup.manifest['replacement_plan_sha256'] and
                      not fresh.seal.exists() and not fresh.seal.is_symlink(), 'NEW_GENERATION_BINDINGS')
    with mailbox.CREATION, startup.fence.lock:
        admission.require(mailbox.ACTIVE is startup and value['ticket'] == startup.ticket(), 'STALE_PREDECESSOR')
        prior = closed(startup)
        fence = startup.fence
        admission.require(fence.epoch is None and fence.sealed and not fence.admitted, 'PREDECESSOR_WORK_BUSY')
        fresh.fence, fresh.used, fresh.published, fresh.adopted = fence, True, True, True
        fresh.fixture = startup.fixture
        fresh.predecessor = dict(ticket_sha256=digest(prior['ticket']), readback_sha256=digest(prior),
                                 request_sha256=digest(value))
        fence.generation = fresh.manifest['generation']
        fence.opened = False
        fence.sealed = False
        mailbox.ACTIVE = fresh
        return fresh.observe()


def consume(startup, request):
    value = json.loads(owned(request, startup.owner_uid), object_pairs_hook=unique)
    admission.require(type(value) is dict and set(value) == {'action', 'ticket', 'witness', 'reservation'} and
                      value['action'] == 'OWNER_FORWARD_RESUME', 'RESUME_REQUEST')
    with startup.fence.lock:
        admission.require(value['ticket'] == startup.ticket(), 'STALE_RESUME_TICKET')
        admission.require(not startup.seal.exists() and not startup.seal.is_symlink() and
                          not startup.fence.sealed, 'OPENING_INVALIDATED')
        request_sha = digest(value)
        if startup.consumed is not None:
            admission.require(startup.consumed['request_sha256'] == request_sha, 'WITNESS_ALREADY_CONSUMED')
            return startup.observe()
        witness, reservation = value['witness'], value['reservation']
        expected = {'schema', 'result', 'controller_uid', 'fixture', 'ticket_sha256', 'plan_sha256',
                    'old_binding', 'candidate_binding', 'archive_sha256', 'accepted_sha256',
                    'reservation_sha256', 'predecessor_sha256', 'reclosure_sha256', 'absence_sha256',
                    'old_process_absent', 'independent_controller', 'legacy_uncertainty_preserved',
                    'data_restored', 'capture_permitted', 'opening_permitted', 'settlement_proven'}
        admission.require(type(witness) is dict and set(witness) == expected and
                          type(witness['schema']) is int and witness['schema'] == 1 and
                          witness['result'] == 'OWNER_FORWARD_RESUME_SAMPLED', 'RESUME_WITNESS')
        admission.require(type(witness['controller_uid']) is int and
                          witness['controller_uid'] == startup.owner_uid and witness['fixture'] is startup.fixture and
                          all(witness[name] is True for name in ('old_process_absent', 'independent_controller',
                                                               'legacy_uncertainty_preserved')) and
                          all(witness[name] is False for name in ('data_restored', 'capture_permitted',
                                                                 'opening_permitted', 'settlement_proven')),
                          'RESUME_AUTHORITY')
        ticket = value['ticket']
        admission.require(witness['ticket_sha256'] == digest(ticket) and
                          witness['plan_sha256'] == ticket['replacement_plan_sha256'] and
                          digest(witness['old_binding']) == ticket['owner_binding_sha256'] and
                          witness['candidate_binding'] != witness['old_binding'], 'RESUME_BINDINGS')
        for name in ('accepted_sha256', 'predecessor_sha256', 'reclosure_sha256', 'absence_sha256'):
            admission.require(type(witness[name]) is str and len(witness[name]) == 64 and
                              all(character in '0123456789abcdef' for character in witness[name]), 'RESUME_EVIDENCE')
        admission.require(witness['archive_sha256'] ==
                          '621009b8df9baffb81e0d9069cfa52b3781e7dd7bf4e435dd89740e38cae5739', 'CANDIDATE_ARCHIVE')
        admission.require(type(reservation) is dict and type(reservation.get('schema')) is int and
                          reservation.get('opening_permitted') is False and reservation.get('capture_permitted') is False and
                          reservation == dict(schema=1, ticket_sha256=digest(ticket),
                          plan_sha256=ticket['replacement_plan_sha256'], accepted_sha256=witness['accepted_sha256'],
                          opening_permitted=False, capture_permitted=False) and
                          digest(reservation) == witness['reservation_sha256'], 'RESUME_RESERVATION')
        startup.fence.open_after_local_drain(startup.manifest['generation'])
        startup.consumed = dict(request_sha256=request_sha, witness_sha256=digest(witness),
                                reservation_sha256=digest(reservation), ticket_sha256=digest(ticket))
        return startup.observe()


class GenerationControl(MailboxControl):
    actions = (*getattr(MailboxControl, 'actions', ('observe', 'consume', 'reclose')), 'advance', 'resume')

    def fixture_plan(self, path):
        selected = Path(path).absolute()
        return (super().fixture_plan(path) or
                fixture_scope(self.plan['manifest'], self.plan['unit']) and
                selected.parent == Path(self.plan['manifest']).parent and
                re.fullmatch('(control|transition)-[0-9a-f]{64}\\.json', selected.name) is not None)

    def invocation(self, action, request):
        if action not in ('advance', 'resume'):
            return super().invocation(action, request)
        source = str(Path(__file__).resolve())
        admission.require(self.plan['sources'].get(source) == sha(source), 'GENERATION_SOURCE_PIN')
        if action == 'advance':
            value = json.loads(owned(request, self.owner), object_pairs_hook=unique)
            arguments = self.plan['restart_argv']
            normal = arguments.count('--manifest') == 1 and arguments[arguments.index('--manifest') + 1] == value.get('manifest')
            fixture = (fixture_scope(value.get('manifest', ''), self.plan['unit']) and len(arguments) == 7 and
                       arguments[2] == str(Path(self.plan['manifest']).parent / 'tests/fixtures/mailbox_startup.py') and
                       arguments[4] == value.get('manifest') and arguments[6] == '0')
            admission.require(normal or fixture,
                              'NEW_RESTART_GUARD_REQUIRED')
        operation = 'advance' if action == 'advance' else 'consume'
        return (f'__import__("runpy").run_path({source!r})[{operation!r}](startup,{str(request)!r})')


def main():
    control.MailboxControl = GenerationControl
    control.main()


if __name__ == '__main__':
    main()
