'use strict';
const $=id=>document.getElementById(id);
const state={all:[],filtered:[],updated:null,feedError:false};
const SECTOR_WORDS={web:['web','website','digital platform','software','it services','website development','ux','user experience','cms','application','frontend'],marketing:['marketing','communications','advertis','campaign','social media','public relation','content creation','media buying'],design:['graphic','brand','design','creative','visual identity','illustrat','artwork'],video:['video','film','photograph','animation','motion','broadcast','production'],research:['research','survey','user research','market research','insight','usability','consultation']};
const CATEGORY_LABELS={web:'Web & software',marketing:'Marketing & communications',design:'Design & branding',video:'Video & production',research:'Research & insight'};
const fmtDate=s=>{if(!s)return 'Not disclosed';let d=new Date(s);return isNaN(d.getTime())?'Not disclosed':new Intl.DateTimeFormat('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'Europe/London'}).format(d)};
const fmtMoney=n=>Number.isFinite(Number(n))&&Number(n)>0?new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP',maximumFractionDigits:0}).format(Number(n)):'Not disclosed';
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function safeLink(s){try{let u=new URL(s);return ['https:','http:'].includes(u.protocol)&&(/(^|\.)find-tender\.service\.gov\.uk$/.test(u.hostname)||/(^|\.)gov\.uk$/.test(u.hostname))?u.href:null}catch{return null}}
function openNotice(d){const end=new Date(d.deadline).getTime();return !d.deadline||!Number.isFinite(end)||end>Date.now()}
function render(){const q=$('query').value.trim().toLowerCase(),cat=$('sector').value,sort=$('sort').value;let filtered=state.all.filter(d=>openNotice(d)&&(!q||[d.title,d.buyer,d.description,d.category,(d.tags||[]).join(' ')].join(' ').toLowerCase().includes(q))&&(cat==='all'||(d.tags||[]).includes(cat)));
filtered.sort((a,b)=>sort==='recent'?(Date.parse(b.published||0)||0)-(Date.parse(a.published||0)||0):sort==='value'?(Number(b.value)||0)-(Number(a.value)||0):(Date.parse(a.deadline||'9999-01-01')||9e15)-(Date.parse(b.deadline||'9999-01-01')||9e15));state.filtered=filtered;
$('result-count').textContent=state.feedError?'Feed unavailable':state.all.length?`${filtered.length} of ${state.all.filter(openNotice).length} tender-stage matches (verify deadlines)`:'No verified opportunities available';
const el=$('tender-list');
if(!filtered.length){el.innerHTML=`<div class="empty"><h3>${state.feedError?'Live feed temporarily unavailable':state.all.length?'No matching opportunities right now':'No verified tenders have been synced yet'}</h3><p>${state.feedError?'Try the official Find a Tender website.':'Try another category or check back after the daily feed refresh. We never create fake listings to fill an empty view.'}</p><p style="margin-top:18px"><a class="btn btn-outline btn-sm" target="_blank" rel="noopener noreferrer" href="https://www.find-tender.service.gov.uk/">Search official government notices ↗</a></p></div>`;}else{el.innerHTML=filtered.slice(0,80).map(d=>{let url=safeLink(d.url);return `<article class="tender"><div><span class="tag">${esc(CATEGORY_LABELS[(d.tags||[])[0]]||'Digital services')}</span><h3>${esc(d.title)}</h3><div class="tender-meta"><span>Buyer: ${esc(d.buyer||'Not disclosed')}</span><span>Deadline: ${esc(fmtDate(d.deadline))}</span><span>Ref: ${esc(d.id)}</span></div></div><div class="tender-side"><b>${esc(fmtMoney(d.value))}</b>${url?`<a class="link" target="_blank" rel="noopener noreferrer" href="${esc(url)}">Official notice ↗</a>`:'<span class="subtle">Source link unavailable</span>'}</div></article>`}).join('');}
const previous=$('selected-tender').value;$('selected-tender').innerHTML='<option value="">Choose a verified live tender above</option>'+state.all.filter(openNotice).map(d=>`<option value="${esc(d.id)}">${esc(d.title.slice(0,100))}</option>`).join('');$('selected-tender').value=state.all.some(d=>d.id===previous)?previous:'';}
const REMOTE_FEED = 'https://raw.githubusercontent.com/edsoniaglaj-crypto/narrowbid/main/data/tenders.json';
async function fetchFeed(url) {
  const response = await fetch(url, {cache: 'no-store', signal: AbortSignal.timeout(6000)});
  if (!response.ok) throw Error('Feed '+response.status);
  const feed = await response.json();
  if (!Array.isArray(feed.tenders) || !Number.isFinite(Date.parse(feed.updated_at))) {
    throw Error('Invalid feed');
  }
  feed.tenders = feed.tenders.filter(d => d && typeof d.id === 'string'
    && typeof d.title === 'string' && Array.isArray(d.tags) && safeLink(d.url));
  return feed;
}
async function load() {
  try {
    const j = await fetchFeed(REMOTE_FEED).catch(() => fetchFeed('./data/tenders.json'));
    state.all=j.tenders;state.updated=j.updated_at;$('feed-date').textContent=j.updated_at?'Last verified sync: '+fmtDate(j.updated_at)+' · '+new Date(j.updated_at).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/London',timeZoneName:'short'}):'Awaiting the first official data sync';let age=j.updated_at?Date.now()-Date.parse(j.updated_at):Infinity;let stale=age>48*3600000;$('feed-status').className='status'+(stale?' warn':'');$('feed-status').textContent=stale?'● Feed pending / stale':'● Synced from official data';state.feedError=stale&&!state.all.length;
  } catch {
    state.feedError = true;
    $('feed-date').textContent = 'Could not retrieve verified data';
    $('feed-status').className = 'status warn';
    $('feed-status').textContent = '● Sync unavailable';
  }
  render();
}
function fit(){const id=$('selected-tender').value,svc=$('services').value.trim().toLowerCase(),loc=$('location').value,cap=Number($('maxvalue').value)||0,d=state.all.find(x=>x.id===id);if(!d||!svc){$('fit-results').innerHTML='<h3>Choose a verified opportunity</h3><p>Enter your services and select a real listing from the feed first. Nothing is scored without source evidence.</p>';return;}
const words=svc.split(/[,\s;/]+/).filter(w=>w.length>2);const doc=[d.title,d.description,(d.tags||[]).map(t=>CATEGORY_LABELS[t]||'').join(' ')].join(' ').toLowerCase();const matched=[...new Set(words)].filter(w=>doc.includes(w));const serviceFit=Math.min(55,matched.length*18);const sectorFit=(d.tags||[]).some(tag=>(SECTOR_WORDS[tag]||[]).some(w=>svc.includes(w)))?20:0;const locKnown=Boolean(d.region);const locMatch=loc==='any'||(locKnown&&d.region.toLowerCase().includes(loc));const locationFit=loc==='any'?15:locMatch?15:0;const sizeFit=cap===0||!d.value?0:d.value<=cap?10:0;const score=serviceFit+sectorFit+locationFit+sizeFit;let lines=[];lines.push(`Keyword overlap: ${matched.length?matched.map(w=>`“${esc(w)}”`).join(', '):'none found in the summary'} · ${serviceFit+sectorFit}/75 potential points`);lines.push(loc==='any'?'Geographic limit: no preference entered':locKnown?'Location as stated by source: '+esc(d.region):'Location not verifiable from feed summary');lines.push(!d.value?'Contract value missing — financial fit not scored':!cap?'You did not set a maximum comfortable contract value':`Published value: ${fmtMoney(d.value)} (${d.value<=cap?'within':'above'} your stated limit)`);lines.push('Insurance, references, accreditations, tender documents and mandatory requirements: NOT VERIFIED');$('fit-results').innerHTML=`<span class="tag">Heuristic indication only</span><h3>${esc(d.title)}</h3><div class="score">${score}<span style="font-size:1rem;color:#6c7986"> / 100</span></div><div class="progress"><div style="width:${score}%"></div></div><p>${score>=65?'Topical match worth reviewing':score>=35?'Some overlap: inspect the full brief':'Weak match based on entered terms'}</p>${lines.map(s=>`<div class="explain">${s}</div>`).join('')}<div class="note">This is not an eligibility assessment or recommendation to bid. Review the official notice and documents before spending money or submitting anything.</div>`;}
$('year').textContent=new Date().getFullYear();['query','sector','sort'].forEach(id=>$(id).addEventListener('input',render));$('clear').addEventListener('click',()=>{$('query').value='';$('sector').value='all';$('sort').value='deadline';render()});$('fit-submit').addEventListener('click',fit);load();
