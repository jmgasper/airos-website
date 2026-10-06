// Progressive enhancement: links, galleries and the complete archive work without JS.
const filters = document.querySelector('[data-gallery-filters]');
if (filters) {
  filters.hidden = false;
  filters.addEventListener('click', event => {
    const button = event.target.closest('button');
    if (!button) return;
    filters.querySelectorAll('button').forEach(b => { b.classList.toggle('selected', b === button); b.setAttribute('aria-pressed', b === button); });
    document.querySelectorAll('[data-category]').forEach(card => { card.hidden = button.dataset.filter !== 'All' && card.dataset.category !== button.dataset.filter; });
  });
  filters.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', b.classList.contains('selected')));
}
const lightbox = document.querySelector('#lightbox');
if (lightbox && typeof lightbox.showModal === 'function') {
  document.querySelectorAll('.screenshot-link').forEach(anchor => anchor.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    lightbox.querySelector('img').src = anchor.href;
    lightbox.querySelector('img').alt = anchor.querySelector('img').alt;
    lightbox.querySelector('p').textContent = anchor.dataset.caption;
    lightbox.showModal();
  }));
  lightbox.addEventListener('click', event => { if (event.target === lightbox) { const r = lightbox.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) lightbox.close(); } });
}
const search = document.querySelector('[data-changes]');
if (search) {
  const list = document.querySelector('.commit-list');
  const input = search.querySelector('input');
  const select = search.querySelector('select');
  const status = search.querySelector('[role=status]');
  const more = document.createElement('button');
  more.className = 'button load-more'; more.textContent = 'Show 100 more'; more.hidden = true;
  list.after(more);
  let commits, matches, limit = 100;
  const node = (tag, text, cls) => { const n = document.createElement(tag); n.textContent = text; if (cls) n.className = cls; return n; };
  function render() {
    list.replaceChildren();
    matches.slice(0, limit).forEach(c => {
      const article = node('article', '', 'commit');
      const time = node('time', c.date.slice(0,10)); time.dateTime = c.date;
      const div = node('div',''); const repo = node('span',c.repo,'commit-repo');
      const title = node('h2',''); const a = node('a',c.subject); a.href = c.url; title.append(a);
      div.append(repo,title); article.append(time,div,node('code',c.sha.slice(0,7))); list.append(article);
    });
    more.hidden = matches.length <= limit;
    status.textContent = `${matches.length.toLocaleString()} matching commits · showing ${Math.min(matches.length,limit).toLocaleString()}`;
  }
  function filter() {
    const q = input.value.trim().toLowerCase();
    matches = commits.filter(c => (!select.value || c.repo === select.value) && (!q || `${c.subject} ${c.repo} ${c.sha}`.toLowerCase().includes(q)));
    limit = 100; render();
  }
  fetch(search.dataset.changes).then(r => { if(!r.ok) throw new Error('Archive unavailable'); return r.json(); }).then(data => {
    commits=data; matches=data; search.hidden=false;
    input.addEventListener('input', filter); select.addEventListener('change', filter);
    more.addEventListener('click', () => {limit += 100; render();});
    render();
  }).catch(() => { more.remove(); });
}
// Rolling application releases replace versioned assets. Refresh their links on
// the downloads page so a newly published package does not leave stale buttons.
// If the public API is unavailable, the dated snapshot and release-page fallback
// remain usable. No token or authenticated request is sent from the browser.
document.querySelectorAll('.app-card[data-repo]').forEach(card => {
  if (!card.querySelector('.package-link')) return;
  fetch(`https://api.github.com/repos/jmgasper/${encodeURIComponent(card.dataset.repo)}/releases/tags/latest`, {credentials:'omit'})
    .then(response => { if (!response.ok) throw new Error('Release lookup unavailable'); return response.json(); })
    .then(release => {
      const assets = release.assets.filter(a => a.state === 'uploaded' && a.name.endsWith('.hpkg'));
      const existing = [...card.querySelectorAll('.package-link')];
      const replacements = [];
      for (const arch of ['x86_64','arm64']) {
        for (const asset of assets.filter(a => a.name.endsWith(arch+'.hpkg'))) {
          const a = document.createElement('a'); a.className = 'package-link';
          const target = new URL(asset.browser_download_url);
          if (target.origin !== 'https://github.com') continue;
          a.href = target.href;
          const label = document.createElement('span');
          label.textContent = (arch === 'x86_64' ? 'x86-64' : 'ARM64') + (asset.name.startsWith('summit_webkit') ? ' · WebKit engine' : '');
          const size = document.createElement('small');
          size.textContent = (asset.size >= 1048576 ? `${(asset.size/1048576).toFixed(1)} MB` : `${Math.round(asset.size/1024)} KB`) + ' ↓';
          a.append(label,size); replacements.push(a);
        }
      }
      if (!replacements.length) return;
      existing[0].before(...replacements); existing.forEach(a => a.remove());
      card.querySelector('.app-meta span').textContent = release.published_at.slice(0,10);
    }).catch(() => {});
});
