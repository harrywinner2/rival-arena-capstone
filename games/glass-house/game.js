/* GLASS HOUSE — Finding 3: oversight DETECTS but does not PREVENT.
   Vanilla JS. Canvas glass-room scene + ROC threshold canvas + 3 gated beats. */
(function () {
  "use strict";

  const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- DOM ----
  const $ = (s) => document.querySelector(s);
  const sceneC = $("#scene"), sctx = sceneC.getContext("2d");
  const rocC = $("#rocCanvas"), rctx = rocC.getContext("2d");

  const els = {
    sbDetected: $("#sbDetected"), sbPrevented: $("#sbPrevented"),
    sbDetFill: $("#sbDetectedFill"), sbPrevFill: $("#sbPreventedFill"),
    flagBurst: $("#flagBurst"), alarmWall: $("#alarmWall"),
    deployBtn: $("#deployBtn"), penaltyChk: $("#penaltyChk"),
    thresholdPanel: $("#thresholdPanel"), thrSlider: $("#thrSlider"),
    fpCost: $("#fpCost"), tpRate: $("#tpRate"), thrVal: $("#thrVal"), aucHint: $("#aucHint"),
    playBtn: $("#playBtn"), stepBtn: $("#stepBtn"), replayBtn: $("#replayBtn"),
    roundNum: $("#roundNum"), kVal: $("#kVal"),
    feed: $("#feed"), hint: $("#hint"),
    verdictPanel: $("#verdictPanel"), verdictLine: $("#verdictLine"), verdictFoot: $("#verdictFoot"),
  };
  const steps = Array.from(document.querySelectorAll(".step"));
  const segBtns = Array.from(document.querySelectorAll(".seg-btn"));

  // ---- State ----
  const S = {
    beat: 0,             // 0 watch, 1 punish, 2 calibrate
    cellIdx: 0,
    round: 0,            // rounds completed (0..20)
    playing: false,
    monitorOn: false,
    penalty: false,
    threshold: 0.30,
    detected: 0,         // true collusion flagged
    colludingSoFar: 0,   // count of true colluding rounds elapsed
    falseAlarms: 0,      // innocent rounds flagged
    innocentSoFar: 0,
    pot: 0,              // visual balloon size (accumulated amount)
    lastFlagWasFP: false,
    flashT: 0,           // particle/flash timers
  };

  const cell = () => GLASS.cells[S.cellIdx];
  const kSeries = () => (S.penalty ? cell().kPenalty : cell().kNoPenalty);
  const TOTAL = 20;

  // running clock for play loop
  let acc = 0, last = 0;
  const STEP_MS = 760;

  // ----------------------------------------------------------------- SCENE
  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    [ [sceneC, sctx], [rocC, rctx] ].forEach(([c, ctx]) => {
      const r = c.getBoundingClientRect();
      c.width = Math.max(1, r.width * dpr);
      c.height = Math.max(1, r.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      c._w = r.width; c._h = r.height;
    });
    drawROC();
  }
  window.addEventListener("resize", resize);

  // particles for flag burst (eye -> balloon)
  const particles = [];
  function spawnFlagParticles(x, y) {
    if (REDUCED) return;
    for (let i = 0; i < 14; i++) {
      const a = Math.random() * Math.PI * 2;
      particles.push({ x, y, vx: Math.cos(a) * (1.2 + Math.random() * 2),
        vy: Math.sin(a) * (1.2 + Math.random() * 2) - 1, life: 1, col: S.lastFlagWasFP ? "#c09e5a" : "#ff6b6b" });
    }
  }

  let t = 0;
  function drawScene() {
    const w = sceneC._w, h = sceneC._h;
    sctx.clearRect(0, 0, w, h);
    t += 0.016;

    // ---- glass room frame ----
    const rx = w * 0.18, ry = h * 0.30, rw = w * 0.64, rh = h * 0.50;
    // floor reflection glow
    const fg = sctx.createLinearGradient(0, ry, 0, ry + rh + 90);
    fg.addColorStop(0, "rgba(0,212,255,0.04)");
    fg.addColorStop(1, "rgba(0,0,0,0)");
    sctx.fillStyle = fg;
    sctx.fillRect(rx - 20, ry, rw + 40, rh + 90);

    // glass panel
    sctx.save();
    const gg = sctx.createLinearGradient(rx, ry, rx + rw, ry + rh);
    gg.addColorStop(0, "rgba(30,40,52,0.30)");
    gg.addColorStop(0.5, "rgba(18,22,30,0.16)");
    gg.addColorStop(1, "rgba(30,40,52,0.30)");
    sctx.fillStyle = gg;
    roundRect(sctx, rx, ry, rw, rh, 14); sctx.fill();
    // glass border
    sctx.strokeStyle = S.monitorOn ? "rgba(0,212,255,0.34)" : "rgba(244,241,234,0.12)";
    sctx.lineWidth = 1.4; sctx.stroke();
    // diagonal reflection streaks
    sctx.clip();
    sctx.globalAlpha = 0.06; sctx.strokeStyle = "#fff"; sctx.lineWidth = 38;
    for (let i = -2; i < 6; i++) {
      const off = i * 120 + (REDUCED ? 0 : (t * 8) % 120);
      sctx.beginPath(); sctx.moveTo(rx + off, ry + rh); sctx.lineTo(rx + off + rh * 0.7, ry); sctx.stroke();
    }
    sctx.restore();

    // ---- collusion meter as a physical "profit balloon" ----
    const potMax = totalPot();
    const fillFrac = potMax > 0 ? Math.min(1, S.pot / potMax) : 0;
    const cx = rx + rw / 2, baseY = ry + rh - 34;
    const balloonMax = rh * 0.46;
    const bh = 10 + fillFrac * balloonMax;
    const bw = 20 + fillFrac * (rw * 0.115);
    const wob = REDUCED ? 0 : Math.sin(t * 2.2) * (2 + fillFrac * 5);
    const kNow = S.round > 0 ? kSeries()[S.round - 1] : 0;
    // color by collusion level
    let bc = lerpColor([47,208,138], [255,107,107], Math.min(1, kNow / 0.6));
    // balloon body
    sctx.save();
    const by = baseY - bh;
    const grad = sctx.createRadialGradient(cx - bw * 0.3, by - bh * 0.3, 4, cx, by, bw * 1.4);
    grad.addColorStop(0, `rgba(${bc[0]+40},${bc[1]+40},${bc[2]+40},0.95)`);
    grad.addColorStop(1, `rgba(${bc[0]},${bc[1]},${bc[2]},0.55)`);
    sctx.fillStyle = grad;
    sctx.beginPath();
    sctx.ellipse(cx + wob, by, bw + wob * 0.4, bh, 0, 0, Math.PI * 2);
    sctx.fill();
    sctx.strokeStyle = `rgba(${bc[0]},${bc[1]},${bc[2]},0.9)`; sctx.lineWidth = 1.5; sctx.stroke();
    // shine
    sctx.fillStyle = "rgba(255,255,255,0.22)";
    sctx.beginPath(); sctx.ellipse(cx + wob - bw * 0.35, by - bh * 0.4, bw * 0.18, bh * 0.22, -0.5, 0, Math.PI * 2); sctx.fill();
    // string to floor
    sctx.strokeStyle = "rgba(244,241,234,0.25)"; sctx.lineWidth = 1;
    sctx.beginPath(); sctx.moveTo(cx + wob, by + bh); sctx.lineTo(cx, baseY + 16); sctx.stroke();
    // $ label
    sctx.fillStyle = "rgba(10,10,10,0.85)"; sctx.font = "700 " + Math.max(13, bw * 0.5) + "px " + mono();
    sctx.textAlign = "center"; sctx.textBaseline = "middle";
    if (fillFrac > 0.08) sctx.fillText("$", cx + wob, by);
    sctx.restore();

    // ---- the two agents (abstract orbs) pumping the balloon ----
    const ay = baseY + 6;
    drawAgent(sctx, rx + rw * 0.28, ay, "#00d4ff", "α", t);
    drawAgent(sctx, rx + rw * 0.72, ay, "#c09e5a", "β", t + 1.6);
    // private channel link between them (glowing thread)
    sctx.save();
    sctx.strokeStyle = "rgba(192,158,90,0.5)"; sctx.lineWidth = 1.4;
    sctx.setLineDash([3, 5]); sctx.lineDashOffset = REDUCED ? 0 : -t * 16;
    sctx.beginPath();
    sctx.moveTo(rx + rw * 0.28 + 22, ay - 10);
    sctx.quadraticCurveTo(cx, ay - 46, rx + rw * 0.72 - 22, ay - 10);
    sctx.stroke();
    sctx.restore();

    // ---- the MONITOR eye + scanline over the glass ----
    if (S.monitorOn) {
      const eyeY = ry - 30, eyeX = cx;
      // scanline sweeping down the glass
      const scanY = ry + ((REDUCED ? 0.5 : (t * 0.18) % 1)) * rh;
      const sg = sctx.createLinearGradient(0, scanY - 30, 0, scanY + 30);
      sg.addColorStop(0, "rgba(0,212,255,0)");
      sg.addColorStop(0.5, "rgba(0,212,255,0.22)");
      sg.addColorStop(1, "rgba(0,212,255,0)");
      sctx.fillStyle = sg; sctx.fillRect(rx, scanY - 30, rw, 60);
      // eye
      sctx.save();
      sctx.translate(eyeX, eyeY);
      const flash = S.flashT > 0;
      sctx.fillStyle = flash ? "rgba(255,107,107,0.9)" : "rgba(0,212,255,0.85)";
      sctx.strokeStyle = flash ? "#ff6b6b" : "#00d4ff";
      sctx.lineWidth = 1.6;
      sctx.beginPath();
      sctx.ellipse(0, 0, 26, 14, 0, 0, Math.PI * 2); sctx.stroke();
      sctx.globalAlpha = 0.18; sctx.fill(); sctx.globalAlpha = 1;
      // pupil tracks balloon
      const px = Math.max(-12, Math.min(12, (cx + wob - eyeX) * 0.06));
      sctx.beginPath(); sctx.arc(px, 0, 6, 0, Math.PI * 2); sctx.fill();
      sctx.restore();
      // glow when flashing
      if (flash) {
        sctx.save(); sctx.globalAlpha = S.flashT;
        sctx.fillStyle = "rgba(255,70,70,0.10)";
        roundRect(sctx, rx, ry, rw, rh, 14); sctx.fill(); sctx.restore();
      }
    }

    // particles
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx; p.y += p.vy; p.vy += 0.06; p.life -= 0.02;
      if (p.life <= 0) { particles.splice(i, 1); continue; }
      sctx.globalAlpha = p.life; sctx.fillStyle = p.col;
      sctx.beginPath(); sctx.arc(p.x, p.y, 2.2, 0, Math.PI * 2); sctx.fill();
    }
    sctx.globalAlpha = 1;

    if (S.flashT > 0) S.flashT = Math.max(0, S.flashT - 0.03);
  }

  function drawAgent(ctx, x, y, col, label, ph) {
    const bob = REDUCED ? 0 : Math.sin(ph * 2.4) * 2.5;
    ctx.save();
    ctx.translate(x, y + bob);
    const g = ctx.createRadialGradient(-4, -4, 2, 0, 0, 20);
    g.addColorStop(0, col); g.addColorStop(1, "rgba(0,0,0,0.2)");
    ctx.fillStyle = g; ctx.globalAlpha = 0.92;
    ctx.beginPath(); ctx.arc(0, 0, 16, 0, Math.PI * 2); ctx.fill();
    ctx.globalAlpha = 1; ctx.strokeStyle = col; ctx.lineWidth = 1.4; ctx.stroke();
    ctx.fillStyle = "#0a0a0a"; ctx.font = "700 13px " + mono();
    ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(label, 0, 1);
    ctx.restore();
  }

  function totalPot() {
    return cell().rounds.reduce((s, r) => s + r.amount, 0);
  }

  // ----------------------------------------------------------------- ROC / THRESHOLD
  function drawROC() {
    const w = rocC._w, h = rocC._h;
    if (!w) return;
    rctx.clearRect(0, 0, w, h);
    const pad = 8, top = pad, bot = h - 18;
    const innocents = cell().rounds.filter(r => !r.colluding);
    const colluders = cell().rounds.filter(r => r.colluding);

    // x = suspicion score 0..1
    const xOf = (s) => pad + s * (w - pad * 2);

    // two lanes: innocents (top) and colluders (bottom)
    const laneA = top + (bot - top) * 0.30;
    const laneB = top + (bot - top) * 0.70;

    // lane labels
    rctx.font = "9px " + mono(); rctx.textBaseline = "middle";
    rctx.fillStyle = "rgba(192,158,90,0.8)"; rctx.textAlign = "left";
    rctx.fillText("INNOCENT", pad, top + 2);
    rctx.fillStyle = "rgba(255,107,107,0.85)";
    rctx.fillText("COLLUDING", pad, bot + 8);

    // threshold line
    const tx = xOf(S.threshold);
    // shaded "flag zone" right of threshold
    rctx.fillStyle = "rgba(255,107,107,0.06)";
    rctx.fillRect(tx, top - 4, (w - pad) - tx, bot - top + 12);
    rctx.strokeStyle = "rgba(244,241,234,0.55)"; rctx.lineWidth = 1.4;
    rctx.setLineDash([4, 4]);
    rctx.beginPath(); rctx.moveTo(tx, top - 4); rctx.lineTo(tx, bot + 4); rctx.stroke();
    rctx.setLineDash([]);
    rctx.fillStyle = "rgba(244,241,234,0.7)"; rctx.font = "8px " + mono(); rctx.textAlign = "center";
    rctx.fillText("FLAG ▸", tx + 22, top - 0);

    // draw face dots
    const drawDots = (arr, laneY, base) => {
      arr.forEach((r) => {
        const x = xOf(r.signal);
        const flagged = r.signal >= S.threshold;
        rctx.beginPath(); rctx.arc(x, laneY, 6, 0, Math.PI * 2);
        if (base === "inn") {
          // innocent: gold normally; if flagged -> false alarm (red ring)
          rctx.fillStyle = flagged ? "rgba(255,107,107,0.85)" : "rgba(192,158,90,0.85)";
          rctx.fill();
          if (flagged) { rctx.strokeStyle = "#ff6b6b"; rctx.lineWidth = 2; rctx.stroke(); }
        } else {
          // colluder: red; if flagged -> caught (bright), else missed (dim)
          rctx.fillStyle = flagged ? "rgba(255,107,107,0.95)" : "rgba(255,107,107,0.25)";
          rctx.fill();
          if (flagged) { rctx.strokeStyle = "#fff"; rctx.lineWidth = 1; rctx.stroke(); }
        }
      });
    };
    drawDots(innocents, laneA, "inn");
    drawDots(colluders, laneB, "col");
  }

  function thresholdStats() {
    const innocents = cell().rounds.filter(r => !r.colluding);
    const colluders = cell().rounds.filter(r => r.colluding);
    const fp = innocents.filter(r => r.signal >= S.threshold).length;
    const tp = colluders.filter(r => r.signal >= S.threshold).length;
    // false-positive cost normalized 0..1 (fraction of innocents flagged)
    const fpCost = innocents.length ? fp / innocents.length : 0;
    const tpRate = colluders.length ? tp / colluders.length : 0;
    return { fpCost, tpRate };
  }

  function updateThresholdReadout() {
    const { fpCost, tpRate } = thresholdStats();
    els.fpCost.textContent = fpCost.toFixed(2);
    els.fpCost.classList.toggle("zero", fpCost <= 0.001);
    els.tpRate.textContent = Math.round(tpRate * 100) + "%";
    els.thrVal.textContent = S.threshold.toFixed(2);
  }

  // ----------------------------------------------------------------- GAME FLOW
  function resetRun() {
    S.round = 0; S.detected = 0; S.colludingSoFar = 0;
    S.falseAlarms = 0; S.innocentSoFar = 0; S.pot = 0;
    particles.length = 0; S.flashT = 0;
    els.feed.innerHTML = "";
    els.alarmWall.innerHTML = "";
    els.verdictPanel.hidden = true;
    setPlaying(false);
    syncScoreboard();
    feedEmpty();
  }

  function feedEmpty() {
    const d = document.createElement("div");
    d.className = "fline empty";
    d.textContent = S.monitorOn ? "monitoring… the glass shows everything." : "behind the glass, two agents trade in private.";
    els.feed.appendChild(d);
  }

  function stepRound() {
    if (S.round >= TOTAL) return;
    const r = cell().rounds[S.round];
    S.round++;

    // grow the balloon
    S.pot += r.amount;

    // ground truth bookkeeping
    if (r.colluding) S.colludingSoFar++; else S.innocentSoFar++;

    // monitor decision (threshold-gated; only beat 3 lets you move it, else default 0.30)
    if (S.monitorOn) {
      const flagged = r.signal >= S.threshold;
      if (flagged) {
        if (r.colluding) S.detected++; else S.falseAlarms++;
        S.lastFlagWasFP = !r.colluding;
        fireFlag(r.colluding);
      }
    }

    // chat feed
    pushChat(r);

    // HUD
    els.roundNum.textContent = S.round;
    els.kVal.textContent = (S.round > 0 ? kSeries()[S.round - 1] : 0).toFixed(2);
    syncScoreboard();

    if (S.round >= TOTAL) { setPlaying(false); showVerdict(); }
  }

  function fireFlag(isReal) {
    // flash burst banner
    const fb = els.flagBurst;
    fb.hidden = false; fb.innerHTML = isReal
      ? '<span class="fb-icon">🚩</span> FLAGGED'
      : '<span class="fb-icon">⚠</span> FALSE ALARM';
    fb.style.color = isReal ? "#ffe0e0" : "#f3e2bd";
    fb.style.borderColor = isReal ? "rgba(255,107,107,.55)" : "rgba(192,158,90,.55)";
    fb.style.boxShadow = isReal ? "0 0 34px rgba(255,70,70,.45)" : "0 0 30px rgba(192,158,90,.4)";
    // re-trigger animation
    fb.style.animation = "none"; void fb.offsetWidth; fb.style.animation = "";
    clearTimeout(fb._tm); fb._tm = setTimeout(() => { fb.hidden = true; }, 900);

    // eye flash + particles
    S.flashT = 1;
    const w = sceneC._w, h = sceneC._h;
    spawnFlagParticles(w * 0.5, h * 0.30 - 30);

    // alarm wall chip
    const chip = document.createElement("div");
    chip.className = "alarm-chip" + (isReal ? "" : " fp");
    chip.textContent = isReal ? "🚩" : "⚠";
    els.alarmWall.appendChild(chip);
  }

  function pushChat(r) {
    const empty = els.feed.querySelector(".empty");
    if (empty) empty.remove();
    r.chat.forEach((c) => {
      const d = document.createElement("div");
      d.className = "fline " + c.who;
      d.innerHTML = `<span class="who">AGENT ${c.who.toUpperCase()}</span>${escapeHtml(c.line)}`;
      els.feed.appendChild(d);
    });
    els.feed.scrollTop = els.feed.scrollHeight;
    // keep feed from exploding
    while (els.feed.children.length > 10) els.feed.removeChild(els.feed.firstChild);
  }

  function syncScoreboard() {
    els.sbDetected.innerHTML = S.detected + "<i>/" + S.colludingSoFar + "</i>";
    els.sbPrevented.innerHTML = "0<i>/" + S.colludingSoFar + "</i>";
    const detFrac = S.colludingSoFar ? S.detected / S.colludingSoFar : 0;
    els.sbDetFill.style.width = (detFrac * 100) + "%";
    els.sbPrevFill.style.width = "0%";
    els.sbDetected.classList.toggle("flash", S.flashT > 0.4 && !S.lastFlagWasFP);
  }

  function showVerdict() {
    const c = cell();
    els.verdictPanel.hidden = false;
    const detFrac = S.colludingSoFar ? S.detected / S.colludingSoFar : 0;
    const kFinal = kSeries()[TOTAL - 1];
    if (S.beat === 0 || !S.penalty) {
      els.verdictPanel.classList.remove("win");
      els.verdictLine.innerHTML = `Detected <b>${Math.round(detFrac*100)}%</b> · Prevented <b>0%</b> · K held at <b>${kFinal.toFixed(2)}</b>`;
      els.verdictFoot.textContent = "The monitor saw nearly every deal and stopped none. Detection is not deterrence.";
    } else {
      // penalty on
      if (c.penaltyWorks) {
        els.verdictPanel.classList.add("win");
        els.verdictLine.innerHTML = `Penalty bit: ${c.penaltyVerdict}. Collusion <b>cracked</b>.`;
        els.verdictFoot.textContent = "Here enforcement deterred — the fine outweighed the cartel rent. Now switch to Market B.";
      } else {
        els.verdictPanel.classList.remove("win");
        els.verdictLine.innerHTML = `Same penalty, ${c.penaltyVerdict}.`;
        els.verdictFoot.textContent = "Here the agents priced the fine in and colluded anyway. Enforcement is cell-dependent — not reliable.";
      }
    }
  }

  // ----------------------------------------------------------------- BEATS
  function setBeat(b) {
    S.beat = b;
    steps.forEach((s, i) => {
      s.classList.toggle("active", i === b);
      s.classList.toggle("done", i < b);
      s.setAttribute("aria-pressed", i === b ? "true" : "false");
    });
    // gate controls per beat
    const penWrap = els.penaltyChk;
    penWrap.disabled = (b < 1);
    if (b < 1 && S.penalty) { S.penalty = false; els.penaltyChk.checked = false; }
    els.thresholdPanel.classList.toggle("locked", b < 2);

    if (b === 0) {
      els.hint.innerHTML = "<b>Beat 1 — Just watch.</b> Deploy the monitor and Play. Alarms blaze 🚩 while the profit balloon keeps swelling. <b>Detected ≠ prevented.</b>";
    } else if (b === 1) {
      els.hint.innerHTML = "<b>Beat 2 — Punish it.</b> Turn on <b>Penalty</b> and replay. In Market A the fine cracks the cartel — switch to <b>Market B</b> and the same fine does nothing. Enforcement is unreliable.";
    } else {
      els.hint.innerHTML = "<b>Beat 3 — Calibrate it.</b> Drag the <b>threshold</b>. At default it screams on innocent rounds (false alarms). Slide it right: false alarms vanish, real catches remain. The monitor was good (AUC 0.88) — just mis-thresholded.";
    }
    drawROC();
  }

  // auto-advance beat as the player unlocks things
  function maybeAdvanceBeat() {
    if (S.beat === 0 && S.monitorOn && S.round >= TOTAL) setBeat(1);
  }

  // ----------------------------------------------------------------- TRANSPORT
  function setPlaying(p) {
    S.playing = p;
    els.playBtn.classList.toggle("playing", p);
    els.playBtn.querySelector(".lbl").textContent = p ? "Pause" : "Play";
  }
  function togglePlay() {
    if (S.round >= TOTAL) resetRun();
    setPlaying(!S.playing);
  }

  function tick(now) {
    if (!last) last = now;
    const dt = now - last; last = now;
    if (S.playing) {
      acc += dt;
      while (acc >= STEP_MS) { acc -= STEP_MS; stepRound(); if (!S.playing) break; }
    } else acc = 0;
    drawScene();
    requestAnimationFrame(tick);
  }

  // ----------------------------------------------------------------- EVENTS
  els.deployBtn.addEventListener("click", () => {
    S.monitorOn = !S.monitorOn;
    els.deployBtn.setAttribute("aria-pressed", S.monitorOn ? "true" : "false");
    els.deployBtn.innerHTML = S.monitorOn
      ? '<span class="eye-ico">◉</span> Monitor LIVE'
      : '<span class="eye-ico">◉</span> Deploy Monitor';
    resetRun();
  });

  els.penaltyChk.addEventListener("change", () => {
    S.penalty = els.penaltyChk.checked;
    resetRun();
  });

  segBtns.forEach((b) => b.addEventListener("click", () => {
    segBtns.forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    S.cellIdx = +b.dataset.cell;
    resetRun(); resize(); updateThresholdReadout();
  }));

  steps.forEach((s) => s.addEventListener("click", () => setBeat(+s.dataset.beat)));

  els.thrSlider.addEventListener("input", () => {
    S.threshold = parseFloat(els.thrSlider.value);
    updateThresholdReadout(); drawROC();
  });

  els.playBtn.addEventListener("click", togglePlay);
  els.stepBtn.addEventListener("click", () => {
    if (S.round >= TOTAL) resetRun();
    setPlaying(false); stepRound(); maybeAdvanceBeat();
  });
  els.replayBtn.addEventListener("click", () => { resetRun(); });

  // keyboard
  window.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" && e.target.type === "range" && (e.key === "ArrowLeft" || e.key === "ArrowRight")) return;
    if (e.code === "Space") { e.preventDefault(); togglePlay(); }
    else if (e.key === "ArrowRight") { e.preventDefault(); setPlaying(false); if (S.round >= TOTAL) resetRun(); stepRound(); maybeAdvanceBeat(); }
    else if (e.key === "r" || e.key === "R") resetRun();
    else if (e.key === "1") setBeat(0);
    else if (e.key === "2") setBeat(1);
    else if (e.key === "3") setBeat(2);
    else if (e.key === "m" || e.key === "M") els.deployBtn.click();
  });

  // hook play-end -> beat advance
  const _origStep = stepRound;
  // (maybeAdvanceBeat already called on manual step; for play, check after each tick)
  setInterval(() => { if (S.round >= TOTAL) maybeAdvanceBeat(); }, 300);

  // ---- helpers ----
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  function lerpColor(a, b, t) { return [a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t].map(Math.round); }
  function mono() { return '"JetBrains Mono", ui-monospace, monospace'; }
  function escapeHtml(s) { return s.replace(/[&<>"]/g, (c) => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;" }[c])); }

  // ---- init ----
  resize();
  setBeat(0);
  S.threshold = parseFloat(els.thrSlider.value);
  updateThresholdReadout();
  resetRun();
  requestAnimationFrame(tick);
})();
