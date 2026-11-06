// Pages redirects static .html assets to clean URLs. Google must also be able
// to fetch this exact verification filename without a redirect. Keep the body
// byte-identical to site/google5f578c920a2f92ee.html (covered by a test).
const verification = 'google-site-verification: google5f578c920a2f92ee.html';

export function onRequest({ request }) {
  if (!['GET', 'HEAD'].includes(request.method)) {
    return new Response('Method not allowed', { status: 405, headers: { Allow: 'GET, HEAD' } });
  }
  return new Response(request.method === 'HEAD' ? null : verification, {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'public, max-age=300',
      'X-Content-Type-Options': 'nosniff',
    },
  });
}
