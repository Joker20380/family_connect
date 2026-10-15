import argparse
import json
import os
from pathlib import Path
import subprocess

from apply import reconstruct
from package import build


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--go', type=Path, required=True)
    parser.add_argument('--gopath', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--build-disk', type=Path)
    args = parser.parse_args()
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    root = Path(__file__).resolve().parent
    base = reconstruct(args.archive, args.out/'base', before=True)
    source = reconstruct(args.archive, args.out/'source')
    disk = args.build_disk or args.out
    (disk/'go-tmp').mkdir(mode=0o700, parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(source/'controller')+':'+str(source/'api'),
        GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off', GOCACHE=str(disk/'go-cache'),
        GOTMPDIR=str(disk/'go-tmp'), GOPATH=str(args.gopath))
    for name in ('GOFLAGS', 'FC_FAMILY_TEST_FIXTURES', 'FC_TELEMOST_ROOM', 'YANDEX_TELEMOST_OAUTH_TOKEN'):
        env.pop(name, None)
    runs = []
    def run(name, command, cwd, environment=env):
        with (args.out/(name+'.log')).open('wb') as log:
            result = subprocess.run(command, cwd=cwd, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
        runs.append(dict(name=name, exit_code=result.returncode, command=[str(item) for item in command]))
        (args.out/'runs.json').write_text(json.dumps(runs, indent=2)+'\n')
        if result.returncode:
            raise SystemExit('fixed run failed; preserve receipts, do not retry until pass')
    before_env = dict(env, PYTHONPATH=str(base/'controller')+':'+str(base/'api'))
    before_script = root/'changed/controller/characterize_expired.py'
    run('before', [args.python, '-c', 'import runpy;runpy.run_path('+repr(str(before_script))+',run_name="__main__")'], base, before_env)
    run('full', [args.python, '-m', 'pytest', '-q', 'controller', '--basetemp='+str(args.out/'pytest-full')], source)
    for iteration in range(1, 4):
        run('fault-'+str(iteration), [args.python, '-m', 'pytest', '-q', 'controller/test_expired_recovery.py',
            '-k', 'partial_node_writes_resume', '--basetemp='+str(args.out/('pytest-fault-'+str(iteration)))], source)
    binaries = {}
    for label, count, flags in [('normal', 1, []), ('race', 3, ['-race'])]:
        binaries[label] = disk/('family-'+label+'.test')
        run('build-'+label, [args.go, 'test', '-p=1', '-c', '-o', binaries[label], *flags, './familysession'], source/'gateway')
    vectors = args.out/'vectors'
    run('vectors', [args.python, 'controller/recovery_vectors.py', vectors], source)
    env['FC_EXPIRED_RECOVERY_FIXTURE'] = str(vectors/'vectors.json')
    for label, count in [('normal', 1), ('race', 3)]:
        run('family-'+label, [binaries[label], '-test.v', '-test.count='+str(count), '-test.timeout=180s',
            '-test.run=^TestExpiredRecoveryStrictFamilyTLS$'], source/'gateway')
    source_identity = build(source, args.out/'management')
    print(json.dumps(dict(result='RECOVERY_PATH_IMPLEMENTED_AND_LOCALLY_VERIFIED',
        management_source_sha256=source_identity, production_actions=0)))


if __name__ == '__main__':
    main()
