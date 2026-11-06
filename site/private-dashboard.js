const status = document.querySelector('#status'), exclude = document.querySelector('#exclude');
async function requestJson(url, options = {}) {
  const response = await fetch(url, { ...options, signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error(response.status === 401 ? 'Sign in again.' : 'Request failed.');
  return response.json();
}
const setupStatus = document.querySelector('#setup-status'), refreshSetup = document.querySelector('#refresh-setup');
async function loadSetup() {
  refreshSetup.disabled = true;
  setupStatus.textContent = 'Checking configuration…';
  try {
    const data = await requestJson('/api/owner/setup');
    const list = document.querySelector('#setup-checks'); list.replaceChildren();
    for (const check of data.checks) {
      const item = document.createElement('li'), title = document.createElement('strong'), detail = document.createElement('p');
      title.textContent = check.title + ' · ' + (check.configured ? 'Configured' : 'Needs setup');
      detail.textContent = check.message; item.append(title, detail); list.append(item);
    }
    setupStatus.textContent = 'Configuration checks only. Confirm feedback delivery and live behavior before considering setup complete.';
  } catch { setupStatus.textContent = 'Setup checks unavailable. Check your connection or sign in again, then select Check again.'; }
  finally { refreshSetup.disabled = false; }
}
refreshSetup.addEventListener('click', loadSetup);
loadSetup();
exclude.disabled = true;
requestJson('/api/owner/stats').then(data => {
  exclude.checked = data.owner_excluded; exclude.disabled = false;
  const days = new Map(); for (const row of data.rows) { if (!days.has(row.day)) days.set(row.day, {}); days.get(row.day)[row.area] = row.views; }
  const body = document.querySelector('#rows');
  for (const [day, counts] of days) { const tr = document.createElement('tr'); for (const value of [day, counts.professional || 0, counts.sports || 0]) { const td = document.createElement('td'); td.textContent = value; tr.append(td); } body.append(tr); }
  status.textContent = days.size ? 'Only aggregate counts are retained. Your exclusion preference applies to this browser.' : 'No activity has been recorded yet.';
}).catch(() => { status.textContent = 'Statistics unavailable. Check database configuration or sign in again.'; });
exclude.addEventListener('change', async () => {
  exclude.disabled = true;
  try { await requestJson('/api/owner/exclude', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ exclude: exclude.checked }) }); status.textContent = exclude.checked ? 'Your activity is excluded on this browser, including after sign-out.' : 'Your activity will be counted on this browser.'; }
  catch { exclude.checked = !exclude.checked; status.textContent = 'Preference could not be saved. Try again.'; }
  finally { exclude.disabled = false; }
});
document.querySelector('#logout').addEventListener('click', async event => {
  const button = event.currentTarget; button.disabled = true;
  try { await requestJson('/api/auth/logout', { method: 'POST' }); location.reload(); }
  catch { status.textContent = 'Sign-out failed. Check your connection and try again.'; button.disabled = false; }
});
