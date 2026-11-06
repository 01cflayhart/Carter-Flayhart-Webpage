// CI-only credential preflight. Never print token values or API response bodies.
async function checkAccess(env, fetcher = fetch) {
  const { CLOUDFLARE_API_TOKEN: token, CLOUDFLARE_ACCOUNT_ID: account, CLOUDFLARE_D1_DATABASE_ID: database } = env;
  if (!token) throw new Error('Missing GitHub Actions secret CLOUDFLARE_API_TOKEN.');
  if (!/^[a-f0-9]{32}$/i.test(account || '')) throw new Error('CLOUDFLARE_ACCOUNT_ID must contain the 32-character Cloudflare account ID, not a database ID or API token.');
  if (!/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(database || '')) throw new Error('CLOUDFLARE_D1_DATABASE_ID must be the D1 UUID repository variable.');
  const checks = [
    { name: 'D1 query', path: `/d1/database/${database}/query`, method: 'POST', body: JSON.stringify({ sql: 'SELECT 1 AS ready' }) },
    { name: 'Pages project', path: '/pages/projects/carterflayhart', method: 'GET' },
  ];
  for (const check of checks) {
    let response, data;
    try {
      response = await fetcher(`https://api.cloudflare.com/client/v4/accounts/${account}${check.path}`, {
        method: check.method, headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
        ...(check.body ? { body: check.body } : {}), signal: AbortSignal.timeout(20000),
      });
      data = await response.json();
    } catch { throw new Error(`${check.name} preflight could not reach or decode the Cloudflare API. Retry; no credentials were printed.`); }
    if (!response.ok || data.success !== true) {
      const code = data.errors?.find(error => Number.isInteger(error.code))?.code ?? 'unknown';
      throw new Error(`${check.name} authorization failed (HTTP ${response.status}, Cloudflare code ${code}). Verify the account ID and replace/update CLOUDFLARE_API_TOKEN if needed: Account policy, D1 Edit and Cloudflare Pages Edit, restricted to the account containing these resources. See docs/launch-guide.md. No credential values were printed.`);
    }
  }
}
if (require.main === module) checkAccess(process.env).then(() => {
  console.log('Cloudflare preflight passed: D1 read-only query and Pages project lookup authorized. Deployment will separately verify write access.');
}).catch(error => { console.error(error.message); process.exitCode = 1; });
module.exports = { checkAccess };
