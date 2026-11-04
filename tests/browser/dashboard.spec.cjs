const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

async function ready(page) {
  await page.goto('/');
  await expect(page.locator('#rankings')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('#table-body tr')).toHaveCount(25);
}

test('responsive overview, source honesty, and accessible page', async ({ page }, testInfo) => {
  const errors=[];
  page.on('pageerror', error=>errors.push(error.message));
  await ready(page);
  await expect(page.locator('#freshness')).toContainText('Coverage is not certified exhaustive');
  await expect(page.locator('#edition-date')).toContainText('2026');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.screenshot({ path: `/tmp/opencode/court-current-${testInfo.project.name}.png` });
  const accessibility=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(accessibility.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,issue:n.failureSummary}))}))).toEqual([]);
  expect(errors).toEqual([]);
});

test('search, empty state, sorting, surfaces, and full statistics', async ({ page }) => {
  await ready(page);
  await page.getByLabel('Search player or country').fill('Sinner');
  await expect(page.locator('#result-count')).toContainText('of 1 players');
  await expect(page.locator('#table-body')).toContainText('Jannik Sinner');
  await page.getByLabel('Search player or country').fill('not-a-real-tennis-player-000');
  await expect(page.locator('#table-body')).toContainText('No players match');
  await page.getByLabel('Search player or country').fill('');
  await expect(page.locator('#table-body tr')).toHaveCount(25);
  await page.locator('[data-surface="Clay"]').click();
  await expect(page.locator('[data-surface="Clay"]')).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('#result-count')).toContainText('Clay');
  await page.locator('#basis').selectOption('power');
  await page.locator('#window').selectOption('recent');
  await expect(page.locator('#result-count')).toContainText('3-month');
  await page.locator('#filter-toggle').click();
  await page.locator('#expanded').check();
  await expect(page.locator('#table-head')).toContainText('vs similar');
  await page.locator('[data-sort="atp_rank"]').click();
  await expect(page.locator('th[aria-sort]')).toContainText('ATP rank');
  await page.locator('[data-sort="record"][data-metric="similar"]').click();
  await expect(page.locator('th[aria-sort]')).toContainText('vs similar');
});

test('player notebook, unavailable official ranks, all results, and dialog accessibility', async ({ page }) => {
  await ready(page);
  await page.getByLabel('Search player or country').fill('Sinner');
  await expect(page.locator('#table-body tr')).toHaveCount(1);
  await page.getByRole('button',{name:'Open Jannik Sinner notebook'}).click();
  await expect(page.getByRole('dialog',{name:'Jannik Sinner'})).toBeVisible();
  await expect(page.locator('#match-count-label')).toContainText('results');
  await expect(page.locator('#player-content')).toContainText('Past 12 months');
  await expect(page.locator('#player-content')).toContainText('Past 3 months');
  await expect(page.locator('#profile-basis option[value="atp"]')).toHaveAttribute('disabled','');
  await expect(page.locator('#profile-basis')).toHaveValue('power');
  await page.locator('#result-mode').selectOption('0');
  await expect(page.locator('#match-results .match-card').first()).toBeVisible();
  const accessibility=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(accessibility.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,issue:n.failureSummary}))}))).toEqual([]);
  await page.keyboard.press('Escape');
  await expect(page.locator('#player-dialog')).not.toBeVisible();
});

test('methodology, coverage ledger, independent WTA and keyboard access', async ({ page }) => {
  await ready(page);
  await page.locator('#wta').click();
  await expect(page.locator('#freshness')).toContainText('Separate WTA rankings');
  await expect(page.locator('#table-head')).toContainText('WTA rank');
  await expect(page.locator('#table-body')).not.toContainText('Jannik Sinner');
  await page.locator('#coverage-open').click();
  await expect(page.locator('#info-content')).toContainText('SHA-256');
  await expect(page.locator('#info-content')).toContainText('Excluded rows');
  await page.keyboard.press('Escape');
  await page.locator('#method-open').focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#info-content')).toContainText('historical Elo anchor');
  await expect(page.locator('#info-content')).toContainText('Basic Elo');
  await page.keyboard.press('Escape');
  await expect(page.locator('#method-open')).toBeFocused();
});

test('API error state is actionable and retryable', async ({page})=>{
  await page.route('**/api/rankings?*', route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Test data temporarily unavailable'})}));
  await page.goto('/');
  await expect(page.locator('#table-body')).toContainText('Test data temporarily unavailable');
  await page.unroute('**/api/rankings?*');
  await page.locator('#retry').click();
  await expect(page.locator('#table-body tr')).toHaveCount(25);
});

test('open page follows new publications and reports a lost connection',async({page})=>{
  await page.clock.install();
  await page.goto('/');
  await expect(page.locator('#table-body tr')).toHaveCount(25);
  const response=await page.request.get('/api/meta?tour=ATP');
  const current=await response.json();
  await page.route('**/api/meta?*',route=>route.fulfill({json:{...current,generated_at:'a-new-validated-publication'}}));
  await page.clock.fastForward(61000);
  await expect(page.locator('#toast')).toContainText('Rankings have been refreshed');
  await page.unroute('**/api/meta?*');
  await page.route('**/api/meta?*',route=>route.fulfill({status:503,json:{error:'Unavailable'}}));
  await page.clock.fastForward(61000);
  await expect(page.locator('#freshness')).toContainText('cannot be reached');
  await expect(page.locator('#table-body tr')).toHaveCount(25);
});
