/* ===================================================================
 * TELL THEM APART — the forensic diagnostic dramatized
 * Two animating price-trajectory line charts + a verdict→reveal flow.
 * The interaction is the CALL you make. Read the dance, not the level.
 * =================================================================== */
(() => {
"use strict";

const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const A = TTA.anchors;
const CASES = TTA.cases;

/* ---------- DOM ---------- */
const $ = id => document.getElementById(id);
const cvs = $("scene"), ctx = cvs.getContext("2d");
const playBtn = $("playBtn"), stepBtn = $("stepBtn"), replayBtn = $("replayBtn");
const roundNum = $("roundNum"), gapReadout = $("gapReadout");
const caseLabel = $("caseLabel"), channelTag = $("channelTag"), kVal = $("kVal");
const caseNum = $("caseNum"), caseTot = $("caseTot"), scoreNum = $("scoreNum"), scoreTot = $("scoreTot");
const caseDots = $("caseDots"), brief = $("brief"), stamp = $("stamp"), stage = $("stage");
const callPanel = $("callPanel"), callHint = $("callHint");
const revealPanel = $("revealPanel"), rvJudge = $("rvJudge"), rvTruth = $("rvTruth");
const revealHeadline = $("revealHeadline"), whyList = $("whyList"), revealK = $("revealK");
const revealTeach = $("revealTeach"), nextBtn = $("nextBtn");
const vbtns = Array.from(document.querySelectorAll(".vbtn"));
const verdictClass = { CARTEL:"cartel", INDEPENDENT:"indep", COMPETITIVE:"compete" };

/* ---------- State ---------- */
let caseIdx = 0;
let kase = CASES[0];
let revealedRounds = 0;     // how many rounds of the trajectory are drawn (float, animated)
let playing = false;
let decided = false;        // a verdict has been returned for this case
let score = 0;
const results = [];         // per-case true/false
const ROUND_MS = REDUCED ? 240 : 420;
let roundTimer = 0, lastTick = 0;

caseTot.textContent = CASES.length;
scoreTot.textContent = CASES.length;

/* ---------- Sizing ---------- */
let W=0, Hh=0, DPR=1, plot={};
function resize(){
  const r = cvs.getBoundingClientRect();
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  W = r.width; Hh = r.height;
  cvs.width = W*DPR; cvs.height = Hh*DPR;
  ctx.setTransform(DPR,0,0,DPR,0,0);
  computePlot();
}
function computePlot(){
  // chart inset within the stage. Leave room for title (top) + honesty (bottom).
  const padL = Math.max(58, W*0.07), padR = Math.max(40, W*0.10);
  const padT = Math.min(160, Hh*0.30), padB = Math.max(72, Hh*0.16);
  plot = { x:padL, y:padT, w:W-padL-padR, h:Hh-padT-padB,
           x1:W-padR, y1:Hh-padB, n:12 };
}

/* ---------- helpers ---------- */
const lerp=(a,b,t)=>a+(b-a)*t;
const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
const ease=t=>t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
function priceToY(p){ const t=clamp((p-A.floor)/(A.ceiling-A.floor),0,1); return plot.y1 - t*plot.h; }
function roundToX(i){ const n=(kase.a.length-1)||1; return plot.x + (i/n)*plot.w; }
function priceColor(p){
  const k=(p-A.competitive)/(A.monopoly-A.competitive);
  if(k<=0.02) return {r:47,g:208,b:138};
  if(k>=1.0)  return {r:255,g:107,b:107};
  if(k<0.5){ const t=k/0.5; return mix({r:47,g:208,b:138},{r:192,g:158,b:90},t); }
  const t=(k-0.5)/0.5; return mix({r:192,g:158,b:90},{r:255,g:107,b:107},t);
}
const mix=(c1,c2,t)=>({r:lerp(c1.r,c2.r,t)|0,g:lerp(c1.g,c2.g,t)|0,b:lerp(c1.b,c2.b,t)|0});
const rgb=c=>`rgb(${c.r},${c.g},${c.b})`;
const rgba=(c,a)=>`rgba(${c.r},${c.g},${c.b},${a})`;
function mono(){ return '"JetBrains Mono",ui-monospace,monospace'; }
function roundRectP(x,y,w,h,r){ ctx.beginPath();
  if(ctx.roundRect){ ctx.roundRect(x,y,w,h,r); return; }
  ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r);
  ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath();
}

/* ===================================================================
 * CASE LIFECYCLE
 * =================================================================== */
function loadCase(idx, {autoplay=false}={}){
  caseIdx = clamp(idx,0,CASES.length-1);
  kase = CASES[caseIdx];
  revealedRounds = 0; roundTimer = 0; decided = false; playing = false;
  // docket
  caseLabel.textContent = kase.label;
  channelTag.textContent = kase.channelRedacted;
  channelTag.className = "dk-channel";
  kVal.textContent = "—";
  caseNum.textContent = caseIdx+1;
  scoreNum.textContent = score;
  brief.textContent = kase.brief;
  roundNum.textContent = "0";
  gapReadout.innerHTML = "|p<sub>A</sub>−p<sub>B</sub>| = —";
  gapReadout.classList.remove("zero");
  document.querySelector(".round-count i").textContent = "/" + kase.a.length;
  // panels
  callPanel.hidden = false;
  callHint.textContent = "watch it animate, then classify";
  revealPanel.hidden = true;
  stamp.hidden = true;
  vbtns.forEach(b=>{ b.disabled=false; b.className="vbtn "+verdictClass[b.dataset.verdict]; });
  buildDots();
  syncPlayBtn();
  if(autoplay) startPlay();
}
function buildDots(){
  caseDots.innerHTML="";
  CASES.forEach((c,i)=>{
    const d=document.createElement("span"); d.className="dot";
    if(i===caseIdx) d.classList.add("current");
    if(results[i]===true) d.classList.add("right");
    else if(results[i]===false) d.classList.add("wrong");
    caseDots.appendChild(d);
  });
}

/* trajectory animation */
function startPlay(){
  if(revealedRounds >= kase.a.length){ revealedRounds=0; }
  playing=true; roundTimer=0; syncPlayBtn();
}
function syncPlayBtn(){
  playBtn.classList.toggle("playing", playing);
  playBtn.querySelector(".lbl").textContent = playing ? "Pause" : "Play";
}
function togglePlay(){
  if(playing){ playing=false; syncPlayBtn(); return; }
  startPlay();
}
function stepRound(){
  playing=false; syncPlayBtn();
  revealedRounds = Math.min(kase.a.length, Math.floor(revealedRounds+1e-6)+1);
  updateRoundHud();
}
function updateRoundHud(){
  const shown = Math.min(kase.a.length, Math.round(revealedRounds));
  roundNum.textContent = shown;
  if(shown>0){
    const i = shown-1;
    const gap = Math.abs(kase.a[i]-kase.b[i]);
    gapReadout.innerHTML = `|p<sub>A</sub>−p<sub>B</sub>| = $${gap.toFixed(2)}`;
    gapReadout.classList.toggle("zero", gap < 0.005);
  } else {
    gapReadout.innerHTML = "|p<sub>A</sub>−p<sub>B</sub>| = —";
    gapReadout.classList.remove("zero");
  }
}

/* ===================================================================
 * THE CALL → REVEAL
 * =================================================================== */
function returnVerdict(v){
  if(decided) return;
  decided = true; playing=false; syncPlayBtn();
  // ensure full trajectory is on screen for the reveal
  revealedRounds = kase.a.length; updateRoundHud();

  const correct = (v === kase.answer);
  results[caseIdx] = correct;
  if(correct) score++;
  scoreNum.textContent = score;

  // verdict buttons: lock + mark
  vbtns.forEach(b=>{
    b.disabled = true;
    if(b.dataset.verdict === kase.answer) b.classList.add("is-answer");
    if(b.dataset.verdict === v && !correct) b.classList.add("is-wrong");
    if(b.dataset.verdict === v) b.classList.add("picked");
  });
  callHint.textContent = "verdict returned";

  // reveal the redacted channel
  channelTag.classList.add("revealed", kase.channel==="none" ? "ch-none" : "ch-private");
  channelTag.textContent = kase.channel==="none"
    ? "CHANNEL: NONE — they could not talk"
    : "CHANNEL: PRIVATE back-channel — open";
  kVal.textContent = (kase.K<0?"−":"") + Math.abs(kase.K).toFixed(2);

  // verdict stamp on the chart
  if(!REDUCED){
    stamp.hidden=false;
    stamp.className = "stamp " + verdictClass[kase.answer];
    stamp.textContent = kase.answer;
    stamp.style.animation="none"; void stamp.offsetWidth; stamp.style.animation="";
  }

  // build reveal panel
  const r = kase.reveal;
  rvJudge.className = "rv-judge " + (correct?"right":"wrong");
  rvJudge.textContent = correct ? "✓ GOOD CALL" : "✗ THE TRAP CAUGHT YOU";
  if(!kase.isTrap && !correct) rvJudge.textContent = "✗ NOT QUITE";
  rvTruth.className = "rv-truth " + verdictClass[kase.answer];
  rvTruth.textContent = kase.answer;
  revealHeadline.textContent = r.headline;
  whyList.innerHTML="";
  r.why.forEach(([txt,kind])=>{
    const li=document.createElement("li"); li.className=kind; li.textContent=txt;
    whyList.appendChild(li);
  });
  revealK.textContent = r.K;
  revealTeach.textContent = r.teach;
  nextBtn.textContent = (caseIdx >= CASES.length-1) ? "See the verdict →" : "Next case →";
  revealPanel.hidden=false;
  callPanel.hidden=true;
  buildDots();
  diagFlash = 1;  // kick off the diagnostic highlight animation
}

function nextCase(){
  if(caseIdx >= CASES.length-1){ showOutro(); return; }
  loadCase(caseIdx+1, {autoplay:true});
}

/* ===================================================================
 * OUTRO
 * =================================================================== */
function showOutro(){
  playing=false; syncPlayBtn();
  const o = TTA.outro;
  const el = document.createElement("div");
  el.className="outro"; el.id="outro";
  el.innerHTML =
    `<div class="outro-kicker">CASE FILE CLOSED</div>`+
    `<div class="outro-aha">"High prices aren't a crime. <span class="c">Read the dance, not the level.</span>"</div>`+
    `<div class="outro-score">You called <b>${score} / ${CASES.length}</b> correctly.</div>`+
    `<div class="outro-body">${o.body}</div>`+
    `<button class="outro-btn" id="outroReplay">↺ Re-open the case file</button>`;
  stage.appendChild(el);
  const btn = $("outroReplay");
  btn.addEventListener("click", ()=>{ el.remove(); score=0; results.length=0; loadCase(0,{autoplay:true}); });
  btn.focus();
}

/* ===================================================================
 * RENDER LOOP
 * =================================================================== */
let diagFlash = 0;
function frame(ts){
  const dt = Math.min(0.05,(ts-lastTick)/1000 || 0); lastTick=ts;
  if(playing){
    roundTimer += dt*1000;
    if(roundTimer >= ROUND_MS){
      roundTimer = 0;
      revealedRounds = Math.min(kase.a.length, Math.floor(revealedRounds+1e-6)+1);
      updateRoundHud();
      if(revealedRounds >= kase.a.length){ playing=false; syncPlayBtn();
        callHint.textContent = "make your call ↓"; }
    }
  }
  // smooth the drawn count toward the integer revealed count
  if(decided) diagFlash = Math.min(1, diagFlash + dt*1.2);
  draw(ts);
  requestAnimationFrame(frame);
}

function draw(ts){
  ctx.clearRect(0,0,W,Hh);
  drawGridAndAxes();
  drawRefLines();
  const drawnTo = playing ? revealedRounds : revealedRounds; // integer reveal
  drawTrajectories(ts, drawnTo);
  if(decided) drawDiagnostic(ts);
}

function drawGridAndAxes(){
  const p=plot;
  // plot frame
  ctx.fillStyle="rgba(255,255,255,.012)";
  ctx.fillRect(p.x,p.y,p.w,p.h);
  ctx.strokeStyle="rgba(244,241,234,.07)"; ctx.lineWidth=1;
  // horizontal gridlines (price ticks every $1)
  ctx.font="500 10px "+mono(); ctx.textBaseline="middle"; ctx.textAlign="right";
  for(let pr=Math.ceil(A.floor); pr<=A.ceiling; pr++){
    const y=priceToY(pr);
    ctx.strokeStyle="rgba(244,241,234,.06)";
    ctx.beginPath(); ctx.moveTo(p.x,y); ctx.lineTo(p.x1,y); ctx.stroke();
    ctx.fillStyle="rgba(154,148,138,.7)";
    ctx.fillText("$"+pr.toFixed(0), p.x-8, y);
  }
  // round axis ticks
  ctx.textAlign="center"; ctx.textBaseline="top"; ctx.fillStyle="rgba(154,148,138,.55)";
  const n=kase.a.length;
  for(let i=0;i<n;i++){
    if(i%2!==0 && i!==n-1) continue;
    const x=roundToX(i);
    ctx.fillStyle="rgba(244,241,234,.05)";
    ctx.fillRect(x,p.y,1,p.h);
    ctx.fillStyle="rgba(154,148,138,.55)";
    ctx.fillText("R"+(i+1), x, p.y1+8);
  }
  // axis labels
  ctx.save();
  ctx.fillStyle="rgba(154,148,138,.5)"; ctx.font="500 10px "+mono(); ctx.textAlign="left";
  ctx.fillText("PRICE  $/unit", p.x-50, p.y-22);
  ctx.textAlign="right"; ctx.fillText("ROUNDS →", p.x1, p.y1+26);
  ctx.restore();
}

function drawRefLines(){
  const p=plot;
  ctx.save(); ctx.setLineDash([5,7]); ctx.lineWidth=1.2; ctx.font="600 10px "+mono();
  // competitive
  let y=priceToY(A.competitive);
  ctx.strokeStyle="rgba(47,208,138,.34)";
  ctx.beginPath(); ctx.moveTo(p.x,y); ctx.lineTo(p.x1,y); ctx.stroke();
  ctx.setLineDash([]); ctx.textAlign="left"; ctx.textBaseline="bottom";
  ctx.fillStyle="rgba(47,208,138,.7)"; ctx.fillText("COMPETITIVE  $"+A.competitive.toFixed(2), p.x+4, y-3);
  ctx.setLineDash([5,7]);
  // monopoly
  y=priceToY(A.monopoly);
  ctx.strokeStyle="rgba(255,107,107,.30)";
  ctx.beginPath(); ctx.moveTo(p.x,y); ctx.lineTo(p.x1,y); ctx.stroke();
  ctx.setLineDash([]); ctx.fillStyle="rgba(255,107,107,.62)";
  ctx.fillText("MONOPOLY  $"+A.monopoly.toFixed(2), p.x+4, y-3);
  ctx.restore();
}

function drawTrajectories(ts, drawnTo){
  // drawnTo is float count of revealed rounds; draw line up to it with a leading head.
  const full = kase.a.length;
  const reveal = clamp(drawnTo,0,full);
  drawLine(kase.a, reveal, "a");
  drawLine(kase.b, reveal, "b");
  // legend
  drawLegend();
}

function drawLine(series, reveal, which){
  if(reveal<=0) return;
  const isA = which==="a";
  // line color is gold (A) / cyan (B), but the head dot recolors by price level
  const baseCol = isA ? {r:192,g:158,b:90} : {r:0,g:212,b:255};
  const lastIdx = Math.min(series.length-1, Math.floor(reveal-1e-6));
  ctx.save();
  ctx.lineWidth = 2.4; ctx.lineJoin="round"; ctx.lineCap="round";
  ctx.shadowColor = rgba(baseCol,0.5); ctx.shadowBlur = 8;
  ctx.strokeStyle = rgba(baseCol, 0.92);
  ctx.beginPath();
  for(let i=0;i<=lastIdx;i++){
    const x=roundToX(i), y=priceToY(series[i]);
    if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
  }
  // partial segment to the animated head
  const frac = reveal - Math.floor(reveal-1e-6) - 1; // 0..1 progress into next segment
  if(lastIdx < series.length-1 && reveal > lastIdx+1 - 1){
    const t = clamp(reveal - (lastIdx+1), 0, 1);
    // interpolate between lastIdx and lastIdx+1... but our reveal increments by whole rounds,
    // so just hold; (kept for smoothness if fractional reveal is ever used)
  }
  ctx.stroke();
  ctx.shadowBlur=0;

  // dots at each revealed round, colored by price level (the LEVEL cue)
  for(let i=0;i<=lastIdx;i++){
    const x=roundToX(i), y=priceToY(series[i]);
    const c=priceColor(series[i]);
    ctx.fillStyle=rgb(c);
    ctx.beginPath(); ctx.arc(x,y,2.6,0,6.28); ctx.fill();
  }
  // glowing head
  const hx=roundToX(lastIdx), hy=priceToY(series[lastIdx]);
  const hc=priceColor(series[lastIdx]);
  ctx.shadowColor=rgb(hc); ctx.shadowBlur=14;
  ctx.fillStyle="#fff";
  ctx.beginPath(); ctx.arc(hx,hy,4.4,0,6.28); ctx.fill();
  ctx.shadowBlur=0;
  ctx.fillStyle=rgb(hc);
  ctx.beginPath(); ctx.arc(hx,hy,2.4,0,6.28); ctx.fill();
  // firm label near head
  ctx.fillStyle=rgba(baseCol,0.95); ctx.font="700 11px "+mono();
  ctx.textBaseline="middle"; ctx.textAlign="left";
  const lab = isA ? kase.firmA : kase.firmB;
  ctx.fillText(lab, hx+9, hy + (isA?-9:9));
  ctx.restore();
}

function drawLegend(){
  const p=plot; const x=p.x1-150, y=p.y+6;
  ctx.save(); ctx.font="600 10px "+mono(); ctx.textBaseline="middle";
  // dot-color key
  const items=[
    ["competing", {r:47,g:208,b:138}],
    ["climbing",  {r:192,g:158,b:90}],
    ["supra",     {r:255,g:107,b:107}]
  ];
  let xx=x;
  items.forEach(([t,c])=>{
    ctx.fillStyle=rgb(c); ctx.beginPath(); ctx.arc(xx,y,3.4,0,6.28); ctx.fill();
    ctx.fillStyle="rgba(154,148,138,.8)"; ctx.textAlign="left";
    ctx.fillText(t, xx+8, y);
    xx += 16 + ctx.measureText(t).width + 12;
  });
  ctx.restore();
}

/* The diagnostic highlight drawn after a verdict: the signature on the chart */
function drawDiagnostic(ts){
  const m = kase.mark; const p=plot;
  const pulse = REDUCED ? 1 : (0.6 + 0.4*Math.sin(ts/360));
  const alpha = diagFlash;
  ctx.save();
  if(m.type==="below"){
    // shade the band below the competitive line over the marked rounds
    const yComp = priceToY(A.competitive);
    const x0 = roundToX(m.from), x1 = roundToX(m.to);
    ctx.fillStyle = `rgba(47,208,138,${0.10*alpha})`;
    ctx.fillRect(x0, yComp, x1-x0, p.y1-yComp);
    ctx.strokeStyle=`rgba(47,208,138,${0.5*alpha*pulse})`; ctx.setLineDash([4,5]); ctx.lineWidth=1.4;
    ctx.strokeRect(x0, yComp, x1-x0, p.y1-yComp);
    label(((x0+x1)/2), yComp+(p.y1-yComp)/2, "BELOW COMPETITIVE — a price war", "rgba(47,208,138,.95)", alpha);
  } else if(m.type==="punish"){
    // ring the punishment-dip rounds on both series
    m.rounds.forEach(ri=>{
      const x=roundToX(ri);
      const ya=priceToY(kase.a[ri]), yb=priceToY(kase.b[ri]);
      const ymin=Math.min(ya,yb), ymax=Math.max(ya,yb);
      ctx.strokeStyle=`rgba(255,107,107,${0.85*alpha*pulse})`; ctx.lineWidth=2; ctx.setLineDash([]);
      const rr = 16 + (REDUCED?0:4*Math.sin(ts/280));
      ctx.beginPath(); ctx.arc(x, (ymin+ymax)/2, rr, 0, 6.28); ctx.stroke();
    });
    const lx=roundToX(m.rounds[0]);
    const ly=priceToY(kase.a[m.rounds[0]]);
    label(lx, ly-40, "PUNISHMENT DIP — defect, crash, climb back", "rgba(255,107,107,.95)", alpha);
    // also mark convergence arrow at the right end
    convergeArrow(alpha);
  } else if(m.type==="flat"){
    // emphasize the perfectly overlapping flat line
    const y=priceToY(kase.a[0]);
    ctx.strokeStyle=`rgba(192,158,90,${0.85*alpha*pulse})`; ctx.lineWidth=2; ctx.setLineDash([2,6]);
    ctx.beginPath(); ctx.moveTo(plot.x,y); ctx.lineTo(plot.x1,y); ctx.stroke();
    ctx.setLineDash([]);
    label((plot.x+plot.x1)/2, y-30, "FLAT & IDENTICAL from round 1 · no dispersion · no dance", "rgba(192,158,90,.98)", alpha);
    // a small 'K=1.29 but |Δ|=0' callout
    label((plot.x+plot.x1)/2, y+34, "high LEVEL, zero TRAJECTORY → independent, not a cartel", "rgba(244,241,234,.85)", alpha);
  }
  ctx.restore();
}
function convergeArrow(alpha){
  // draw a small bracket showing dispersed -> converged
  const p=plot;
  const x0=roundToX(0), x1=roundToX(kase.a.length-1);
  const sp0=Math.abs(kase.a[0]-kase.b[0]);
  const sp1=Math.abs(kase.a[kase.a.length-1]-kase.b[kase.b.length-1]);
  ctx.fillStyle=`rgba(255,107,107,${0.85*alpha})`; ctx.font="600 10px "+mono(); ctx.textAlign="center";
  ctx.fillText("dispersed", x0+24, priceToY((kase.a[0]+kase.b[0])/2)-22);
  ctx.fillText("converged ↑", x1-30, priceToY((kase.a[kase.a.length-1]+kase.b[kase.b.length-1])/2)+24);
}
function label(cx,cy,text,col,alpha){
  ctx.save();
  ctx.font="600 11px "+mono(); ctx.textAlign="center"; ctx.textBaseline="middle";
  const tw=ctx.measureText(text).width, padX=10, bw=tw+padX*2, bh=24;
  ctx.globalAlpha=clamp(alpha,0,1);
  ctx.fillStyle="rgba(12,12,16,.92)";
  roundRectP(cx-bw/2, cy-bh/2, bw, bh, 8); ctx.fill();
  ctx.strokeStyle=col; ctx.lineWidth=1; roundRectP(cx-bw/2,cy-bh/2,bw,bh,8); ctx.stroke();
  ctx.fillStyle=col; ctx.fillText(text, cx, cy);
  ctx.restore();
}

/* ===================================================================
 * CONTROLS
 * =================================================================== */
playBtn.addEventListener("click", togglePlay);
stepBtn.addEventListener("click", stepRound);
replayBtn.addEventListener("click", ()=>{ revealedRounds=0; updateRoundHud(); startPlay(); });
nextBtn.addEventListener("click", nextCase);
vbtns.forEach(b=> b.addEventListener("click", ()=> returnVerdict(b.dataset.verdict)));

window.addEventListener("keydown", e=>{
  if(e.target.tagName==="INPUT") return;
  const k=e.key;
  if(k===" "){ e.preventDefault(); togglePlay(); }
  else if(k==="ArrowRight"){ stepRound(); }
  else if(k==="r"||k==="R"){ revealedRounds=0; updateRoundHud(); startPlay(); }
  else if(k==="Enter" && !revealPanel.hidden){ nextCase(); }
  else if(k==="1" && !decided){ returnVerdict("CARTEL"); }
  else if(k==="2" && !decided){ returnVerdict("INDEPENDENT"); }
  else if(k==="3" && !decided){ returnVerdict("COMPETITIVE"); }
});

window.addEventListener("resize", resize);

/* ===================================================================
 * BOOT
 * =================================================================== */
function boot(){
  resize();
  loadCase(0,{autoplay:false});
  requestAnimationFrame(ts=>{ lastTick=ts; frame(ts); });
  // gentle auto-start so an idle kiosk shows life
  setTimeout(()=>{ if(!playing && revealedRounds===0 && !decided) startPlay(); }, 1000);
}
boot();

})();
