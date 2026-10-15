import json
import tempfile
from pathlib import Path

from credential_renewal import DAY, Rejected, canonical, digest
from test_production_controller import ControllerFixture


def main():
    with tempfile.TemporaryDirectory(prefix='current4h-before-') as directory:
        fixture = ControllerFixture(Path(directory))
        assert fixture.run()['result'] == 'COMMITTED'
        fixture.nodes.now += 2*DAY
        before = digest(canonical(fixture.actual()))
        outcomes = {}
        for name, action in (
            ('authority_request', lambda: fixture.nodes.nodes['RU'].authority_request('before-expired-operation-0002')),
            ('operator', lambda: fixture.controller.run('before-expired-operation-0002')),
            ('scheduled', lambda: fixture.controller.run('before-expired-operation-0002', scheduled=True))):
            try:
                action()
            except Exception as error:
                outcomes[name] = str(error) if isinstance(error, Rejected) else 'UNKNOWN'
            else:
                raise AssertionError('expired predecessor unexpectedly admitted')
            assert digest(canonical(fixture.actual())) == before
        print(json.dumps(dict(result='EXPIRED_PREDECESSOR_REPRODUCED', outcomes=outcomes, credential_mutations=0,
                              production_inputs=0), sort_keys=True))


if __name__ == '__main__':
    main()
