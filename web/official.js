// Dated rankings have their own provider identities. Never join them to match
// histories by player name, or let a late ATP response replace WTA's table.
(() => {
  let tours, currentTour = new URLSearchParams(location.search).get('tour') === 'WTA' ? 'WTA' : 'ATP';
  let limit = 50;
  const search = document.querySelector('#published-search');
  const more = document.querySelector('#published-more');
  function render() {
    if (!tours) return;
    const item = tours[currentTour];
    const source = document.querySelector('#published-source');
    const body = document.querySelector('#published-body');
    if (!item?.rows?.length) {
      source.textContent = `${currentTour} published rankings are unavailable; no other tour is substituted.`;
      body.innerHTML = '<tr><td colspan="4">No validated edition available.</td></tr>';
      document.querySelector('#published-count').textContent = '';
      more.hidden = true;
      return;
    }
    const stale = Date.now() - new Date(item.edition + 'T00:00:00Z').getTime() > 10 * 86400000;
    source.innerHTML = `<a href="${safeURL(item.source_url)}" target="_blank" rel="noreferrer">${esc(item.source_name)}</a> · Edition ${fmtDate(item.edition)} · Retrieved ${esc(item.checked_at.slice(0, 10))}. ${esc(item.coverage)}.${item.ok === false ? ' Last refresh failed; showing the last validated edition.' : ''}${stale ? ' This edition is more than ten days old.' : ''}`;
    document.querySelector('#official-date').textContent = fmtDate(item.edition);
    document.querySelector('#official-caption').innerHTML = `<a href="#published-rankings">${esc(item.source_name)} ↓</a>`;
    const query = search.value.trim().toLocaleLowerCase();
    const matches = item.rows.filter(row => `${row.name} ${row.country}`.toLocaleLowerCase().includes(query));
    body.innerHTML = matches.slice(0, limit).map(row => `<tr data-published-tour="${currentTour}"><td>${num(row.rank)}</td><td><a href="${safeURL(row.url)}" target="_blank" rel="noreferrer">${esc(row.name)}</a></td><td>${esc(row.country || '—')}</td><td>${num(row.points)}</td></tr>`).join('') || '<tr><td colspan="4">No matching players.</td></tr>';
    document.querySelector('#published-count').textContent = `${Math.min(limit, matches.length)} of ${matches.length} ${currentTour} players`;
    more.hidden = matches.length <= limit;
  }
  const onTour = event => {
    if (currentTour !== event.detail.tour) { currentTour = event.detail.tour; limit = 50; search.value = ''; }
    render();
  };
  document.addEventListener('court:meta', onTour);
  document.addEventListener('court:tour', onTour);
  search.addEventListener('input', () => { limit = 50; render(); });
  more.addEventListener('click', () => { limit += 50; render(); });
  fetch('./official-rankings.json', {cache: 'no-store'}).then(response => {
    if (!response.ok) throw new Error('Ranking snapshot unavailable');
    return response.json();
  }).then(snapshot => { tours = snapshot.tours; render(); }).catch(() => {
    document.querySelector('#published-source').textContent = 'Published rankings could not be loaded. The power model remains available.';
    document.querySelector('#published-body').innerHTML = '<tr><td colspan="4">Ranking snapshot unavailable.</td></tr>';
  });
})();
