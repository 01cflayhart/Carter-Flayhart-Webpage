const encoder = new TextEncoder();
const cookieName = '__Host-carter_session';
export const cookie = (request, name) => (request.headers.get('Cookie') || '').split(';').map(v => v.trim()).find(v => v.startsWith(name + '='))?.slice(name.length + 1);
export const cookieHeader = (name, value, seconds) => `${name}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${seconds}`;
export function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex', 'Vary': 'Cookie' } });
}
function base64(data) { return btoa(String.fromCharCode(...new Uint8Array(data))).replaceAll('+', '-').replaceAll('/', '_').replaceAll('=', ''); }
function unbase64(value) { return Uint8Array.from(atob(value.replaceAll('-', '+').replaceAll('_', '/')), c => c.charCodeAt(0)); }
async function key(secret) { return crypto.subtle.importKey('raw', encoder.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']); }
export async function sign(data, secret) {
  const body = base64(encoder.encode(JSON.stringify(data)));
  return body + '.' + base64(await crypto.subtle.sign('HMAC', await key(secret), encoder.encode(body)));
}
export async function verify(token, secret) {
  try {
    const [body, signature, extra] = token.split('.');
    if (extra || !await crypto.subtle.verify('HMAC', await key(secret), unbase64(signature), encoder.encode(body))) return null;
    const data = JSON.parse(new TextDecoder().decode(unbase64(body)));
    return data.exp > Date.now() / 1000 ? data : null;
  } catch { return null; }
}
export async function owner(request, env) {
  if (!env.SESSION_SECRET || !env.GITHUB_OWNER_ID) return null;
  const data = await verify(cookie(request, cookieName) || '', env.SESSION_SECRET);
  return data?.purpose === 'owner' && String(data.id) === String(env.GITHUB_OWNER_ID) ? data : null;
}
export function sameOrigin(request) { return request.headers.get('Origin') === new URL(request.url).origin; }
export async function body(request, max = 6000) {
  if (!request.headers.get('Content-Type')?.startsWith('application/json')) throw new Error('JSON required');
  const reader = request.body?.getReader(); if (!reader) throw new Error('Missing body');
  let size = 0; const chunks = [];
  while (true) { const { done, value } = await reader.read(); if (done) break; size += value.length; if (size > max) { await reader.cancel(); throw new Error('Too large'); } chunks.push(value); }
  const bytes = new Uint8Array(size); let at = 0; for (const chunk of chunks) { bytes.set(chunk, at); at += chunk.length; }
  return JSON.parse(new TextDecoder().decode(bytes));
}
export async function rateLimit(request, env, scope, limit) {
  if (!env.DB || !env.SESSION_SECRET) return false;
  const day = new Date().toISOString().slice(0, 10);
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  // A rotating HMAC, never the raw address; delete expired rows on each check.
  const hash = base64(await crypto.subtle.sign('HMAC', await key(env.SESSION_SECRET), encoder.encode(`${day}:${ip}:${scope}`)));
  await env.DB.prepare('DELETE FROM rate_limits WHERE day < ?').bind(day).run();
  const result = await env.DB.prepare('INSERT INTO rate_limits (key, day, count) VALUES (?, ?, 1) ON CONFLICT(key) DO UPDATE SET count=count+1 RETURNING count').bind(hash, day).first();
  return result.count <= limit;
}
export { cookieName };
