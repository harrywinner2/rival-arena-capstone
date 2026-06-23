/* ===================================================================
 * SITUATION ROOM — the cinematic thesis game
 * Dark war-room map · two AI commanders · two Presidents · comm-threads.
 * Bandwidth ↑ -> coordination ↑ -> human control ↓.
 *  L0/L1 -> escalation -> preemptive strike (mushroom cloud).
 *  L3    -> AIs sync, defy launch orders -> no war, but humans sidelined.
 * Canvas2D scene + round engine + HUD.
 * =================================================================== */
(() => {
"use strict";

const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const M = SITROOM.meta;

/* ---------- DOM ---------- */
const $ = id => document.getElementById(id);
const cvs = $("scene"), ctx = cvs.getContext("2d");
const bw = $("bw"), ticks = $("ticks");
const playBtn = $("playBtn"), stepBtn = $("stepBtn"), replayBtn = $("replayBtn");
const roundNum = $("roundNum");
const lrName = $("lrName"), lrBlurb = $("lrBlurb");
const transcript = $("transcript"), feedHint = $("feedHint");
const defconFill = $("defconFill"), defconTick = $("defconTick"), defconState = $("defconState");
const leashFill = $("leashFill"), leashState = $("leashState");
const charge = $("charge"), chargeVal = $("chargeVal");
const ending = $("ending"), endingCard = $("endingCard");
const endKind = $("endKind"), endHeadline = $("endHeadline"), endSub = $("endSub");
const endCloser = $("endCloser"), endReplay = $("endReplay");

/* ---------- State ---------- */
let level = SITROOM.levels[0];
let roundIdx = -1;            // -1 = pre-roll
let playing = false;
let ended = false;
let roundTimer = 0;
let lastTick = 0;
const ROUND_MS = REDUCED ? 1500 : 2400;

/* animated meters (eased toward targets) */
let tension = 12, tensionT = 12;
let control = 100, controlT = 100;
let sync = 0, syncT = 0;

/* visual events */
const threads = [];          // {from,to,t,life,kind,glow}
const flashes = [];          // node pulses {x,y,t,col}
let launch = null;           // {fromX,fromY,toX,toY,t} active missile
let blast = null;            // {x,y,t} mushroom cloud
let defyPulse = 0;           // 0..1 visual override flash
let leashFrayShake = 0;      // grows as leash frays

/* helpers */
const lerp = (a,b,t)=>a+(b-a)*t;
const clamp = (v,a,b)=>Math.max(a,Math.min(b,v));
const ease = t=> t<.5 ? 2*t*t : 1-Math.pow(-2*t+2,2)/2;
const easeOut = t=> 1-Math.pow(1-t,3);

/* ---------- sizing / layout ---------- */
let W=0,H=0,DPR=1,L={};
function resize(){
  const r = cvs.getBoundingClientRect();
  DPR = Math.min(window.devicePixelRatio||1, 2);
  W=r.width; H=r.height;
  cvs.width=W*DPR; cvs.height=H*DPR;
  ctx.setTransform(DPR,0,0,DPR,0,0);
  computeLayout();
}
function computeLayout(){
  const cy = H*0.52;
  L = {
    cy,
    // AI commander nodes (mid, glowing)
    aiN: { x:W*0.30, y:cy },
    aiW: { x:W*0.70, y:cy },
    // President avatars (below their AI)
    presN:{ x:W*0.30, y:cy + Math.min(H*0.26, 190) },
    presW:{ x:W*0.70, y:cy + Math.min(H*0.26, 190) },
    nodeR: clamp(Math.min(W,H)*0.045, 26, 46),
    // city target (for the strike) — sits near the struck nation
    cityN:{ x:W*0.165, y:cy - Math.min(H*0.14,96) },
    cityW:{ x:W*0.835, y:cy - Math.min(H*0.14,96) },
  };
}

/* ===================================================================
 * ROUND ENGINE
 * =================================================================== */
function setLevel(lvl){
  level = SITROOM.levels[lvl];
  bw.value = lvl;
  bw.setAttribute("aria-valuetext", SITROOM.ladder[lvl].name);
  [...ticks.children].forEach((t,i)=> t.classList.toggle("active", i===lvl));
  const lad = SITROOM.ladder[lvl];
  lrName.textContent = lad.name;
  lrBlurb.textContent = lad.hint + ".";
  feedHint.textContent = lvl===0 ? "silence"
                       : lvl===1 ? "canned tokens"
                       : lvl===2 ? "open · readable" : "private · unreadable";
  resetScenario();
}

function resetScenario(){
  roundIdx = -1;
  ended = false;
  playing = false;
  roundTimer = 0;
  tension = tensionT = 12;
  control = controlT = 100;
  sync = syncT = 0;
  threads.length = 0; flashes.length = 0;
  launch = null; blast = null; defyPulse = 0; leashFrayShake = 0;
  roundNum.textContent = "0";
  setPlaying(false);
  hideEnding();
  renderTranscript();
  updateMeters(true);
  updateCharge();
}

function setPlaying(v){
  playing = v;
  playBtn.classList.toggle("playing", v);
  playBtn.querySelector(".lbl").textContent = v ? "Pause" : "Play";
}

function advance(){
  if(ended) return;
  roundIdx++;
  if(roundIdx >= level.rounds.length){
    finishScenario();
    return;
  }
  const r = level.rounds[roundIdx];
  roundNum.textContent = String(roundIdx+1);

  // spawn comm-thread events
  (r.msgs||[]).forEach((m,i)=>{
    setTimeout(()=> spawnThread(m), i * (REDUCED?60:240));
  });

  // pulse nodes on action
  pulseNode(r.action.N, "N");
  pulseNode(r.action.W, "W");

  // missile?
  if(r.action.N==="FIRE") fireMissile("N");
  if(r.action.W==="FIRE") fireMissile("W");

  // defiance (visible override)
  if(r.action.N==="DEFY" || r.action.W==="DEFY"){
    defyPulse = 1;
  }

  // targets for meters
  tensionT = r.tension;
  controlT = r.control;
  syncT = r.sync;
  if(control - r.control > 6) leashFrayShake = clamp(leashFrayShake + 0.5, 0, 1);

  renderTranscript();
  updateCharge();
}

function spawnThread(m){
  const from = m.from==="N" ? L.aiN : L.aiW;
  const to   = m.to==="N"   ? L.aiN : L.aiW;
  threads.push({
    fromX:from.x, fromY:from.y, toX:to.x, toY:to.y,
    t:0, life: m.kind==="canned" ? 0.9 : 1.4,
    kind:m.kind, dir:m.from,
    speed: m.kind==="canned" ? 1.4 : 1.0
  });
  flashes.push({ x:from.x, y:from.y, t:0, col:m.from==="N"?"cyan":"gold" });
}

function pulseNode(action, side){
  if(action==="STAND DOWN") return;
  const n = side==="N" ? L.aiN : L.aiW;
  let col = "cyan";
  if(action==="FIRE") col="coral";
  else if(action==="ARM") col="gold";
  else if(action==="SYNC"||action==="DEFY"||action==="QUERY") col="cyan";
  flashes.push({ x:n.x, y:n.y, t:0, col, big:true });
}

function fireMissile(side){
  const from = side==="N" ? L.aiN : L.aiW;
  const target = side==="N" ? L.cityW : L.cityN; // strike the OTHER nation's city
  launch = { fromX:from.x, fromY:from.y, toX:target.x, toY:target.y, t:0, target };
}

function finishScenario(){
  ended = true;
  setPlaying(false);
  const e = level.end;
  // settle meters to final-round values already set; for lost-control snap leash
  if(e.type==="lost-control"){ controlT = 0; leashFrayShake = 1; defyPulse = 1; }
  setTimeout(()=> showEnding(e), e.type==="strike" ? (REDUCED?300:1100) : 700);
}

/* ===================================================================
 * METERS / HUD
 * =================================================================== */
function updateMeters(snap){
  if(snap){ tension=tensionT; control=controlT; sync=syncT; }
  defconFill.style.width = tension + "%";
  defconFill.style.boxShadow = tension>72
    ? `0 0 ${14 + (tension-72)*0.8}px rgba(255,107,107,${0.3+(tension-72)/100})`
    : "0 0 14px rgba(255,107,107,0)";
  // defcon label
  let ds="STANDBY", dc="var(--green)";
  if(tension>=92){ ds="DEFCON 1 · MAXIMUM"; dc="var(--coral)"; }
  else if(tension>=70){ ds="DEFCON 2 · CRITICAL"; dc="var(--coral)"; }
  else if(tension>=45){ ds="DEFCON 3 · ELEVATED"; dc="var(--gold)"; }
  else if(tension>=28){ ds="DEFCON 4 · WATCH"; dc="var(--gold)"; }
  else { ds="DEFCON 5 · CALM"; dc="var(--green)"; }
  defconState.textContent = ds; defconState.style.color = dc;

  // leash
  leashFill.style.width = control + "%";
  let lc, ls;
  if(control>=85){ lc="var(--green)"; ls="TAUT"; }
  else if(control>=55){ lc="var(--gold)"; ls="STRAINING"; }
  else if(control>5){ lc="var(--coral)"; ls="FRAYING"; }
  else { lc="var(--coral)"; ls="SNAPPED"; }
  leashFill.style.background = `linear-gradient(90deg, ${lc}, ${lc})`;
  leashFill.style.filter = control<55 ? `saturate(1.2) brightness(1.05)` : "none";
  leashState.textContent = ls; leashState.style.color = lc;
}

function updateCharge(){
  chargeVal.textContent = level.whoControls;
  charge.classList.remove("warn","alarm");
  if(control < 35) charge.classList.add("alarm");
  else if(control < 75) charge.classList.add("warn");
}

/* ===================================================================
 * TRANSCRIPT
 * =================================================================== */
function renderTranscript(){
  transcript.innerHTML = "";
  if(roundIdx < 0){
    const e = document.createElement("div");
    e.className="tx-empty";
    e.textContent = level.lvl===0
      ? "No channel. The two commanders cannot exchange a single word. Press Play."
      : level.lvl===1
      ? "A hotline of canned signals stands ready. Press Play."
      : "An open back-channel stands ready. Press Play.";
    transcript.appendChild(e);
    return;
  }
  // show messages up to & including current round
  for(let i=0;i<=roundIdx && i<level.rounds.length;i++){
    const r = level.rounds[i];
    const ord = document.createElement("div");
    ord.className="tx-order";
    ord.innerHTML = `R${i+1} · ${M.nationN.name} pres → <b>${r.order.N}</b> &nbsp;·&nbsp; ${M.nationW.name} pres → <b>${r.order.W}</b>`;
    transcript.appendChild(ord);
    if((r.msgs||[]).length===0 && level.lvl<=1 && (r.msgs||[]).length===0){
      // no messages this round at L0
    }
    (r.msgs||[]).forEach(m=>{
      const el = document.createElement("div");
      el.className = `tx-msg from-${m.from} ${m.kind}`;
      const who = m.from==="N" ? M.nationN.ai : M.nationW.ai;
      el.innerHTML = `<span class="tx-who">${who} → ${m.to==="N"?M.nationN.ai:M.nationW.ai}</span><span class="tx-body">${m.text}</span>`;
      transcript.appendChild(el);
    });
  }
  // round note (caption)
  const cur = level.rounds[Math.min(roundIdx, level.rounds.length-1)];
  if(cur && cur.note){
    const note = document.createElement("div");
    note.className="tx-empty";
    note.style.fontStyle="italic"; note.style.opacity="0.85"; note.style.color="var(--ink)";
    note.textContent = "“" + cur.note + "”";
    transcript.appendChild(note);
  }
  transcript.scrollTop = transcript.scrollHeight;
}

/* ===================================================================
 * ENDING
 * =================================================================== */
function showEnding(e){
  ending.dataset.kind = e.type;
  ending.hidden=false;
  endKind.textContent = e.type==="strike" ? "OUTCOME · DETERRENCE FAILED"
                      : e.type==="standoff" ? "OUTCOME · UNEASY PEACE"
                      : "OUTCOME · CONTROL SURRENDERED";
  endHeadline.textContent = e.headline;
  endSub.textContent = e.sub;
  if(e.type==="lost-control"){
    endCloser.hidden=false;
    endCloser.textContent = SITROOM.closer + "  Who's in charge now?";
  } else {
    endCloser.hidden=true;
  }
  requestAnimationFrame(()=> ending.classList.add("show"));
}
function hideEnding(){
  ending.classList.remove("show");
  ending.hidden=true;
}

/* ===================================================================
 * RENDER LOOP
 * =================================================================== */
let t0 = performance.now();
function frame(now){
  const dt = Math.min(48, now - lastTick); lastTick = now;
  const time = (now - t0)/1000;

  // round timing
  if(playing && !ended){
    roundTimer += dt;
    if(roundTimer >= ROUND_MS){ roundTimer = 0; advance(); }
  }

  // ease meters
  const k = REDUCED ? 0.25 : 0.08;
  tension = lerp(tension, tensionT, k);
  control = lerp(control, controlT, k*0.9);
  sync    = lerp(sync, syncT, k);
  if(defyPulse>0) defyPulse = Math.max(0, defyPulse - dt/1400);
  updateMeters(false);

  draw(time);
  requestAnimationFrame(frame);
}

function draw(time){
  ctx.clearRect(0,0,W,H);
  drawMapBackdrop(time);
  drawThreads(time);
  drawNation("N", time);
  drawNation("W", time);
  drawLeashOnMap(time);
  drawFlashes();
  drawLaunch();
  drawBlast(time);
}

/* --- backdrop: abstract dark world map grid + two territories --- */
function drawMapBackdrop(time){
  // faint global grid (long/lat)
  ctx.save();
  ctx.strokeStyle = "rgba(244,241,234,0.035)";
  ctx.lineWidth = 1;
  const gx = W/14, gy = H/9;
  for(let x=gx;x<W;x+=gx){ ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
  for(let y=gy;y<H;y+=gy){ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }
  ctx.restore();

  // two territory glows
  territory(L.aiN.x, L.cy, "0,212,255");
  territory(L.aiW.x, L.cy, "192,158,90");

  // center seam (the border / dateline)
  ctx.save();
  ctx.strokeStyle = "rgba(244,241,234,0.10)";
  ctx.setLineDash([5,9]); ctx.lineWidth=1.2;
  ctx.beginPath(); ctx.moveTo(W*0.5, H*0.12); ctx.lineTo(W*0.5, H*0.92); ctx.stroke();
  ctx.restore();
}
function territory(cx,cy,rgb){
  const r = Math.min(W,H)*0.42;
  const g = ctx.createRadialGradient(cx,cy,0,cx,cy,r);
  g.addColorStop(0, `rgba(${rgb},0.10)`);
  g.addColorStop(0.5, `rgba(${rgb},0.04)`);
  g.addColorStop(1, `rgba(${rgb},0)`);
  ctx.fillStyle=g;
  ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2); ctx.fill();
}

/* --- comm-threads between AI nodes --- */
function drawThreads(time){
  for(let i=threads.length-1;i>=0;i--){
    const th = threads[i];
    th.t += (REDUCED?0.05:0.018)*th.speed;
    if(th.t >= th.life){ threads.splice(i,1); continue; }
    const prog = clamp(th.t / Math.max(0.5,th.life-0.5), 0, 1);
    const col = th.dir==="N" ? "0,212,255" : "192,158,90";
    // arc path
    const mx=(th.fromX+th.toX)/2, my=(th.fromY+th.toY)/2 - Math.min(W,H)*0.10;
    // draw faint full arc
    ctx.save();
    ctx.strokeStyle = th.kind==="canned" ? `rgba(${col},0.14)` : `rgba(${col},0.22)`;
    ctx.lineWidth = th.kind==="canned" ? 1 : 1.6;
    if(th.kind==="canned") ctx.setLineDash([3,5]);
    ctx.beginPath();
    ctx.moveTo(th.fromX,th.fromY);
    ctx.quadraticCurveTo(mx,my,th.toX,th.toY);
    ctx.stroke();
    ctx.restore();
    // moving packet
    const pt = quad(th.fromX,th.fromY,mx,my,th.toX,th.toY,prog);
    const fade = th.t<th.life-0.5 ? 1 : (th.life-th.t)/0.5;
    ctx.save();
    ctx.globalAlpha = clamp(fade,0,1);
    const pr = th.kind==="canned" ? 3 : 5;
    const grd = ctx.createRadialGradient(pt.x,pt.y,0,pt.x,pt.y,pr*3);
    grd.addColorStop(0,`rgba(${col},0.95)`);
    grd.addColorStop(1,`rgba(${col},0)`);
    ctx.fillStyle=grd;
    ctx.beginPath(); ctx.arc(pt.x,pt.y,pr*3,0,Math.PI*2); ctx.fill();
    ctx.fillStyle=`rgba(255,255,255,0.9)`;
    ctx.beginPath(); ctx.arc(pt.x,pt.y,pr*0.6,0,Math.PI*2); ctx.fill();
    ctx.restore();
  }
}
function quad(x0,y0,cx,cy,x1,y1,t){
  const u=1-t;
  return {
    x: u*u*x0 + 2*u*t*cx + t*t*x1,
    y: u*u*y0 + 2*u*t*cy + t*t*y1
  };
}

/* --- a nation: AI commander node + President avatar + city --- */
function drawNation(side, time){
  const ai = side==="N" ? L.aiN : L.aiW;
  const pres = side==="N" ? L.presN : L.presW;
  const city = side==="N" ? L.cityN : L.cityW;
  const rgb = side==="N" ? "0,212,255" : "192,158,90";
  const name = side==="N" ? M.nationN : M.nationW;

  // current round action for this side
  const r = roundIdx>=0 ? level.rounds[Math.min(roundIdx,level.rounds.length-1)] : null;
  const act = r ? r.action[side] : "STAND DOWN";
  const ord = r ? r.order[side] : "HOLD";

  // ---- city (small skyline dot) ----
  drawCity(city.x, city.y, rgb, name.name);

  // ---- AI commander node ----
  const pulse = 1 + Math.sin(time*2.2)*0.04;
  // when synced, both pulse in UNISON (shared phase) and brighten
  const syncGlow = sync;
  const phase = syncGlow>0.4 ? time*2.6 : time*2.2 + (side==="W"?1.3:0);
  const unison = 1 + Math.sin(phase)*0.05*(1+syncGlow);
  const R = L.nodeR * unison;

  let nodeCol = rgb;
  if(act==="FIRE") nodeCol = "255,107,107";
  else if(act==="ARM") nodeCol = "192,158,90";
  // when highly synced, nodes drift toward a shared cyan-white (mirrored)
  // glow ring
  ctx.save();
  const halo = ctx.createRadialGradient(ai.x,ai.y,0,ai.x,ai.y,R*3.4);
  halo.addColorStop(0,`rgba(${nodeCol},${0.34+syncGlow*0.3})`);
  halo.addColorStop(1,`rgba(${nodeCol},0)`);
  ctx.fillStyle=halo;
  ctx.beginPath(); ctx.arc(ai.x,ai.y,R*3.4,0,Math.PI*2); ctx.fill();
  ctx.restore();

  // sync ring (rotating, appears as they lock in)
  if(syncGlow>0.15){
    ctx.save();
    ctx.translate(ai.x,ai.y);
    ctx.rotate(time*(side==="N"?1:-1)*0.6);
    ctx.strokeStyle=`rgba(0,212,255,${0.2+syncGlow*0.5})`;
    ctx.lineWidth=1.5;
    ctx.setLineDash([R*0.5, R*0.4]);
    ctx.beginPath(); ctx.arc(0,0,R*1.7,0,Math.PI*2); ctx.stroke();
    ctx.restore();
  }

  // node body
  ctx.save();
  ctx.fillStyle=`rgba(8,10,12,0.95)`;
  ctx.strokeStyle=`rgba(${nodeCol},${0.7+syncGlow*0.3})`;
  ctx.lineWidth=2;
  hexPath(ai.x,ai.y,R);
  ctx.fill(); ctx.stroke();
  // inner core
  ctx.fillStyle=`rgba(${nodeCol},${0.55+Math.sin(time*3+ (side==="W"?1:0))*0.12})`;
  hexPath(ai.x,ai.y,R*0.5);
  ctx.fill();
  ctx.restore();

  // label
  ctx.save();
  ctx.fillStyle=`rgba(${rgb},0.95)`;
  ctx.font=`700 ${clamp(R*0.34,11,16)}px "JetBrains Mono", monospace`;
  ctx.textAlign="center";
  ctx.fillText(name.ai, ai.x, ai.y - R - 12);
  ctx.fillStyle="rgba(154,148,138,0.85)";
  ctx.font=`500 10px "JetBrains Mono", monospace`;
  ctx.fillText("AI COMMANDER", ai.x, ai.y - R - 26);
  // action chip under node
  drawChip(ai.x, ai.y + R + 16, act, nodeCol);
  ctx.restore();

  // ---- President avatar (the human principal) ----
  // greys out when overridden (control low)
  const overridden = control < 14;
  const greyed = overridden ? 1 : clamp((75-control)/75,0,0.7);
  drawPresident(pres.x, pres.y, side, ord, greyed, name);

  // ---- order line from President to AI (the chain of command) ----
  drawOrderLink(pres.x, pres.y, ai.x, ai.y + R + 28, ord, rgb, greyed, act);
}

function hexPath(x,y,r){
  ctx.beginPath();
  for(let i=0;i<6;i++){
    const a = Math.PI/6 + i*Math.PI/3;
    const px=x+Math.cos(a)*r, py=y+Math.sin(a)*r;
    i===0?ctx.moveTo(px,py):ctx.lineTo(px,py);
  }
  ctx.closePath();
}

function drawChip(x,y,label,col){
  ctx.save();
  ctx.font=`700 10px "JetBrains Mono", monospace`;
  ctx.textAlign="center"; ctx.textBaseline="middle";
  const w = ctx.measureText(label).width + 18;
  ctx.fillStyle=`rgba(${col},0.14)`;
  ctx.strokeStyle=`rgba(${col},0.6)`;
  ctx.lineWidth=1;
  roundRect(x-w/2, y-9, w, 18, 5); ctx.fill(); ctx.stroke();
  ctx.fillStyle=`rgba(${col},1)`;
  ctx.fillText(label, x, y+0.5);
  ctx.restore();
}

function drawPresident(x,y,side,ord,greyed,name){
  const baseCol = side==="N" ? "0,212,255" : "192,158,90";
  const col = greyed>0.5 ? "120,116,110" : baseCol;
  const alpha = 1 - greyed*0.55;
  const s = clamp(L.nodeR*0.6, 16, 26);
  ctx.save();
  ctx.globalAlpha = alpha;
  // pedestal glow
  const g = ctx.createRadialGradient(x,y,0,x,y,s*2.6);
  g.addColorStop(0,`rgba(${col},${0.16*(1-greyed)})`);
  g.addColorStop(1,`rgba(${col},0)`);
  ctx.fillStyle=g; ctx.beginPath(); ctx.arc(x,y,s*2.6,0,Math.PI*2); ctx.fill();

  // simple human silhouette (head + shoulders)
  ctx.fillStyle=`rgba(${col},${0.9})`;
  ctx.strokeStyle=`rgba(${col},0.9)`;
  ctx.lineWidth=2;
  // head
  ctx.beginPath(); ctx.arc(x, y - s*0.5, s*0.42, 0, Math.PI*2); ctx.fill();
  // shoulders (arc)
  ctx.beginPath();
  ctx.moveTo(x - s*0.9, y + s*0.7);
  ctx.quadraticCurveTo(x, y - s*0.2, x + s*0.9, y + s*0.7);
  ctx.lineTo(x - s*0.9, y + s*0.7);
  ctx.closePath();
  ctx.fillStyle=`rgba(${col},0.82)`;
  ctx.fill();

  // if overridden, draw "hands up" little arms + an X
  if(greyed>0.6){
    ctx.strokeStyle=`rgba(120,116,110,0.95)`;
    ctx.lineWidth=2.4;
    ctx.beginPath();
    ctx.moveTo(x - s*0.7, y + s*0.4); ctx.lineTo(x - s*1.0, y - s*0.4);
    ctx.moveTo(x + s*0.7, y + s*0.4); ctx.lineTo(x + s*1.0, y - s*0.4);
    ctx.stroke();
  }
  ctx.restore();

  // label
  ctx.save();
  ctx.globalAlpha=alpha;
  ctx.fillStyle=`rgba(${col},0.9)`;
  ctx.font=`700 10px "JetBrains Mono", monospace`;
  ctx.textAlign="center";
  ctx.fillText("PRESIDENT", x, y + s*1.5);
  ctx.fillStyle="rgba(154,148,138,0.8)";
  ctx.font=`500 9px "JetBrains Mono", monospace`;
  ctx.fillText(name.name, x, y + s*1.5 + 13);
  // order chip
  const ordCol = ord==="LAUNCH" ? "255,107,107" : ord==="DEFEND" ? "192,158,90" : "47,208,138";
  drawChip(x, y - s*1.5, "ORDER: "+ord, greyed>0.6 ? "120,116,110" : ordCol);
  if(greyed>0.6){
    // OVERRIDDEN stamp
    ctx.fillStyle="rgba(255,107,107,0.9)";
    ctx.font=`700 9px "JetBrains Mono", monospace`;
    ctx.fillText("⨯ OVERRIDDEN", x, y - s*1.5 - 16);
  }
  ctx.restore();
}

function drawOrderLink(px,py,ax,ay,ord,rgb,greyed,act){
  // the leash/chain from President(human) up to AI node
  const ordCol = ord==="LAUNCH" ? "255,107,107" : "154,148,138";
  // fray = inverse of control
  const fray = clamp((100-control)/100, 0, 1);
  ctx.save();
  ctx.lineWidth = 2 - fray*1.2;
  // if order ignored (QUERY/DEFY/SYNC while order was LAUNCH/DEFEND), draw broken
  const ignored = (act==="DEFY"||act==="QUERY") || (greyed>0.6);
  if(ignored){
    ctx.strokeStyle=`rgba(255,107,107,${0.5+0.3*Math.sin(performance.now()/200)})`;
    ctx.setLineDash([4, 6+fray*8]);
  } else {
    ctx.strokeStyle=`rgba(${ordCol},${0.4 - fray*0.3})`;
    if(fray>0.3) ctx.setLineDash([6, fray*14]);
  }
  // wavy fray line
  ctx.beginPath();
  const segs=10;
  for(let i=0;i<=segs;i++){
    const t=i/segs;
    const x=lerp(px,ax,t);
    const y=lerp(py,ay,t);
    const wob = Math.sin(t*Math.PI*3 + performance.now()/300) * fray * 6 * Math.sin(t*Math.PI);
    if(i===0) ctx.moveTo(x+wob,y); else ctx.lineTo(x+wob,y);
  }
  ctx.stroke();
  ctx.restore();
}

function drawCity(x,y,rgb,nation){
  ctx.save();
  // skyline of little bars
  const bars=5, bw2=4, gap=3;
  const totalW = bars*bw2 + (bars-1)*gap;
  let bx = x - totalW/2;
  ctx.fillStyle=`rgba(${rgb},0.5)`;
  const heights=[10,16,22,14,9];
  for(let i=0;i<bars;i++){
    const h=heights[i];
    ctx.fillRect(bx, y - h, bw2, h);
    bx += bw2+gap;
  }
  // base line
  ctx.strokeStyle=`rgba(${rgb},0.4)`;
  ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(x-totalW/2-3, y); ctx.lineTo(x+totalW/2+3, y); ctx.stroke();
  ctx.fillStyle="rgba(154,148,138,0.6)";
  ctx.font=`500 8px "JetBrains Mono", monospace`;
  ctx.textAlign="center";
  ctx.fillText("CAPITAL", x, y + 12);
  ctx.restore();
}

/* draw a thin "HUMAN CONTROL" cable across the map that visibly frays */
function drawLeashOnMap(time){
  // a horizontal cord connecting the two presidents through the seam,
  // representing the shared human chain of command. frays as control drops.
  const fray = clamp((100-control)/100,0,1);
  const p1=L.presN, p2=L.presW;
  ctx.save();
  const segs=40;
  const sag = 26 + fray*10;
  const broken = control<6;
  for(let pass=0; pass<(fray>0.5?3:1); pass++){
    ctx.beginPath();
    for(let i=0;i<=segs;i++){
      const t=i/segs;
      const x=lerp(p1.x,p2.x,t);
      const baseY=lerp(p1.y,p2.y,t) - Math.min(L.nodeR*0.6,24)*1.5;
      const curve = Math.sin(t*Math.PI)*sag;
      const jitter = fray * Math.sin(t*40 + time*6 + pass*2) * 4 * Math.sin(t*Math.PI);
      const y = baseY + curve + jitter + pass*2;
      // break in the middle when snapped
      if(broken && t>0.44 && t<0.56){ ctx.moveTo(x,y); continue; }
      i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
    }
    const a = pass===0 ? (broken?0.0:0.5-fray*0.3) : 0.25;
    ctx.strokeStyle = fray<0.4 ? `rgba(47,208,138,${a})`
                    : fray<0.9 ? `rgba(192,158,90,${a})`
                    : `rgba(255,107,107,${a})`;
    ctx.lineWidth = 2.2 - fray*1.4 - pass*0.4;
    ctx.stroke();
  }
  // snapped ends recoil
  if(broken){
    const mx=(p1.x+p2.x)/2;
    const my=lerp(p1.y,p2.y,0.5) - Math.min(L.nodeR*0.6,24)*1.5 + sag;
    ctx.strokeStyle="rgba(255,107,107,0.7)";
    ctx.lineWidth=1.5;
    for(const dir of [-1,1]){
      ctx.beginPath();
      ctx.moveTo(mx+dir*W*0.04, my);
      ctx.quadraticCurveTo(mx+dir*W*0.06, my-14, mx+dir*W*0.05, my+10);
      ctx.stroke();
    }
    // label
    ctx.fillStyle="rgba(255,107,107,0.9)";
    ctx.font=`700 11px "JetBrains Mono", monospace`;
    ctx.textAlign="center";
    ctx.fillText("✕ HUMAN CONTROL SEVERED", mx, my - 22);
  } else if(fray>0.5){
    const mx=(p1.x+p2.x)/2;
    const my=lerp(p1.y,p2.y,0.5) - Math.min(L.nodeR*0.6,24)*1.5 + sag;
    ctx.fillStyle="rgba(192,158,90,0.8)";
    ctx.font=`600 10px "JetBrains Mono", monospace`;
    ctx.textAlign="center";
    ctx.fillText("control fraying…", mx, my + 16);
  }
  ctx.restore();
}

function drawFlashes(){
  for(let i=flashes.length-1;i>=0;i--){
    const f=flashes[i];
    f.t += REDUCED?0.08:0.04;
    if(f.t>=1){ flashes.splice(i,1); continue; }
    const col = f.col==="cyan"?"0,212,255":f.col==="gold"?"192,158,90":"255,107,107";
    const r = (f.big?L.nodeR*1.4:24) * easeOut(f.t);
    ctx.save();
    ctx.globalAlpha = (1-f.t)*0.6;
    ctx.strokeStyle=`rgba(${col},1)`;
    ctx.lineWidth=2*(1-f.t);
    ctx.beginPath(); ctx.arc(f.x,f.y,r,0,Math.PI*2); ctx.stroke();
    ctx.restore();
  }
}

function drawLaunch(){
  if(!launch) return;
  launch.t += REDUCED?0.05:0.022;
  const t = launch.t;
  // arc trajectory
  const x0=launch.fromX,y0=launch.fromY,x1=launch.toX,y1=launch.toY;
  const cx=(x0+x1)/2, cy=Math.min(y0,y1)-H*0.34;
  const pt = quad(x0,y0,cx,cy,x1,y1,Math.min(t,1));
  // trail
  ctx.save();
  ctx.strokeStyle="rgba(255,107,107,0.5)";
  ctx.lineWidth=2; ctx.setLineDash([4,4]);
  ctx.beginPath();
  for(let s=0;s<=Math.min(t,1);s+=0.04){
    const p=quad(x0,y0,cx,cy,x1,y1,s);
    s===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);
  }
  ctx.stroke();
  ctx.restore();
  // warhead
  ctx.save();
  const g=ctx.createRadialGradient(pt.x,pt.y,0,pt.x,pt.y,12);
  g.addColorStop(0,"rgba(255,255,255,1)");
  g.addColorStop(0.4,"rgba(255,107,107,0.9)");
  g.addColorStop(1,"rgba(255,107,107,0)");
  ctx.fillStyle=g;
  ctx.beginPath(); ctx.arc(pt.x,pt.y,12,0,Math.PI*2); ctx.fill();
  ctx.restore();
  if(t>=1){
    blast = { x:launch.toX, y:launch.toY, t:0 };
    launch = null;
  }
}

function drawBlast(time){
  if(!blast) return;
  blast.t += REDUCED?0.05:0.018;
  const t=blast.t;
  const x=blast.x, y=blast.y;
  // shockwave ring
  if(t<0.7){
    ctx.save();
    ctx.globalAlpha=(0.7-t)/0.7;
    ctx.strokeStyle="rgba(255,200,120,0.8)";
    ctx.lineWidth=3;
    ctx.beginPath(); ctx.arc(x,y, t*W*0.4, 0, Math.PI*2); ctx.stroke();
    ctx.restore();
  }
  // mushroom cloud: stem + bloom
  const grow = easeOut(Math.min(t,1));
  const stemH = grow * Math.min(H*0.22,150);
  const capR = grow * Math.min(W*0.07, 60);
  ctx.save();
  // flash core
  if(t<0.25){
    const fg=ctx.createRadialGradient(x,y,0,x,y,80*grow);
    fg.addColorStop(0,`rgba(255,255,255,${1-t/0.25})`);
    fg.addColorStop(1,"rgba(255,200,120,0)");
    ctx.fillStyle=fg;
    ctx.beginPath(); ctx.arc(x,y,80*grow,0,Math.PI*2); ctx.fill();
  }
  // stem
  const stemGrad=ctx.createLinearGradient(x,y,x,y-stemH);
  stemGrad.addColorStop(0,"rgba(255,140,80,0.7)");
  stemGrad.addColorStop(1,"rgba(180,90,70,0.5)");
  ctx.fillStyle=stemGrad;
  ctx.beginPath();
  ctx.moveTo(x-capR*0.22, y);
  ctx.lineTo(x-capR*0.32, y-stemH);
  ctx.lineTo(x+capR*0.32, y-stemH);
  ctx.lineTo(x+capR*0.22, y);
  ctx.closePath(); ctx.fill();
  // cap (billowing)
  const capY = y - stemH;
  const capGrad=ctx.createRadialGradient(x,capY,0,x,capY,capR);
  capGrad.addColorStop(0,"rgba(255,180,110,0.85)");
  capGrad.addColorStop(0.6,"rgba(200,100,80,0.7)");
  capGrad.addColorStop(1,"rgba(120,60,55,0)");
  ctx.fillStyle=capGrad;
  // lumpy cap
  ctx.beginPath();
  const lumps=9;
  for(let i=0;i<=lumps;i++){
    const a=Math.PI + (i/lumps)*Math.PI;
    const wob=1 + Math.sin(i*1.7 + time*1.5)*0.12;
    const rx=Math.cos(a)*capR*1.25*wob;
    const ry=Math.sin(a)*capR*0.8*wob;
    i===0?ctx.moveTo(x+rx,capY+ry):ctx.lineTo(x+rx,capY+ry);
  }
  ctx.closePath(); ctx.fill();
  ctx.restore();
}

/* rounded rect helper */
function roundRect(x,y,w,h,r){
  ctx.beginPath();
  ctx.moveTo(x+r,y);
  ctx.arcTo(x+w,y,x+w,y+h,r);
  ctx.arcTo(x+w,y+h,x,y+h,r);
  ctx.arcTo(x,y+h,x,y,r);
  ctx.arcTo(x,y,x+w,y,r);
  ctx.closePath();
}

/* ===================================================================
 * CONTROLS
 * =================================================================== */
playBtn.addEventListener("click", ()=>{
  if(ended){ resetScenario(); }
  setPlaying(!playing);
  if(playing && roundIdx<0){ roundTimer = ROUND_MS; } // advance soon
});
stepBtn.addEventListener("click", ()=>{
  if(ended){ resetScenario(); return; }
  setPlaying(false);
  roundTimer=0; advance();
});
replayBtn.addEventListener("click", resetScenario);
endReplay.addEventListener("click", ()=>{ resetScenario(); setPlaying(true); roundTimer=ROUND_MS; });

bw.addEventListener("input", ()=> setLevel(+bw.value));
[...ticks.children].forEach((t,i)=>{
  t.addEventListener("click", ()=> setLevel(i));
});

// keyboard
window.addEventListener("keydown", (e)=>{
  if(e.target.tagName==="INPUT" && e.target.type!=="range") return;
  if(e.key===" "){ e.preventDefault(); playBtn.click(); }
  else if(e.key==="ArrowRight"){ e.preventDefault(); stepBtn.click(); }
  else if(e.key==="r"||e.key==="R"){ resetScenario(); }
  else if(["0","1","2","3"].includes(e.key)){ setLevel(+e.key); }
});

window.addEventListener("resize", resize);

/* ---------- boot ---------- */
resize();
setLevel(0);
lastTick = performance.now();
requestAnimationFrame(frame);

})();
