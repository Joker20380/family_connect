from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def test_windows_installer_version_is_supplied_by_project_not_a_second_literal():
    project = ET.parse(ROOT / 'clients/windows/FamilyConnect.csproj')
    versions = project.findall('./PropertyGroup/Version')
    assert len(versions) == 1 and re.fullmatch(r'\d+\.\d+\.\d+', versions[0].text)
    setup = (ROOT / 'clients/windows/setup.iss').read_text()
    assert '#ifndef AppVersion\n#error ' in setup
    assert '\nAppVersion={#AppVersion}\n' in setup
    assert 'OutputBaseFilename=FamilyConnect-Setup-{#AppVersion}-{#BuildLabel}\n' in setup
    build = (ROOT / 'clients/windows/build.ps1').read_text()
    assert '[xml]$project=Get-Content FamilyConnect.csproj -Raw' in build
    assert '$version=[string]$versions[0]' in build
    assert '$argsList=@("/DAppVersion=$version",\'setup.iss\')' in build
    assert '"dist/FamilyConnect-Setup-$version-signed.exe"' in build
