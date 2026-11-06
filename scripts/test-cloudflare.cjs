// Isolated local Workers runtime + real local D1 migrations; no Cloudflare account.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const net = require('node:net');
const { spawn, execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const { setTimeout: delay } = require('node:timers/promises');
const { configuration } = require('./configure-cloudflare.cjs');

async function main() {
  const root = path.resolve(__dirname, '..');
  const tempBase = '/tmp/opencode'; fs.mkdirSync(tempBase, { recursive: true });
  const directory = fs.mkdtempSync(path.join(tempBase, 'carter-cloudflare-test-'));
  const env = { ...process.env, CI: 'true', WRANGLER_SEND_METRICS: 'false' };
  // Never supply an inherited API token to a local test process.
  for (const key of Object.keys(env)) if (/^(CLOUDFLARE_|CF_|WRANGLER_API)/.test(key)) delete env[key];
  const npx = process.platform === 'win32' ? 'npx.cmd' : 'npx';
  const prefix = ['--yes', 'wrangler@4.158.0'];
  let server, output = '';
  try {
    const listener = net.createServer();
    await new Promise((resolve, reject) => { listener.once('error', reject); listener.listen(0, '127.0.0.1', resolve); });
    const port = listener.address().port; await new Promise(resolve => listener.close(resolve));
    const origin = `http://127.0.0.1:${port}`;
    const config = configuration({ CLOUDFLARE_D1_DATABASE_ID: '12345678-1234-1234-1234-123456789abc' });
    const secret = 'synthetic-local-smoke-secret-never-use-in-production';
    config.vars = { ...config.vars, SITE_ORIGIN: origin, SESSION_SECRET: secret, GITHUB_CLIENT_ID: 'local-fixture', GITHUB_CLIENT_SECRET: 'local-fixture' };
    fs.cpSync(path.join(root, 'functions'), path.join(directory, 'functions'), { recursive: true });
    fs.cpSync(path.join(root, 'migrations'), path.join(directory, 'migrations'), { recursive: true });
    fs.mkdirSync(path.join(directory, '_site'));
    for (const file of ['_routes.json', 'site.css', 'private.css', 'private-dashboard.js']) fs.copyFileSync(path.join(root, 'site', file), path.join(directory, '_site', file));
    fs.writeFileSync(path.join(directory, '_site/index.html'), '<!doctype html><title>Local test only</title>');
    fs.writeFileSync(path.join(directory, 'wrangler.jsonc'), JSON.stringify(config));
    execFileSync(npx, [...prefix, 'd1', 'migrations', 'apply', 'carter-site-activity', '--local'], { cwd: directory, env, timeout: 60000, stdio: 'pipe' });
    server = spawn(npx, [...prefix, 'pages', 'dev', '_site', '--ip', '127.0.0.1', '--port', String(port), '--inspector-port', '0', '--log-level', 'error'], { cwd: directory, env, detached: process.platform !== 'win32', stdio: ['ignore', 'pipe', 'pipe'] });
    server.on('error', error => { output += error.message; });
    const append = chunk => { output = (output + chunk.toString()).slice(-8000); };
    server.stdout.on('data', append); server.stderr.on('data', append);
    const get = (url, options = {}) => fetch(origin + url, { ...options, signal: AbortSignal.timeout(3000) });
    let ready = false;
    for (let attempt = 0; attempt < 80; attempt++) {
      if (server.exitCode !== null) throw new Error('Local runtime exited before startup.\n' + output);
      try { if ((await get('/')).ok) { ready = true; break; } } catch { /* Wait only for this test server's readiness. */ }
      await delay(250);
    }
    assert.ok(ready, 'Local runtime did not become ready.\n' + output);
    for (const route of ['/api/owner/stats', '/api/owner/setup']) assert.equal((await get(route)).status, 401);
    assert.match(await (await get('/private')).text(), /Sign in with GitHub/);
    const { sign } = await import(pathToFileURL(path.join(root, 'functions/_lib/security.js')).href);
    const session = await sign({ purpose: 'owner', id: 168453384, exp: Date.now() / 1000 + 300 }, secret);
    const headers = { Cookie: '__Host-carter_session=' + session };
    const setup = await (await get('/api/owner/setup', { headers })).json();
    assert.equal(setup.checks.find(check => check.id === 'database').configured, true);
    assert.equal(setup.checks.find(check => check.id === 'email').configured, false);
    assert.match(await (await get('/private', { headers })).text(), /id="setup-checks"/);
    const post = (url, data, extra = {}) => get(url, { method: 'POST', headers: { Origin: origin, 'Content-Type': 'application/json', ...extra }, body: JSON.stringify(data) });
    for (const area of ['professional', 'sports']) assert.equal((await post('/api/track', { area })).status, 200);
    assert.deepEqual(await (await post('/api/track', { area: 'sports' }, { Cookie: '__Host-carter_exclude=1' })).json(), { skipped: true });
    const stats = await (await get('/api/owner/stats', { headers })).json();
    assert.equal(stats.rows.length, 2); assert.ok(stats.rows.every(row => row.views === 1));
    assert.equal((await post('/api/feedback', { message: 'Local test; must not send any email.' })).status, 503);
    assert.equal((await post('/api/owner/exclude', { exclude: false }, headers)).status, 200);
    assert.equal((await post('/api/auth/logout', {}, headers)).status, 200);
    console.log('Local Cloudflare/D1 checks passed: migrations, protected routes, owner setup, split counts, exclusion, missing email and sign-out. No remote resources or email were used.');
  } finally {
    if (server?.pid) {
      const exited = new Promise(resolve => server.once('close', resolve));
      try { if (process.platform === 'win32') server.kill(); else process.kill(-server.pid, 'SIGTERM'); } catch { /* Already stopped. */ }
      await Promise.race([exited, delay(3000)]);
    }
    // Only the unique directory created above; never the user's data or config.
    fs.rmSync(directory, { recursive: true, force: true });
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
