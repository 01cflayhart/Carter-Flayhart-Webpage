import { owner } from './_lib/security.js';
import { loginConfigured, siteOrigin } from './_lib/setup.js';

export async function onRequest({ request, env }) {
  const user = await owner(request, env);
  const loginAvailable = loginConfigured(env) && new URL(request.url).origin === siteOrigin(env);
  const content = user ? `
    <h1>Site activity</h1>
    <p>Private · Carter’s GitHub account only</p>
    <section aria-labelledby="setup-title">
      <h2 id="setup-title">Setup checks</h2>
      <p id="setup-status" role="status">Checking configuration…</p>
      <ul id="setup-checks" class="setup-checks"></ul>
      <button id="refresh-setup" type="button">Check again</button>
    </section>
    <section aria-labelledby="activity-title">
      <h2 id="activity-title">Daily activity</h2>
      <p>Daily page views—not unique people. UTC dates. Professional and sports traffic are counted separately; reloads and bots may affect totals. DNT and Global Privacy Control are respected.</p>
      <label><input id="exclude" type="checkbox" checked disabled> Exclude my activity on this browser</label>
      <p id="status" role="status">Loading activity…</p>
      <div class="table-wrap"><table><thead><tr><th scope="col">Date (UTC)</th><th scope="col">Professional views</th><th scope="col">Sports views</th></tr></thead><tbody id="rows"></tbody></table></div>
    </section>
    <button id="logout" type="button">Sign out</button>
    <noscript><p>Enable JavaScript to load private statistics and account controls.</p></noscript>
    <script src="/private-dashboard.js" defer></script>` : `
    <h1>Private site activity</h1>
    <p>Only Carter’s authorized GitHub account can access these statistics.</p>
    ${loginAvailable ? '<a href="/api/auth/start">Sign in with GitHub</a>' : '<p>Owner sign-in is not available on this deployment yet. The public website remains available; no statistics are exposed here.</p>'}`;
  return new Response(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Private site activity</title><link rel="stylesheet" href="/site.css"><link rel="stylesheet" href="/private.css"></head><body><main><a href="/">← Website</a>${content}</main></body></html>`, { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'private, no-store', 'X-Robots-Tag': 'noindex, nofollow', 'Vary': 'Cookie', 'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'" } });
}
