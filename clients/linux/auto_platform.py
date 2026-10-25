"""Root Auto host: existing normal/MESH attempts, without a second retry policy."""
import base64
import copy
from contextlib import contextmanager
from dataclasses import asdict
import ipaddress
import json
import os
from pathlib import Path
import stat
import threading
import time

from auto_policy import Failure, require
from auto_configuration import AppliedSession, LEGACY_TARGETS, Preference, TargetChoices, legacy_target
from auto_guard import System
from auto_mesh import rejection
from auto_normal import NormalCandidate
from auto_normal_worker import trusted
from mesh_system import private_read, private_write
from profile_config import parse, AWG31_FIELDS


class Underlying:
    def __init__(self, system=None):
        self.system = system or System()

    def read(self, context):
        context.check()
        routes = self.system.run(('/usr/sbin/ip', '-j', '-4', 'route', 'show', 'table', 'main', 'default'))
        context.check()
        links = self.system.run(('/usr/sbin/ip', '-j', '-d', 'link', 'show'))
        context.check()
        addresses = self.system.run(('/usr/sbin/ip', '-j', '-4', 'address', 'show'))
        context.check()
        require(isinstance(routes, list) and isinstance(links, list) and isinstance(addresses, list))
        choices = []
        for route in routes:
            if route.get('type', 'unicast') != 'unicast' or route.get('dst') != 'default' or 'nexthops' in route:
                continue
            name = route.get('dev', '')
            if not isinstance(name, str) or name == 'lo' or name.startswith(('fcmesh', 'fcawg', 'fctcp')):
                continue
            matching = [link for link in links if link.get('ifname') == name]
            if len(matching) != 1:
                continue
            link = matching[0]
            if ('UP' not in link.get('flags', []) or 'LOWER_UP' not in link.get('flags', []) or
                    link.get('linkinfo', {}).get('info_kind') in ('wireguard', 'tun', 'gre', 'gretap', 'ipip', 'sit', 'vti', 'vti6')):
                continue
            index, metric = link.get('ifindex'), route.get('metric', 0)
            require(type(index) is int and 0 < index < 2**31 and type(metric) is int and 0 <= metric < 2**32)
            local = []
            for entry in addresses:
                if entry.get('ifindex') != index or entry.get('ifname') != name:
                    continue
                for address in entry.get('addr_info', []):
                    if address.get('family') != 'inet' or address.get('scope') != 'global' or address.get('valid_life_time') == 0:
                        continue
                    value = ipaddress.IPv4Address(address['local'])
                    if not (value.is_loopback or value.is_link_local or value.is_unspecified or value.is_multicast):
                        local.append(str(value))
            if local:
                gateway = str(ipaddress.IPv4Address(route['gateway'])) if 'gateway' in route else ''
                choices.append((metric, index, name, gateway, tuple(sorted(set(local)))))
        if not choices:
            raise Failure('NETWORK')
        choices.sort()
        best = choices[0]
        if any(other[0] == best[0] and other[1:] != best[1:] for other in choices[1:]):
            raise Failure('NETWORK')
        return dict(index=best[1], name=best[2], gateway=best[3], addresses=list(best[4]))


class Capabilities:
    def __init__(self, library=Path('/usr/local/lib'), config=Path('/etc/family-connect'),
                 units=Path('/etc/systemd/system'), tun=Path('/dev/net/tun')):
        self.library, self.config, self.units, self.tun = library, config, units, tun

    def __call__(self, configuration, context):
        context.check()
        try:
            if not stat.S_ISCHR(self.tun.stat().st_mode):
                return []
        except FileNotFoundError:
            return []
        available = []
        for kind, engines in (('awg', ('amneziawg-go', 'awg', 'awg-quick')), ('tcp', ('xray',))):
            root = self.library / ('family-connect-'+kind)
            try:
                for parent in (root, *root.parents):
                    trusted(parent, True)
                for parent in (self.config / kind, *self.config.parents, self.config):
                    trusted(parent, True)
                for name in ('helper', 'backend.py', 'profile_config.py', 'authorization-session-v2', *engines):
                    info = trusted(root / name)
                    if name in ('helper', *engines):
                        require(bool(info.st_mode & 0o111))
                if kind == 'awg':
                    trusted(root / 'awg_lifecycle.py')
                    fields = parse(configuration.awg, allow_awg=True, allow_awg31=True)
                    if set(fields['Interface']) & AWG31_FIELDS:
                        trusted(root / 'awg31.json')
                        with (root / 'awg31.json').open('rb') as stream:
                            raw = stream.read(4097)
                        require(len(raw) <= 4096)
                        value = json.loads(raw)
                        if (type(value.get('schema')) is not int or value['schema'] != 1 or
                                value.get('engine') != 'b5928efb6ca19f0153958460c3d141f04abc5c2e' or
                                value.get('tools') != 'ee0f0a9aa34ff0a0da4b3433b9512781cfe02843'):
                            continue
                else:
                    for parent in (self.units, *self.units.parents):
                        trusted(parent, True)
                    trusted(self.units / 'family-connect-tcp@.service')
            except FileNotFoundError:
                continue
            except (OSError, ValueError, TypeError):
                raise Failure('CONFIGURATION') from None
            available.append(kind)
            context.check()
        return available


