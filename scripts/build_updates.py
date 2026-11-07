#!/usr/bin/env python3
"""Build website pages from preserved content and one plain-text update document."""
from pathlib import Path
from datetime import date, datetime
import argparse
import html
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r'::: \{\.record-row\}\s*\n::: \{\.record-label\}\n(.*?)\n:::\s*\n::: \{\.record-body\}\n(.*?)\n:::\s*\n:::', re.S)
PUB = re.compile(r'::: \{\.publication-entry\}\n(.*?)\n:::', re.S)
FIELDS = {
 'service': {'title','details','period','section','url','announce','date','id','action'},
 'news': {'title','date','details','url','id','action'},
 'publication': {'title','authors','journal','year','doi','url','details','category','announce','date','id','action'},
 'student': {'name','programme','status','topic','year','endyear','photo','position','details','announce','date','id','action'},
 'talk': {'title','date','enddate','event','kind','details','announce','id','action'},
 'project': {'title','agency','role','year','endyear','status','funding','kind','details','announce','date','id','action'},
 'teaching': {'code','title','level','semesters','details','id','action'},
 'award': {'title','year','details','announce','date','id','action'},
 'profile': {'field','text','id'},
 'page': {'page','find','replace','id'},
}
REQUIRED = {'service':['title','details','period'], 'news':['title','date','details'], 'publication':['title','authors','journal','year'],
 'student':['name','programme','status','topic'], 'talk':['title','date','event'],
 'project':['title','agency','role','year','status'], 'teaching':['code','title','level','semesters'],
 'award':['title','year','details'], 'profile':['field','text'], 'page':['page','find','replace']}

def norm(s):
 s = re.sub(r'<[^>]+>|https?://\S+', ' ', html.unescape(s))
 s = re.sub(r'\b(?:mr|ms|mrs|dr|prof)\b\.?', '', s, flags=re.I)
 return re.sub(r'[^a-z0-9]+',' ',s.casefold()).strip()

def plain(s):
 # Inline fields cannot introduce raw HTML, Quarto directives, or new fenced blocks.
 return html.escape(re.sub(r'\s+', ' ', s).strip(), quote=False).replace('`','\\`')

def url(s):
 s=s.strip()
 if not re.fullmatch(r'https?://[^\s<>"\[\]()]+',s):
  raise ValueError('Links must be complete http:// or https:// addresses without spaces or brackets.')
 return s

def parse_date(s):
 s=s.strip()
 for fmt in ('%Y-%m-%d','%d %B %Y','%d %b %Y','%B %Y','%b %Y','%Y'):
  try:return datetime.strptime(s,fmt).date()
  except ValueError:pass
 raise ValueError(f'Date "{s}" is not recognized. Use YYYY-MM-DD, e.g. 2026-10-18.')

def year(s):
 if not re.fullmatch(r'(19|20|21)\d{2}',s.strip()):raise ValueError('Year must contain four digits.')
 return int(s)

def parse_updates(document):
 records=[]
 for n,match in enumerate(re.finditer(r'^```update\s*\n(.*?)^```\s*$',document,re.M|re.S),1):
  fields={};last=None
  for line in match[1].splitlines():
   if not line.strip() or line.lstrip().startswith('#'):continue
   m=re.match(r'^([A-Za-z][A-Za-z ]*):\s*(.*)$',line)
   if m:
    key=m[1].lower().replace(' ','');value=m[2].strip()
    if key in fields:raise ValueError(f'Update {n}: repeated field {m[1]}.')
    fields[key]=value;last=key
   elif line[:1].isspace() and last:
    fields[last]+=' '+line.strip()
   else:raise ValueError(f'Update {n}: expected Field: value, or an indented continuation line.')
  kind=fields.pop('type','').lower()
  if kind not in FIELDS:raise ValueError(f'Update {n}: Type must be one of {", ".join(FIELDS)}.')
  unknown=set(fields)-FIELDS[kind]
  if unknown:raise ValueError(f'Update {n}: unknown fields: {", ".join(sorted(unknown))}.')
  action=fields.get('action','update').lower()
  if action not in ('update','remove'):raise ValueError(f'Update {n}: Action must be Update or Remove.')
  required=REQUIRED[kind] if action!='remove' else [REQUIRED[kind][0]]
  for field in required:
   if not fields.get(field):raise ValueError(f'Update {n}: {field.title()} is required.')
  for field in ('year','endyear'):
   if fields.get(field):year(fields[field])
  for field in ('date','enddate'):
   if fields.get(field):parse_date(fields[field])
  if fields.get('enddate') and parse_date(fields['enddate'])<parse_date(fields['date']):raise ValueError('EndDate cannot precede Date.')
  if fields.get('year') and fields.get('endyear') and year(fields['endyear'])<year(fields['year']):raise ValueError('EndYear cannot precede Year.')
  if fields.get('url'):url(fields['url'])
  if fields.get('doi'):
   doi=re.sub(r'^https?://(?:dx\.)?doi.org/','',fields['doi'])
   if not re.fullmatch(r'10\.\d{4,9}/[^\s<>"\[\]()]+',doi):raise ValueError(f'Update {n}: DOI must start with 10., followed by its identifier.')
   fields['doi']=doi
  if fields.get('announce','no').lower() not in ('yes','no'):raise ValueError('Announce must be Yes or No.')
  if fields.get('announce','no').lower()=='yes' and not fields.get('date'):raise ValueError('Date is required when Announce is Yes.')
  fields['type']=kind;fields['action']=action
  records.append(fields)
 if document.count('```update')!=len(records):raise ValueError('An update block is unclosed or incorrectly formatted.')
 # Repeating an explicit ID revises that record instead of applying two copies.
 result=[];ids={}
 for r in records:
  key=(r['type'],r.get('id'))
  if key[1] and key in ids:result[ids[key]]=r
  else:
   if key[1]:ids[key]=len(result)
   result.append(r)
 return result

