import { body, cookie, cookieHeader, cookieName, json, owner, rateLimit, sameOrigin, sign, verify } from '../_lib/security.js';
import { loginConfigured, setupChecks, siteOrigin } from '../_lib/setup.js';

export async function onRequest({ request, env }) {
  const url = new URL(request.url), path = url.pathname;
  try {
    if (path === '/api/auth/start' || path === '/api/auth/callback') {
      if (url.origin !== siteOrigin(env)) return json({ error: 'Owner login is available only on the configured production website.' }, 403);
    }
    if (path === '/api/auth/start' && request.method === 'GET') {
      if (!loginConfigured(env)) return json({ error: 'Owner login is not configured yet.' }, 503);
      const state = crypto.randomUUID();
      const authorize = new URL('https://github.com/login/oauth/authorize');
      authorize.search = new URLSearchParams({ client_id: env.GITHUB_CLIENT_ID, redirect_uri: url.origin + '/api/auth/callback', state }).toString();
      return new Response(null, { status: 302, headers: { Location: authorize.href, 'Cache-Control': 'no-store', 'Set-Cookie': cookieHeader('__Host-carter_oauth', await sign({ purpose: 'oauth', state, exp: Date.now() / 1000 + 600 }, env.SESSION_SECRET), 600) } });
    }
    if (path === '/api/auth/callback' && request.method === 'GET') {
      if (!loginConfigured(env)) return json({ error: 'Login unavailable' }, 503);
      const state = await verify(cookie(request, '__Host-carter_oauth') || '', env.SESSION_SECRET);
      if (state?.purpose !== 'oauth' || !state?.state || state.state !== url.searchParams.get('state') || !url.searchParams.get('code')) return json({ error: 'Invalid or expired login state' }, 403);
      const exchange = await fetch('https://github.com/login/oauth/access_token', { method: 'POST', headers: { Accept: 'application/json', 'Content-Type': 'application/json' }, body: JSON.stringify({ client_id: env.GITHUB_CLIENT_ID, client_secret: env.GITHUB_CLIENT_SECRET, code: url.searchParams.get('code'), redirect_uri: url.origin + '/api/auth/callback' }) });
      const token = await exchange.json();
      if (!exchange.ok || !token.access_token) return json({ error: 'GitHub login failed' }, 403);
      const response = await fetch('https://api.github.com/user', { headers: { Authorization: 'Bearer ' + token.access_token, 'User-Agent': 'CarterFlayhartWebsite', Accept: 'application/vnd.github+json' } });
      const user = await response.json();
      // Authorize by immutable GitHub numeric ID, not a mutable login or email.
      if (!response.ok || String(user.id) !== String(env.GITHUB_OWNER_ID)) return json({ error: 'This dashboard is owner-only.' }, 403);
      const headers = new Headers({ Location: '/private', 'Cache-Control': 'no-store' });
      headers.append('Set-Cookie', cookieHeader(cookieName, await sign({ purpose: 'owner', id: user.id, exp: Date.now() / 1000 + 28800 }, env.SESSION_SECRET), 28800));
      headers.append('Set-Cookie', cookieHeader('__Host-carter_oauth', '', 0));
      if (cookie(request, '__Host-carter_exclude') !== '0') headers.append('Set-Cookie', cookieHeader('__Host-carter_exclude', '1', 31536000));
      return new Response(null, { status: 302, headers });
    }
    if (path === '/api/owner/session' && request.method === 'GET') {
      return await owner(request, env) ? json({ owner: true }) : json({ owner: false }, 401);
    }
    if (path === '/api/owner/setup' && request.method === 'GET') {
      if (!await owner(request, env)) return json({ error: 'Owner login required' }, 401);
      return json(await setupChecks(env));
    }
    if (path === '/api/owner/stats' && request.method === 'GET') {
      if (!await owner(request, env)) return json({ error: 'Owner login required' }, 401);
      if (!env.DB) return json({ error: 'Analytics database not configured' }, 503);
      const totals = await env.DB.prepare('SELECT day, area, SUM(views) AS views FROM page_views GROUP BY day, area ORDER BY day DESC LIMIT 730').all();
      return json({ rows: totals.results, owner_excluded: cookie(request, '__Host-carter_exclude') !== '0' });
    }
    if (path === '/api/owner/exclude' && request.method === 'POST') {
      if (!sameOrigin(request) || !await owner(request, env)) return json({ error: 'Owner login required' }, 403);
      const data = await body(request); if (typeof data.exclude !== 'boolean') return json({ error: 'Boolean required' }, 400);
      const response = json({ owner_excluded: data.exclude });
      response.headers.append('Set-Cookie', cookieHeader('__Host-carter_exclude', data.exclude ? '1' : '0', 31536000));
      return response;
    }
    if (path === '/api/auth/logout' && request.method === 'POST') {
      if (!sameOrigin(request)) return json({ error: 'Forbidden' }, 403);
      const response = json({ ok: true }); response.headers.append('Set-Cookie', cookieHeader(cookieName, '', 0)); return response;
    }
    if (path === '/api/track' && request.method === 'POST') {
      if (!sameOrigin(request)) return json({ error: 'Forbidden' }, 403);
      if (request.headers.get('DNT') === '1' || request.headers.get('Sec-GPC') === '1') return json({ skipped: true });
      if (cookie(request, '__Host-carter_exclude') === '1' || (await owner(request, env) && cookie(request, '__Host-carter_exclude') !== '0')) return json({ skipped: true });
      if (!await rateLimit(request, env, 'track', 300)) return json({ error: 'Unavailable or rate limited' }, 429);
      const data = await body(request, 1000);
      // Store a coarse area, not URLs, queries, identifiers, user agents or referrers.
      if (!['sports', 'professional'].includes(data.area)) return json({ error: 'Invalid area' }, 400);
      await env.DB.prepare('INSERT INTO page_views (day, area, views) VALUES (?, ?, 1) ON CONFLICT(day,area) DO UPDATE SET views=views+1').bind(new Date().toISOString().slice(0, 10), data.area).run();
      return json({ ok: true });
    }
    if (path === '/api/feedback' && request.method === 'POST') {
      if (!sameOrigin(request)) return json({ error: 'Forbidden' }, 403);
      if (!env.RESEND_API_KEY || !env.FEEDBACK_FROM) return json({ error: 'Email service not configured. Please email Carter directly.' }, 503);
      const data = await body(request);
      if (data.website) return json({ ok: true });
      if (typeof data.message !== 'string' || data.message.trim().length < 10 || data.message.length > 4000 || (data.email && (typeof data.email !== 'string' || data.email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)))) return json({ error: 'Invalid feedback' }, 400);
      if (!await rateLimit(request, env, 'feedback', 5)) return json({ error: 'Please try again later or email directly.' }, 429);
      const result = await fetch('https://api.resend.com/emails', { method: 'POST', headers: { Authorization: 'Bearer ' + env.RESEND_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ from: env.FEEDBACK_FROM, to: ['carter.flayhart@gmail.com'], subject: 'Sports Analysis Hub feedback', ...(data.email ? { reply_to: data.email } : {}), text: data.message.trim() }) });
      return result.ok ? json({ ok: true }) : json({ error: 'Email delivery failed. Please email directly.' }, 502);
    }
    return json({ error: 'Not found' }, 404);
  } catch { return json({ error: 'Request could not be processed' }, 400); }
}
