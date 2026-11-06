// Generate deployment configuration, never a token or runtime secret.
const fs = require('node:fs');
const path = require('node:path');

function configuration(env) {
  const id = env.CLOUDFLARE_D1_DATABASE_ID?.trim();
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id || '')) {
    throw new Error('Set CLOUDFLARE_D1_DATABASE_ID to the database UUID from Cloudflare D1. No configuration was written.');
  }
  return {
    name: 'carterflayhart',
    pages_build_output_dir: '_site',
    compatibility_date: '2026-11-01',
    vars: { GITHUB_OWNER_ID: '168453384', SITE_ORIGIN: 'https://carterflayhart.pages.dev' },
    d1_databases: [{ binding: 'DB', database_name: 'carter-site-activity', database_id: id, migrations_dir: 'migrations' }],
  };
}

if (require.main === module) {
  try {
    const config = configuration(process.env);
    const target = path.resolve(__dirname, '../wrangler.jsonc');
    // Refuse to overwrite a locally customized configuration.
    const content = JSON.stringify(config, null, 2) + '\n';
    if (fs.existsSync(target) && fs.readFileSync(target, 'utf8') !== content) {
      throw new Error('wrangler.jsonc already differs. Review it manually; it was not overwritten.');
    }
    fs.writeFileSync(target, content, { mode: 0o600 });
    console.log('Created wrangler.jsonc with the D1 binding and production origin. No secrets were written.');
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}

module.exports = { configuration };