def row(label,body):
 return '\n::: {.record-row}\n::: {.record-label}\n'+plain(label)+'\n:::\n::: {.record-body}\n'+body+'\n:::\n:::\n'

def find_remove(page,needle,pattern=ROW):
 needle=norm(needle);matches=[m for m in pattern.finditer(page) if needle and needle in norm(m[0])]
 if len(matches)>1:raise ValueError('More than one matching entry found; use a more specific title or name.')
 if not matches:return page,False
 m=matches[0];return page[:m.start()]+page[m.end():],True

def insert_section(page,heading,entry,level=2):
 marker='#'*level+' '+heading
 m=re.search(r'^'+re.escape(marker)+r'(?:\s*\{[^}]+\})?\s*$',page,re.M)
 if m:return page[:m.end()]+'\n\n'+entry+page[m.end():]
 if level!=2:raise ValueError('Missing section: '+heading)
 # Keep numbered publication years in descending order.
 ys=re.search(r'(19|20|21)\d{2}',heading)
 if ys:
  for old in re.finditer(r'^## (.+)$',page,re.M):
   oy=re.search(r'(19|20|21)\d{2}',old[1])
   if oy and int(oy[0])<int(ys[0]):
    return page[:old.start()]+marker+'\n\n'+entry+'\n'+page[old.start():]
 return page.rstrip()+'\n\n'+marker+'\n\n'+entry+'\n'

def dated(r):
 d=parse_date(r['date']);label=d.strftime('%d %B %Y').lstrip('0')
 if r.get('enddate'):label+=' – '+parse_date(r['enddate']).strftime('%d %B %Y').lstrip('0')
 return label

def news_item(title,stamp,details,link=''):
 return '### '+plain(title)+'\n\n**'+plain(stamp)+'** · '+plain(details)+((' [Read more]('+link+')') if link else '')+'\n\n'

