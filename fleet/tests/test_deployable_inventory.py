from pathlib import Path

from fleet.contracts import canonical, digest, load
from fleet.provenance import validate
from fleet.role_config import DISABLED, ROLES
import pytest
from fleet.contracts import FleetError


def test_v2_preserves_native_source_bindings_and_exact_roles():
    root=Path(__file__).parents[1]
    native=validate(load((root/'inventory/deployable-gateway-v1.json').read_bytes()))
    deployable=validate(load((root/'inventory/deployable-gateway-v2.json').read_bytes()))
    by_id={artifact['id']:artifact for artifact in deployable['artifacts']}
    for original in native['artifacts']:
        for field in ('path','sha256','size','source_commit','source_inventory_sha256','license','receipt','architecture'):
            assert by_id[original['id']][field]==original[field]
    assert {role for artifact in deployable['artifacts'] for role in artifact['roles']}==set(ROLES)
    assert set(deployable['disabled_roles'])==set(DISABLED)
    monitor=by_id['rehearsal-monitoring']
    source=(root/'monitoring.py').read_bytes()
    assert digest(source)==monitor['sha256'] and len(source)==monitor['size']
    assert digest(canonical(dict(source_commit=monitor['source_commit'],files={'fleet/monitoring.py':digest(source)})))==monitor['source_inventory_sha256']
    assert monitor['listeners']==['tcp:127.0.0.1:19727'] and monitor['secret_slots']==[]


def test_python_dependencies_are_exact_architecture_and_license_bound():
    root=Path(__file__).parents[1]
    dependencies=load((root/'inventory/python-rehearsal.json').read_bytes())
    assert dependencies['python']=='3.12' and dependencies['architecture']=='x86_64'
    assert len(dependencies['wheels'])==3
    for record in dependencies['wheels']:
        assert record['path'].startswith('dependencies/') and record['path'].endswith('.whl')
        assert len(record['sha256'])==64 and record['size']>0 and record['license']


@pytest.mark.parametrize('field',['patch_sha256','source_inventory_sha256'])
def test_operator_cache_requires_exact_reviewed_source_before_use(tmp_path,field):
    from fleet.package import GO_IMAGE, operator_probe
    expected=dict(patch_sha256=digest(b'patch'),source_inventory_sha256=digest(canonical({})),compiler_image=GO_IMAGE)
    expected[field]='a'*64
    with pytest.raises(FleetError,match='operator_probe_source_binding'):
        operator_probe({},b'patch',tmp_path,expected=expected,cache=tmp_path/'cache')
