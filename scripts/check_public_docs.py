"""Check the public landing pages and guides; standard library only.

Validates local Markdown links, heading anchors and HTML image paths.
Lists external URLs for a separate HTTP check; does not claim network validation.
Historical reports are outside this public-entry-point check.
"""
from pathlib import Path
import re, urllib.parse, json, sys
ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/p for p in ['README.md','README.en.md','README.ru.md','SECURITY.md','CONTRIBUTING.md']]
files += [ROOT/'docs'/p for p in ['README.md','architecture.md','getting-started.en.md','getting-started.ru.md','clients.en.md','clients.ru.md','privacy.md','licensing.md','releases.md','assets/README.md']]
files += [ROOT/'.github/pull_request_template.md',ROOT/'.github/ISSUE_TEMPLATE/bug_report.md']
if len(sys.argv) > 1:
 files = [ROOT / arg for arg in sys.argv[1:]]
def anchors(p):
 text=p.read_text();result=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+?)\s*#*$',text,re.M):
  slug=re.sub(r'[^\w\- ]','',title.lower()).replace(' ','-');count=counts.get(slug,0);counts[slug]=count+1;result.add(slug+(f'-{count}' if count else ''))
 result.update(re.findall(r'(?:id|name)=["\']([^"\']+)',text));return result
errors=[];external=set();count=0
for p in files:
 text=re.sub(r'```.*?```','',p.read_text(),flags=re.S)
 links=re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',text)+re.findall(r'<img[^>]+src="([^"]+)"',text)
 for target in links:
  count+=1;target=target.strip('<>');u=urllib.parse.urlsplit(target)
  if u.scheme in ('https','http'):external.add(target);continue
  if u.scheme:continue
  dest=(p.parent/urllib.parse.unquote(u.path)).resolve() if u.path else p
  if not dest.exists():errors.append(f'{p.relative_to(ROOT)}: missing {target}')
  elif u.fragment and dest.suffix=='.md' and urllib.parse.unquote(u.fragment) not in anchors(dest):errors.append(f'{p.relative_to(ROOT)}: missing anchor {target}')
print(json.dumps({'files':len(files),'links':count,'external':sorted(external),'errors':errors},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
