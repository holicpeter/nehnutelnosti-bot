const PAGE_SIZE = 20;
let allListings = [];
let filtered = [];
let page = 0;

async function init() {
  await Promise.all([loadStats(), loadListings()]);
  pollStatus();
}

async function loadStats() {
  try {
    const [stats, health] = await Promise.all([
      fetch('/api/stats').then(r => r.json()),
      fetch('/health').then(r => r.json()),
    ]);
    document.getElementById('statTotal').textContent = stats.total ?? '—';
    document.getElementById('statStored').textContent = stats.stored ?? '—';
    const job = health.next_run;
    document.getElementById('statNextRun').textContent = job ? formatTime(job) : '—';
    updateStatusBadge(health.status === 'ok');
  } catch {
    updateStatusBadge(false);
  }
}

async function loadListings() {
  try {
    const res = await fetch('/api/listings');
    allListings = await res.json();
    page = 0;
    applyFilters();
  } catch {
    showToast('Chyba pri načítaní inzerátov', 'error');
  }
}

function applyFilters() {
  const src = document.getElementById('filterSource').value;
  const maxPrice = parseFloat(document.getElementById('filterMaxPrice').value) || Infinity;
  const minArea = parseFloat(document.getElementById('filterMinArea').value) || 0;
  const q = document.getElementById('filterSearch').value.toLowerCase();
  const sort = document.getElementById('sortBy').value;

  filtered = allListings.filter(l => {
    if (src && l.source !== src) return false;
    if (l.price != null && l.price > maxPrice) return false;
    if (l.area != null && l.area < minArea) return false;
    if (q && !`${l.title} ${l.location} ${l.description}`.toLowerCase().includes(q)) return false;
    return true;
  });

  filtered.sort((a, b) => {
    if (sort === 'price_asc') return (a.price ?? Infinity) - (b.price ?? Infinity);
    if (sort === 'price_desc') return (b.price ?? 0) - (a.price ?? 0);
    if (sort === 'area_desc') return (b.area ?? 0) - (a.area ?? 0);
    return new Date(b.seen_at ?? 0) - new Date(a.seen_at ?? 0);
  });

  page = 0;
  renderListings(true);
}

function renderListings(reset = false) {
  const grid = document.getElementById('listingsGrid');
  const empty = document.getElementById('emptyState');
  const loadMoreWrap = document.getElementById('loadMoreWrap');
  const count = document.getElementById('listingsCount');

  count.textContent = `Inzeráty (${filtered.length})`;

  if (reset) {
    grid.innerHTML = '';
    grid.appendChild(empty);
  }

  if (filtered.length === 0) {
    empty.style.display = '';
    loadMoreWrap.style.display = 'none';
    return;
  }
  empty.style.display = 'none';

  const slice = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  slice.forEach(l => grid.insertBefore(makeCard(l), loadMoreWrap));

  const hasMore = (page + 1) * PAGE_SIZE < filtered.length;
  loadMoreWrap.style.display = hasMore ? '' : 'none';
}

function loadMore() {
  page++;
  renderListings(false);
}

function makeCard(l) {
  const card = document.createElement('article');
  card.className = 'card';

  const sourceSlug = (l.source || '').split('.')[0];
  const priceStr = l.price != null ? `${Math.round(l.price).toLocaleString('sk-SK')} €` : 'Cena neuvedená';
  const areaStr = l.area != null ? `${l.area} m²` : null;
  const timeStr = l.seen_at ? timeAgo(l.seen_at) : '';

  card.innerHTML = `
    ${l.image_url
      ? `<img class="card-img" src="${esc(l.image_url)}" alt="" loading="lazy" onerror="this.style.display='none';this.nextSibling.style.display='flex'">`
      : ''}
    <div class="card-img-placeholder" style="display:${l.image_url ? 'none' : 'flex'}">🏠</div>
    <div class="card-body">
      <div class="card-title">
        ${l.url ? `<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.title || 'Bez názvu')}</a>`
                : esc(l.title || 'Bez názvu')}
      </div>
      <div class="card-meta">
        ${l.location ? `<span>📍 ${esc(l.location)}</span>` : ''}
        ${areaStr ? `<span>📐 ${areaStr}</span>` : ''}
      </div>
      <div class="card-price">${priceStr}</div>
      ${l.description ? `<div class="card-desc">${esc(l.description)}</div>` : ''}
    </div>
    <div class="card-footer">
      <span class="source-badge source-${sourceSlug}">${esc(l.source || 'N/A')}</span>
      <span class="card-time">${timeStr}</span>
    </div>
  `;
  return card;
}

async function scrapeNow() {
  const btn = document.getElementById('scrapeBtn');
  btn.classList.add('loading');
  btn.textContent = '⏳ Scrapujem...';
  btn.disabled = true;
  try {
    const res = await fetch('/scrape/now', { method: 'POST' });
    if (!res.ok) throw new Error();
    showToast('Scraping dokončený!', 'success');
    await Promise.all([loadStats(), loadListings()]);
  } catch {
    showToast('Chyba pri scrapingu', 'error');
  } finally {
    btn.classList.remove('loading');
    btn.textContent = '▶ Spustiť teraz';
    btn.disabled = false;
  }
}

function pollStatus() {
  setInterval(async () => {
    try {
      const health = await fetch('/health').then(r => r.json());
      updateStatusBadge(health.status === 'ok');
      if (health.next_run) {
        document.getElementById('statNextRun').textContent = formatTime(health.next_run);
      }
    } catch {
      updateStatusBadge(false);
    }
  }, 30_000);
}

function updateStatusBadge(ok) {
  const badge = document.getElementById('statusBadge');
  badge.className = `status-badge${ok ? ' ok' : ''}`;
  badge.innerHTML = `<span class="dot"></span> ${ok ? 'Beží' : 'Offline'}`;
}

function showToast(msg, type = '') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type} show`;
  setTimeout(() => t.classList.remove('show'), 3500);
}

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'práve teraz';
  if (mins < 60) return `pred ${mins} min`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `pred ${hrs} hod`;
  return `pred ${Math.floor(hrs / 24)} dňami`;
}

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('sk-SK', { hour: '2-digit', minute: '2-digit' });
}

function esc(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

init();
