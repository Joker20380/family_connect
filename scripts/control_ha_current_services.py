"""Check native service snapshot/start-intent content; never call systemd."""
import math
import re

from scripts.control_ha_import import require
from scripts.control_ha_recovery_bundle import parse

FIELDS = {'ActiveState', 'SubState', 'MainPID', 'InvocationID', 'NRestarts', 'Result'}
STATES = {'active', 'activating', 'inactive', 'failed', 'deactivating', 'reloading', 'maintenance', 'refreshing'}


def inspect_services(files, units, slot, issued, completed):
    suffixes = ('.service', '.timer', '.service', '.timer', '.service') if slot == 'RU' else ('.service',)
    require(type(units) in (list, tuple) and len(units) == len(suffixes) and all(
        type(unit) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}', unit)
        and unit.endswith(suffix) for unit, suffix in zip(units, suffixes)), 'CURRENT_UNIT_CONFIG')
    require(len(set(units)) == len(units), 'CURRENT_UNIT_CONFIG')
    before = parse(files['services-before.json'])
    require(type(before) is dict and set(before) == set(units), 'CURRENT_SERVICE_COHORT')
    expected = {'services-before.json'}
    for index, unit in enumerate(units):
        state = before[unit]
        require(type(state) is dict and {'ActiveState', 'SubState'} <= set(state) <= FIELDS and
            all(type(value) is str and len(value) <= 256 for value in state.values()) and
            state['ActiveState'] in STATES and bool(state['SubState']), 'CURRENT_SERVICE_STATE')
        if unit.endswith('.service'):
            require(type(state.get('MainPID')) is str and re.fullmatch('[0-9]{1,20}', state['MainPID']),
                    'CURRENT_SERVICE_PID')
        start = (slot != 'RU' or index in (0, 3)) and (state['ActiveState'] in ('active', 'activating')
                or (slot != 'RU' and state['ActiveState'] == 'failed'))
        if start:
            name = 'start-intent-' + str(index) + '.json'
            expected.add(name)
            intent = parse(files[name])
            require(type(intent) is dict and set(intent) == {'schema', 'unit', 'timestamp'} and
                type(intent['schema']) is int and intent['schema'] == 1 and intent['unit'] == unit,
                'CURRENT_START_INTENT')
            timestamp = intent['timestamp']
            require(type(timestamp) in (int, float) and math.isfinite(timestamp) and
                issued <= timestamp < completed + 1, 'CURRENT_START_TIME')
    observed = {name for name in files if name == 'services-before.json' or name.startswith('start-intent-')}
    require(observed == expected, 'CURRENT_START_COVERAGE')
    return expected
