const {test,expect}=require('@playwright/test');
const AxeBuilder=require('@axe-core/playwright').default;
test('personal website and sports navigation are accessible',async({page},info)=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('/');
 await expect(page.getByRole('heading',{level:1})).toContainText('Carter');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(audit.violations).toEqual([]);
 await page.screenshot({path:'/tmp/opencode/carter-website-'+info.project.name+'.png',fullPage:true});
 await page.getByRole('navigation').getByRole('link',{name:'Sports Analysis'}).click();
 await expect(page.locator('#ATP-status')).toContainText('players');
 await expect(page.locator('#WTA-status')).toContainText('players');
  expect(errors).toEqual([]);
 });
test('academic profile sections, history, and deep links work',async({page})=>{
 await page.goto('/');
 const nav=page.getByRole('navigation',{name:'Main navigation'});
  await expect(nav.getByRole('link')).toHaveText(['About Me','Research','Publications','Talks & Conferences','Sports Analysis','Hobbies','CV','Contact']);
  expect(await page.locator('.portrait').evaluate(img=>img.complete&&img.naturalWidth>0)).toBeTruthy();
 await expect(page.locator('.profile-details')).toHaveText('Graduate Student • Rochester Institute of Technology');
 await expect(page.locator('.profile-intro')).toHaveText('I am an astrophysics graduate student working on high redshift galaxy evolution, focusing on quiescent galaxies, utilizing the COSMOS-Web dataset.');
 for(const [label,id] of [['Research','research'],['Publications','publications'],['Talks & Conferences','talks'],['Hobbies','hobbies'],['About Me','about']]){
  await nav.getByRole('link',{name:label,exact:true}).click();
  await expect(page.locator('#'+id)).toBeVisible();
  await expect(page.locator('.content-section:visible')).toHaveCount(1);
  await expect(page.locator('.profile-header')).toBeInViewport();
  await expect(nav.getByRole('link',{name:label,exact:true})).toHaveAttribute('aria-current','page');
 }
 await page.goBack();await expect(page.locator('#hobbies')).toBeVisible();
 await page.goto('/#research');await expect(page.locator('#research')).toBeVisible();
 await expect(page.locator('.profile-header')).toBeInViewport();
 await expect(page.locator('.research-image img')).toBeVisible();
 expect(await page.locator('.research-image img').evaluate(img=>img.complete&&img.naturalWidth>0)).toBeTruthy();
 const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(audit.violations).toEqual([]);
 await page.goto('/sports/');await nav.getByRole('link',{name:'Publications',exact:true}).click();
 await expect(page.locator('#publications')).toBeVisible();
});
test('publications are paper-only, deduplicated, and citation-ranked',async({page})=>{
 await page.goto('/#publications');
 const publications=page.locator('#publications');
  await expect(publications).toBeVisible();
  await expect(publications).not.toContainText('Articles and preprints, with each paper listed once.');
  await expect(publications).not.toContainText('Citation counts are a dated SciX snapshot');
 await expect(page.locator('.profile-header')).toBeInViewport();
 const snapshot=require('../../site/publications.json');
 const items=await publications.locator('.publication').evaluateAll(els=>els.map(el=>({id:el.dataset.bibcode,citations:Number(el.dataset.citations),text:el.textContent})));
 expect(items.length).toBeGreaterThan(0);
 expect(new Set(items.map(i=>i.id)).size).toBe(items.length);
  expect(items.map(i=>i.citations)).toEqual(items.map(i=>i.citations).sort((a,b)=>b-a));
  await expect(publications.locator('.publication-list')).toHaveCount(1);
  await expect(publications.getByRole('heading',{name:'Co-authored papers'})).toHaveCount(0);
 const types=new Map(snapshot.records.map(d=>[d.bibcode,d.doctype]));
 expect(items.every(i=>['article','eprint'].includes(types.get(i.id)))).toBeTruthy();
 await expect(publications.locator('time')).toHaveAttribute('datetime',snapshot.checked_at.slice(0,10));
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.screenshot({path:'/tmp/opencode/carter-publications.png',fullPage:true});
 const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(audit.violations).toEqual([]);
});
test('publication filters and ordering work independently',async({page})=>{
 await page.goto('/#publications');const section=page.locator('#publications');
 const total=await section.locator('.publication').count();
 await section.getByRole('button',{name:'First author',exact:true}).click();
 const first=await section.locator('.publication[data-first-author="true"]').count();
 await expect(section.locator('.publication:visible')).toHaveCount(first);
 if(!first)await expect(section.getByRole('status')).toHaveText('No papers in this selection yet.');
 await section.getByRole('button',{name:'Refereed',exact:true}).click();
 const refereed=await section.locator('.publication[data-refereed="true"]').count();
 await expect(section.locator('.publication:visible')).toHaveCount(refereed);
 await section.getByRole('button',{name:'Non-refereed',exact:true}).click();
 await expect(section.locator('.publication:visible')).toHaveCount(total-refereed);
 await section.locator('#publication-sort').selectOption('newest');
 const dates=await section.locator('.publication:visible').evaluateAll(es=>es.map(e=>e.dataset.date));expect(dates).toEqual([...dates].sort().reverse());
 await section.getByRole('button',{name:'All papers',exact:true}).click();await expect(section.locator('.publication:visible')).toHaveCount(total);
 await section.locator('#publication-sort').selectOption('title');
 const titles=await section.locator('.publication:visible h3').allTextContents();expect(titles).toEqual([...titles].sort((a,b)=>a.localeCompare(b)));
 const nonFirst=section.locator('.publication[data-first-author="false"]');
 if(await nonFirst.count()){
  await nonFirst.first().evaluate(el=>el.dataset.firstAuthor='true');
  await section.getByRole('button',{name:'First author',exact:true}).click();await expect(section.locator('.publication:visible')).toHaveCount(first+1);
 }
});
test('CV, Contact, hobbies and newest-first talks use supplied information',async({page,request})=>{
 await page.goto('/#talks');
 const dates=await page.locator('.talk-list li').evaluateAll(es=>es.map(e=>e.dataset.date));expect(dates).toEqual(['2026-03','2025-10','2025-05','2024-10']);
 const nav=page.getByRole('navigation',{name:'Main navigation'});
 const cv=nav.getByRole('link',{name:'CV (PDF, opens in a new tab)',exact:true});
 const response=await request.get(await cv.getAttribute('href'));expect(response.ok()).toBeTruthy();expect((await response.body()).subarray(0,5).toString()).toBe('%PDF-');
 await nav.getByRole('link',{name:'Contact',exact:true}).click();
 await expect(page.locator('#contact a[href="mailto:cbf2388@rit.edu"]')).toBeVisible();await expect(page.locator('#contact a[href="mailto:carter.flayhart@gmail.com"]')).toBeVisible();
 await nav.getByRole('link',{name:'Hobbies',exact:true}).click();
 await expect(page.locator('#hobbies h3')).toHaveText(['Climbing','Hiking / Walking','Travel','Watching Sports']);
 await expect(page.locator('#hobbies')).toContainText('F1, and MMA');
 const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(audit.violations).toEqual([]);
});
test('published rankings are dated, searchable, and tour-isolated',async({page})=>{
 await page.goto('/sports/tennis/?tour=ATP');
  await expect(page.locator('#published-source')).toContainText('ATP rankings via TennisONE');
  await expect(page.locator('#published-source')).toContainText('edition date not supplied');
 await expect(page.locator('#published-body tr')).toHaveCount(50);
 await page.locator('#published-search').fill('Sinner');await expect(page.locator('#published-body')).toContainText('Jannik Sinner');await expect(page.locator('#published-body tr')).toHaveCount(1);
 await page.locator('#wta').click();
  await expect(page.locator('#published-source')).toContainText('WTA rankings via TennisONE');await expect(page.locator('#published-search')).toHaveValue('');
 await expect(page.locator('#published-body tr')).toHaveCount(50);await expect(page.locator('#published-body')).not.toContainText('Jannik Sinner');
 await page.locator('#published-search').fill('Rybakina');await expect(page.locator('#published-body')).toContainText('Elena Rybakina');
 await page.locator('#published-search').fill('');await page.locator('#published-more').click();await expect(page.locator('#published-body tr')).toHaveCount(100);
 const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(audit.violations).toEqual([]);
});
test('academic site remains usable without JavaScript',async({browser,baseURL})=>{
 const context=await browser.newContext({javaScriptEnabled:false});
 const page=await context.newPage();await page.goto(baseURL+'/');
  await expect(page.locator('.content-section:visible')).toHaveCount(6);
  const papers=await page.locator('.publication').count();expect(papers).toBeGreaterThan(0);
  await expect(page.locator('.publication:visible')).toHaveCount(papers);
  await expect(page.locator('.publication-controls')).toBeHidden();
 await page.getByRole('navigation').getByRole('link',{name:'Research',exact:true}).click();
 await expect(page).toHaveURL(/#research$/);
 await context.close();
});
test('static Pages ATP/WTA work without a Python API and remain isolated',async({page},info)=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/sports/tennis/?tour=ATP');await expect(page.locator('#table-body tr')).toHaveCount(25);
 await expect(page.locator('#freshness')).toContainText('Separate ATP');
  await page.locator('#search').fill('Sinner');await expect(page.locator('#table-body tr')).toHaveCount(1);
  const published=await(await page.request.get('/sports/tennis/official-rankings.json')).json();
  const officialSinner=published.tours.ATP.rows.find(p=>p.name==='Jannik Sinner');
  await expect(page.locator('#table-body')).toContainText(officialSinner.points.toLocaleString('en-US')+' pts');
  await page.getByRole('button',{name:'Open Jannik Sinner notebook'}).click();await expect(page.locator('#player-title')).toHaveText('Jannik Sinner');
  await expect(page.locator('#player-content')).toContainText('rank prior');
  await expect(page.locator('#player-content')).toContainText('TennisONE observed');
  await expect(page.locator('#profile-basis option[value="atp"]')).toHaveJSProperty('disabled',true);
 await page.locator('#result-mode').selectOption('0');await expect(page.locator('.match-card').first()).toBeVisible();
 const audit=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(audit.violations).toEqual([]);
 await page.keyboard.press('Escape');await page.locator('#wta').click();await expect(page.locator('#freshness')).toContainText('Separate WTA');
  await expect(page.locator('#table-body tr')).toHaveCount(25);await expect(page.locator('#table-body')).not.toContainText('Jannik Sinner');
  await expect(page.locator('[data-surface="Carpet"]')).toHaveCount(0);
  for(const surface of ['Indoor hard','Outdoor hard']){
   await page.locator(`[data-surface="${surface}"]`).click();await expect(page.locator('#result-count')).toContainText(surface);
   await expect(page.locator('#table-body tr')).toHaveCount(25);
  }
 await page.locator('[data-surface="Clay"]').click();await expect(page.locator('#result-count')).toContainText('Clay');
 await page.locator('#window').selectOption('recent');await expect(page.locator('#result-count')).toContainText('3-month');
 await page.locator('#filter-toggle').click();await page.locator('#no-ret').check();await page.locator('#expanded').check();await expect(page.locator('#table-head')).toContainText('vs similar');
 await page.locator('#coverage-open').click();await expect(page.locator('#info-content')).toContainText('CC BY 4.0');await page.keyboard.press('Escape');
  await page.locator('#method-open').click();await expect(page.locator('#info-content')).toContainText('not hidden');
  await expect(page.locator('#info-content')).toContainText('ITF 8%');await expect(page.locator('#info-content')).toContainText('35% blend');await page.keyboard.press('Escape');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.screenshot({path:'/tmp/opencode/pages-tennis-'+info.project.name+'.png'});expect(errors).toEqual([]);
});