def compile_pages(base,records,root=ROOT):
 pages=dict(base);news=[]
 original=pages['_latest-updates']
 for m in re.finditer(r'^### ([^\n]+)\n(.*?)(?=^### |^:::\s*$|\Z)',original,re.M|re.S):
  news.append((m[1],m[0].strip()+'\n\n'))
 for r in records:
  k=r['type'];remove=r.get('action')=='remove';P=lambda key:plain(r.get(key,''));entry='';target=None;section=None
  if k=='news':
   news=[(name,body) for name,body in news if norm(name)!=norm(r['title'])]
   if not remove:news.insert(0,(r['title'],news_item(r['title'],dated(r),r['details'],r.get('url',''))))
   continue
  if k=='profile':
   text=plain(r['text'])
   if r['field'].lower()=='research-introduction':
    pages['index'],count=re.subn(r'(<section class="research-introduction"[^>]*>.*?<p>).*?(</p>)',lambda m:m[1]+text+m[2],pages['index'],count=1,flags=re.S)
   elif r['field'].lower()=='biography':
    page=pages['about'];fm=re.search(r'\A---\n.*?\n---\n',page,re.S);end=page.index('\n## ',fm.end())
    pages['about']=page[:fm.end()]+'\n'+text+'\n'+page[end:];count=1
   else:raise ValueError('Profile Field must be research-introduction or biography.')
   if count!=1:raise ValueError('Could not locate the profile paragraph; no pages have been written.')
   continue
  if k=='page':
   name=r['page'].removesuffix('.qmd')
   if name not in pages:raise ValueError('Unknown Page: '+name)
   if pages[name].count(r['find'])!=1:raise ValueError('Page Find must match exactly once. No pages have been written.')
   pages[name]=pages[name].replace(r['find'],r['replace'],1);continue
  if remove:
   targets={'publication':'publications','student':'group','talk':'talks','project':'projects','teaching':'teaching','award':'about','service':'service'}
   target=targets[k];needle=r[REQUIRED[k][0]]
   pages[target],found=find_remove(pages[target],needle,PUB if k=='publication' else ROW)
   if not found:raise ValueError('Cannot remove an entry that was not found: '+needle)
   continue
  if k=='publication':
   target='publications';category=r.get('category','journal').lower()
   categories={'journal':'Journal Articles – '+r.get('year',''),'preprint':'Preprints (arXiv)','chapter':'Book Chapter – '+r.get('year',''),'patent':'Patents'}
   if category not in categories:raise ValueError('Publication Category: Journal, Preprint, Chapter, or Patent.')
   section=categories[category];pages[target],found=find_remove(pages[target],r['title'],PUB)
   link=('https://doi.org/'+r['doi']) if r.get('doi') else r.get('url','')
   body=P('authors')+'. “'+P('title')+'.” *'+P('journal')+'* ('+P('year')+').'+((' [Read publication]('+link+')') if link else '')
   if r.get('details'):body+=' '+P('details')
   entry='::: {.publication-entry}\n'+body+'\n:::\n'
  elif k=='student':
   target='group';programme=r.get('programme','PhD').lower().replace('.','').replace(' ','');status=r.get('status','current').lower()
   if status not in ('current','alumni'):raise ValueError('Student Status must be Current or Alumni.')
   if programme in ('phd','doctoral'):section='Ph.D. Graduates' if status=='alumni' else 'Ph.D. Scholars (ongoing)'
   elif programme in ('postdoc','postdoctoral','ms','ms(research)'):section='Postdoctoral and M.S. research'
   elif programme in ('msc','mtech','masters','project'):section='Master’s and project students'
   else:raise ValueError('Student Programme must be PhD, Postdoc, MS, MSc, MTech, or Project.')
   pages[target],found=find_remove(pages[target],r['name'])
   # Prevent adding a duplicate of a name in the legacy plain-text supervision list.
   if not found and norm(r['name']) in norm(pages[target]):raise ValueError('This name already appears in the supervision list. Use a Page update for that legacy entry.')
   photo=''
   if r.get('photo'):
    image=Path(r['photo'])
    if image.is_absolute() or '..'in image.parts or not r['photo'].startswith('assets/'):raise ValueError('Photo must be a local path inside assets/.')
    if not (root/image).is_file():raise ValueError('Photo file not found: '+r['photo'])
    photo='```{=html}\n<img class="member-photo" src="'+html.escape(r['photo'],quote=True)+'" width="90" height="100" alt="'+html.escape(r['name'],quote=True)+'" loading="lazy" decoding="async">\n```\n\n'
   label=(r.get('year','')+(' – '+r['endyear'] if r.get('endyear') else (' – present' if status=='current' and r.get('year') else ''))) or r.get('programme','')
   body=photo+'**'+P('name')+'** — '+P('topic')
   if r.get('position'):body+=' — '+P('position')
   if r.get('details'):body+=' — '+P('details')
   entry=row(label,body)
  elif k=='talk':
   target='talks';pages[target],found=find_remove(pages[target],r['title']);section=str(parse_date(r.get('date','2000')).year)
   kind=r.get('kind','Invited talk');entry=row(dated(r),'**'+P('title')+'** — '+plain(kind)+'. '+P('event')+(' '+P('details') if r.get('details') else ''))
  elif k=='project':
   target='projects';pages[target],found=find_remove(pages[target],r['title']);kind=r.get('kind','sponsored').lower()
   if kind not in ('sponsored','consultancy'):raise ValueError('Project Kind must be Sponsored or Consultancy.')
   if r.get('role','').upper() not in ('PI','CO-PI'):raise ValueError('Project Role must be PI or Co-PI.')
   section='Consultancy Projects' if kind=='consultancy' else 'Sponsored Research Projects'
   label=r.get('year','')+(' – '+r['endyear'] if r.get('endyear') else '')
   body='**'+P('agency')+'** · '+P('role')+(' · '+P('funding') if r.get('funding') else '')+' · '+P('status')+' — '+P('title')+(' — '+P('details') if r.get('details') else '')
   entry=row(label,body)
  elif k=='teaching':
   target='teaching';pages[target],found=find_remove(pages[target],r['code']);level=r.get('level','').lower()
   if level not in ('undergraduate','postgraduate'):raise ValueError('Teaching Level must be Undergraduate or Postgraduate.')
   section='Undergraduate Courses' if level=='undergraduate' else 'Postgraduate and Ph.D. Courses'
   entry=row(r['code'],'**'+P('title')+'** — '+P('semesters')+(' — '+P('details') if r.get('details') else ''))
  elif k=='service':
   target='service';section=r.get('section','Service to the Scientific Community')
   if section not in {'Service to the Scientific Community','Administrative Responsibilities at IIT Tirupati','Conference organization'}:raise ValueError('Unsupported Service section.')
   pages[target],found=find_remove(pages[target],r['title'])
   body='**'+P('title')+'** — '+P('details')
   if r.get('url'):body+=' [Details]('+r['url']+')'
   entry=row(r['period'],body)
  elif k=='award':
   target='about';section='Fellowships and honours';pages[target],found=find_remove(pages[target],r['title']);entry=row(r.get('year',''),'**'+P('title')+'** — '+P('details'))
  if remove:
   if not found:raise ValueError('Cannot remove an entry that was not found: '+r.get('title',r.get('name',r.get('code',''))))
   continue
  if k=='talk':
   page=pages[target];ym=re.search(r'^## '+section+r'\s*$',page,re.M)
   if ym:
    tail=page[ym.end():];end=re.search(r'^## ',tail,re.M);limit=ym.end()+(end.start() if end else len(tail));chunk=page[ym.end():limit]
    heading='FDP, training & popular talks' if any(w in r.get('kind','').lower() for w in ('fdp','training','popular','tutorial','lecture')) else 'Invited talks'
    if '### ' in chunk:chunk=insert_section(chunk,heading,entry,3)
    else:chunk='\n\n'+entry+chunk
    pages[target]=page[:ym.end()]+chunk+page[limit:]
   else:pages[target]=insert_section(page,section,entry)
  else:pages[target]=insert_section(pages[target],section,entry)
  if r.get('announce','no').lower()=='yes':
   title=r.get('title',r.get('name',r.get('code','')));prefix={'publication':'New publication','student':'Research group update','talk':'Talk','project':'Research project','award':'Recognition','service':'Professional service'}.get(k,'Update')
   news_title=prefix+': '+title;news=[(n,b) for n,b in news if norm(n)!=norm(news_title)]
   news.insert(0,(news_title,news_item(news_title,dated(r),r.get('details') or r.get('topic') or title,target+'.qmd')))
 # Sort dated announcements so new records land in chronological order.
 def news_key(item):
  stamp=re.search(r'\*\*([^*]+)\*\*',item[1])
  if not stamp:return date.min
  try:return parse_date(stamp[1])
  except ValueError:
   y=re.search(r'(19|20|21)\d{2}',stamp[1])
   if not y:return date.min
   return date(int(y[0]),1,1)
 news.sort(key=news_key,reverse=True)
 # Generate the full archive as well as a compact homepage feed from the same records.
 pages['_latest-updates']='::: {.news-updates}\n\n'+''.join(body for _,body in news[:5])+':::\n'
 pages['_news-archive']='::: {.news-updates}\n\n'+''.join(body for _,body in news)+':::\n'
 pages['news']=pages['news'].replace('{{< include _latest-updates.qmd >}}','{{< include _news-archive.qmd >}}').replace('## Latest updates','## Updates archive')
 return pages

def build(root=ROOT):
 root=Path(root);base={f.stem:f.read_text() for f in (root/'_content/base').glob('*.qmd')}
 records=parse_updates((root/'UPDATE-WEBSITE.md').read_text());pages=compile_pages(base,records,root)
 from build_cv import build as build_cv
 build_cv(root=root)
 for name,text in pages.items():(root/(name+'.qmd')).write_text(text)
 print(f'Website updates: validated {len(records)} active entries; generated {len(pages)} source files.')
 return pages

if __name__=='__main__':
 try:build()
 except (ValueError,KeyError) as e:
  print('WEBSITE UPDATE ERROR: '+str(e),file=sys.stderr);sys.exit(1)
