'use strict';
const $ = id => document.getElementById(id);
const image = $('feed'), canvas = $('overlay'), ctx = canvas.getContext('2d');
image.style.zIndex = '1';
canvas.style.zIndex = '2';
document.querySelector('.scan').style.zIndex = '3';
document.querySelector('.hud').style.zIndex = '4';
$('notice').style.zIndex = '5';
const sample = document.createElement('canvas'); sample.width = 640; sample.height = 480;
const sampleCtx = sample.getContext('2d');
let online = false, running = false, model = null, tracks = [], nextId = 1, eventCount = 0;
let pendingRetry = null, lastSeenSequence = -1, lastAdvanced = 0, natural = false;
const wanted = new Set(['person','car','truck','bus','motorcycle','bicycle','dog']);
setInterval(() => { $('clock').textContent = new Date().toLocaleTimeString(); }, 1000);
function offline(message) {
  online = false; image.hidden = true; $('led').classList.remove('live'); $('connection').textContent = 'CAMERA OFFLINE';
  $('notice').textContent = message; tracks = []; draw([]); counts([]);
}
function connect() { image.src = '/video.mjpg?t=' + Date.now(); }
image.onerror = () => { offline('Camera unavailable. Check that the Pi camera server is running.'); scheduleReconnect(); };
function scheduleReconnect() { if (!pendingRetry) pendingRetry = setTimeout(() => { pendingRetry = null; connect(); }, 4000); }
async function health() {
  try {
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 3000);
    let status;
    try { const r = await fetch('/status.json', {cache:'no-store', signal:controller.signal}); if (!r.ok) throw Error('Status unavailable'); status = await r.json(); }
    finally { clearTimeout(timeout); }
    if (status.sequence !== lastSeenSequence) { lastSeenSequence = status.sequence; lastAdvanced = performance.now(); }
    if (!status.camera || performance.now() - lastAdvanced > 5000) throw Error('No fresh camera frames');
    if (!image.naturalWidth) { scheduleReconnect(); }
    else {
      online = true; image.hidden = false; $('led').classList.add('live'); $('connection').textContent = 'LIVE / WI-FI'; $('notice').textContent = '';
    }
  } catch (e) { offline('No fresh camera frames. Waiting for Pi at ' + location.host + '.'); scheduleReconnect(); }
  setTimeout(health, 2000);
}
function loadScript(src) { return new Promise((resolve,reject) => { const s = document.createElement('script'); s.src = src; s.onload = resolve; s.onerror = reject; document.head.append(s); }); }
let libraries = false;
$('start').onclick = async () => {
  if (running) { running = false; $('start').textContent = 'Enable detection'; $('engine').textContent = 'AI PAUSED'; tracks=[];draw([]);counts([]); return; }
  $('start').disabled = true; $('engine').textContent = 'LOADING AI MODEL';
  try {
    if (!libraries) {
      await loadScript('/assets/vendor/tf.min.js');
      await loadScript('/assets/vendor/coco-ssd.min.js');
      libraries = true;
    }
    if (!model) model = await cocoSsd.load({base:'lite_mobilenet_v2',modelUrl:'/assets/model/model.json'});
    running = true; $('start').textContent = 'Pause detection'; $('engine').textContent = 'AI ACTIVE / LOCAL'; loop();
  } catch(e) { $('engine').textContent = 'AI LOAD FAILED'; $('notice').textContent = 'The local detection model could not load. Reconnect to the Pi and retry. Internet is not required.'; }
  finally { $('start').disabled = false; }
};
function counts(items) { $('people').textContent=items.filter(x=>x.class==='person').length; $('dogs').textContent=items.filter(x=>x.class==='dog').length; $('vehicles').textContent=items.filter(x=>x.class!=='person'&&x.class!=='dog').length; }
function updateTracks(items, now) {
  const unused = new Set(tracks.filter(t=>now-t.seen<1500));
  return items.map(item => {
    const [x,y,w,h]=item.bbox, center=[x+w/2,y+h/2];
    let best=null, distance=90;
    for(const t of unused) { const d=Math.hypot(t.center[0]-center[0],t.center[1]-center[1]); if(t.class===item.class&&d<distance){best=t;distance=d;} }
    if(best) unused.delete(best);
    const motion=best ? Math.hypot(center[0]-best.origin[0],center[1]-best.origin[1])>12 : false;
    const origin=best && now-best.originTime<1200 ? best.origin : center;
    const originTime=best && now-best.originTime<1200 ? best.originTime : now;
    const t={...item,id:best?.id||nextId++,center,origin,originTime,seen:now,motion,trail:[...(best?.trail||[]),center].slice(-12)};
    if(!best) logEvent(t);
    return t;
  });
}
function logEvent(t) {
  if(!eventCount) $('events').textContent='';
  eventCount++; $('count').textContent=eventCount+' EVENTS';
  const line=document.createElement('div'); line.className='event'; line.textContent=`${new Date().toLocaleTimeString()} · ${t.class.toUpperCase()} #${t.id} · ${Math.round(t.score*100)}%`;
  $('events').prepend(line); while($('events').children.length>40) $('events').lastChild.remove();
}
function draw(items) {
  ctx.clearRect(0,0,640,480); ctx.strokeStyle='#b5ff63';ctx.fillStyle='#c8ff9b';ctx.lineWidth=1.5;ctx.font='11px monospace';
  for(const t of items){ const [x,y,w,h]=t.bbox,L=Math.min(22,w/3,h/3);
    ctx.beginPath(); for(const [a,b,dx,dy] of [[x,y,1,1],[x+w,y,-1,1],[x,y+h,1,-1],[x+w,y+h,-1,-1]]){ctx.moveTo(a+dx*L,b);ctx.lineTo(a,b);ctx.lineTo(a,b+dy*L);}ctx.stroke();
    ctx.beginPath();ctx.moveTo(t.center[0]-6,t.center[1]);ctx.lineTo(t.center[0]+6,t.center[1]);ctx.moveTo(t.center[0],t.center[1]-6);ctx.lineTo(t.center[0],t.center[1]+6);ctx.stroke();
    ctx.beginPath();t.trail.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke();
    const text=`${t.class.toUpperCase()} #${t.id} ${Math.round(t.score*100)}% ${t.motion?'MOVING':'DETECTED'}`;
    const labelX=Math.max(0,Math.min(x,640-ctx.measureText(text).width-8)),labelY=Math.max(17,y-5);
    ctx.fillStyle='#07110be6';ctx.fillRect(labelX,labelY-13,ctx.measureText(text).width+8,17);ctx.fillStyle='#c8ff9b';ctx.fillText(text,labelX+4,labelY);
  }
  $('tracking').textContent=items.length ? `${items.length} OBJECT${items.length===1?'':'S'} TRACKED` : 'NO OBJECTS TRACKED';
}
async function loop(){
  if(!running)return;
  if(online&&image.naturalWidth){
    const start=performance.now();
    try{sampleCtx.drawImage(image,0,0,640,480);const items=(await model.detect(sample,20,Number($('threshold').value)/100)).filter(x=>wanted.has(x.class));
      if(!running)return;if(!online){tracks=[];draw([]);counts([]);}else{tracks=updateTracks(items,performance.now());draw(tracks);counts(tracks);$('fps').textContent=`AI ${Math.round(performance.now()-start)} ms / 2 Hz target`;}
    }catch(e){$('engine').textContent='AI ERROR / RETRYING';}
  }
  if(running)setTimeout(loop,500);
}
$('threshold').oninput=()=>{$('thresholdText').textContent=$('threshold').value+'%';};
$('fullscreen').onclick=()=>{if(!document.fullscreenElement)$('viewport').requestFullscreen().catch(()=>{});else document.exitFullscreen();};
$('color').onclick=()=>{natural=!natural;image.style.filter=natural?'none':'';$('color').textContent=natural?'Green optics':'Natural colour';};
$('snapshot').onclick=()=>{if(!online){$('notice').textContent='A live camera frame is required to save an image.';return;}const shot=document.createElement('canvas');shot.width=640;shot.height=480;const c=shot.getContext('2d');c.drawImage(image,0,0,640,480);c.drawImage(canvas,0,0);c.fillStyle='#b5ff63';c.font='12px monospace';c.fillText('GREENWATCH / '+new Date().toISOString(),12,465);shot.toBlob(blob=>{const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='greenwatch-'+Date.now()+'.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);});};
connect();health();
