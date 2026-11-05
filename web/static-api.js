"use strict";
// Same interface as the read-only Python API, backed by exported Pages files.
// No tennis source is queried by a visitor; no key or Python server is needed.
(() => {
  const base=new URL('./data/',location.href),cache=new Map(),versions=new Map();
  async function file(path,options={},fresh=false){
    const url=new URL(path,base);const tour=path.split('/')[0];
    if(versions.has(tour))url.searchParams.set('v',versions.get(tour));
    if(!fresh&&cache.has(url.href))return cache.get(url.href);
    const response=await fetch(url,{...options,cache:'no-cache'});
    if(!response.ok)throw new Error('Publication unavailable ('+response.status+'). Please retry shortly.');
    const data=await response.json();if(!fresh)cache.set(url.href,data);return data;
  }
  const category=(a,b)=>a==null||b==null?'unknown':Math.abs(a-b)<=25?'similar':b<a?'better':'worse';
  function stats(history,cutoff,basis,noRet,surface='Overall'){
    const s=Object.fromEntries(['overall','top50','similar','better','worse','unknown','Outdoor hard','Indoor hard','Clay','Grass','Unknown'].map(k=>[k,[0,0]]));
    for(const r of history){
      if(r.date<=cutoff||(noRet&&r.retired)||(surface!=='Overall'&&r.surface!==surface))continue;
      const keys=['overall',category(r['own_'+basis],r['opp_'+basis]),r.surface];
      if(r['opp_'+basis]!=null&&r['opp_'+basis]<=50)keys.push('top50');
      for(const key of keys)s[key][r.won?0:1]++;
    }return s;
  }
  window.courtStaticAPI=async(url,options={})=>{
    const q=url.searchParams,tour=q.get('tour')||'ATP';
    if(!['ATP','WTA'].includes(tour))throw new Error('Unknown tour');
    if(url.pathname.endsWith('/api/meta')){
      const m=await file(tour+'/meta.json',options,true);versions.set(tour,m.generated_at);
      m.staleness_days=Math.floor((Date.now()-Date.parse(m.latest_result+'T00:00:00Z'))/86400000);return m;
    }
    const basis=q.get('basis')||'power',period=q.get('window')||'year',surface=q.get('surface')||'Overall',noRet=q.get('no_ret')==='1';
    const offset=Math.max(0,Number(q.get('offset'))||0),limit=Math.min(100,Math.max(1,Number(q.get('limit'))||50));
    const meta=await file(tour+'/meta.json',options);
    const cutoff=period==='recent'?meta.recent_start_exclusive:meta.window_start_exclusive;
    if(url.pathname.includes('/api/players/')){
      const parts=url.pathname.split('/api/players/')[1].split('/'),id=decodeURIComponent(parts[0]);
      if(!id.startsWith('valuebetennis:'+tour+':'))throw new Error('Player not found in this tour');
      const p=await file(tour+'/players/'+encodeURIComponent(id.replaceAll(':','_'))+'.json',options);
      if(parts[1]==='results'){
        const rows=p.history.filter(r=>r.date>cutoff&&(!noRet||!r.retired)&&(surface==='Overall'||r.surface===surface)).filter(r=>{
          if(q.get('significant')==='0')return true;
          const c=category(r['own_'+basis],r['opp_'+basis]);return c==='similar'||(r.won&&c==='better')||(!r.won&&c==='worse');
        });return {total:rows.length,offset,results:rows.slice(offset,offset+limit)};
      }
      return {...p,selected_stats:stats(p.history,cutoff,basis,noRet,surface),
        selected_stats_year:stats(p.history,meta.window_start_exclusive,basis,noRet,surface),
        selected_stats_recent:stats(p.history,meta.recent_start_exclusive,basis,noRet,surface),
        all_stats:{year:stats(p.history,meta.window_start_exclusive,basis,noRet),recent:stats(p.history,meta.recent_start_exclusive,basis,noRet)}};
    }
    const all=await file(tour+'/rankings/'+surface+'-'+(noRet?'1':'0')+'.json',options);
    const search=(q.get('q')||'').toLocaleLowerCase().trim(),sample=Number(q.get('sample'))||0,flag=q.get('flag'),tier=q.get('tier');
    let rows=all.filter(p=>(p.name+' '+p.country).toLocaleLowerCase().includes(search)&&p.matches>=sample&&(!flag||p.flags.includes(flag))&&(!tier||p.tiers.includes(tier))&&(q.get('active')!=='1'||p.inactive_days<42));
    rows=rows.map(p=>({...p,selected_stats:p.stats[basis][period]}));
    const sort=q.get('sort')||'rank',metric=q.get('metric')||'overall',descending=q.get('direction')==='desc';
    const value=p=>{
      if(sort==='rank')return p.selected_rank;if(sort==='rating')return p.selected_rating;
      if(sort.startsWith('surface:'))return p.surfaces[sort.slice(8)].rank;
      if(sort==='record'){const [w,l]=p.selected_stats[metric];return w+l?w/(w+l):null;}return p[sort];
    };
    rows.sort((a,b)=>{const x=value(a),y=value(b);if(x==null||y==null)return x==null?(y==null?a.id.localeCompare(b.id):1):-1;return (typeof x==='string'?x.localeCompare(y):x-y)*(descending?-1:1)||a.id.localeCompare(b.id);});
    return {total:rows.length,offset,players:rows.slice(offset,offset+limit)};
  };
})();
