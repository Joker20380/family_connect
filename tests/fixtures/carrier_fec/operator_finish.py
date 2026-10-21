from lab import *


def main():
    operator=WORK/'run_phase.py'
    replace(operator,"bundle.add(source,arcname=name)","bundle.add(source,arcname=name)\n            bundle.add(SOURCE/'licenses',arcname='licenses')")
    replace(operator,'from lab import ROOT, WORK, FIX, digest','from lab import ROOT, WORK, FIX, SOURCE, digest')
    replace(operator,"assert {member.name for member in archive.getmembers()}=={'telemost-capacity','family.json','room.input','capacity.json','worker.py'}", "assert all(member.name in {'telemost-capacity','family.json','room.input','capacity.json','worker.py','licenses'} or member.name.startswith('licenses/') for member in archive.getmembers())")
    replace(operator,"path.chmod(0o700 if path.name=='telemost-capacity' else 0o600)","path.chmod(0o700 if path.name=='telemost-capacity' or path.is_dir() else 0o600)")
    build=json.loads((WORK/'build.json').read_text());build['operator_sha256']=digest(operator)
    write(WORK/'build.json',json.dumps(build,indent=2)+'\n')
    save(WORK/'operator-amendment.json',dict(before_live=True,licenses_included=True,operator_sha256=digest(operator)))


if __name__=='__main__':main()
