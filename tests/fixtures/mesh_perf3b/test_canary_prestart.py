import importlib.util
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location('canary_prestart', Path(__file__).with_name('canary_prestart.py'))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def fixture():
    manifest = dict(uid=979,gid=979,user='gateway',working_directory='/test/state',
                    environment={'FC_PERF_OWNER_GUARD':'/test/state/guard'},executable_arguments=['/test/candidate','--duration','2h'])
    environment = dict(manifest['environment'],YANDEX_TELEMOST_OAUTH_TOKEN='synthetic')
    properties = dict(EnvironmentFiles=validator.PROVIDER+' (ignore_errors=no)',User='gateway',Group='979',
                      WorkingDirectory='/test/state',Restart='no',ReadWritePaths='/test/state',ProtectSystem='strict',
                      UnsetEnvironment='',Environment='FC_PERF_OWNER_GUARD=/test/state/guard',
                      ExecStart='{ path=/test/candidate ; argv[]=/test/candidate --duration 2h ; ignore_errors=no ; }')
    info = SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=0)
    return manifest,environment,properties,info


def test_same_unit_environment_passes_without_network_or_payload():
    manifest,environment,properties,info = fixture()
    assert validator.validate(manifest,environment,properties,979,979,info)=='PASS'


@pytest.mark.parametrize('value',[None,'','  '])
def test_missing_or_empty_token_fails(value):
    manifest,environment,properties,info = fixture()
    if value is None:
        del environment[validator.REQUIRED]
    else:
        environment[validator.REQUIRED]=value
    assert validator.validate(manifest,environment,properties,979,979,info)=='PROVIDER_VARIABLE_EMPTY_OR_ABSENT'


def test_missing_file_fails():
    manifest,environment,properties,info = fixture()
    assert validator.validate(manifest,environment,properties,979,979,None)=='PROVIDER_FILE_MISSING'


@pytest.mark.parametrize('key,value',[
    ('EnvironmentFiles',''),('Restart','always'),('WorkingDirectory','/production'),
    ('ReadWritePaths','/production'),('User','root'),('UnsetEnvironment',validator.REQUIRED),
    ('ExecStart','{ path=/wrong ; argv[]=/wrong ; ignore_errors=no ; }'),
    ('Environment','FC_PERF_OWNER_GUARD=/test/state/guard YANDEX_TELEMOST_OAUTH_TOKEN='),
])
def test_wrong_final_unit_fails(key,value):
    manifest,environment,properties,info = fixture()
    properties[key]=value
    assert validator.validate(manifest,environment,properties,979,979,info)!='PASS'


def test_transport_environment_cannot_leak_from_production():
    manifest,environment,properties,info = fixture()
    environment['FC_DIAGNOSTIC_CONTROL_DIR']='/production'
    assert validator.validate(manifest,environment,properties,979,979,info)=='UNEXPECTED_TRANSPORT_ENVIRONMENT'
