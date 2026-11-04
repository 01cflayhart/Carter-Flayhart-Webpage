"use strict";
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num = value => value == null ? "—" : Number(value).toLocaleString("en-US", {maximumFractionDigits: 0});
const fmtDate = value => value ? new Date(value + "T12:00:00").toLocaleDateString("en-US", {month:"short", day:"numeric", year:"numeric"}) : "Unavailable";
const surfaces = ["Hard", "Clay", "Grass", "Carpet"];
const safeURL = value => {try {const u = new URL(value); return u.protocol === "https:" ? esc(u.href) : "";} catch {return "";}};
const state = {tour:new URLSearchParams(location.search).get('tour')==='WTA'?'WTA':'ATP',surface:"Overall", basis:"power", window:"year", offset:0, limit:25, sort:"rank", direction:"asc", metric:"overall", q:"", active:false, no_ret:false, sample:0, flag:"", tier:"", expanded:false};
let meta, listController, profileId, resultOffset = 0, resultMode = "1", profileSequence = 0, resultSequence = 0, toastTimer;
const params = extra => new URLSearchParams({...state, active:state.active ? "1":"0", no_ret:state.no_ret ? "1":"0", ...extra});
async function api(path, options) {const url=new URL(path,location.href);url.searchParams.set('tour',state.tour);if(window.COURT_STATIC)return window.courtStaticAPI(url,options);const response = await fetch(url, options); const body = await response.json(); if (!response.ok) throw new Error(body.error || "The request could not be completed."); return body;}
function toast(message) {$("#toast").textContent = message; $("#toast").hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $("#toast").hidden = true, 5000);}
function avatar(p, large = false) {const initials = p.name.split(/\s+/).filter(Boolean).map(x=>x[0]).filter((_,i,a)=>i===0||i===a.length-1).join(""); const url = p.photo ? safeURL(p.photo.url) : ""; return `<span class="avatar${large ? " large":""}" aria-hidden="true">${url ? `<img src="${url}" alt="" loading="lazy" data-fallback="${esc(initials)}">` : esc(initials)}</span>`;}
document.addEventListener("error", e => {if (e.target.matches?.("img[data-fallback]")) e.target.replaceWith(document.createTextNode(e.target.dataset.fallback));}, true);
function wl(pair) {const [w,l] = pair || [0,0]; return `<span class="wl">${w}–${l}<small>${w+l ? Math.round(w/(w+l)*100)+"%" : "No matches"}</small></span>`;}
function movement(value) {return `<span class="movement ${value > 0 ? "up" : value < 0 ? "down" : "neutral"}">${value == null ? "New" : value > 0 ? "↑ "+value : value < 0 ? "↓ "+Math.abs(value) : "—"}</span>`;}
function syncControls() {$("#basis").value = state.basis; $("#window").value = state.window;}
function accessibleTables(root) {
  $$('.table-scroll',root).forEach((box,index)=>{
    box.tabIndex=0;
    box.setAttribute('role','region');
    box.setAttribute('aria-label',`Scrollable data table ${index+1}`);
  });
}
function columns() {
  const base = [
    {title:"Power",sort:"rank",render:p=>`<span class="${p.selected_rank <= 3 ? "rank leader":"rank"}">${String(p.selected_rank).padStart(2,"0")}</span>`,cls:"rank"},
    {title:"Player",sort:"name",render:p=>`<button class="player-link" data-player="${esc(p.id)}" aria-label="Open ${esc(p.name)} notebook">${avatar(p)}<span><span class="player-name">${esc(p.name)}</span><span class="player-meta">${esc(p.country)}${p.flags.slice(0,1).map(f=>`<span class="flag-label">${esc(f)}</span>`).join("")}</span></span></button>`,cls:"player-cell"},
    {title:"Rating",sort:"rating",render:p=>`<span class="rating">${num(p.selected_rating)}<small>${esc(p.confidence)}</small></span>`},
    {title:state.tour+" rank",sort:"atp_rank",render:p=>`<span class="dual">${p.atp_rank ? "#"+num(p.atp_rank) : "—"}<small>${p.atp_points != null ? num(p.atp_points)+" pts" : "Not in feed"}</small></span>`},
    {title:"Surface power",render:p=>`<div class="surface-ranks">${surfaces.slice(0,3).map(s=>`<span title="${s}: #${p.surfaces[s].rank}, ${p.surfaces[s].matches} matches${p.surfaces[s].provisional ? ', provisional' : ''}" class="${p.surfaces[s].provisional ? "provisional":""}"><i class="surface-dot ${s.toLowerCase()}"></i>${p.surfaces[s].rank}</span>`).join("")}</div>`},
    {title:"Record",sort:"record",metric:"overall",render:p=>wl(p.selected_stats.overall)},
    {title:"vs Top 50",sort:"record",metric:"top50",render:p=>wl(p.selected_stats.top50)},
    {title:"7d change",sort:"movement",render:p=>movement(p.movement)},
    {title:"Recent form",render:p=>`<div class="form" aria-label="Recent results, oldest to newest: ${p.form.map(w=>w?'win':'loss').join(', ')}">${p.form.map(w=>`<i class="${w?'':'loss'}">${w?'W':'L'}</i>`).join("")}</div>`}
  ];
  if (state.expanded) {
    base.splice(7,0,...["similar","better","worse","unknown"].map(k=>({title:"vs "+k,sort:"record",metric:k,render:p=>wl(p.selected_stats[k])})));
    base.push(...surfaces.flatMap(s=>[
      {title:s+" rank",sort:"surface:"+s,render:p=>`<span class="${p.surfaces[s].provisional?'provisional':''}" title="${p.surfaces[s].matches} matches">#${p.surfaces[s].rank}</span>`},
      {title:s+" W–L",sort:"record",metric:s,render:p=>wl(p.selected_stats[s])}
    ]), {title:state.tour+" points",sort:"atp_points",render:p=>num(p.atp_points)}, {title:"Matches",sort:"matches",render:p=>num(p.matches)}, {title:"Age ≈",sort:"age",render:p=>p.age ?? "—"}, {title:"Days absent",sort:"inactive_days",render:p=>p.inactive_days});
  }
  return base;
}
async function loadRankings() {
  listController?.abort(); listController = new AbortController();
  const cols = columns();
  $("#table-head").innerHTML = `<tr>${cols.map(c=>{const selected=c.sort===state.sort&&(c.sort!=="record"||c.metric===state.metric); return `<th${selected ? ` aria-sort="${state.direction==='asc'?'ascending':'descending'}"` : ""}>${c.sort ? `<button data-sort="${esc(c.sort)}" data-metric="${esc(c.metric||'overall')}">${esc(c.title)}${selected ? state.direction==='asc'?' ↑':' ↓' : ''}</button>` : esc(c.title)}</th>`;}).join("")}</tr>`;
  $("#rankings").setAttribute("aria-busy","true");
  try {
    const data = await api("/api/rankings?"+params(), {signal:listController.signal});
    $("#table-body").innerHTML = data.players.length ? data.players.map(p=>`<tr>${cols.map(c=>`<td class="${c.cls||''}">${c.render(p)}</td>`).join("")}</tr>`).join("") : `<tr><td colspan="${cols.length}" class="empty">No players match this search.<br>Try a different name or loosen your filters.</td></tr>`;
    $("#result-count").textContent = data.total ? `${num(state.offset+1)}–${num(Math.min(state.offset+state.limit,data.total))} of ${num(data.total)} players · ${state.surface === 'Overall' ? 'all courts':state.surface} · ${state.window==='year'?'12-month':'3-month'} records` : "No matching players";
    $("#previous").disabled = state.offset === 0;
    $("#next").disabled = state.offset+state.limit >= data.total;
    $("#rankings").setAttribute("aria-busy","false");
  } catch(error) {
    if (error.name === "AbortError") return;
    $("#table-body").innerHTML = `<tr><td colspan="${cols.length}" class="empty error-copy">${esc(error.message)}<br><button class="text-button" id="retry">Try again ↻</button></td></tr>`;
    $("#result-count").textContent = "Rankings unavailable";
    $("#previous").disabled = $("#next").disabled = true;
    $("#rankings").setAttribute("aria-busy","false");
  }
}
function refresh() {state.offset=0; syncControls(); loadRankings();}
function updateFreshness() {
  $("#edition-date").textContent = fmtDate(meta.as_of);
  $("#edition-caption").textContent = meta.historical ? "Results cutoff · event-start dates" : "Checked through · UTC";
  $("#player-count").textContent = num(meta.player_count);
  $("#match-count").textContent = num(meta.match_count);
  $("#official-date").textContent = fmtDate(meta.ranking_date);
  $('#official-caption').innerHTML=meta.official_rankings_available===false?`Not in feed · <a href="${state.tour==='ATP'?'https://www.atptour.com/en/rankings/singles':'https://www.wtatennis.com/rankings/singles'}" target="_blank" rel="noreferrer">Official ${state.tour} rankings ↗</a>`:state.tour+' edition used for display';
  const official=$('#basis option[value="atp"]');official.textContent='Historical '+state.tour+' rank*';official.disabled=meta.official_rankings_available===false;
  $('#source-credit').innerHTML=`Data: <a href="${safeURL(meta.source.url)}" target="_blank" rel="noreferrer">${esc(meta.source.name)}</a> · <a href="${safeURL(meta.source.license_url)}" target="_blank" rel="noreferrer">${esc(meta.source.license)}</a>`;
  $('#comparison-note').textContent='* '+state.tour+' only. Categories use pre-date '+(state.basis==='power'?'power':'official')+' ranks; similar = ±25. '+(meta.official_rankings_available===false?'Official ranks/points and age metadata are absent from this feed. ':'')+'Click a player for the full story.';
  $("#source-status").textContent = meta.historical ? "HISTORICAL SNAPSHOT" : "RESULTS FEED · CHECK COVERAGE";
  const failed = meta.update_status?.ok === false;
  $("#freshness").classList.toggle("error",failed);
  const quarantined = meta.audit.quarantined_official_rankings?.length || 0;
  $("#freshness").textContent = `${meta.historical ? "Historical archive, not a live feed." : 'Separate '+state.tour+' rankings. Open feed checked through '+fmtDate(meta.as_of)+'.'} Latest accepted result: ${fmtDate(meta.latest_result||meta.as_of)}${meta.staleness_days > 0 ? ` (${meta.staleness_days} days before today)` : ''}. Coverage is not certified exhaustive; missing or incomplete scores are excluded.${quarantined ? ` ${quarantined} ambiguous official ranking entries quarantined.`:''}${failed ? ' Last update failed; showing the last good publication.':''}`;
  $("#build-info").textContent = `Model ${meta.model_version}`;
}
function profileParams(extra={}) {return params({...extra, offset:resultOffset, limit:10, significant:resultMode});}
async function openPlayer(id, first=true) {
  profileId=id; resultOffset=0;
  const sequence = ++profileSequence;
  if (first) {$("#player-content").innerHTML = '<h2 id="player-title">Opening the notebook…</h2>'; $("#player-dialog").showModal();}
  try {
    const p = await api(`/api/players/${encodeURIComponent(id)}?`+profileParams());
    if (sequence!==profileSequence) return;
    const rank = state.surface==='Overall' ? p.rank : p.surfaces[state.surface].rank;
    const rows = [["overall","All opponents"],["top50","Top 50"],["similar","Similar (±25)"],["better","Better (outside ±25)"],["worse","Worse (outside ±25)"],["unknown","Unknown rank"]];
    $("#player-content").innerHTML = `<div class="profile-heading">${avatar(p,true)}<div><h2 id="player-title">${esc(p.name)}</h2><p>${esc(p.country)} · ${p.age!=null ? 'Age ≈'+p.age+' · ':''}${p.hand==='R'?'Right-handed':p.hand==='L'?'Left-handed':'Hand unknown'}${p.height?' · '+p.height+' cm':''}</p><div class="badges">${p.flags.map(f=>`<span class="badge">${esc(f)}</span>`).join("")}<span class="badge">${esc(p.confidence)} sample</span></div></div></div>
      <div class="profile-grid"><div class="metric-card"><span class="eyebrow">${state.tour} POWER RANK</span><strong>#${rank}</strong><small>${esc(state.surface)} · ${movement(p.movement)} overall, vs 7d cutoff</small></div><div class="metric-card"><span class="eyebrow">STRENGTH / SCORE</span><strong>${num(p.strength)} / ${num(p.rating)}</strong><small>Overall strength / availability-adjusted score</small></div><div class="metric-card"><span class="eyebrow">${state.tour} RANK / POINTS</span><strong>${p.atp_rank?'#'+num(p.atp_rank):'—'}</strong><small>${num(p.atp_points)} points · ${fmtDate(p.atp_date)}</small></div><div class="metric-card"><span class="eyebrow">LAST OBSERVED</span><strong>${p.inactive_days}d before cutoff</strong><small>${fmtDate(p.last_played)} · source-reported date</small></div></div>
      <p class="dialog-copy">${p.matches} covered matches in the past year. Availability adjustment: ${p.availability_adjustment.toFixed(1)} rating points. Younger players and veterans are flagged, not given an age bonus or penalty. ${p.health ? `Reported status: <strong>${esc(p.health.status)}</strong> · ${esc(p.health.confidence)} confidence · <a href="${safeURL(p.health.source_url)}" target="_blank" rel="noreferrer">source (${esc(p.health.reported_at)})</a>; review by ${esc(p.health.review_after)}.` : 'Injury status: unknown / not independently verified.'}</p>
      ${p.photo?`<p class="update-time">Photo: ${esc(p.photo.credit)} · <a href="${safeURL(p.photo.license_url)}" target="_blank" rel="noreferrer">License</a></p>`:''}
      <div class="dialog-section"><div class="results-tools"><label>Opponent categories <select id="profile-basis"><option value="atp"${state.basis==='atp'?' selected':''}${meta.official_rankings_available===false?' disabled':''}>Historical ${state.tour} rank*</option><option value="power"${state.basis==='power'?' selected':''}>Historical power rank*</option></select></label><label><input type="checkbox" id="profile-no-ret"${state.no_ret?' checked':''}> Exclude retirements from records</label></div><h3>The record, in context</h3><p class="table-note">* Pre-date snapshots within ${state.tour} only. Better/worse exclude the ±25 band; top 50 overlaps. Unknown ranks stay unknown. Both windows end ${fmtDate(meta.as_of)}.</p><div class="table-scroll"><table class="stats-table"><thead><tr><th>Opponents · all courts</th><th>Past 12 months</th><th>Past 3 months</th></tr></thead><tbody>${rows.map(([k,l])=>`<tr><td>${l}</td><td>${wl(p.all_stats.year[k])}</td><td>${wl(p.all_stats.recent[k])}</td></tr>`).join("")}</tbody></table></div></div>
      <div class="dialog-section"><h3>A feel for every court</h3><div class="table-scroll"><table class="stats-table"><thead><tr><th>Surface</th><th>Power rank / rating</th><th>12-month W–L</th><th>3-month W–L</th><th>Sample</th></tr></thead><tbody>${surfaces.map(s=>`<tr><td><span class="surface-dot ${s.toLowerCase()}"></span> ${s}</td><td>#${p.surfaces[s].rank} / ${num(p.surfaces[s].rating)}</td><td>${wl(p.all_stats.year[s])}</td><td>${wl(p.all_stats.recent[s])}</td><td>${p.surfaces[s].matches} matches${p.surfaces[s].provisional?' · provisional':''}</td></tr>`).join("")}</tbody></table></div><p class="table-note">Sparse surface ratings borrow strength from the overall model. A rank with few or no matches is an estimate, not proven surface form.</p></div>
      <div class="dialog-section"><h3>The matches behind the movement</h3><div class="results-tools"><label>Show <select id="result-mode"><option value="1"${resultMode==='1'?' selected':''}>Significant results</option><option value="0"${resultMode==='0'?' selected':''}>All results</option></select></label><label>Window <select id="profile-window"><option value="year"${state.window==='year'?' selected':''}>Past 12 months</option><option value="recent"${state.window==='recent'?' selected':''}>Past 3 months</option></select></label><label>Surface <select id="profile-surface">${['Overall',...surfaces].map(s=>`<option${state.surface===s?' selected':''}>${s}</option>`).join('')}</select></label></div><div id="match-results" class="match-list" aria-live="polite">Loading results…</div><div class="pagination"><span id="match-count-label"></span><div><button id="match-prev">← Previous</button><button id="match-next">Next →</button></div></div></div>
      <p class="table-note">Rating impact is the immediate, pre-decay match contribution—not the entire subsequent rank change. Positive means added strength, negative means lost strength. Records use raw W–L; rating evidence is weighted. Source cutoff and event-date uncertainty apply to every result.</p>`;
    accessibleTables($("#player-content"));
    $("#profile-basis").addEventListener('change',e=>{state.basis=e.target.value; refresh(); openPlayer(id,false);});
    $("#profile-no-ret").addEventListener('change',e=>{state.no_ret=e.target.checked; $("#no-ret").checked=state.no_ret; refresh(); openPlayer(id,false);});
    $("#result-mode").addEventListener('change',e=>{resultMode=e.target.value; resultOffset=0; loadResults();});
    $("#profile-window").addEventListener('change',e=>{state.window=e.target.value; resultOffset=0; refresh(); loadResults();});
    $("#profile-surface").addEventListener('change',e=>{setSurface(e.target.value); openPlayer(id,false);});
    $("#match-prev").addEventListener('click',()=>{resultOffset=Math.max(0,resultOffset-10);loadResults();});
    $("#match-next").addEventListener('click',()=>{resultOffset+=10;loadResults();});
    loadResults();
  } catch(error) {if(sequence===profileSequence) $("#player-content").innerHTML=`<h2 id="player-title">Notebook unavailable</h2><p class="dialog-copy error-copy">${esc(error.message)}</p>`;}
}
async function loadResults() {
  const sequence=++resultSequence;
  try {
    const data = await api(`/api/players/${encodeURIComponent(profileId)}/results?`+profileParams());
    if(sequence!==resultSequence||!$("#match-results"))return;
    $("#match-results").innerHTML=data.results.length ? data.results.map(r=>`<article class="match-card"><span class="match-outcome ${r.won?'':'loss'}">${r.won?'W':'L'}</span><div><strong>${r.won?'Defeated':'Lost to'} ${esc(r.opponent)}</strong><p>${esc(r.event)} · ${esc(r.tier)} · ${esc(r.round)} · <span class="surface-dot ${r.surface.toLowerCase()}"></span> ${esc(r.surface)}<br>${fmtDate(r.date)} (${esc(r.precision)}) · ${state.basis==='atp'?'ATP':'Power'}: own #${r['own_'+state.basis]??'?'} vs opponent #${r['opp_'+state.basis]??'?'}${r.retired?' · Retirement':''}</p></div><div class="score">${esc(r.score)}<br><span class="${r.delta>=0?'positive':'negative'}">${r.delta>=0?'+':''}${r.delta.toFixed(1)} rating</span><br><small>${Math.round(r.expected*100)}% pre-match win estimate</small></div></article>`).join(""):'<p class="dialog-copy">No matching results in this window. Try all results or another surface.</p>';
    $("#match-count-label").textContent=data.total ? `${resultOffset+1}–${Math.min(resultOffset+10,data.total)} of ${data.total} results`:'No results';
    $("#match-prev").disabled=resultOffset===0; $("#match-next").disabled=resultOffset+10>=data.total;
  }catch(error){if(sequence===resultSequence&&$("#match-results"))$("#match-results").textContent=error.message;}
}
function setSurface(surface) {state.surface=surface;$$('[data-surface]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.surface===surface)));refresh();}
function showInfo(kind) {
  if(!meta){toast('The dataset is not available yet.');return;}
  if(!meta.historical){showCurrentInfo(kind);return;}
  if(kind==='coverage') {
    $("#info-content").innerHTML=`<h2 id="info-title">Good analysis starts with honest data.</h2><p class="dialog-copy">${esc(meta.source.name)}. An archival mirror, not an official live feed. Results dates are usually the start of the event, not the day each match was played. No claim of exhaustive ATP-points coverage is made.</p><div class="info-block"><strong>Publication:</strong> ${fmtDate(meta.as_of)}<br><strong>Last successful build:</strong> ${esc(new Date(meta.generated_at).toLocaleString())}<br><strong>Last attempt:</strong> ${esc(meta.update_status.message||'Unknown')}<br><strong>Record windows:</strong> (${esc(meta.window_start_exclusive)}, ${esc(meta.as_of)}] and (${esc(meta.recent_start_exclusive)}, ${esc(meta.as_of)}]<br><strong>Official ranking edition:</strong> ${fmtDate(meta.ranking_date)}<br><strong>License:</strong> <a href="${safeURL(meta.source.license_url)}" target="_blank" rel="noreferrer">${esc(meta.source.license)}</a> · Noncommercial / share-alike obligations apply.</div><h3>Coverage by tier and court</h3><div class="table-scroll"><table class="coverage-table"><thead><tr><th>Tier / surface</th><th>Latest event start</th><th>12-month matches</th></tr></thead><tbody>${Object.entries(meta.coverage).sort().map(([k,v])=>`<tr><td>${esc(k)}</td><td>${fmtDate(v.latest)}</td><td>${num(v.matches)}</td></tr>`).join('')}</tbody></table></div><h3>Known limitations</h3><ul class="method-list">${meta.warnings.map(w=>`<li>${esc(w)}</li>`).join('')}</ul><p class="dialog-copy">Quarantined conflicting official ranking entries: ${meta.audit.quarantined_official_rankings?.length||0}. These players have unknown official ranks for affected editions, rather than arbitrarily selected numbers. Qualifying and non-point team events are identified separately.</p><details><summary>Source ledger & checksums</summary>${meta.manifest.map(m=>`<p class="update-time"><strong>${esc(m.file)}</strong> · ${num(m.rows)} rows · retrieved ${esc(m.retrieved_at)}<br>SHA-256: ${esc(m.sha256)}</p>`).join('')}</details><p class="dialog-copy"><a href="${safeURL(meta.source.url)}" target="_blank" rel="noreferrer">Visit the source archive ↗</a></p>`;
  } else {
    const report=meta.backtest?.common_ranked_sample;
    $("#info-content").innerHTML=`
      <h2 id="info-title">More than a win–loss column.</h2>
      <p class="dialog-copy">An explainable model of recent playing strength, not a replacement for the official ATP rankings. Model ${esc(meta.model_version)}. Parameters remain provisional.</p>
      <ol class="method-list">
        <li><strong>Quality of opposition.</strong> Elo-style expected win probabilities mean an upset adds more than a routine win, and a bad loss costs more than losing to a strong favorite. No ATP points enter the formula.</li>
        <li><strong>Recent tennis matters more.</strong> A match-updated historical Elo anchor preserves cross-tier strength. Recent-form evidence adds ${meta.rating_config.form_weight} times its weighted contributions, decaying with a ${meta.rating_config.half_life_days}-day half-life and expiring after 12 calendar months. The bounded first-observed ATP rank supplies a cold-start prior, never future information. Older evidence remains indirectly in the anchor.</li>
        <li><strong>Every court has a character.</strong> Separate surface evidence is blended with overall strength; low-sample grass or carpet estimates are flagged provisional.</li>
        <li><strong>Absence is not improvement.</strong> Strength and availability-adjusted score are separate. During absence, the score cannot rise merely because negative evidence fades. An additional conservative penalty starts after 42 days, capped at 160 points. This is a policy choice, not a medical prediction.</li>
        <li><strong>Age is context, not a multiplier.</strong> Under-21 and 35+ flags provide context. Evidence-driven provisional ratings can move more quickly at any age. Injuries require dated, sourced reports; absent evidence means unknown.</li>
        <li><strong>The timing is honest.</strong> This archive generally provides event-start dates and ranks. Pre-date power rankings freeze before all same-date outcomes. Debutants without a prior power rank are unknown, not invented. No historical category is reassigned using today's ranking.</li>
        <li><strong>Records are real counts.</strong> W–L records are unweighted. Similar means ±25 inclusive. Better/worse exclude that band, unknown is separate, and top-50 records overlap. The ATP/power toggle changes categories, not ratings.</li>
        <li><strong>Exceptions are explicit.</strong> Walkovers, byes, abandonments and defaults are excluded; retirements count as played and carry ${meta.rating_config.retirement_weight*100}% rating influence. The records filter does not recompute the rating. Team results ${meta.rating_config.include_team?'are included':'are excluded'}.</li>
      </ol>
      <h3>Does it predict better?</h3>
      ${report?`<p class="dialog-copy">Walk-forward frozen-date replay, ${fmtDate(meta.backtest.start_exclusive)} to ${fmtDate(meta.backtest.end_inclusive)}. Same ranked-opponent sample; retirements excluded. Lower is better. This is not an independently tuned final holdout.</p>
      <div class="table-scroll"><table class="coverage-table"><thead><tr><th>Model</th><th>Matches</th><th>Log loss</th><th>Brier score</th></tr></thead><tbody>${[['model','Court Current'],['elo','Basic Elo'],['atp','ATP-rank baseline']].map(([k,label])=>`<tr><td>${label}</td><td>${num(report[k].n)}</td><td>${report[k].log_loss??'—'}</td><td>${report[k].brier??'—'}</td></tr>`).join('')}</tbody></table></div>
      <p class="dialog-copy">Full calibration bins and tier/surface breakdowns are in reports/backtest.json. The interface does not imply predictive superiority when a baseline performs better.</p>`:'<p class="dialog-copy">No backtest has been published yet. Run python3 -m tennis.backtest. Do not assume predictive superiority.</p>'}
      <div class="info-block">The routine updater is deterministic. The OpenCode maintenance agent helps inspect failures and maintain source adapters; it does not invent scores, injuries or ranking changes. Scheduling and public hosting are separate, opt-in setup steps.</div>`;
  }
  if(kind==='coverage'&&meta.audit.excluded_ranking_editions?.length){
    const notice=document.createElement('p');
    notice.className='dialog-copy';
    notice.textContent='Excluded incomplete ranking editions: '+meta.audit.excluded_ranking_editions.map(e=>`${e.date}: ${e.rows} rows. ${e.reason}`).join(' ');
    $('#info-content').append(notice);
  }
  accessibleTables($("#info-content"));
  if(!meta.historical){
    const title=$('#info-title');
    const note=document.createElement('p');note.className='dialog-copy';note.textContent=meta.date_precision+' '+state.tour+' has its own independent rating universe; ATP and WTA scores are not comparable. '+meta.warnings.join(' ');title.after(note);
    // The legacy archival explanation remains useful only for archival sources.
    if(kind==='coverage'){
      const first=$('#info-content > p.dialog-copy');if(first!==note)first?.remove();
      $$('#info-content .info-block').forEach(e=>{e.textContent=e.textContent.replace('Noncommercial / share-alike obligations apply.','Attribution required under CC BY 4.0.');});
    }
    if(kind!=='coverage'){
      $$('#info-content .method-list li').forEach(e=>{e.textContent=e.textContent.replace('The bounded first-observed ATP rank supplies a cold-start prior, never future information.','This feed has no official ranks; all players start from the same prior.').replace('No ATP points','No ranking points').replace('The ATP/power toggle changes categories, not ratings.','Official-rank comparisons are disabled when the feed supplies none.').replace('This archive generally provides event-start dates and ranks.','This CSV supplies source-reported UTC match dates, but no official rankings.');});
    }
    if(meta.backtest?.all_played_sample){
      const block=document.createElement('p');block.className='dialog-copy';const b=meta.backtest.all_played_sample;block.textContent=`${state.tour} open-feed walk-forward sample: ${num(b.model.n)} matches. Model log loss ${b.model.log_loss}; basic Elo ${b.elo.log_loss}. No official-ranking baseline is available. Provisional comparison, not a final untouched holdout.`;$('#info-content').append(block);
    }
  }
  $("#info-dialog").showModal();
}
function showCurrentInfo(kind){
  const report=meta.backtest?.all_played_sample;
  $('#info-content').innerHTML=kind==='coverage'?`
    <h2 id="info-title">Good analysis starts with honest data.</h2>
    <p class="dialog-copy">${esc(state.tour)} only. Checked through ${fmtDate(meta.as_of)}; latest accepted result ${fmtDate(meta.latest_result)}. This is the coverage of one open dataset, not a guarantee of every completed professional match.</p>
    <div class="info-block"><strong>Source:</strong> <a href="${safeURL(meta.source.url)}" target="_blank" rel="noreferrer">${esc(meta.source.name)}</a><br><strong>License:</strong> <a href="${safeURL(meta.source.license_url)}" target="_blank" rel="noreferrer">${esc(meta.source.license)}</a> · attribution required.<br><strong>Last successful build:</strong> ${esc(new Date(meta.generated_at).toLocaleString())}<br><strong>Dates:</strong> ${esc(meta.date_precision)}<br><strong>Official ranks/points:</strong> unavailable in this CSV; not substituted with old archive ranks.</div>
    <h3>Coverage by tier and court</h3><div class="table-scroll"><table class="coverage-table"><thead><tr><th>Tier / surface</th><th>Latest accepted result</th><th>12-month matches</th></tr></thead><tbody>${Object.entries(meta.coverage).sort().map(([k,v])=>`<tr><td>${esc(k)}</td><td>${fmtDate(v.latest)}</td><td>${num(v.matches)}</td></tr>`).join('')}</tbody></table></div>
    <h3>Excluded rows across the imported seasons</h3><div class="info-block">${Object.entries(meta.audit).map(([k,v])=>`${esc(k.replaceAll('_',' '))}: ${num(v)}`).join('<br>')}</div>
    <h3>Known limitations</h3><ul class="method-list">${meta.warnings.map(w=>`<li>${esc(w)}</li>`).join('')}</ul><details><summary>Source ledger & checksums</summary>${meta.manifest.map(m=>`<p class="update-time">${esc(m.file)} · ${num(m.rows)} rows<br>SHA-256: ${esc(m.sha256)}</p>`).join('')}</details>`:`
    <h2 id="info-title">More than a win–loss column.</h2><p class="dialog-copy">An experimental estimate of playing strength within ${esc(state.tour)}, never a combined ATP/WTA ranking. Missing results can materially distort the estimates. Model ${esc(meta.model_version)}.</p>
    <ol class="method-list"><li><strong>Quality of opposition.</strong> Elo-style probabilities reward upsets more than routine wins and punish bad losses more than expected ones. No official ranking points enter the formula.</li><li><strong>Recency and longer-term strength.</strong> A historical Elo anchor is combined with a ${meta.rating_config.form_weight} form overlay, ${meta.rating_config.half_life_days}-day half-life, and a trailing-year evidence window. Without official historical ranks, every player starts from the same prior.</li><li><strong>Separate tours, separate courts.</strong> ATP and WTA have independent identities, rating state, opponent categories, ranks, and surface estimates. Thin surface samples borrow overall strength and are flagged.</li><li><strong>Availability is not a diagnosis.</strong> Observed inactivity can reduce scores after 42 days. Missing source matches may look like inactivity: this flag is not proof of an injury. Photos, age and health metadata are unknown unless sourced.</li><li><strong>No future labels.</strong> Same-date batches use power ranks frozen before any outcome that day. Today's official rank is never used to rewrite old opponent categories.</li><li><strong>Comparable opponents.</strong> Similar means ±25 inclusive; better/worse exclude that band. Top 50 overlaps. Records are raw counts, not weighted wins. Official-rank categories are unavailable in this feed, so the default is historical power rank.</li><li><strong>Conservative score validation.</strong> Missing or incomplete scores are excluded, even with a reported winner, because walkovers, unmarked retirements and unfinished matches cannot always be distinguished. The coverage ledger quantifies these exclusions.</li></ol>
    <h3>Does it predict better?</h3>${report?`<p class="dialog-copy">${num(report.model.n)} same-sample played matches, ${fmtDate(meta.backtest.start_exclusive)}–${fmtDate(meta.backtest.end_inclusive)}. Lower is better. No official-rank baseline is available.</p><div class="table-scroll"><table class="coverage-table"><thead><tr><th>Model</th><th>Log loss</th><th>Brier score</th></tr></thead><tbody>${[['model','Court Current'],['elo','Basic Elo']].map(([k,n])=>`<tr><td>${n}</td><td>${report[k].log_loss??'—'}</td><td>${report[k].brier??'—'}</td></tr>`).join('')}</tbody></table></div><p class="dialog-copy">${report.model.log_loss>report.elo.log_loss?'The form model currently performs worse than basic Elo on this covered sample.':'The form model currently matches or improves on basic Elo log loss on this covered sample.'} Baseline results are shown, not hidden. This approximate-date walk-forward comparison is not an untouched final holdout.</p>`:'<p class="dialog-copy">No evaluation is available for this publication.</p>'}
    <p class="dialog-copy">GitHub Actions checks the feed every six hours when enabled and deploys only after both tours validate. Schedules can be delayed; the last successful static publication stays available if a build fails. Check the build timestamp and Actions status.</p>`;
  accessibleTables($('#info-content'));$('#info-dialog').showModal();
}
$("#table-head").addEventListener('click',e=>{const b=e.target.closest('[data-sort]');if(!b)return;const same=state.sort===b.dataset.sort&&(state.sort!=='record'||state.metric===b.dataset.metric);state.direction=same?(state.direction==='asc'?'desc':'asc'):['rating','movement','matches','atp_points','record'].includes(b.dataset.sort)?'desc':'asc';state.sort=b.dataset.sort;state.metric=b.dataset.metric;refresh();});
$("#table-body").addEventListener('click',e=>{const b=e.target.closest('[data-player]');if(b)openPlayer(b.dataset.player);if(e.target.closest('#retry'))loadRankings();});
$$('[data-surface]').forEach(b=>b.addEventListener('click',()=>setSurface(b.dataset.surface)));
let searchTimer;$("#search").addEventListener('input',e=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state.q=e.target.value;refresh();},200);});
['basis','window','sample','flag','tier'].forEach(id=>$('#'+id).addEventListener('change',e=>{state[id]=e.target.value;refresh();}));
['active','no-ret','expanded'].forEach(id=>$('#'+id).addEventListener('change',e=>{state[id.replace('-','_')]=e.target.checked;refresh();}));
$("#filter-toggle").addEventListener('click',()=>{const open=$("#extra-filters").hidden;$("#extra-filters").hidden=!open;$("#filter-toggle").setAttribute('aria-expanded',String(open));$("#filter-toggle").textContent=open?'Filters −':'Filters +';});
$("#previous").addEventListener('click',()=>{state.offset=Math.max(0,state.offset-state.limit);loadRankings();});
$("#next").addEventListener('click',()=>{state.offset+=state.limit;loadRankings();});
$$('[data-tour]').forEach(b=>b.addEventListener('click',()=>selectTour(b.dataset.tour)));
['method-open','footer-method'].forEach(id=>$('#'+id).addEventListener('click',()=>showInfo('method')));
$("#coverage-open").addEventListener('click',()=>showInfo('coverage'));
$$('[data-close]').forEach(b=>b.addEventListener('click',()=>$('#'+b.dataset.close).close()));
$$('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));
$("#player-dialog").addEventListener('close',()=>{profileSequence++;resultSequence++;});
let tourSequence=0;
async function selectTour(tour){
  const sequence=++tourSequence;
  state.tour=tour;state.offset=0;state.q='';$('#search').value='';meta=undefined;
  listController?.abort();profileSequence++;resultSequence++;$('#player-dialog').close();
  $('#table-body').innerHTML='<tr><td>Loading '+tour+' rankings…</td></tr>';
  $$('[data-tour]').forEach(b=>{b.classList.toggle('active',b.dataset.tour===tour);b.setAttribute('aria-pressed',String(b.dataset.tour===tour));});
  const url=new URL(location.href);url.searchParams.set('tour',tour);history.replaceState(null,'',url);
  try {const latest=await api('/api/meta');if(sequence!==tourSequence)return;meta=latest;if(meta.official_rankings_available===false)state.basis='power';syncControls();updateFreshness();await loadRankings();}
  catch(error){if(sequence!==tourSequence)return;$('#freshness').textContent=tour+' publication unavailable: '+error.message;$('#freshness').classList.add('error');$('#table-body').innerHTML='<tr><td>Could not load '+tour+' data. No other tour has been substituted.</td></tr>';}
}
async function init(){await selectTour(state.tour);}
init();
// The worker publishes independently; an already-open page follows new snapshots.
let checkingFreshness=false;
setInterval(async()=>{
  if(checkingFreshness||document.hidden)return;
  checkingFreshness=true;
  try {
    const tour=state.tour;
    const latest=await api('/api/meta');
    if(tour!==state.tour)return;
    const changed=meta&&latest.generated_at!==meta.generated_at;
    meta=latest;
    updateFreshness();
    if(changed){
      await loadRankings();
      if($('#player-dialog').open&&profileId)openPlayer(profileId,false);
      toast('A new validated snapshot is available. Rankings have been refreshed.');
    }
  }catch(error){
    $('#freshness').textContent='The publication server cannot be reached. Showing the last loaded snapshot; freshness cannot be verified.';
    $('#freshness').classList.add('error');
  }finally{checkingFreshness=false;}
},60000);
