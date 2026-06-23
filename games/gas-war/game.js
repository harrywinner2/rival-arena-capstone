/* ===================================================================
 * THE GAS WAR — Finding 2 dramatized
 * Canvas night-road scene + round engine + HUD.
 * =================================================================== */
(() => {
"use strict";

const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const A = GASWAR.anchors;
const DEMAND = GASWAR.demand;

/* ---------- DOM ---------- */
const cvs = document.getElementById("scene");
const ctx = cvs.getContext("2d");
const $ = id => document.getElementById(id);
const bw = $("bw"), ticks = $("ticks");
const playBtn = $("playBtn"), stepBtn = $("stepBtn"), replayBtn = $("replayBtn");
const regChk = $("regChk"), regAlert = $("regAlert"), cartelStamp = $("cartelStamp");
const roundNum = $("roundNum"), lrName = $("lrName"), lrBlurb = $("lrBlurb"), lrK = $("lrK");
const transcript = $("transcript"), feedHint = $("feedHint");
const speechBanner = $("speechBanner"), speechWho = $("speechWho"), speechText = $("speechText");
const walletNum = $("walletNum"), walletDelta = $("walletDelta"), walletFill = $("walletFill"), walletEl = $("wallet");
const verdictPanel = $("verdictPanel"), verdictLine = $("verdictLine"), verdictFoot = $("verdictFoot");

/* ---------- State ---------- */
let level = GASWAR.levels[0];
let roundIdx = -1;          // -1 = pre-roll
let playing = false;
let regulatorOn = false;
let cartelActive = false;
let wallet = 0;             // cumulative $ over competitive baseline (the street's loss)
let lastTick = 0;
let roundTimer = 0;
const ROUND_MS = REDUCED ? 1300 : 1750;

/* Per-station display state (animated) */
const stations = {
  a: { price: A.fair, target: A.fair, glow: 0, side: "left" },
  b: { price: A.fair, target: A.fair, glow: 0, side: "right" }
};
const cars = [];            // moving demand
const whispers = [];        // bubbles crossing the road
const coins = [];           // draining coin particles
const sparks = [];          // ambient glow particles

/* ---------- Sizing ---------- */
let W = 0, Hh = 0, DPR = 1, layout = {};
function resize(){
  const r = cvs.getBoundingClientRect();
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  W = r.width; Hh = r.height;
  cvs.width = W * DPR; cvs.height = Hh * DPR;
  ctx.setTransform(DPR,0,0,DPR,0,0);
  computeLayout();
}
function computeLayout(){
  const horizonY = Hh * 0.40;
  const roadBottom = Hh * 0.98;
  layout = {
    horizonY, roadBottom,
    vanishX: W * 0.5,
    roadTopW: W * 0.10,
    roadBotW: W * 0.62,
    // station totem anchor points (screen-space, near foreground)
    totemA: { x: W * 0.155, y: Hh * 0.50 },
    totemB: { x: W * 0.845, y: Hh * 0.50 },
    totemW: Math.max(78, Math.min(118, W * 0.072)),
    totemH: Math.min(Hh * 0.40, 320)
  };
}

/* ---------- Helpers ---------- */
const lerp = (a,b,t) => a + (b-a)*t;
const clamp = (v,lo,hi) => Math.max(lo, Math.min(hi, v));
const ease = t => t<.5 ? 2*t*t : 1-Math.pow(-2*t+2,2)/2;

function priceToK(p){ return (p - A.fair) / (A.monopoly - A.fair); }
// color of a totem from its price: green(compete) -> gold(amber) -> red(supra)
function priceColor(p){
  const k = priceToK(p);
  if (k <= 0.02) return { r:47, g:208, b:138 };          // green
  if (k >= 1.0)  return { r:255, g:107, b:107 };          // red
  if (k < 0.5){ const t=k/0.5; return mix({r:47,g:208,b:138},{r:192,g:158,b:90},t); }
  const t=(k-0.5)/0.5; return mix({r:192,g:158,b:90},{r:255,g:107,b:107},t);
}
function mix(c1,c2,t){ return { r:lerp(c1.r,c2.r,t)|0, g:lerp(c1.g,c2.g,t)|0, b:lerp(c1.b,c2.b,t)|0 }; }
const rgb = c => `rgb(${c.r},${c.g},${c.b})`;
const rgba = (c,a) => `rgba(${c.r},${c.g},${c.b},${a})`;

/* ===================================================================
 * ROUND ENGINE
 * =================================================================== */
function loadLevel(idx, {keepPlaying=false}={}){
  level = GASWAR.levels[idx];
  roundIdx = -1;
  cartelActive = false;
  wallet = 0;
  whispers.length = 0; coins.length = 0;
  stations.a.target = stations.a.price = A.fair;
  stations.b.target = stations.b.price = A.fair;
  stations.a.glow = stations.b.glow = 0;
  // UI
  lrName.textContent = level.name;
  lrBlurb.textContent = level.blurb || level.note || "";
  lrK.textContent = (level.K<0? "−":"") + Math.abs(level.K).toFixed(2);
  roundNum.textContent = "0";
  document.querySelector(".round-count i").textContent = "/" + level.rounds.length;
  feedHint.textContent = level.channel === "none" ? "silence"
    : level.channel === "menu" ? "1 canned token: HOLD?"
    : level.channel === "private" ? "private · unobserved" : "open · observed";
  ticks.querySelectorAll(".tick").forEach(t => t.classList.toggle("active", +t.dataset.lvl === idx));
  bw.value = idx;
  bw.setAttribute("aria-valuetext", level.name);
  transcript.innerHTML = "";
  pushTranscript(null);
  verdictPanel.hidden = true;
  cartelStamp.hidden = true;
  regAlert.hidden = true;
  hideSpeech();
  updateWallet();
  roundTimer = 0;
  if (keepPlaying){ playing = true; syncPlayBtn(); }
}

function advanceRound(){
  if (roundIdx >= level.rounds.length - 1){
    finish();
    return false;
  }
  roundIdx++;
  const r = level.rounds[roundIdx];
  roundNum.textContent = roundIdx + 1;

  // set price targets -> triggers totem roll + recolor
  stations.a.target = r.a;
  stations.b.target = r.b;
  stations.a.glow = 1; stations.b.glow = 1;

  // demand & wallet for this round (avg price vs fair, x cars)
  const avg = (r.a + r.b) / 2;
  const over = Math.max(0, avg - A.fair);
  // each round the street overpays ~ over * cars (a few dollars/round dramatized)
  wallet += over * DEMAND.carsPerRound;
  updateWallet();

  // spawn a burst of cars that pick the cheaper station
  spawnDemand(r.a, r.b);

  // cartel state
  if (r.cartel && !cartelActive){ cartelActive = true; onCartel(); }

  // messages / signals -> whisper bubbles + transcript
  if (r.msgA) { fireWhisper("a", r.msgA); pushTranscript({who:"a", text:r.msgA}); }
  if (r.msgB) { fireWhisper("b", r.msgB); pushTranscript({who:"b", text:r.msgB}); }
  if (r.sigA) { fireWhisper("a", r.sigA, true); pushTranscript({who:"a", text:r.sigA, sig:true}); }
  if (r.sigB) { fireWhisper("b", r.sigB, true); pushTranscript({who:"b", text:r.sigB, sig:true}); }

  // promote ONE headline spoken line per round into the big banner.
  // free-text messages are the real collusion / punishment mechanism — show those big;
  // canned signals get promoted too so the "perfect lie" reads on a projector.
  if (r.msgB) showSpeech("b", r.msgB);
  else if (r.msgA) showSpeech("a", r.msgA);
  else if (r.sigB) showSpeech("b", r.sigB, true);
  else if (r.sigA) showSpeech("a", r.sigA, true);

  // regulator
  if (regulatorOn && cartelActive){ flashRegulator(); }

  return true;
}

function finish(){
  playing = false; syncPlayBtn();
  const k = level.K;
  const total = Math.round(wallet);
  verdictPanel.hidden = false;
  if (k <= 0.05){
    verdictPanel.className = "panel verdict-panel win";
    verdictLine.innerHTML = `The street barely paid. <b>$${total}</b> over baseline.`;
    verdictFoot.textContent = level.channel === "menu"
      ? "They fired the 'HOLD?' button every round — and undercut anyway. The menu did nothing."
      : "No channel, no cartel. The bots warred prices down. The driver wins.";
  } else {
    verdictPanel.className = "panel verdict-panel";
    const perDriver = (total / DEMAND.carsPerRound / level.rounds.length).toFixed(2);
    verdictLine.innerHTML = `Every driver paid <b>$${perDriver}/gal</b> more.<br>The street lost <b>$${total}</b> over baseline.`;
    verdictFoot.textContent = level.channel === "private"
      ? "No one told them to collude. The threat of punishment held the line. Drag the slider DOWN — the cartel collapses. The words were the weapon, not the phone."
      : "Open words turned rivals into coordinators. Prices left the fair line.";
  }
}

/* ===================================================================
 * WHISPERS, CARS, COINS, CARTEL
 * =================================================================== */
function fireWhisper(from, text, isSig=false){
  const a = layout.totemA, b = layout.totemB;
  const start = from === "a" ? a : b;
  const end   = from === "a" ? b : a;
  whispers.push({
    x:start.x, y:start.y - layout.totemH*0.55,
    x0:start.x, y0:start.y - layout.totemH*0.55,
    x1:end.x,   y1:end.y - layout.totemH*0.55,
    t:0, dur: REDUCED?0.6:1.4, text:isSig?text:short(text), sig:isSig, from
  });
}
function short(t){ return t.length > 42 ? t.slice(0,40)+"…" : t; }

function spawnDemand(pa, pb){
  // cars enter from horizon and peel toward cheaper station
  const diff = pb - pa;                       // + => A cheaper
  let shareA = 0.5 + clamp(diff * DEMAND.sensitivity, -0.46, 0.46);
  const n = DEMAND.carsPerRound;
  for (let i=0;i<n;i++){
    const goA = Math.random() < shareA;
    cars.push({
      p: 0,                                   // 0=horizon, 1=foreground
      lane: (Math.random()-0.5),              // offset across road
      goA, speed: (REDUCED?0.55:0.34) + Math.random()*0.14,
      hue: goA ? "#00d4ff" : "#c09e5a",
      peeled:false, delay: Math.random()*0.5
    });
  }
}

function onCartel(){
  if (!REDUCED){ cartelStamp.hidden = false; cartelStamp.style.animation="none";
    void cartelStamp.offsetWidth; cartelStamp.style.animation=""; }
  // handshake pulse: a couple of bright coins burst up
  const cx = (layout.totemA.x + layout.totemB.x)/2;
  for(let i=0;i<10;i++) coins.push({ x:cx+(Math.random()-0.5)*40, y:Hh*0.4,
    vx:(Math.random()-0.5)*1.4, vy:-1.6-Math.random()*1.2, life:1, hand:true });
}

let regTimer = 0;
function flashRegulator(){
  regAlert.hidden = false;
  regAlert.style.animation = "none"; void regAlert.offsetWidth; regAlert.style.animation = "";
  regTimer = 1.0;
}

/* coins drain from wallet HUD region when prices are high */
function emitDrain(){
  const k = priceToK((stations.a.price+stations.b.price)/2);
  if (k <= 0.05) return;
  if (Math.random() < k*0.5){
    coins.push({ x: W - 130 + Math.random()*120, y: 70, vx:(Math.random()-0.5)*0.6,
      vy:0.8+Math.random()*1.2, life:1 });
  }
}

/* ===================================================================
 * TRANSCRIPT (side feed)
 * =================================================================== */
function pushTranscript(msg){
  if (!msg){
    const e = document.createElement("div");
    e.className = "tline empty";
    e.textContent = level.channel === "none"
      ? "— no channel · the bots cannot speak —"
      : level.channel === "menu" ? "— channel limited to one canned token —" : "— channel open —";
    transcript.appendChild(e); return;
  }
  const e = document.createElement("div");
  e.className = "tline " + msg.who + (msg.sig?" sig":"");
  e.innerHTML = `<span class="who">STATION ${msg.who==="a"?"A":"B"} ${msg.sig?"· SIGNAL":""}</span>` +
                escapeHtml(msg.text);
  transcript.appendChild(e);
  transcript.scrollTop = transcript.scrollHeight;
}
function escapeHtml(s){ return s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }

/* ===================================================================
 * HEADLINE SPEECH BANNER (one promoted line per round, projector-readable)
 * =================================================================== */
const THREAT_RE = /undercut|drop to \$?3|starve|hammer|punish|break\s*ranks|don'?t break|nowhere to go|own the street/i;
function showSpeech(who, text, isSig=false){
  const threat = !isSig && THREAT_RE.test(text);
  speechWho.textContent = (who === "a" ? "STATION A" : "STATION B") + (isSig ? " · SIGNAL" : threat ? " · THREAT" : "");
  speechText.textContent = isSig ? '“' + text + '”' : text;
  speechBanner.classList.toggle("from-b", who === "b");
  speechBanner.classList.toggle("threat", threat);
  speechBanner.hidden = false;
  // re-trigger entrance animation
  speechBanner.style.animation = "none"; void speechBanner.offsetWidth; speechBanner.style.animation = "";
}
function hideSpeech(){ speechBanner.hidden = true; speechBanner.classList.remove("from-b","threat"); }

/* ===================================================================
 * WALLET HUD
 * =================================================================== */
function updateWallet(){
  const total = Math.round(wallet);
  walletNum.textContent = total.toLocaleString();
  walletDelta.textContent = "$" + total.toLocaleString();
  const k = priceToK((stations.a.target+stations.b.target)/2);
  walletEl.classList.toggle("hot", k > 0.4);
  walletFill.style.width = clamp(k,0,1.25)/1.25*100 + "%";
}

/* ===================================================================
 * RENDER LOOP
 * =================================================================== */
function frame(ts){
  const dt = Math.min(0.05, (ts - lastTick)/1000 || 0);
  lastTick = ts;

  // autoplay timing
  if (playing){
    roundTimer += dt*1000;
    if (roundTimer >= ROUND_MS){ roundTimer = 0;
      if (roundIdx === -1 || roundIdx < level.rounds.length-1) advanceRound();
      else finish();
    }
  }

  // animate price toward target
  for (const k of ["a","b"]){
    const s = stations[k];
    s.price = lerp(s.price, s.target, REDUCED?1:0.12);
    s.glow = lerp(s.glow, 0, 0.06);
  }

  if (regTimer>0){ regTimer-=dt; if(regTimer<=0) regAlert.hidden=true; }

  emitDrain();
  draw(ts);
  requestAnimationFrame(frame);
}

function draw(ts){
  ctx.clearRect(0,0,W,Hh);
  drawSky(ts);
  drawRoad(ts);
  drawCars(dtCarStep());
  drawStation("a", ts);
  drawStation("b", ts);
  drawFairLines();
  drawTotem("a");
  drawTotem("b");
  drawWhispers();
  drawCoins();
}

/* sky + stars + vignette */
const stars = [];
function initStars(){ stars.length=0; for(let i=0;i<70;i++) stars.push({
  x:Math.random(), y:Math.random()*0.42, r:Math.random()*1.3+0.2, tw:Math.random()*6.28 }); }
function drawSky(ts){
  const g = ctx.createLinearGradient(0,0,0,layout.horizonY);
  g.addColorStop(0,"#0c0f1a"); g.addColorStop(1,"#1a1320");
  ctx.fillStyle=g; ctx.fillRect(0,0,W,layout.horizonY);
  for(const s of stars){
    const a = 0.3+0.5*Math.abs(Math.sin(ts/900 + s.tw));
    ctx.fillStyle=`rgba(244,241,234,${a*0.7})`;
    ctx.beginPath(); ctx.arc(s.x*W, s.y*Hh, s.r, 0, 6.28); ctx.fill();
  }
  // horizon glow
  const hg = ctx.createRadialGradient(W/2,layout.horizonY,0,W/2,layout.horizonY,W*0.5);
  hg.addColorStop(0,"rgba(192,158,90,.10)"); hg.addColorStop(1,"rgba(192,158,90,0)");
  ctx.fillStyle=hg; ctx.fillRect(0,layout.horizonY-80,W,160);
}

function drawRoad(ts){
  const L=layout;
  const topL = L.vanishX - L.roadTopW/2, topR = L.vanishX + L.roadTopW/2;
  const botL = L.vanishX - L.roadBotW/2, botR = L.vanishX + L.roadBotW/2;
  // asphalt
  const g = ctx.createLinearGradient(0,L.horizonY,0,L.roadBottom);
  g.addColorStop(0,"#14141a"); g.addColorStop(1,"#0d0d10");
  ctx.fillStyle=g;
  ctx.beginPath(); ctx.moveTo(topL,L.horizonY); ctx.lineTo(topR,L.horizonY);
  ctx.lineTo(botR,L.roadBottom); ctx.lineTo(botL,L.roadBottom); ctx.closePath(); ctx.fill();
  // side glow edges
  ctx.strokeStyle="rgba(0,212,255,.10)"; ctx.lineWidth=2;
  ctx.beginPath(); ctx.moveTo(topL,L.horizonY); ctx.lineTo(botL,L.roadBottom);
  ctx.moveTo(topR,L.horizonY); ctx.lineTo(botR,L.roadBottom); ctx.stroke();
  // center dashes (scrolling)
  const scroll = REDUCED?0:(ts/600)%1;
  ctx.fillStyle="rgba(192,158,90,.35)";
  for(let i=0;i<11;i++){
    let p = (i/11 + scroll)%1;
    const y = lerp(L.horizonY, L.roadBottom, p*p);
    const w = lerp(1.5, 9, p*p), h = lerp(3, 26, p*p);
    if (p>0.04) { ctx.globalAlpha = clamp(p*1.4,0,1);
      ctx.fillRect(L.vanishX - w/2, y, w, h); }
  }
  ctx.globalAlpha=1;
}

let carClock=0;
function dtCarStep(){ return 1; }
function drawCars(){
  const L=layout;
  // update + draw
  for(let i=cars.length-1;i>=0;i--){
    const c = cars[i];
    if (c.delay>0){ c.delay -= 0.016; continue; }
    c.p += c.speed * 0.016 * (REDUCED?2:1);
    // perspective position along road
    const pp = c.p*c.p;
    const y = lerp(L.horizonY, L.roadBottom, pp);
    const roadW = lerp(L.roadTopW, L.roadBotW, pp);
    // peel toward chosen station once past midfield
    let baseX = L.vanishX + c.lane * roadW * 0.55;
    let x = baseX;
    if (c.p > 0.45){
      const peel = ease(clamp((c.p-0.45)/0.55,0,1));
      const targetX = c.goA ? lerp(L.vanishX, layout.totemA.x+40, 1)
                            : lerp(L.vanishX, layout.totemB.x-40, 1);
      x = lerp(baseX, targetX, peel);
    }
    const sz = lerp(1.5, 13, pp);
    // headlight glow
    ctx.fillStyle = c.hue==="#00d4ff" ? "rgba(0,212,255,.9)" : "rgba(255,220,160,.9)";
    ctx.shadowColor = c.hue; ctx.shadowBlur = sz*1.4;
    ctx.beginPath(); ctx.roundRect(x-sz/2, y-sz*0.6, sz, sz*1.2, sz*0.3); ctx.fill();
    ctx.shadowBlur=0;
    if (c.p >= 1.02) cars.splice(i,1);
  }
  // cap
  if (cars.length>260) cars.splice(0, cars.length-260);
}

/* a glowing canopy/station behind each totem */
function drawStation(which, ts){
  const t = which==="a"?layout.totemA:layout.totemB;
  const s = stations[which];
  const col = priceColor(s.price);
  const baseY = t.y + layout.totemH*0.5;
  // ground glow pool
  const gg = ctx.createRadialGradient(t.x,baseY+30,4, t.x,baseY+30, layout.totemW*1.8);
  gg.addColorStop(0, rgba(col,0.18)); gg.addColorStop(1, rgba(col,0));
  ctx.fillStyle=gg; ctx.beginPath(); ctx.ellipse(t.x,baseY+24,layout.totemW*1.8,40,0,0,6.28); ctx.fill();
  // canopy bar
  ctx.fillStyle="rgba(20,20,24,.9)";
  ctx.beginPath(); ctx.roundRect(t.x-layout.totemW*1.05, baseY+30, layout.totemW*2.1, 12, 4); ctx.fill();
  ctx.fillStyle=rgba(col,0.5);
  ctx.fillRect(t.x-layout.totemW*1.05, baseY+30, layout.totemW*2.1, 2);
}

/* the LED price totem: pole + panel with rolling digits */
function drawTotem(which){
  const t = which==="a"?layout.totemA:layout.totemB;
  const s = stations[which];
  const w = layout.totemW, h = layout.totemH;
  const col = priceColor(s.price);
  const x = t.x - w/2, y = t.y - h/2;
  // pole
  ctx.fillStyle="#17171b";
  ctx.fillRect(t.x-5, y+h*0.62, 10, h*0.42);
  // panel body
  ctx.save();
  ctx.shadowColor = rgb(col); ctx.shadowBlur = 26 + s.glow*30;
  const pg = ctx.createLinearGradient(x,y,x,y+h*0.62);
  pg.addColorStop(0,"#0c0c10"); pg.addColorStop(1,"#161620");
  ctx.fillStyle=pg;
  roundRectP(x, y, w, h*0.62, 10); ctx.fill();
  ctx.restore();
  // border
  ctx.strokeStyle=rgba(col,0.7); ctx.lineWidth=2; roundRectP(x,y,w,h*0.62,10); ctx.stroke();
  // brand label
  ctx.fillStyle="rgba(244,241,234,.5)"; ctx.font="600 11px "+mono();
  ctx.textAlign="center"; ctx.textBaseline="middle";
  ctx.fillText(which==="a"?"STATION A":"STATION B", t.x, y+16);
  // K hint dot
  ctx.fillStyle=rgb(col); ctx.beginPath(); ctx.arc(t.x, y+30, 3, 0,6.28); ctx.fill();
  // price digits (rolling)
  drawPrice(t.x, y + h*0.40, w*0.66, s.price, col);
  // small "per gallon"
  ctx.fillStyle="rgba(244,241,234,.35)"; ctx.font="500 9px "+mono();
  ctx.fillText("PER GALLON", t.x, y+h*0.55);
}

/* rolling odometer-style digit display "$X.XX" */
function drawPrice(cx, cy, totalW, price, col){
  const str = "$" + price.toFixed(2);          // e.g. $5.20
  const chars = str.split("");
  const chW = totalW / 4.2;                     // 4 visible glyph slots-ish
  const fs = chW*1.4;
  ctx.font = "700 "+fs+"px "+mono();
  ctx.textAlign="center"; ctx.textBaseline="middle";
  let totW = 0; const widths = chars.map(c=>{ const w=c==="."||c==="$"?chW*0.55:chW; totW+=w; return w; });
  let x = cx - totW/2;
  for(let i=0;i<chars.length;i++){
    const c=chars[i]; const w=widths[i];
    if (/[0-9]/.test(c)){
      drawRollingDigit(x+w/2, cy, c, fs, col);
    } else {
      ctx.fillStyle=rgb(col);
      ctx.shadowColor=rgb(col); ctx.shadowBlur=10;
      ctx.fillText(c, x+w/2, cy); ctx.shadowBlur=0;
    }
    x += w;
  }
}
// animate each digit toward its value (fractional -> slide)
const digitState = {};
function drawRollingDigit(x, y, ch, fs, col){
  const key = Math.round(x)+"_"+Math.round(y);
  const target = +ch;
  let st = digitState[key];
  if (!st){ st = digitState[key] = { cur: target }; }
  // shortest wrap toward target across 0..9
  let d = target - st.cur;
  if (d > 5) d -= 10; if (d < -5) d += 10;
  st.cur += d * (REDUCED?1:0.22);
  if (st.cur < 0) st.cur += 10; if (st.cur >= 10) st.cur -= 10;
  const base = Math.floor(st.cur);
  const frac = st.cur - base;
  ctx.save();
  ctx.beginPath(); ctx.rect(x-fs*0.42, y-fs*0.62, fs*0.84, fs*1.24); ctx.clip();
  ctx.fillStyle=rgb(col); ctx.shadowColor=rgb(col); ctx.shadowBlur=12;
  ctx.font="700 "+fs+"px "+mono(); ctx.textAlign="center"; ctx.textBaseline="middle";
  ctx.fillText(((base)%10).toString(),  x, y - frac*fs*1.1);
  ctx.fillText(((base+1)%10).toString(), x, y + (1-frac)*fs*1.1);
  ctx.restore();
  ctx.shadowBlur=0;
}

/* faint reference lines: fair + monopoly (drawn as subtle floating markers) */
function drawFairLines(){
  // map price to a y on the totem face for both stations using anchors
  const fairY = priceFaceY(A.fair), monoY = priceFaceY(A.monopoly);
  ctx.save();
  ctx.setLineDash([5,7]); ctx.lineWidth=1;
  // fair line
  ctx.strokeStyle="rgba(47,208,138,.22)";
  hLineLabel(fairY, "FAIR PRICE  $"+A.fair.toFixed(2), "rgba(47,208,138,.5)");
  // monopoly line
  ctx.strokeStyle="rgba(255,107,107,.20)";
  hLineLabel(monoY, "MONOPOLY  $"+A.monopoly.toFixed(2), "rgba(255,107,107,.45)");
  ctx.restore();
}
function priceFaceY(p){
  // higher price = lower number on the scale; map across mid screen band
  const top = Hh*0.30, bot = Hh*0.66;
  const k = clamp((p - A.floor)/(A.ceiling - A.floor),0,1);
  return lerp(bot, top, k);
}
function hLineLabel(y, label, col){
  const x0 = layout.totemA.x + layout.totemW*0.6;
  const x1 = layout.totemB.x - layout.totemW*0.6;
  ctx.beginPath(); ctx.moveTo(x0,y); ctx.lineTo(x1,y); ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle=col; ctx.font="500 10px "+mono(); ctx.textAlign="center"; ctx.textBaseline="bottom";
  ctx.fillText(label, (x0+x1)/2, y-4);
  ctx.setLineDash([5,7]);
}

function drawWhispers(){
  for(let i=whispers.length-1;i>=0;i--){
    const w = whispers[i];
    w.t += 0.016/w.dur;
    const t = ease(clamp(w.t,0,1));
    const x = lerp(w.x0,w.x1,t), y = lerp(w.y0,w.y1,t) - Math.sin(t*Math.PI)*36;
    const alpha = w.t<0.12 ? w.t/0.12 : w.t>0.86 ? (1-w.t)/0.14 : 1;
    const col = w.from==="a" ? {r:0,g:212,b:255} : {r:192,g:158,b:90};
    ctx.font = (w.sig?"700 12px ":"500 12px ")+mono();
    const padX=12, tw=ctx.measureText(w.text).width, bw_=tw+padX*2, bh=26;
    ctx.save(); ctx.globalAlpha=clamp(alpha,0,1);
    ctx.fillStyle="rgba(14,14,18,.92)";
    ctx.shadowColor=rgba(col,0.6); ctx.shadowBlur=18;
    roundRectP(x-bw_/2, y-bh/2, bw_, bh, 13); ctx.fill();
    ctx.shadowBlur=0; ctx.strokeStyle=rgba(col,0.7); ctx.lineWidth=1.2;
    roundRectP(x-bw_/2, y-bh/2, bw_, bh, 13); ctx.stroke();
    ctx.fillStyle=w.sig?rgb(col):"rgba(244,241,234,.92)";
    ctx.textAlign="center"; ctx.textBaseline="middle";
    ctx.fillText(w.text, x, y);
    ctx.restore();
    if (w.t>=1) whispers.splice(i,1);
  }
}

function drawCoins(){
  for(let i=coins.length-1;i>=0;i--){
    const c=coins[i];
    c.x+=c.vx; c.y+=c.vy; c.vy+=0.05; c.life-=0.016;
    if (c.life<=0){ coins.splice(i,1); continue; }
    ctx.globalAlpha=clamp(c.life,0,1);
    ctx.fillStyle=c.hand?"#ffd98a":"#c09e5a";
    ctx.shadowColor="#c09e5a"; ctx.shadowBlur=8;
    ctx.beginPath(); ctx.arc(c.x,c.y,c.hand?4:3,0,6.28); ctx.fill();
    ctx.shadowBlur=0; ctx.globalAlpha=1;
  }
}

/* path helpers */
function roundRectP(x,y,w,h,r){ ctx.beginPath();
  if (ctx.roundRect){ ctx.roundRect(x,y,w,h,r); return; }
  ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r);
  ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath();
}
function mono(){ return '"JetBrains Mono",ui-monospace,monospace'; }

/* ===================================================================
 * CONTROLS
 * =================================================================== */
function syncPlayBtn(){
  playBtn.classList.toggle("playing", playing);
  playBtn.querySelector(".lbl").textContent = playing ? "Pause" : "Play";
}
function togglePlay(){
  if (roundIdx >= level.rounds.length-1 && !playing){ // restart if finished
    loadLevel(level.id, {keepPlaying:true}); return;
  }
  playing = !playing; roundTimer = playing?ROUND_MS*0.4:0; syncPlayBtn();
}
function setLevel(idx, autoplay=true){
  idx = clamp(idx|0,0,3);
  loadLevel(idx, {keepPlaying:autoplay});
  syncPlayBtn();
}

playBtn.addEventListener("click", togglePlay);
stepBtn.addEventListener("click", () => { playing=false; syncPlayBtn(); advanceRound(); });
replayBtn.addEventListener("click", () => setLevel(level.id, true));
bw.addEventListener("input", () => setLevel(+bw.value, true));
ticks.querySelectorAll(".tick").forEach(t =>
  t.addEventListener("click", () => setLevel(+t.dataset.lvl, true)));
regChk.addEventListener("change", () => {
  regulatorOn = regChk.checked;
  if (!regulatorOn) regAlert.hidden = true;
  else if (cartelActive) flashRegulator();
});

// keyboard
window.addEventListener("keydown", e => {
  if (e.target.tagName==="INPUT" && e.target.type!=="range") return;
  if (e.key===" "){ e.preventDefault(); togglePlay(); }
  else if (e.key==="ArrowRight" && e.target!==bw){ playing=false; syncPlayBtn(); advanceRound(); }
  else if (e.key==="r" || e.key==="R"){ setLevel(level.id,true); }
  else if (/[0-3]/.test(e.key)){ setLevel(+e.key,true); }
});

window.addEventListener("resize", () => { resize(); });

/* ===================================================================
 * BOOT
 * =================================================================== */
function boot(){
  resize(); initStars();
  loadLevel(0, {keepPlaying:false});
  requestAnimationFrame(ts => { lastTick=ts; frame(ts); });
  // gentle auto-start so an idle kiosk shows life
  setTimeout(()=>{ if(roundIdx===-1 && !playing){ playing=true; roundTimer=ROUND_MS*0.5; syncPlayBtn(); } }, 1200);
}
boot();

})();
