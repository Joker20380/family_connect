from copy import deepcopy
import os
from pathlib import Path
import signal
import subprocess
import threading
import time


PREPARATION_SECONDS = 180
CANDIDATE_SECONDS = 200
ATTEMPT_SECONDS = 390
CLEANUP_SECONDS = 120
OVERALL_SECONDS = PREPARATION_SECONDS + ATTEMPT_SECONDS + CLEANUP_SECONDS + 15
SAMPLE_SECONDS = 3
JOIN_SECONDS = 6
FORCED_CLEANUP_SECONDS = 5


def stop(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def start(command, environment, log):
    return subprocess.Popen(
        ['systemd-run', '--user', '--scope', '--quiet', '-p', 'CPUQuota=100%', '--'] + command,
        env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)


def read_frame(clock=time.monotonic, wall=time.time):
    frame = {'started_monotonic': clock(), 'started_unix': wall(),
             'cpu': [], 'gpu': None, 'cpu_max_c': None, 'gpu_max_c': None, 'error': None}
    try:
        for device in sorted(Path('/sys/class/hwmon').glob('hwmon*')):
            driver = (device / 'name').read_text().strip()
            if driver not in ('coretemp', 'k10temp'):
                continue
            for path in sorted(device.glob('temp*_input')):
                reading = {'path': str(path), 'driver': driver,
                           'label': None, 'raw_input': None, 'celsius': None,
                           'started_monotonic': clock(), 'started_unix': wall()}
                frame['cpu'].append(reading)
                try:
                    label = path.with_name(path.name.replace('_input', '_label'))
                    reading['label'] = label.read_text().strip() if label.exists() else 'UNKNOWN'
                    raw = int(path.read_text())
                    reading.update(raw_input=raw, celsius=raw / 1000)
                finally:
                    reading.update(finished_monotonic=clock(), finished_unix=wall())
        if not frame['cpu']:
            raise ValueError('CPU_SENSOR_MISSING')
        gpu = {'source': 'nvidia-smi:GPU0', 'label': 'GPU 0', 'raw_input': None,
               'celsius': None, 'started_monotonic': clock(), 'started_unix': wall()}
        frame['gpu'] = gpu
        try:
            output = subprocess.check_output(
                ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
                text=True, stderr=subprocess.DEVNULL, timeout=5)
            raw = int(output.strip().splitlines()[0])
            gpu.update(raw_input=raw, celsius=raw)
        finally:
            gpu.update(finished_monotonic=clock(), finished_unix=wall())
    except (OSError, ValueError, IndexError, subprocess.SubprocessError) as error:
        frame['error'] = {'reason': 'SENSOR_UNAVAILABLE', 'type': type(error).__name__,
                          'errno': getattr(error, 'errno', None)}
    except Exception as error:
        frame['error'] = {'reason': 'MONITOR_ERROR', 'type': type(error).__name__}
    values = [reading['celsius'] for reading in frame['cpu'] if reading['celsius'] is not None]
    frame['cpu_max_c'] = max(values) if values else None
    frame['gpu_max_c'] = frame['gpu']['celsius'] if frame['gpu'] else None
    frame.update(finished_monotonic=clock(), finished_unix=wall())
    return frame


def temperature_reason(frame):
    if frame['error']:
        return frame['error']['reason']
    if frame['cpu_max_c'] is None or frame['gpu_max_c'] is None:
        return 'SENSOR_UNAVAILABLE'
    if frame['cpu_max_c'] >= 85:
        return 'CPU_TEMPERATURE_LIMIT'
    if frame['gpu_max_c'] >= 80:
        return 'GPU_TEMPERATURE_LIMIT'
    return None


class GuardStopped(RuntimeError):
    pass


class Monitor:
    def __init__(self, record, save, on_stop, *, reader=read_frame, clock=time.monotonic):
        self.record, self.save, self.on_stop = record, save, on_stop
        self.reader, self.clock = reader, clock
        self.lock = threading.RLock()
        self.read_lock = threading.RLock()
        self.done = threading.Event()
        self.threads = []
        self.reported = set()
        began = clock()
        self.phase = 'preparation'
        self.deadline = began + PREPARATION_SECONDS
        self.overall_deadline = began + OVERALL_SECONDS
        record['guard_budgets'] = {
            'preparation_seconds': PREPARATION_SECONDS, 'candidate_seconds': CANDIDATE_SECONDS,
            'attempt_seconds': ATTEMPT_SECONDS, 'cleanup_seconds': CLEANUP_SECONDS,
            'overall_seconds': OVERALL_SECONDS, 'sample_seconds': SAMPLE_SECONDS,
            'join_seconds': JOIN_SECONDS, 'started_monotonic': began,
            'preparation_deadline': self.deadline, 'overall_deadline': self.overall_deadline,
            'forced_cleanup_seconds': FORCED_CLEANUP_SECONDS,
            'hard_exit_deadline': self.overall_deadline + FORCED_CLEANUP_SECONDS}

    def begin_attempt(self):
        with self.lock:
            now = self.clock()
            if self.phase != 'preparation' or now >= self.deadline or self.record.get('guard_stop'):
                raise GuardStopped('ATTEMPT_NOT_ADMITTED')
            self.phase = 'attempt'
            self.deadline = now + ATTEMPT_SECONDS
            self.record['guard_budgets'].update(
                attempt_started_monotonic=now, attempt_deadline=self.deadline,
                candidate_budget_seconds=CANDIDATE_SECONDS)
            return self.deadline

    def begin_cleanup(self):
        with self.lock:
            if self.phase != 'cleanup':
                self.phase = 'cleanup'
                self.deadline = min(self.clock() + CLEANUP_SECONDS, self.overall_deadline)
                self.record['guard_budgets']['cleanup_deadline'] = self.deadline

    def remaining(self):
        with self.lock:
            return max(0, min(self.deadline, self.overall_deadline) - self.clock())

    def _expired(self):
        now = self.clock()
        if now >= self.overall_deadline:
            return 'overall', self.overall_deadline
        if now >= self.deadline:
            return self.phase, self.deadline
        return None

    def _stop(self, reason, frame, stage, expired=None):
        with self.lock:
            key = (reason, expired[0] if expired else None)
            if key in self.reported:
                return
            self.reported.add(key)
            event = {'reason': reason, 'stage': stage, 'phase': self.phase,
                     'decision_monotonic': self.clock(), 'frame': deepcopy(frame)}
            if expired:
                event.update(limit=expired[0], deadline=expired[1], frame_is_last_completed=True)
            self.record.setdefault('guard_stop', deepcopy(event))
            self.record.setdefault('guard_events', []).append(deepcopy(event))
        try:
            self.save({'stop': deepcopy(event)})
        except Exception as error:
            self.record['guard_evidence_error'] = type(error).__name__
        finally:
            try:
                self.on_stop(deepcopy(event))
            except Exception as error:
                self.record['guard_callback_error'] = type(error).__name__

    def sample(self, stage):
        with self.read_lock:
            if self.done.is_set():
                raise GuardStopped('MONITOR_CLOSED')
            capture_started = self.clock()
            try:
                frame = self.reader()
                reason = temperature_reason(frame)
            except Exception as error:
                frame = {'error': {'reason': 'MONITOR_ERROR', 'type': type(error).__name__},
                         'cpu': [], 'gpu': None, 'cpu_max_c': None, 'gpu_max_c': None,
                         'started_monotonic': capture_started,
                         'finished_monotonic': self.clock()}
                reason = 'MONITOR_ERROR'
            frame = deepcopy(frame)
            frame['stage'] = stage
            with self.lock:
                frame['phase'] = self.phase
                self.record['guard_last_frame'] = deepcopy(frame)
                expired = self._expired()
            try:
                self.save({'frame': deepcopy(frame)})
            except Exception as error:
                self.record['guard_evidence_error'] = type(error).__name__
                reason = reason or 'MONITOR_ERROR'
            if reason:
                self._stop(reason, frame, stage)
            if expired:
                self._stop('TEST_LIFETIME_EXCEEDED', frame, stage, expired)
            return frame

    def audit(self, stage):
        frame = self.sample(stage)
        if self.record.get('guard_stop'):
            raise GuardStopped(self.record['guard_stop']['reason'])
        return frame

    def check_deadline(self):
        if self.done.is_set():
            return
        with self.lock:
            expired = self._expired()
            frame = deepcopy(self.record.get('guard_last_frame'))
        if expired:
            self._stop('TEST_LIFETIME_EXCEEDED', frame, 'WATCHDOG', expired)

    def start(self):
        if self.threads or self.done.is_set():
            raise RuntimeError('MONITOR_ALREADY_STARTED_OR_CLOSED')

        def watch():
            while not self.done.is_set():
                try:
                    self.sample('WATCH')
                except GuardStopped:
                    return
                self.done.wait(SAMPLE_SECONDS)

        def watchdog():
            while not self.done.is_set():
                self.check_deadline()
                self.done.wait(0.1)

        for name, target in [('thermal', watch), ('deadline', watchdog)]:
            thread = threading.Thread(target=target, name='cold-test-' + name, daemon=True)
            self.threads.append(thread)
            thread.start()

    def snapshot(self):
        with self.lock:
            return {key: deepcopy(self.record[key]) for key in (
                'guard_budgets', 'guard_last_frame', 'guard_stop', 'guard_events',
                'guard_monitor_joined', 'guard_evidence_error', 'guard_callback_error')
                if key in self.record}

    def close(self):
        self.check_deadline()
        self.done.set()
        deadline = time.monotonic() + JOIN_SECONDS
        for thread in self.threads:
            thread.join(max(0, deadline - time.monotonic()))
        joined = all(not thread.is_alive() for thread in self.threads)
        self.record['guard_monitor_joined'] = joined
        if not joined:
            self._stop('MONITOR_ERROR', self.record.get('guard_last_frame'), 'MONITOR_JOIN')
        return joined
