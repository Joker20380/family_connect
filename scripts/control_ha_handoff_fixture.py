"""Native-format synthetic legacy and successor history; no installed state inputs."""
import importlib.util
from pathlib import Path

from scripts.control_ha_handoff_import import manifest
from scripts.control_ha_import import digest, require
from scripts.control_ha_sqlite_fixture import joint_fixture, refresh_fixture
from scripts.referral_postgres_rehearsal import NOW
from scripts.restricted_postgres_rehearsal import issue_proof


def closed_handoff_fixture(root):
    fixture = joint_fixture(root)
    pin = manifest()
    source = Path(__file__).resolve().parents[1] / pin['source']
    require(digest(source.read_bytes()) == pin['source_sha256'], 'HANDOFF_FIXTURE_SOURCE_CHANGED')
    spec = importlib.util.spec_from_file_location('control.friends.owner_handoff', source)
    handoff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handoff)
    response = fixture.service.fetch(issue_proof(fixture.service, fixture.device))
    saved = handoff.encode(handoff.floor(response))
    legacy_ddl = next(row[3] for row in pin['definitions'] if row[1] == 'restricted_owner_handoff')
    with fixture.access.db() as database:
        database.execute(legacy_ddl)
        database.execute('INSERT INTO restricted_owner_handoff VALUES (1,?,?,?,?,?,?,?,?,?,?,?)',
            ('retired-first', fixture.device.reference, 'a' * 32, 'b' * 32, 'CLEANED', NOW + 2400,
             '', None, None, saved, 'synthetic-fetch-first'))
        handoff.migrate(database)
        handoff.prepare(database, 'retired-second', fixture.device.reference, 'a' * 32, 'b' * 32, NOW + 2401, NOW)
        handoff.record_floor(database, response, fixture.device.reference, 'a' * 32, 'b' * 32,
                             'retired-second', 2, 'synthetic-fetch-second')
        database.execute("UPDATE restricted_owner_handoff_operations SET phase='CLEANED',captured=1 WHERE generation=2")
    refresh_fixture(fixture)
    return fixture
