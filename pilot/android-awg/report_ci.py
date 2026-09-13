"""Expose bounded synthetic Android test diagnostics in public CI annotations."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]

def clean(value):
    # No raw profiles, fixture payloads, long encodings or unbounded log output.
    value = re.sub(r'[A-Za-z0-9+/=_-]{40,}', '[redacted]', str(value))
    return value[:1200]

def report(root):
    suites = []
    failures = []
    for path in sorted((root/'clients/android/app/build/outputs/androidTest-results').rglob('*.xml')):
        try: tree = ET.parse(path)
        except (OSError, ET.ParseError): continue
        for case in tree.iter('testcase'):
            suites.append(case.get('classname', '')+'.'+case.get('name', ''))
            for kind in ('failure', 'error'):
                for failure in case.findall(kind):
                    lines = (failure.text or '').splitlines()
                    frames = [line.strip() for line in lines if 'com.familyconnect.' in line][:5]
                    failures.append(dict(test=suites[-1],kind=kind,
                        message=clean(failure.get('message') or (lines[0] if lines else '')),
                        frames=[clean(frame) for frame in frames]))
    hints = []
    for name in ('android-tcp-runner.log', 'android-awg-runtime.log'):
        path=root/name
        if not path.is_file(): continue
        lines=path.read_text(errors='replace').splitlines()
        for line in lines:
            if any(marker in line for marker in ('FAILED', 'AssertionError', 'Caused by:', 'What went wrong', 'tests completed', 'ProcessException', 'TimeoutError')):
                hints.append(clean(line))
    return dict(instrumentation_cases=len(suites),failures=failures[:12],hints=hints[-12:])

if __name__ == '__main__':
    data=report(ROOT)
    (ROOT/'android-ci-summary.json').write_text(json.dumps(data,indent=2)+'\n')
    text=json.dumps(data,separators=(',',':'))
    for old,new in (('%','%25'),('\r','%0D'),('\n','%0A')):text=text.replace(old,new)
    print('::notice title=Android runtime test summary::'+text)
