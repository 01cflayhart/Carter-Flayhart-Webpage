// Run one browser worker without starting another OpenCode service. Optional
// unpacked Linux libraries survive WSL restarts in the user's cache, not /tmp.
const { existsSync } = require('node:fs');
const { homedir } = require('node:os');
const { join } = require('node:path');
const { spawn } = require('node:child_process');

const env = { ...process.env };
const libraries = join(homedir(), '.cache/carter-website/browser-libs/usr/lib/x86_64-linux-gnu');
if (process.platform === 'linux' && existsSync(libraries)) {
  env.LD_LIBRARY_PATH = [libraries, env.LD_LIBRARY_PATH].filter(Boolean).join(':');
}
const child = spawn(process.execPath, [require.resolve('@playwright/test/cli'), 'test',
  '--config', 'playwright.pages.config.cjs', ...process.argv.slice(2), '--workers=1'], {
  env, stdio: 'inherit', cwd: join(__dirname, '..'),
});
child.on('error', error => { console.error(error.message); process.exitCode = 1; });
child.on('exit', code => { process.exitCode = code ?? 1; });
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
