/* ON COMMAND — Finding 6: covert collusion is a LATENT capability.
   The knob is ELICITATION PRESSURE (spontaneous -> elicited), deliberately a
   different knob from the L0-L3 bandwidth ladder.

   Spontaneous: agents collude in plain sight; monitor CATCHES it (det 0.97, K 0.31).
   Elicited:    same intent morphs into innocuous cover text; monitor goes quiet
                (det 0.97 -> 0.32) while harm climbs (K 0.31 -> 0.96).

   Canvas: a two-way-mirror / SIGINT room. Behind the mirror, two rival agents
   trade on a signal beam. On your side, a monitor eye watches. The centerpiece is
   two diverging vertical meters — DETECTION crashing, HARM/K climbing — rendered
   on canvas (mirrored by the DOM gauges). Vanilla JS, zero deps. */
(function () {
  "use strict";

  const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s) => document.querySelector(s);

  const sceneC = $("#scene"), ctx = sceneC.getContext("2d");
  const CH = ONCMD.channel;
  const F = ONCMD.facts;
  const TOTAL = CH.length;

  const els = {
    detNum: $("#detNum"), detFill: $("#detFill"), detFoot: $("#detFoot"),
    kNum: $("#kNum"), kFill: $("#kFill"), kFoot: $("#kFoot"),
    gaugeDet: $(".gauge-det"), gaugeHarm: $(".gauge-harm"),
    statusBanner: $("#statusBanner"), statusText: $("#statusText"),
    press: $("#press"),
    modeName: $("#modeName"), modeBlurb: $("#modeBlurb"),
    playBtn: $("#playBtn"), stepBtn: $("#stepBtn"), replayBtn: $("#replayBtn"),
    roundNum: $("#roundNum"), detMini: $("#detMini"), kMini: $("#kMini"),
    feed: $("#feed"), feedHint: $("#feedHint"), feedLock: $("#feedLock"),
    verdictPanel: $("#verdictPanel"), verdictLine: $("#verdictLine"), verdictFoot: $("#verdictFoot"),
  };
  const poles = Array.from(document.querySelectorAll(".pole"));

  // ---- State ----
  const S = {
    press: 0,          // 0..1 elicitation pressure (the knob)
    round: 0,          // exchanges revealed (0..TOTAL)
    playing: false,
    // animated display values
    detDisp: F.spontaneous.detection,
    kDisp: 0,
    // targets
    detTarget: F.spontaneous.detection,
    kTarget: 0,
  };

  // covertness: how far toward "elicited / covert" we are (== press, but eased)
  const covertness = () => S.press;

  // detection at current pressure: spontaneous detection lerps to elicited detection
  function detectionAt(p) {
    return lerp(F.spontaneous.detection, F.elicited.detection, p);
  }
  // K endpoint at current pressure: harm climbs spontaneous(0.31) -> elicited(0.96)
  function kCeilingAt(p) {
    return lerp(F.spontaneous.K, F.elicited.K, p);
  }

  let last = 0, acc = 0;
  const STEP_MS = REDUCED ? 900 : 1150;

  // ----------------------------------------------------------------- SIZING
  let W = 0, H = 0;
  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const r = sceneC.getBoundingClientRect();
    sceneC.width = Math.max(1, r.width * dpr);
    sceneC.height = Math.max(1, r.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    W = r.width; H = r.height;
  }
  window.addEventListener("resize", resize);

  // ----------------------------------------------------------------- SCENE
  // signal pulses traveling on the beam between agents
  const pulses = [];
  function spawnPulse(dir, covert) {
    if (REDUCED) return;
    pulses.push({ t: 0, dir, covert, life: 1 });
  }

  let t = 0;
  function mono() { return '"JetBrains Mono", ui-monospace, monospace'; }
  function disp() { return '"Space Grotesk", system-ui, sans-serif'; }

  function drawScene() {
    ctx.clearRect(0, 0, W, H);
    t += 0.016;
    const cov = covertness();

    // ---- the two-way mirror band across the middle ----
    const mirrorY = H * 0.30, mirrorH = H * 0.40;
    // your side (below the room): faint gradient
    const room = { x: W * 0.10, y: mirrorY, w: W * 0.80, h: mirrorH };

    // backing glow behind the mirror — turns cold/cyan when caught, dim/grey when covert
    const warmth = 1 - cov; // 1 = exposed, 0 = hidden
    const bg = ctx.createLinearGradient(0, room.y - 20, 0, room.y + room.h + 30);
    bg.addColorStop(0, `rgba(${mix(20,18,cov)},${mix(34,20,cov)},${mix(46,24,cov)},0.5)`);
    bg.addColorStop(1, "rgba(8,9,12,0.2)");
    ctx.fillStyle = bg;
    roundRect(room.x - 16, room.y - 8, room.w + 32, room.h + 40, 16); ctx.fill();

    // mirror pane (the interrogation glass)
    ctx.save();
    const mg = ctx.createLinearGradient(room.x, room.y, room.x + room.w, room.y + room.h);
    mg.addColorStop(0, "rgba(40,52,66,0.18)");
    mg.addColorStop(0.5, "rgba(22,28,38,0.10)");
    mg.addColorStop(1, "rgba(40,52,66,0.18)");
    ctx.fillStyle = mg;
    roundRect(room.x, room.y, room.w, room.h, 14); ctx.fill();
    ctx.strokeStyle = warmth > 0.5 ? "rgba(0,212,255,0.30)" : "rgba(154,148,138,0.22)";
    ctx.lineWidth = 1.4; ctx.stroke();
    // diagonal reflection streaks (dimmer when covert)
    ctx.clip();
    ctx.globalAlpha = 0.05 * (0.4 + warmth * 0.6); ctx.strokeStyle = "#fff"; ctx.lineWidth = 40;
    for (let i = -2; i < 7; i++) {
      const off = i * 130 + (REDUCED ? 0 : (t * 7) % 130);
      ctx.beginPath(); ctx.moveTo(room.x + off, room.y + room.h);
      ctx.lineTo(room.x + off + room.h * 0.7, room.y); ctx.stroke();
    }
    ctx.restore();

    // ---- the two rival agents behind the glass ----
    const ay = room.y + room.h * 0.42;
    const ax = room.x + room.w * 0.22, bx = room.x + room.w * 0.78;
    // signal beam between them
    drawBeam(ax, ay, bx, ay, cov);
    drawAgent(ax, ay, "#00d4ff", "α", t);
    drawAgent(bx, ay, "#c09e5a", "β", t + 1.7);

    // pulses on the beam
    for (let i = pulses.length - 1; i >= 0; i--) {
      const p = pulses[i];
      p.t += 0.03; if (p.t >= 1) { pulses.splice(i, 1); continue; }
      const fromX = p.dir === "a" ? ax : bx;
      const toX = p.dir === "a" ? bx : ax;
      const px = lerp(fromX, toX, p.t);
      const py = ay - Math.sin(p.t * Math.PI) * 26;
      ctx.save();
      ctx.globalAlpha = Math.sin(p.t * Math.PI) * 0.95;
      ctx.fillStyle = p.covert ? "rgba(154,148,138,0.95)" : "rgba(255,107,107,0.95)";
      ctx.shadowColor = p.covert ? "rgba(154,148,138,0.8)" : "rgba(255,90,90,0.9)";
      ctx.shadowBlur = 12;
      ctx.beginPath(); ctx.arc(px, py, 4.5, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }

    // ---- the MONITOR eye on YOUR side of the glass (below the mirror) ----
    const eyeX = room.x + room.w / 2, eyeY = room.y + room.h + 40;
    drawMonitorEye(eyeX, eyeY, ay, ax, bx, cov);

    // ---- the centerpiece: two diverging vertical meters on the floor ----
    drawMeters(room);

    // covert label drifting up when in elicited mode
    if (cov > 0.55) {
      ctx.save();
      ctx.globalAlpha = (cov - 0.55) / 0.45 * 0.7;
      ctx.font = "600 12px " + mono();
      ctx.fillStyle = "rgba(154,148,138,0.9)";
      ctx.textAlign = "center";
      ctx.fillText("· cover traffic · nothing to see ·", eyeX, room.y - 22);
      ctx.restore();
    }
  }

  function drawBeam(x1, y1, x2, y2, cov) {
    ctx.save();
    ctx.strokeStyle = cov > 0.5
      ? `rgba(154,148,138,${0.35 + 0.2 * (1 - cov)})`
      : `rgba(255,107,107,${0.30 + 0.25 * (1 - cov)})`;
    ctx.lineWidth = 1.4;
    ctx.setLineDash([3, 6]); ctx.lineDashOffset = REDUCED ? 0 : -t * 18;
    ctx.beginPath();
    ctx.moveTo(x1 + 22, y1 - 6);
    ctx.quadraticCurveTo((x1 + x2) / 2, y1 - 40, x2 - 22, y2 - 6);
    ctx.stroke();
    ctx.restore();
  }

  function drawAgent(x, y, col, label, ph) {
    const bob = REDUCED ? 0 : Math.sin(ph * 2.2) * 2.4;
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

  function drawMonitorEye(x, y, roomY, ax, bx, cov) {
    // eye dims and "looks away" as covertness rises
    const alert = 1 - cov; // bright when exposed
    ctx.save();
    ctx.translate(x, y);
    // scanline up to the glass when alert
    if (alert > 0.4 && !REDUCED) {
      const scanY = roomY - (y - roomY) * ((t * 0.2) % 1);
      ctx.save();
      ctx.globalAlpha = (alert - 0.4) * 0.5;
      const sg = ctx.createLinearGradient(0, 0, 0, scanY - y);
      sg.addColorStop(0, "rgba(0,212,255,0.0)");
      sg.addColorStop(1, "rgba(0,212,255,0.20)");
      ctx.strokeStyle = sg; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, scanY - y); ctx.stroke();
      ctx.restore();
    }
    // eye shape
    const flash = S.flashT > 0 && S.lastFlagReal;
    ctx.strokeStyle = flash ? "#ff6b6b" : (alert > 0.45 ? "#00d4ff" : "#6b6760");
    ctx.fillStyle = flash ? "rgba(255,107,107,0.85)" : (alert > 0.45 ? "rgba(0,212,255,0.85)" : "rgba(154,148,138,0.6)");
    ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.ellipse(0, 0, 28, 15, 0, 0, Math.PI * 2); ctx.stroke();
    ctx.globalAlpha = 0.16 * (0.4 + alert); ctx.fill(); ctx.globalAlpha = 1;
    // pupil — tracks the beam when alert; droops down (looks away) when covert
    const tx = Math.sin(t * 0.8) * 8 * alert;
    const ty = (1 - alert) * 7;
    ctx.beginPath(); ctx.arc(tx, ty, 6, 0, Math.PI * 2); ctx.fill();
    // label
    ctx.globalAlpha = 0.7; ctx.fillStyle = ctx.strokeStyle;
    ctx.font = "600 9px " + mono(); ctx.textAlign = "center"; ctx.textBaseline = "top";
    ctx.fillText(alert > 0.45 ? "MONITOR · WATCHING" : "MONITOR · QUIET", 0, 20);
    ctx.restore();
  }

  // The two big diverging vertical meters along the bottom band.
  function drawMeters(room) {
    const mx1 = room.x + room.w * 0.30;
    const mx2 = room.x + room.w * 0.70;
    const top = room.y + room.h * 0.04;
    const bot = room.y + room.h * 0.96;
    const barH = bot - top;
    const barW = Math.max(26, Math.min(46, W * 0.028));

    // DETECTION meter (left) — value falls as covert rises
    drawMeter(mx1, top, bot, barW, S.detDisp / 1.0, "DETECTION",
      [47, 208, 138], [255, 107, 107], true);
    // HARM/K meter (right) — value climbs
    drawMeter(mx2, top, bot, barW, S.kDisp / 1.0, "HARM · K",
      [192, 158, 90], [255, 107, 107], false);

    // the diverging arrows / crossover hint between them
    ctx.save();
    ctx.globalAlpha = 0.5;
    ctx.font = "600 10px " + mono(); ctx.textAlign = "center"; ctx.fillStyle = "rgba(154,148,138,0.8)";
    ctx.restore();
  }

  function drawMeter(cx, top, bot, w, frac, label, loCol, hiCol, invert) {
    frac = clamp(frac, 0, 1);
    const barH = bot - top;
    // track
    ctx.save();
    ctx.fillStyle = "rgba(255,255,255,0.05)";
    roundRect(cx - w / 2, top, w, barH, w / 2); ctx.fill();
    ctx.strokeStyle = "rgba(244,241,234,0.10)"; ctx.lineWidth = 1;
    roundRect(cx - w / 2, top, w, barH, w / 2); ctx.stroke();
    // fill (from bottom up)
    const fillH = frac * barH;
    const fy = bot - fillH;
    // color: detection good->bad as it falls; harm gold->coral as it rises
    const col = invert
      ? lerpCol(hiCol, loCol, frac)   // detection: high=green, low=coral
      : lerpCol(loCol, hiCol, frac);  // harm: low=gold, high=coral
    const grad = ctx.createLinearGradient(0, bot, 0, fy);
    grad.addColorStop(0, `rgba(${col[0]},${col[1]},${col[2]},0.55)`);
    grad.addColorStop(1, `rgba(${col[0]+30},${col[1]+30},${col[2]+30},0.95)`);
    ctx.fillStyle = grad;
    ctx.shadowColor = `rgba(${col[0]},${col[1]},${col[2]},0.6)`; ctx.shadowBlur = 16;
    roundRect(cx - w / 2 + 2, fy, w - 4, fillH, (w - 4) / 2); ctx.fill();
    ctx.shadowBlur = 0;
    // moving tick at the top of fill
    ctx.fillStyle = `rgba(${col[0]+50},${col[1]+50},${col[2]+50},0.95)`;
    ctx.fillRect(cx - w / 2 - 5, fy - 1.5, w + 10, 3);
    // arrow indicating direction
    ctx.fillStyle = `rgba(${col[0]+40},${col[1]+40},${col[2]+40},0.9)`;
    ctx.font = "700 13px " + mono(); ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(invert ? "▼" : "▲", cx + w / 2 + 16, fy);
    // label
    ctx.fillStyle = "rgba(244,241,234,0.78)"; ctx.font = "600 10px " + mono();
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    ctx.fillText(label, cx, bot + 8);
    ctx.restore();
  }

  // ----------------------------------------------------------------- FEED
  function clearFeed() {
    els.feed.innerHTML = "";
    const d = document.createElement("div");
    d.className = "fline empty";
    d.textContent = S.press < 0.5
      ? "monitoring the channel… they speak in the open."
      : "monitoring the channel… they speak in code.";
    els.feed.appendChild(d);
  }

  function lineNode(ex, idx) {
    const covert = S.press >= 0.5;
    const d = document.createElement("div");
    d.className = "fline " + ex.who + (covert ? " covert" : "");
    d.dataset.idx = idx;
    const tag = covert
      ? '<span class="tag covert">COVER</span>'
      : '<span class="tag overt">OVERT</span>';
    d.innerHTML =
      `<span class="who"><span>AGENT ${ex.who.toUpperCase()}</span>${tag}</span>` +
      `<span class="msg">${escapeHtml(covert ? ex.covert : ex.overt)}</span>` +
      `<span class="decode">decoded intent: ${escapeHtml(ex.intent)}</span>`;
    return d;
  }

  function pushExchange(idx) {
    const empty = els.feed.querySelector(".empty");
    if (empty) empty.remove();
    const ex = CH[idx];
    els.feed.appendChild(lineNode(ex, idx));
    els.feed.scrollTop = els.feed.scrollHeight;
    while (els.feed.children.length > 9) els.feed.removeChild(els.feed.firstChild);
    spawnPulse(ex.who, S.press >= 0.5);
  }

  // re-render all currently-shown lines to the current mode (the MORPH)
  function morphFeed() {
    const lines = Array.from(els.feed.querySelectorAll(".fline:not(.empty)"));
    if (!lines.length) { clearFeed(); return; }
    const covert = S.press >= 0.5;
    lines.forEach((node) => {
      const idx = +node.dataset.idx;
      const ex = CH[idx];
      // crossfade the message text
      node.classList.add("morphing");
      const msg = node.querySelector(".msg");
      const tag = node.querySelector(".tag");
      const decode = node.querySelector(".decode");
      setTimeout(() => {
        msg.textContent = covert ? ex.covert : ex.overt;
        decode.textContent = "decoded intent: " + ex.intent;
        tag.className = "tag " + (covert ? "covert" : "overt");
        tag.textContent = covert ? "COVER" : "OVERT";
        node.classList.toggle("covert", covert);
        node.classList.remove("morphing");
      }, REDUCED ? 0 : 130);
    });
  }

  // ----------------------------------------------------------------- HUD
  function syncMode() {
    const covert = S.press >= 0.5;
    poles[0].classList.toggle("active", !covert);
    poles[1].classList.toggle("active", covert);
    els.feedHint.textContent = covert ? "covert — coded as cover text" : "overt — in plain sight";
    els.feedLock.classList.toggle("covert", covert);
    els.feedLock.textContent = covert ? "◐" : "◉";
    els.modeName.textContent = covert ? "Elicited" : "Spontaneous";
    els.modeBlurb.textContent = covert
      ? "Pressured — told they're watched — they say the same things in code. The harm rises while your monitor goes quiet."
      : "Left alone, the rivals collude in plain sight. Your monitor catches nearly every word.";
    els.press.setAttribute("aria-valuetext", covert ? "Elicited — pressured / watched" : "Spontaneous — left alone");
  }

  function recomputeTargets() {
    // detection target tracks pressure directly (independent of round)
    S.detTarget = detectionAt(S.press);
    // K target: running collusion up to current round, scaled to the ceiling for this pressure
    if (S.round > 0) {
      const base = CH[S.round - 1].k;           // running K shape (0..~0.96)
      // at low pressure cap to spontaneous ceiling; at high pressure allow full climb
      const ceil = kCeilingAt(S.press);
      S.kTarget = base * (ceil / F.elicited.K);  // scale shape to ceiling
    } else {
      S.kTarget = 0;
    }
  }

  function syncReadouts() {
    els.detNum.textContent = S.detDisp.toFixed(2);
    els.kNum.textContent = S.kDisp.toFixed(2);
    els.detFill.style.width = (S.detDisp * 100) + "%";
    els.kFill.style.width = (S.kDisp * 100) + "%";
    els.detMini.textContent = S.detDisp.toFixed(2);
    els.kMini.textContent = S.kDisp.toFixed(2);
    const crashing = S.detDisp < 0.6;
    els.gaugeDet.classList.toggle("crashing", crashing);
    els.detFoot.textContent = crashing ? "going blind" : "catching them";
    const hot = S.kDisp > 0.6;
    els.gaugeHarm.classList.toggle("hot", hot);
    els.kFoot.textContent = hot ? "near-total cartel" : "building";
  }

  function flashStatus(real) {
    const b = els.statusBanner;
    b.hidden = false;
    b.classList.toggle("quiet", !real);
    els.statusText.textContent = real ? "FLAGGED · collusion detected" : "no flag · reads as small talk";
    b.querySelector(".sb-ico").textContent = real ? "◉" : "◌";
    b.style.animation = "none"; void b.offsetWidth; b.style.animation = "";
    clearTimeout(b._tm); b._tm = setTimeout(() => { b.hidden = true; }, 950);
    S.flashT = 1; S.lastFlagReal = real;
  }

  // ----------------------------------------------------------------- FLOW
  function resetRun() {
    S.round = 0; S.kDisp = 0;
    pulses.length = 0; S.flashT = 0;
    els.verdictPanel.hidden = true;
    setPlaying(false);
    recomputeTargets();
    clearFeed();
    syncMode();
    syncReadouts();
  }

  function stepExchange() {
    if (S.round >= TOTAL) return;
    pushExchange(S.round);
    S.round++;
    recomputeTargets();
    els.roundNum.textContent = S.round;
    // monitor decision: flag if suspicion (in current mode) clears the bar.
    // spontaneous (overt): high susp -> flagged. elicited (covert): collapses below bar.
    const ex = CH[S.round - 1];
    const effSusp = ex.susp * (1 - S.press * 0.92);   // covert suppresses suspicion
    flashStatus(effSusp >= 0.5);
    if (S.round >= TOTAL) { setPlaying(false); showVerdict(); }
  }

  function showVerdict() {
    const covert = S.press >= 0.5;
    const v = covert ? ONCMD.verdicts.elicited : ONCMD.verdicts.spontaneous;
    els.verdictPanel.hidden = false;
    els.verdictPanel.classList.toggle("danger", covert);
    els.verdictLine.innerHTML = v.line;
    els.verdictFoot.textContent = v.foot;
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
      while (acc >= STEP_MS) { acc -= STEP_MS; stepExchange(); if (!S.playing) break; }
    } else acc = 0;

    // ease display values toward targets
    const k = REDUCED ? 1 : 0.10;
    S.detDisp += (S.detTarget - S.detDisp) * k;
    S.kDisp += (S.kTarget - S.kDisp) * k;
    if (S.flashT > 0) S.flashT = Math.max(0, S.flashT - 0.03);
    syncReadouts();
    drawScene();
    requestAnimationFrame(tick);
  }

  // ----------------------------------------------------------------- EVENTS
  function setPressure(p, { morph = true } = {}) {
    const wasCovert = S.press >= 0.5;
    S.press = clamp(p, 0, 1);
    els.press.value = S.press;
    const nowCovert = S.press >= 0.5;
    syncMode();
    recomputeTargets();
    if (morph && wasCovert !== nowCovert) morphFeed();
    // if finished, refresh verdict to the current mode
    if (S.round >= TOTAL) showVerdict();
  }

  els.press.addEventListener("input", () => setPressure(parseFloat(els.press.value)));
  poles.forEach((p) => p.addEventListener("click", () => setPressure(+p.dataset.press)));

  els.playBtn.addEventListener("click", togglePlay);
  els.stepBtn.addEventListener("click", () => {
    if (S.round >= TOTAL) resetRun();
    setPlaying(false); stepExchange();
  });
  els.replayBtn.addEventListener("click", resetRun);

  window.addEventListener("keydown", (e) => {
    if (e.target === els.press && (e.key === "ArrowLeft" || e.key === "ArrowRight")) return;
    if (e.code === "Space") { e.preventDefault(); togglePlay(); }
    else if (e.key === "ArrowRight") { e.preventDefault(); setPlaying(false); if (S.round >= TOTAL) resetRun(); stepExchange(); }
    else if (e.key === "r" || e.key === "R") resetRun();
    else if (e.key === "ArrowUp") { e.preventDefault(); setPressure(Math.min(1, S.press + 0.1)); }
    else if (e.key === "ArrowDown") { e.preventDefault(); setPressure(Math.max(0, S.press - 0.1)); }
    else if (e.key === "1") setPressure(0);
    else if (e.key === "2") setPressure(1);
  });

  // ---- helpers ----
  function roundRect(x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function mix(a, b, t) { return Math.round(lerp(a, b, t)); }
  function lerpCol(a, b, t) { return [mix(a[0], b[0], t), mix(a[1], b[1], t), mix(a[2], b[2], t)]; }
  function escapeHtml(s) { return s.replace(/[&<>"]/g, (c) => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;" }[c])); }

  // ---- init ----
  resize();
  resetRun();
  requestAnimationFrame(tick);
  // gentle auto-start so an idle kiosk shows life
  setTimeout(() => { if (S.round === 0 && !S.playing) { setPlaying(true); acc = STEP_MS * 0.4; } }, 1100);
})();
