// Read-only access to the public Overleaf project. Never store its session,
// compilation URLs, document sources, or cookies in the public site.
const { chromium } = require('@playwright/test');
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const source = 'https://www.overleaf.com/read/qsmrnbtftnkq#74c7cd';

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    const pdfPromise = page.waitForResponse(response => {
      const url = new URL(response.url());
      return url.hostname === 'compiles.overleafusercontent.com' && url.pathname.endsWith('/output/output.pdf') && [200, 206].includes(response.status());
    }, { timeout: 120000 });
    // Handle rejection even if navigation fails before awaiting the PDF.
    pdfPromise.catch(() => {});
    const navigation = await page.goto(source, { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (!navigation.ok()) throw new Error('Overleaf read-only document is unavailable');
    const response = await pdfPromise;
    const full = await context.request.get(response.url(), { timeout: 60000 });
    const bytes = await full.body();
    if (full.status() !== 200 || bytes.length < 1000 || bytes.length > 10000000 || !bytes.subarray(0, 5).equals(Buffer.from('%PDF-')) || !bytes.subarray(-2048).includes(Buffer.from('%%EOF'))) throw new Error('Overleaf returned an incomplete or invalid PDF');
    const target = path.resolve(__dirname, '../site/assets/carter-flayhart-cv.pdf');
    // No timestamp-only commits when the PDF is unchanged.
    let previous;
    try { previous = await fs.readFile(target); } catch {}
    if (!previous?.equals(bytes)) {
      await fs.writeFile(target + '.download', bytes);
      await fs.rename(target + '.download', target);
    }
    console.log(`CV: validated PDF (${bytes.length} bytes, SHA-256 ${crypto.createHash('sha256').update(bytes).digest('hex')})`);
  } finally { await browser.close(); }
})().catch(() => { console.error('CV refresh failed; last valid PDF preserved. Check public Overleaf access and compilation.'); process.exitCode = 1; });
