export const siteOrigin = env => env.SITE_ORIGIN || 'https://carterflayhart.pages.dev';
export const loginConfigured = env => Boolean(env.GITHUB_CLIENT_ID && env.GITHUB_CLIENT_SECRET &&
  typeof env.SESSION_SECRET === 'string' && new TextEncoder().encode(env.SESSION_SECRET).length >= 32 &&
  /^\d+$/.test(String(env.GITHUB_OWNER_ID || '')));

// Only called after owner authorization. No credential values or provider calls.
export async function setupChecks(env) {
  let database = false;
  if (env.DB) {
    try {
      const { results } = await env.DB.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('page_views','rate_limits')").all();
      database = ['page_views', 'rate_limits'].every(name => results.some(row => row.name === name));
    } catch { /* Misconfigured/missing migrations must remain visible as incomplete. */ }
  }
  return { checks: [
    { id: 'login', title: 'Owner sign-in', configured: loginConfigured(env), message: loginConfigured(env) ? 'Configuration present. This request passed owner authorization.' : 'Check the GitHub OAuth credentials, owner ID and a session secret of at least 32 bytes.' },
    { id: 'database', title: 'Activity database', configured: database, message: database ? 'DB is connected and both required tables are present.' : 'Bind the D1 database as DB and apply its migrations.' },
    { id: 'email', title: 'Feedback email', configured: Boolean(env.RESEND_API_KEY && env.FEEDBACK_FROM), message: env.RESEND_API_KEY && env.FEEDBACK_FROM ? 'Sender configuration present. Send a feedback message and confirm arrival; delivery has not been verified by this check.' : 'Add RESEND_API_KEY and FEEDBACK_FROM, then verify actual delivery.' },
  ], checked_at: new Date().toISOString() };
}
