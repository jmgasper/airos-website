# airos.works

The public airOS project website. Static HTML, CSS and small progressive
JavaScript enhancements, hosted by GitHub Pages. No framework, database,
third-party fonts, analytics, or visitor login.

## Run locally

Python 3.12 or newer is sufficient. The committed public GitHub snapshot lets
the website build without network access or credentials.

```sh
python3 scripts/build.py
python3 scripts/check.py
python3 -m http.server 8787 --directory dist
```

Refresh source histories and release metadata with a read-only GitHub token
(`GH_TOKEN` / `GITHUB_TOKEN`), or a signed-in `gh` CLI:

```sh
python3 scripts/sync.py
python3 scripts/build.py
python3 scripts/check.py
```

`BASE_PATH=/airos-website` supports a GitHub project URL. `SITE_URL` controls
the canonical URL, sitemap and social metadata. The Pages workflow derives
both from the repository's actual Pages configuration.

## Content and design

- Home: credit Haiku, explain the independent project and AI-assisted approach.
- Screenshots: real application and hardware captures, with full-size viewing.
- New hardware: curated capabilities, gaps and links to the lab's test notes.
- Downloads: actual public `.hpkg` release assets, plus immutable OS images.
- Source: the operating system, apps and every branch in the CI fork manifest.
- Changelog: all collected fork changes, monthly archives and global search.

The established air/OS artwork supplies the identity. Warm white, deep teal,
muted green, sky blue and amber echo the logo. Typography and whitespace lead;
real screenshots live on their own page. Navigation and content work without
JavaScript. With JavaScript, the gallery supports filtering and an accessible
native dialog, and the changelog searches its full local archive.

Curated content lives in `content/`. `static/assets/` holds the logo, original
captures, CSS and JavaScript. The build produces `dist/`. Screenshots are
unaltered captures; historical development images can show earlier branding.
The AirTime capture includes Big Buck Bunny, © Blender Foundation,
[CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).

## Keeping Git history current

The Pages workflow runs on every main-branch push, every six hours, manually,
and on a `source-updated` repository dispatch. It refreshes the site from public
GitHub APIs and deploys only after a complete successful sync and validation.
Failures leave the previous deployment intact.

The sync reads `jmgasper/airos-ci` at a fixed commit for each run. Its
`forks/forks.json` and `forks/forks.lock.json` determine dependency branches
and upstream baselines. For Haiku the recorded baseline is the common ancestor
of the fork and upstream at initial site creation. The integration branch and
active `airos-release`, `rpi4` and `x399-workstation` branches are all tracked. App history and imported
repositories have no upstream exclusion. Every API page is fetched; compare
counts are checked, and duplicate commits across branches are displayed once.
Nothing is limited to a recent date window. SHA-keyed cache files accelerate
unchanged histories without hiding force-pushed changes. Private repositories
are never exported. The source page links directly to full upstream history.

The public snapshot in `data/github.json` is a local-development fallback.
Scheduled and manual refreshes save the validated snapshot to main before
deployment. This keeps local builds current and avoids GitHub disabling the
public repository’s schedule after 60 days of inactivity. Snapshot pushes use
the repository’s GITHUB_TOKEN and do not trigger recursive workflow runs.
A concurrent editor push is never overwritten; the next run can save it. Hardware claims and screenshots need human
review when new test evidence arrives; the site does not infer support from
commit messages.

## Downloads

App assets come from each public repository's rolling `latest` prerelease.
Summit lists its browser and required WebKit engine separately. The download
page refreshes rolling app links from the public GitHub API when it opens,
with the dated snapshot and release-page links as fallbacks. It identifies architecture and build date and links to checksums in the
release notes. Any app without a public release is explicitly unavailable.

OS images are discovered from public `jmgasper/haiku` prereleases named
`image-{x86_64,arm64,rpi4}-...`. The newest published release for each target
wins. The downloads page also refreshes these image links when opened, so a
build published between scheduled site updates appears immediately. If the
public API is unavailable, the complete static download links remain. `airos-ci/images/publish-github.py` verifies smoke results and compressed
and uncompressed hashes, uploads to a draft, verifies the server's digests,
then publishes. The site includes the image, SHA-256 file and package manifest.
The repository and Pages deployment contain no OS images or application binaries.

GitHub's [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
allow a 1 GB published site. [Release assets](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
are under 2 GiB per file, with no total release storage or bandwidth limit
specified. The current compressed images fit this model.

## Domain

See [DEPLOYMENT.md](DEPLOYMENT.md) for the GitHub Pages and DNS configuration.
