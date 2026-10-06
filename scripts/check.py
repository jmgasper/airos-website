#!/usr/bin/env python3
"""Validate generated routes, assets, download coverage and complete archive."""
from html.parser import HTMLParser
import json
import os
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
BASE=os.getenv('BASE_PATH','').rstrip('/')
errors=[]
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=set();self.h1=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1':self.h1+=1
        if 'id' in a:self.ids.add(a['id'])
        for key in ['href','src']:
            if key in a:self.links.append(a[key])
        if tag=='img' and 'alt' not in a:errors.append('Missing image alt text')
pages={}
for path in OUT.rglob('*.html'):
    p=Page();p.feed(path.read_text());pages[path]=p
    if p.h1!=1:errors.append(f'{path}: {p.h1} h1 headings')
for path,p in pages.items():
    for href in p.links:
        u=urlsplit(href)
        if u.scheme or u.netloc:continue
        target=unquote(u.path)
        if target.startswith('/'):
            if BASE and not target.startswith(BASE+'/'):errors.append(f'Wrong base path: {href}')
            target=target[len(BASE):].lstrip('/')
            dest=OUT/target
        else:dest=path.parent/target if target else path
        if dest.is_dir():dest=dest/'index.html'
        if not dest.exists():errors.append(f'{path}: broken link {href}')
        elif u.fragment and dest in pages and u.fragment not in pages[dest].ids:errors.append(f'{path}: missing anchor {href}')
for route in ['', 'screenshots', 'hardware','downloads','source','changelog']:
    if not (OUT/route/'index.html').is_file():errors.append('Missing route '+route)
snapshot=json.loads((ROOT/'data/github.json').read_text())
changes=json.loads((OUT/'changes.json').read_text())
expected={(s['repo'],c['sha']) for s in snapshot['sources'] for c in s['commits']}
if {(c['repo'],c['sha']) for c in changes}!=expected:errors.append('Changelog lost Git history')
for c in changes:
    month=OUT/'changelog'/c['date'][:7]/'index.html'
    if not month.exists() or c['url'] not in month.read_text():errors.append('Missing monthly archive entry '+c['sha'])
for app in json.loads((ROOT/'content/project.json').read_text())['apps']:
    if app['repo'].lower() not in pages[OUT/'downloads/index.html'].ids:errors.append('Missing app '+app['name'])
for im in snapshot['images']:
    if im['assets']:
        names={a['name'] for a in im['assets']}
        image=next((n for n in names if n.endswith(('.iso.xz','.img.xz'))),None)
        if not image or image+'.sha256' not in names or 'manifest.json' not in names:errors.append('Incomplete image release '+im['target'])
if errors:raise SystemExit('\n'.join(errors))
print(f'OK: {len(pages)} HTML files, every internal link, seven app entries, {len(changes)} archived commits')
