import pytest

from scripts.check_friends_execstart import matches


EXPECTED = ['/runtime/python', '-I', '/artifacts/accepted.pyz', '--port', '18086']


@pytest.mark.parametrize('case', ['same', 'quoted', 'shadowed', 'wrong_port', 'extra_argument', 'extra_command', 'wrong_executable', 'malformed'])
def test_effective_execstart_is_required_not_dropin_presence(case):
    arguments = EXPECTED.copy()
    executable = arguments[0]
    if case == 'shadowed': arguments[2] = '/artifacts/previous.pyz'
    if case == 'wrong_port': arguments[-1] = '18084'
    if case == 'extra_argument': arguments += ['--unexpected']
    if case == 'wrong_executable': executable = '/other/python'
    text = ' '.join('"' + value + '"' for value in arguments) if case == 'quoted' else ' '.join(arguments)
    description = '{ path=' + executable + ' ; argv[]=' + text + ' ; ignore_errors=no ; pid=123 ; status=0/0 }'
    if case == 'extra_command': description += description
    if case == 'malformed': description = 'ExecStart=' + text
    assert matches(description, EXPECTED) == (case in ('same', 'quoted'))
