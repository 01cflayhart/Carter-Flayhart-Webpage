for(const tour of ['ATP','WTA']){
  fetch('./tennis/data/'+tour+'/meta.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Unavailable');return r.json();}).then(m=>{
    document.getElementById(tour+'-status').textContent=`${m.player_count.toLocaleString()} players · ${m.match_count.toLocaleString()} covered matches / year. Checked through ${m.as_of}; latest accepted result ${m.latest_result}.`;
  }).catch(()=>{document.getElementById(tour+'-status').textContent='Publication unavailable. Please check again shortly.';});
}
