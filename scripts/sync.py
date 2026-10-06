#!/usr/bin/env python3
"""Snapshot public GitHub sources. No truncation, invented assets, or runtime API dependency."""
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'content/project.json').read_text())
CACHE = ROOT / '.cache'
CACHE.mkdir(exist_ok=True)
TOKEN = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
if not TOKEN:
    TOKEN = subprocess.check_output(['gh', 'auth', 'token'], text=True).strip()

def api(path, missing=False):
    request = urllib.request.Request('https://api.github.com/' + path, headers={
        'Authorization': 'Bearer ' + TOKEN, 'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'airos-website'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404 and missing:
                return None
            if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
            time.sleep(2 ** attempt)

def contents(repo, path, ref):
    import base64
    result = api(f'repos/{repo}/contents/{path}?ref={ref}')
    return json.loads(base64.b64decode(result['content']))

def quote(value):
    return urllib.parse.quote(value, safe='')

def collect(source):
    repo, branch = source['repo'], source['branch']
    if api(f'repos/{repo}')['private']:
        raise RuntimeError('Refusing to export private Git history: ' + repo)
    head = api(f'repos/{repo}/commits/{quote(branch)}')['sha']
    base = source.get('base')
    key = repo.replace('/', '_') + '_' + quote(branch) + '.json'
    cache_path = CACHE / key
    previous = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    if previous.get('head') == head and previous.get('base') == base:
        records = previous['commits']
    else:
        records = []
        page = 1
        expected = None
        while True:
            if base:
                response = api(f'repos/{repo}/compare/{quote(base)}...{head}?per_page=100&page={page}')
                expected = response['total_commits']
                commits = response['commits']
            else:
                commits = api(f'repos/{repo}/commits?sha={head}&per_page=100&page={page}')
            for c in commits:
                records.append({'sha': c['sha'], 'url': c['html_url'],
                    'date': c['commit']['committer']['date'],
                    'subject': c['commit']['message'].splitlines()[0]})
            if (expected is not None and len(records) >= expected) or len(commits) < 100:
                break
            page += 1
        if expected is not None and len(records) != expected:
            raise RuntimeError(f'Incomplete Git history for {repo}: {len(records)}/{expected}')
        if len({c['sha'] for c in records}) != len(records):
            raise RuntimeError(f'Duplicate Git history pages for {repo}')
        cache_path.write_text(json.dumps({'head': head, 'base': base, 'commits': records}))
    print(f"{repo}@{branch}: {len(records)} commits", flush=True)
    return {**source, 'head': head, 'commits': records,
            'url': f'https://github.com/{repo}/tree/{quote(branch)}'}

def release(app):
    repo = 'jmgasper/' + app['repo']
    metadata = api(f'repos/{repo}', missing=True)
    if metadata is None or metadata['private']:
        return {**app, 'release': None, 'assets': [], 'private': True}
    result = api(f'repos/{repo}/releases/tags/latest', missing=True)
    if result is None:
        return {**app, 'release': None, 'assets': []}
    return {**app, 'release': result['html_url'], 'published': result['published_at'],
            'assets': [{k: a.get(k) for k in ['name', 'size', 'browser_download_url', 'digest']}
                       for a in result['assets'] if a['name'].endswith('.hpkg') and a['state'] == 'uploaded']}

def main():
    ci_head = api('repos/jmgasper/airos-ci/commits/main')['sha']
    manifest = contents('jmgasper/airos-ci', 'forks/forks.json', ci_head)
    lock = contents('jmgasper/airos-ci', 'forks/forks.lock.json', ci_head)
    sources = [dict(name='Haiku / airOS', repo='jmgasper/haiku', branch='master',
                    base=CONFIG['haiku_base'], group='Operating system',
                    description='Haiku kernel, desktop, drivers and airOS integration.'),
               dict(name='Build pipelines', repo='jmgasper/airos-ci', branch='main',
                    group='Build infrastructure', description='SDKs, packages, images and source provenance.')]
    for branch in ['airos-release', 'rpi4', 'x399-workstation']:
        sources.append(dict(name='Haiku / ' + branch, repo='jmgasper/haiku', branch=branch,
                            base=CONFIG['haiku_base'], group='Operating system',
                            description='Active device or release branch; includes work awaiting integration into master.'))
    for app in CONFIG['apps'] + CONFIG['extra_repos']:
        repo = 'jmgasper/' + app['repo']
        metadata = api(f'repos/{repo}', missing=True)
        if metadata is None or metadata['private']:
            print('Skipping nonpublic source: ' + repo, flush=True)
            continue
        entry = dict(name=app['name'], repo=repo, branch=metadata['default_branch'],
                     description=app['description'], group='Applications')
        if app.get('upstream'):
            upstream = api(f"repos/{app['upstream']}")
            comparison = api(f"repos/{repo}/compare/{app['upstream'].split('/')[0]}:{upstream['default_branch']}...{entry['branch']}")
            entry['base'] = comparison['merge_base_commit']['sha']
            entry['group'] = 'Build infrastructure'
        sources.append(entry)
    for component in manifest['components']:
        pin = lock[component['name']]
        sources.append(dict(name=component['name'], repo='jmgasper/' + pin['repo'],
                            branch=pin['branch'], base=pin.get('base_commit'),
                            group='Libraries & firmware', description=component['used_by'],
                            pinned=pin['commit'], upstream=pin.get('upstream')))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        sources = list(pool.map(collect, sources))
        apps = list(pool.map(release, CONFIG['apps']))
    images = []
    releases = []
    page = 1
    while True:
        batch = api(f'repos/jmgasper/haiku/releases?per_page=100&page={page}')
        releases.extend(batch)
        # Do not silently lose a target whose latest build is older than the
        # first page of other architectures' releases.
        if len(batch) < 100:
            break
        page += 1
    for target in ['x86_64', 'arm64', 'rpi4']:
        candidates = [r for r in releases if not r['draft'] and r['tag_name'].startswith(f'image-{target}-')]
        result = max(candidates, key=lambda r: r['published_at']) if candidates else None
        images.append({'target': target, 'release': result['html_url'] if result else None,
                       'published': result['published_at'] if result else None,
                       'assets': [{k: a.get(k) for k in ['name', 'size', 'browser_download_url', 'digest']}
                                  for a in (result or {}).get('assets', []) if a['state'] == 'uploaded']})
    snapshot = dict(updated=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
                    ci_head=ci_head, sources=sources, apps=apps, images=images)
    # Commit the snapshot only after every source succeeds. A failed refresh must not
    # replace the previous complete site with a partial archive.
    destination = ROOT / 'data/github.json'
    temp = destination.with_suffix('.tmp')
    temp.write_text(json.dumps(snapshot, indent=2) + '\n')
    temp.replace(destination)
    print(f'Snapshot complete: {len(sources)} sources, {sum(len(s["commits"]) for s in sources)} commits')

if __name__ == '__main__':
    main()
