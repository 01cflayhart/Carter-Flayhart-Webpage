// Read ordinary public profile pages; never solve challenges or use login cookies.
// A shared name only proposes a candidate. DOB (or country) AND tour must agree.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
const target=path.join(root,'site/sports/tennis/identities.json');
const aliases=JSON.parse(fs.readFileSync(path.join(root,'tennis/identity-aliases.json'),'utf8'));
const key=s=>s.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const countries=new Intl.DisplayNames(['en'],{type:'region'});
const region=c=>key(({GB:'United Kingdom',CZ:'Czech Republic',KR:'South Korea',TW:'Taiwan',RU:'Russia'}[c]||countries.of(c)));
const countryAliases={'united states of america':'united states','usa':'united states','great britain':'united kingdom','czechia':'czech republic','korea republic of':'south korea','russian federation':'russia'};
const countryKey=s=>countryAliases[key(s)]||key(s);
async function main(){
 const candidates=JSON.parse(fs.readFileSync(path.join(root,'data/current/identity-candidates.json'),'utf8'));
 const data=fs.existsSync(target)?JSON.parse(fs.readFileSync(target,'utf8')):{links:{}};
 const limit=Number(process.env.IDENTITY_VERIFICATION_LIMIT||200);
 if(!Number.isInteger(limit)||limit<1||limit>600)throw new Error('Identity verification limit must be 1–600');
 const deadline=Date.now()+240000;
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext();
 let checked=0,added=0;
 try{
  // Two normal page loads at a time. Persist validated links; re-fetching hundreds
  // of stable birth-date/ID proofs on every scheduled build is unnecessary.
  const queue=candidates.slice(0,limit);
  async function worker(){const page=await context.newPage();
   while(queue.length&&Date.now()<deadline){const candidate=queue.shift();checked++;
    const slug=key(candidate.result_name).replace(/ /g,'-');
    const numeric=candidate.result_id.split(':').at(-1);
    if(!/^\d+$/.test(numeric))continue;
    const url=`https://www.valuebetennis.com/players/${slug}-${numeric}.htm`;
    try{
     const response=await page.goto(url,{waitUntil:'domcontentloaded',timeout:20000});
     if(response.status()!==200)continue;
     const html=await page.content();
     const person=await page.evaluate(()=>{
      for(const s of document.querySelectorAll('script[type="application/ld+json"]')){
       try{const j=JSON.parse(s.textContent);for(const p of (j['@graph']||[j]))if(p['@type']==='Person')return p;}catch{}
      }return null;
     });
     if(!person||key(person.name)!==key(candidate.result_name))continue;
     const alias=aliases.find(a=>a.tour===candidate.tour&&key(a.result_name)===key(person.name)&&key(a.official_name)===key(candidate.name));
     if(key(person.name)!==key(candidate.name)&&!alias)continue;
     const u=new URL(person.url||'https://invalid/');
     if(u.hostname!=='www.valuebetennis.com'||!u.pathname.endsWith('-'+numeric+'.htm'))continue;
     const gender=candidate.tour==='ATP'?'male':'female';
     if((person.gender||'').toLowerCase()!==gender||candidate.gender!==gender)continue;
     const dob=person.birthDate?.slice(0,10);
     let method;
     if(alias){
      if(dob!==alias.birth_date||candidate.birth_date!==alias.birth_date||candidate.country!==alias.country||countryKey(person.nationality?.name||'')!==countryKey(region(alias.country)))continue;
      method='documented_alias_birth_date_country_tour';
     }
     else if(dob&&candidate.birth_date){if(dob!==candidate.birth_date)continue;method='name_birth_date_tour';}
     else{
      const country=person.nationality?.name;
      if(!country||!candidate.country||countryKey(country)!==countryKey(region(candidate.country)))continue;
      method='name_country_tour';
     }
     data.links[candidate.result_id]={official_id:candidate.id,official_name:candidate.name,result_name:candidate.result_name,
      method,alias_source_url:alias?.source_url||null,birth_date:candidate.birth_date||null,country:candidate.country,profile_url:url,
      profile_sha256:crypto.createHash('sha256').update(html).digest('hex'),verified_at:new Date().toISOString(),
      ranking_source_url:'https://tennis.one/ranking'};added++;
    }catch(error){console.warn(`Profile verification withheld for ${candidate.result_id}: ${error.name}`);}
   }await page.close();
  }
  await Promise.all([worker(),worker()]);
 }finally{await browser.close();}
 if(added){fs.writeFileSync(target+'.download',JSON.stringify(data));fs.renameSync(target+'.download',target);}
 console.log(`Independently checked ${checked} profiles; verified ${added} links, total ${Object.keys(data.links).length}. Unmatched players remain unknown.`);
}
main().catch(error=>{console.error(error);process.exitCode=1;});