class HintStore:
    def __init__(self, path, uid):
        self.path, self.uid = Path(path), uid

    def read(self):
        try:
            value = private_read(self.path)
        except FileNotFoundError:
            return dict(schema=1, uid=self.uid, countries={})
        require(set(value) == {'schema', 'uid', 'countries'} and type(value['schema']) is int and value['schema'] == 1)
        require(type(value['uid']) is int and value['uid'] == self.uid and isinstance(value['countries'], dict))
        require(not set(value['countries'])-{'ru', 'nl'} and all(kind in ('awg', 'tcp') for kind in value['countries'].values()))
        return value

    def last(self, country):
        return self.read()['countries'].get(country, '')

    def remember(self, country, kind):
        require(country in ('ru', 'nl') and kind in ('awg', 'tcp'))
        value = self.read()
        value['countries'][country] = kind
        private_write(self.path, value)
        require(self.read() == value)


class Platform:
    def __init__(self, guard, normal_owner, mesh, material, *, normal=None, underlying=None, capabilities=None, hints=None, preferred=''):
        self.guard, self.normal_owner, self.mesh = guard, normal_owner, mesh
        self.material = copy.deepcopy(material)
        self.normal = normal or NormalCandidate(guard)
        self.underlying, self.capabilities, self.hints = underlying or Underlying(), capabilities or Capabilities(), hints
        self.lock, self.view_lock = threading.Lock(), threading.Lock()
        self.health_context = None
        self.health_stopping = threading.Event()
        self.configuration, self.selected, self.path = None, '', None
        self.allowed, self.released = [], False
        self.generation = guard.generation
        target = legacy_target(material['country'])
        self.connection = Preference(target.provider, target.reference, preferred, material['profile'])
        self.choices = TargetChoices(LEGACY_TARGETS, self.connection)
        self.assignment, self.active, self.active_context = None, None, None
        self.view = dict(configuration='IDLE', first_reason='', selected='', underlying_index=0, capabilities=[], interface='', attempt=0)

    @contextmanager
    def serialized(self, context, allow_released=False):
        while not self.lock.acquire(timeout=min(.1, max(.001, context.deadline-time.monotonic()))):
            context.check()
        try:
            context.check()
            require(self.guard.generation == self.generation)
            require(allow_released or not self.released)
            yield
        finally:
            self.lock.release()

    def capture(self, **values):
        with self.view_lock:
            self.view.update(values)

    def failed(self, error):
        failure = rejection(error)
        with self.view_lock:
            self.active, self.active_context = None, None
            if not self.view['first_reason']:
                self.view['first_reason'] = failure.category
        return failure

    def cancel_health(self):
        self.health_stopping.set()
        with self.view_lock:
            self.active, self.active_context = None, None
            if self.health_context is not None:
                self.health_context.cancel.set()

    def configure(self, context):
        with self.serialized(context):
            with self.view_lock:
                self.assignment, self.active, self.active_context = None, None, None
            self.normal.close(context)
            network = self.mesh.network
            if os.path.lexists(network.journal):
                network.restore()
                network.cleanup()
                require(not network.owns_journal)
            self.allowed, self.configuration = [], None
            try:
                self.normal_owner.validate(self.material, context)
                self.path = self.underlying.read(context)
                private = base64.b64decode(self.material['wireguard_private'], validate=True)
                target = next(target for target in LEGACY_TARGETS if
                              (target.provider, target.reference) == (self.connection.provider, self.connection.target_reference))
                require(target.country == self.material['country'] and self.connection.requested_profile == self.material['profile'])
                self.configuration = self.normal_owner.resolve(self.material, target.country, private,
                    self.material['normal_floors'], self.path['index'], context)
                self.allowed = self.capabilities(self.configuration, context)
                context.check()
                require(self.guard.generation == self.generation)
                assignment = self.normal_owner.assignment(self.configuration, self.generation, self.connection.requested_profile)
                with self.view_lock:
                    self.assignment = assignment
                self.capture(configuration='READY', capabilities=list(self.allowed), underlying_index=self.path['index'])
            except Exception as error:
                failure = self.failed(error)
                self.capture(configuration=failure.category, capabilities=[])
                if failure.category != 'NETWORK':
                    raise failure from None
                context.check()
            return list(self.allowed)

    def prepare(self, context, selected):
        with self.serialized(context):
            require(not self.selected and selected in ('awg', 'tcp', 'restricted'))
            if selected != 'restricted':
                require(selected in self.allowed and self.configuration is not None and self.assignment is not None)
                require(self.assignment.owner_generation == self.generation)
            self.path = self.underlying.read(context)
            self.selected = selected
            self.health_stopping.clear()
            self.capture(selected=selected, underlying_index=self.path['index'])
            try:
                result = self.mesh.prepare(context) if selected == 'restricted' else self.normal.prepare(self.configuration, selected, context)
                self.capture(interface=result['interface'], attempt=self.view['attempt']+1)
                return result
            except Exception as error:
                raise self.failed(error) from None

    def open(self, context, selected):
        with self.serialized(context):
            require(self.selected == selected)
            try:
                if self.path != self.underlying.read(context):
                    raise Failure('NETWORK')
                result = (self.mesh if selected == 'restricted' else self.normal).open(context)
                context.check()
                if self.path != self.underlying.read(context):
                    raise Failure('NETWORK')
                return result
            except Exception as error:
                raise self.failed(error) from None

    def close(self, context):
        self.cancel_health()
        with self.serialized(context, allow_released=True):
            if self.released:
                return
            try:
                self.mesh.close(context)
                self.normal.close(context)
                self.selected = ''
                self.capture(selected='', interface='')
            except Exception as error:
                raise self.failed(error) from None

    def release(self, context):
        with self.serialized(context, allow_released=True):
            if self.released:
                return
            require(not self.selected)
            self.normal.release(context)
            self.mesh.release(context)
            self.configuration, self.path = None, None
            self.material.clear()
            self.allowed.clear()
            self.released = True
            with self.view_lock:
                self.assignment, self.active, self.active_context = None, None, None

    def applied(self, context, selected):
        with self.serialized(context):
            require(self.selected == selected and self.guard.record['current']['mode'] == 'ready')
            with self.view_lock:
                context.check()
                require(not self.health_stopping.is_set())
                self.active = AppliedSession(self.generation, selected, self.connection.requested_profile,
                                             self.view['interface'], None if selected == 'restricted' else self.assignment)
                self.active_context = context

    def refresh_targets(self, targets):
        with self.view_lock:
            self.choices.refresh(targets)

    def select_next(self, preference):
        with self.view_lock:
            self.choices.select(preference)

    def selection_snapshot(self):
        with self.view_lock:
            active = self.active if self.active_context is not None and not self.active_context.cancel.is_set() else None
            return dict(**self.choices.snapshot(), connection=asdict(self.connection),
                        assignment=asdict(self.assignment) if self.assignment else None,
                        applied=asdict(active) if active else None, dynamic_fleet=False)

    def remember(self, context, selected):
        with self.serialized(context):
            require(selected == self.selected and selected in self.allowed)
            if self.hints is not None:
                self.hints.remember(self.material['country'], selected)
            context.check()

    def health(self, context):
        with self.serialized(context):
            require(self.selected)
            with self.view_lock:
                self.health_context = context
                if self.health_stopping.is_set():
                    context.cancel.set()
            try:
                context.check()
                if self.path != self.underlying.read(context):
                    raise Failure('NETWORK')
                (self.mesh if self.selected == 'restricted' else self.normal).health(context)
                context.check()
                return True
            except Exception as error:
                raise self.failed(error) from None
            finally:
                with self.view_lock:
                    self.health_context = None

    def snapshot(self):
        with self.view_lock:
            return copy.deepcopy(self.view)

    def network_matches(self, current):
        if not self.lock.acquire(blocking=False):
            return None
        try:
            return self.path == current
        finally:
            self.lock.release()
