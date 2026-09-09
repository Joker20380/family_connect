import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('profile_config',Path(__file__).parents[1]/'profile_config.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
PROFILE='''[Interface]
PrivateKey = AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
Address = 10.77.0.3/32
DNS = 1.1.1.1
[Peer]
PublicKey = AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=
Endpoint = 185.251.89.19:51820
AllowedIPs = 0.0.0.0/0, ::/0
'''


def test_full_tunnel_roundtrip():
    assert module.validate(module.validate(PROFILE))==module.validate(PROFILE)


@pytest.mark.parametrize('bad',[
    PROFILE.replace('Address =','PostUp = arbitrary command\nAddress ='),
    PROFILE.replace(', ::/0',''),
    PROFILE+'[Peer]\nPublicKey = bad\n',
    PROFILE.replace('DNS = 1.1.1.1','DNS = example.com'),
    PROFILE.replace(':51820',':99999'),
    PROFILE.replace('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=','secret'),
    PROFILE+'#'+'x'*17000])
def test_rejects_unsafe_or_incomplete_profiles(bad):
    with pytest.raises(ValueError):module.validate(bad)
