// Coarse page views only. No cookies, fingerprinting, query strings or referrers sent.
if (navigator.doNotTrack !== '1' && !navigator.globalPrivacyControl) {
  fetch('/api/track', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ area: location.pathname.includes('/sports/') ? 'sports' : 'professional' }), keepalive: true }).catch(() => {});
}
