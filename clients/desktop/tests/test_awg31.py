import base64
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import backend
from profile_config import parse, validate, AWG_FIELDS
from test_awg import PROFILE

ROOT=Path(__file__).resolve().parents[3]
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

HELPER=module('awg_helper_test','clients/linux/awg-helper.py')
BUNDLE=module('awg_bundle_test','clients/linux/check-awg-bundle.py')


def modern():
    fields=parse(PROFILE,allow_awg=True)
    face=fields['Interface'];face['Address']='10.83.42.254/32'
    for i in range(1,5):face['S'+str(i)]='32';face['H'+str(i)]=str(i)
    face.update(HeaderProtectionKey=base64.b64encode(bytes(range(32))).decode(),
                ContentPaddingAddition='0-64',RandomTrailers='true',DisableCookies='false')
    return '\n\n'.join('['+section+']\n'+'\n'.join(k+' = '+v for k,v in values.items()) for section,values in fields.items())+'\n'


def test_modern_import_preserves_full_address_and_helper_gate(tmp_path,monkeypatch):
    path=tmp_path/'profile.conf';path.write_text(modern())
    driver=backend.LinuxTCP();calls=[]
    monkeypatch.setattr(driver,'_awg',lambda action,**kw:calls.append((action,kw['data'])) or 'fcawg12345678')
    assert driver.import_profile(path)=='fcawg12345678'
    assert 'Address = 10.83.42.254/32' in calls[0][1]
    with pytest.raises(ValueError):validate(calls[0][1],allow_awg=True)
    assert validate(calls[0][1],allow_awg=True,allow_awg31=True)


def test_new_fields_without_awg_parameters_cannot_bypass_validation():
    text='\n'.join(line for line in modern().splitlines() if line.split(' = ')[0] not in AWG_FIELDS)
    with pytest.raises(ValueError):validate(text,allow_awg=True,allow_awg31=True)


def test_tools_boolean_translation_roundtrip():
    canonical=validate(modern(),allow_awg=True,allow_awg31=True)
    native=HELPER.quick_flags(canonical,native=True)
    assert 'RandomTrailers = on\n' in native and 'DisableCookies = off\n' in native
    assert HELPER.quick_flags(native,native=False)==canonical
    assert HELPER.quick_flags(PROFILE,native=True)==PROFILE


def test_bundle_tampering_and_unpinned_build_rejected(tmp_path):
    record=dict(schema=1,engine='b5928efb6ca19f0153958460c3d141f04abc5c2e',tools='ee0f0a9aa34ff0a0da4b3433b9512781cfe02843',files={})
    for name in ('awg','amneziawg-go','awg-quick'):
        (tmp_path/name).write_bytes(b'synthetic binary');record['files'][name]=hashlib.sha256(b'synthetic binary').hexdigest()
    marker=tmp_path/'awg31.json';marker.write_text(json.dumps(record));BUNDLE.check(tmp_path)
    (tmp_path/'awg').write_bytes(b'changed')
    with pytest.raises(ValueError):BUNDLE.check(tmp_path)
    (tmp_path/'awg').write_bytes(b'synthetic binary');record['engine']='old-engine';marker.write_text(json.dumps(record))
    with pytest.raises(ValueError):BUNDLE.check(tmp_path)
