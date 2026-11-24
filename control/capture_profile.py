"""Validate the existing snapshot wrapper without bypassing its native guards."""
import ast
import shlex

from scripts import build_profile_snapshot_launcher as launcher


def command(raw, libraries, executable):
    if type(raw) is not bytes or not 0 < len(raw) <= 16384:
        raise ValueError('CAPTURE_PROFILE_WRAPPER')
    values = {}
    for statement in ast.parse(raw).body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name) and target.id in ('COMMAND', 'READ_ONLY'):
                if target.id in values:
                    raise ValueError('CAPTURE_PROFILE_WRAPPER')
                values[target.id] = ast.literal_eval(statement.value)
    if set(values) != {'COMMAND', 'READ_ONLY'} or type(values['COMMAND']) is not str:
        raise ValueError('CAPTURE_PROFILE_WRAPPER')
    arguments = shlex.split(values['COMMAND'])
    launcher.validate_launcher(raw, arguments, read_only=values['READ_ONLY'])
    if (arguments[0] != executable or len(libraries) != 1 or
            libraries[0]['path'] != arguments[-1]):
        raise ValueError('CAPTURE_PROFILE_BINDING')
    return arguments
