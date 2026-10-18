#!/usr/bin/env python3
"""Check build output and local links before a Pages artifact may deploy."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import sys

ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.links=[];self.viewport=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.add(a['id'])
  if tag=='meta' and a.get('name')=='viewport':self.viewport='width=device-width' in a.get('content','')
  for key in ('src','href'):
   if key in a:self.links.append(a[key])
def check(root=ROOT):
 site=Path(root)/'_site';pages={};errors=[]
 expected={'index','about','research','publications','projects','group','teaching','service','talks','news','contact','cv'}
 for name in expected:
  f=site/(name+'.html')
  if not f.is_file():errors.append('Missing page: '+name);continue
  page=Page();page.feed(f.read_text());pages[f.resolve()]=page
  if not page.viewport:errors.append('Missing mobile viewport: '+name)
  if '```update' in f.read_text():errors.append('Editing document leaked into public page: '+name)
 for f,page in pages.items():
  for link in page.links:
   parsed=urlsplit(link)
   if parsed.scheme or parsed.netloc:continue
   path=unquote(parsed.path)
   target=(site/path.lstrip('/')) if path.startswith('/') else f.parent/path
   if not path:target=f
   target=target.resolve()
   if not target.exists():errors.append(f'{f.name}: missing {link}')
   elif parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:errors.append(f'{f.name}: unknown section {link}')
 if (site/'UPDATE-WEBSITE.html').exists() or (site/'README.html').exists():errors.append('Internal editing documents must not be public pages.')
 if errors:raise ValueError('\n'.join(errors))
 (site/'.nojekyll').touch()
 print(f'Build validation passed: {len(pages)} pages, mobile metadata, and all local links.')
if __name__=='__main__':
 try:check()
 except ValueError as e:print('BUILD VALIDATION ERROR: '+str(e),file=sys.stderr);sys.exit(1)
