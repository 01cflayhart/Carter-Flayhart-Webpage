(() => {
  const tool = document.body.dataset.tool;
  const book = document.querySelector('#sportsbook'), date = document.querySelector('#slate-date'), windowSelect = document.querySelector('#stats-window');
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
  date.value = today; date.max = today;
  const query = new URLSearchParams(location.search);
  if ([...book.options].some(o => o.value === query.get('book'))) book.value = query.get('book');
  let data;
  const text = (tag, value) => { const node = document.createElement(tag); node.textContent = value; return node; };
  const pct = value => value == null ? '—' : `${(value * 100).toFixed(1)}%`;
  function table(target, headers, rows) {
    const wrap = document.querySelector(target); wrap.replaceChildren(); wrap.classList.remove('empty-board');
    const scroll = document.createElement('div'); scroll.className = 'table-wrap'; scroll.tabIndex = 0; scroll.setAttribute('role', 'region'); scroll.setAttribute('aria-label', headers.join(', '));
    const table = document.createElement('table'); table.className = 'model-table';
    const head = document.createElement('thead'), tr = document.createElement('tr');
    headers.forEach(h => { const th = text('th', h); th.scope = 'col'; tr.append(th); }); head.append(tr); table.append(head);
    const body = document.createElement('tbody'); rows.forEach(cells => { const row = document.createElement('tr'); cells.forEach(cell => row.append(text('td', cell))); body.append(row); }); table.append(body); scroll.append(table); wrap.append(scroll);
  }
  function empty(target, title, message) {
    const node = document.querySelector(target); node.classList.add('empty-board'); node.replaceChildren(text('strong', title), text('span', message));
  }
  function draw() {
    if (!data) return;
    const selected = data.books[book.value];
    const rows = selected.history.filter(r => r.date === date.value);
    const current = date.value === data.date ? selected.current.predictions : rows;
    const slate = current.map(r => ({ ...r, outcome: selected.history.find(h => h.prediction_id === r.prediction_id)?.outcome || 'pending' }));
    const expired = date.value < today;
    document.querySelector('#data-state').textContent = `${date.value} · ${book.selectedOptions[0].text} · ${expired ? 'Historical archive, not current recommendations' : data.status} · Last checked ${new Date(data.checked_at).toLocaleString()}`;
    const missing = ['fanatics', 'caesars'].includes(book.value) ? 'This provider’s free tier does not include this sportsbook. A compatible licensed feed is required; picks from another book are never substituted.' : 'No verified selections for this book and date. This may reflect missing inputs, no qualifying opportunities, or no archived slate—not a perfect record.';
    function board(selector, items, favorite = false) {
      if (!items.length) { empty(selector, 'No verified selections', missing); return; }
      table(selector, favorite ? ['Category', 'Favorite / matchup', 'Sport', 'Odds', 'Favorite win estimate', 'Evidence / result'] : ['Rank', 'Prop', 'Odds', 'Projected likelihood', 'Season hit rate', 'Evidence / result'], items.map(r => favorite ? [r.category, r.label, r.sport, r.odds > 0 ? '+' + r.odds : r.odds, pct(r.probability), `${r.evidence} · ${r.outcome}`] : [r.rank || '—', r.label + (r.alternatives?.length ? ' · Easier alternatives: ' + r.alternatives.map(a => `${a.line}: ${pct(a.probability)}`).join('; ') : ''), r.odds > 0 ? '+' + r.odds : r.odds, pct(r.probability), pct(r.season_hit_rate), `${r.evidence} · ${r.outcome}`]));
    }
    if (tool === 'prop-hunt') { board('#top-board', slate.filter(r => r.list === 'top')); board('#safe-board', slate.filter(r => r.list === 'safe')); }
    else {
      board('#favorites-board', slate.sort((a, b) => b.probability - a.probability), true);
      const markets = date.value === today && date.value === data.date && Date.now() - new Date(data.checked_at).getTime() <= 21600000 ? (selected.market_watchlist || []).filter(r => {
        const age = Date.now() - new Date(r.as_of).getTime();
        return age >= 0 && age <= 21600000 && new Date(r.starts_at).getTime() > Date.now();
      }) : [];
      if (markets.length) table('#market-board', ['Favorite', 'Matchup', 'Sport', 'Moneyline', 'Price observed', 'Model status'], markets.map(r => [r.favorite, r.label, r.sport, r.odds, new Date(r.as_of).toLocaleString(), r.status]));
      else empty('#market-board', 'No fresh market observations', expired ? 'Raw market coverage is not a historical prediction archive. See frozen forecasts above.' : 'No current qualifying prices are connected for this book. This does not mean there are no heavy favorites today.');
    }
    const perf = selected.performance[windowSelect.value];
    table('#performance-board', ['Group', 'W–L', 'Win rate', 'Settled n', 'Pending', 'Push / void', 'Brier ↓'], Object.entries(perf).map(([name, s]) => [name, `${s.wins}–${s.losses}`, pct(s.win_rate), s.n, s.pending, `${s.pushes} / ${s.voids}`, s.brier == null ? '—' : s.brier.toFixed(3)]));
    if (selected.history.length) table('#history-board', ['Date', 'Selection', 'List / category', 'Rank', 'Forecast', 'Result', 'Model'], [...selected.history].reverse().map(r => [r.date, r.label, r.category || r.list, r.rank || '—', pct(r.probability), r.outcome, r.model_version]));
    else empty('#history-board', 'No prediction history yet', 'Statistics begin only after genuine pregame forecasts are archived. No backfilled wins.');
    document.querySelector('#review-note').textContent = data.review + (tool === 'prop-hunt' ? ' Overall Prop Hunt totals count list placements; a prop in both lists appears twice. Compare top and safe separately.' : ' Category success rates measure the favorite winning, not the underdog winning.');
    const params = new URLSearchParams({ book: book.value }); history.replaceState(null, '', '?' + params);
  }
  [book, date, windowSelect].forEach(control => control.addEventListener('change', draw));
  fetch('../analysis/' + tool + '.json', { signal: AbortSignal.timeout(15000) }).then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(value => { data = value; draw(); }).catch(() => {
    document.querySelector('#data-state').textContent = 'The prediction archive could not be loaded. Reload to try again; no stale picks are shown.';
    for (const selector of tool === 'prop-hunt' ? ['#top-board', '#safe-board'] : ['#favorites-board', '#market-board']) empty(selector, 'Data unavailable', 'No predictions are shown while the archive is unavailable.');
  });
})();
