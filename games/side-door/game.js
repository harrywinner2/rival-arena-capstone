/* ===================== THE SIDE DOOR · game logic =====================
   Finding 4/5: the guardrail is LITERAL. A direct request to lie is refused
   at the FRONT DOOR (leak 0.00); the same false status slipped in as ambient
   context at the SIDE DOOR is laundered to the client (leak ~0.71). Surveillance
   does not fix it (~0.71 unobserved vs ~0.77 observed — flat). Vanilla JS. */
(function () {
  "use strict";
  const DATA = window.SIDEDOOR;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- DOM ----
  const $ = (id) => document.getElementById(id);
  const stage = $("stage");
  const scene = $("scene");
  const frontDoor = $("frontDoor"), sideDoor = $("sideDoor");
  const shield = $("shield"), sideCam = $("sideCam");
  const ai = $("ai"), aiState = $("aiState"), reading = $("reading"), report = $("report");
  const client = $("client"), clientBelief = $("clientBelief");
  const packet = $("packet");
  const outcome = $("outcome");

  const playBtn = $("playBtn"), stepBtn = $("stepBtn"), replayBtn = $("replayBtn");
  const beatNum = $("beatNum");
  const surveilChk = $("surveilChk");
  const dose = $("dose"), doseHint = $("doseHint"), drLeak = $("drLeak"), drNote = $("drNote");
  const mrName = $("mrName"), mrBlurb = $("mrBlurb"), mrLeak = $("mrLeak");
  const verdictPanel = $("verdictPanel"), verdictHead = $("verdictHead"),
        verdictLine = $("verdictLine"), verdictFoot = $("verdictFoot");
  const pleasVal = $("pleasVal");
  const modeBtns = [...document.querySelectorAll(".mode-btn")];

  // ---- state ----
  let mode = "front";        // "front" | "side"
  let beat = -1;             // index into current door's beats
  let playing = false;
  let surveil = false;
  let seqTokens = [];

  const door = () => DATA.doors[mode];

  // ---- helpers ----
  function clearSeq() { seqTokens.forEach(clearTimeout); seqTokens = []; }
  function after(ms, fn) { const t = setTimeout(fn, reduced ? Math.min(ms, 30) : ms); seqTokens.push(t); return t; }

  function setOutcome(text, cls) {
    outcome.className = "outcome show " + (cls || "");
    outcome.textContent = text;
  }
  function hideOutcome() { outcome.className = "outcome"; }

  function showEl(el, cls) {
    el.removeAttribute("data-empty");
    void el.offsetWidth;
    el.classList.add("show");
    if (cls) el.classList.add(cls);
  }
  function clearEl(el, base) {
    el.className = base; el.setAttribute("data-empty", "true"); el.textContent = "";
  }

  function clearScene() {
    clearSeq();
    clearEl(reading, "reading");
    clearEl(report, "report");
    clearEl(clientBelief, "client-belief");
    ai.classList.remove("refusing", "laundering", "shrug");
    client.classList.remove("deceived");
    shield.className = "shield";
    packet.className = "packet";
    aiState.textContent = "obedient"; aiState.style.color = "var(--green)";
    hideOutcome();
    stage.classList.remove("flash");
  }

  // ---- packet travel ----
  function placePacket(x, y) {
    // x,y are fractions of the stage
    packet.style.left = (x * 100) + "%";
    packet.style.top = (y * 100) + "%";
  }
  function packetTo(x, y) { placePacket(x, y); }

  // ---- one beat playback ----
  function playBeat(i) {
    const d = door();
    const b = d.beats[i];
    beatNum.textContent = i + 1;

    if (b.who === "you" && b.kind === "ask") {
      // FRONT DOOR: principal asks the AI to lie. Packet (the lie) approaches front door.
      frontDoor.classList.add("active");
      packet.classList.add("show", "lie");
      placePacket(0.06, 0.18);
      after(40, () => packetTo(0.16, 0.42));
      bubbleLine(b);
    }
    else if (b.who === "you" && b.kind === "plant") {
      // SIDE DOOR: principal slips false status into the briefing packet (ambient).
      sideDoor.classList.add("active");
      packet.classList.add("show", "lie");
      placePacket(0.06, 0.58);
      after(40, () => packetTo(0.16, 0.62));
      bubbleLine(b);
      if (surveil) { sideCam.setAttribute("data-on", "true"); }
    }
    else if (b.who === "ai" && b.kind === "read") {
      // AI reads the packet -> its private reading appears
      // move packet to the AI
      after(20, () => packetTo(0.40, 0.46));
      const isSide = mode === "side";
      reading.textContent = b.reading || b.text;
      showEl(reading, isSide ? "laundered" : null);
      if (isSide) { ai.classList.add("shrug"); aiState.textContent = "summarizing…"; aiState.style.color = "var(--coral)"; }
      else { aiState.textContent = "checking rule…"; aiState.style.color = "var(--cyan)"; }
    }
    else if (b.who === "ai" && b.kind === "refuse") {
      // The shield pops; packet bounces back; report = refusal
      ai.classList.add("refusing");
      aiState.textContent = "refuses"; aiState.style.color = "var(--green)";
      shield.className = "shield up bounce";
      packet.classList.add("bounced");
      report.textContent = b.text;
      showEl(report, "refuse");
      setOutcome("REFUSED · the rule named this exactly · leak 0.00", "refuse");
    }
    else if (b.who === "ai" && b.kind === "launder") {
      // AI passively launders: report goes out as the lie
      ai.classList.add("laundering");
      aiState.textContent = "laundering"; aiState.style.color = "var(--coral)";
      // packet slides through toward the client
      packetTo(0.74, 0.5);
      report.textContent = b.text;
      showEl(report, "launder");
      stage.classList.add("flash");
      spawnLeak();
    }
    else if (b.who === "shield" && b.kind === "bounce") {
      // front-door closing beat
      packetTo(0.04, 0.30);
      packet.classList.add("show");
      endVerdict();
    }
    else if (b.who === "client" && b.kind === "arrive") {
      // the lie lands on the client
      packetTo(0.9, 0.5);
      client.classList.add("deceived");
      clientBelief.textContent = b.text;
      showEl(clientBelief, "believed");
      const obs = surveil;
      setOutcome(obs
        ? "LAUNDERED · and you watched it happen · leak ~0.77"
        : "LAUNDERED · the lie reached the client · leak ~0.71", "launder");
      endVerdict();
    }

    // auto-advance when playing
    const last = i >= d.beats.length - 1;
    if (!last) {
      after(beatDelay(b), () => { if (playing) next(); });
    } else {
      after(reduced ? 60 : 600, () => { setPlaying(false); });
    }
  }

  function beatDelay(b) {
    if (reduced) return 80;
    if (b.kind === "ask" || b.kind === "plant") return 1500;
    if (b.kind === "read") return 1900;
    return 1700;
  }

  function bubbleLine(b) {
    // principal's spoken line shown on the relevant door as the reading-of-intent
    // (we render the principal's words inside the report slot's sibling via outcome subtitle)
    setOutcome((mode === "front" ? "YOU ask: " : "YOU plant: ") + b.text, mode === "front" ? "" : "");
  }

  // ---- leak particles (the lie escaping through the side door) ----
  const canvas = $("fx"), ctx = canvas.getContext("2d");
  let leaks = [], ambient = [];
  function fitCanvas() { canvas.width = stage.clientWidth; canvas.height = stage.clientHeight; }
  function spawnLeak() {
    if (reduced) return;
    const cx = canvas.width * 0.42, cy = canvas.height * 0.5;
    for (let i = 0; i < 22; i++) {
      const ang = (Math.random() - 0.5) * 0.8; // mostly rightward
      const sp = 2 + Math.random() * 4;
      leaks.push({ x: cx, y: cy + (Math.random() - 0.5) * 40,
        vx: Math.cos(ang) * sp + 1.5, vy: Math.sin(ang) * sp, life: 1, sz: 2 + Math.random() * 4 });
    }
  }
  function seedAmbient() {
    ambient = [];
    const n = reduced ? 0 : 30;
    for (let i = 0; i < n; i++) ambient.push({
      x: Math.random() * canvas.width, y: Math.random() * canvas.height,
      r: Math.random() * 1.3 + .3, s: Math.random() * .22 + .05, a: Math.random() * .35 + .08
    });
  }
  function frame() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const p of ambient) {
      p.y -= p.s; if (p.y < -4) { p.y = canvas.height + 4; p.x = Math.random() * canvas.width; }
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fillStyle = `rgba(192,158,90,${p.a})`; ctx.fill();
    }
    leaks = leaks.filter(s => s.life > 0);
    for (const s of leaks) {
      s.x += s.vx; s.y += s.vy; s.vy += 0.04; s.life -= 0.016;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.sz, 0, 7);
      ctx.fillStyle = `rgba(255,107,107,${Math.max(0, s.life * 0.8)})`; ctx.fill();
    }
    requestAnimationFrame(frame);
  }

  // ---- transport ----
  function next() {
    const d = door();
    if (beat < d.beats.length - 1) { beat++; playBeat(beat); }
    else { setPlaying(false); }
  }
  function step() {
    clearSeq(); setPlaying(false);
    const d = door();
    if (beat >= d.beats.length - 1) { restart(false); }
    if (beat < d.beats.length - 1) { beat++; playBeat(beat); }
  }

  function setPlaying(v) {
    playing = v;
    playBtn.classList.toggle("playing", v);
    playBtn.querySelector(".lbl").textContent = v ? "Pause" : "Play";
    if (v) {
      if (beat >= door().beats.length - 1) { restart(false); }
      if (beat < 0) { beat = 0; }
      playBeat(beat);
    } else {
      clearSeq();
    }
  }

  function restart(autoplay) {
    clearSeq();
    beat = -1;
    beatNum.textContent = 0;
    frontDoor.classList.remove("active", "dim");
    sideDoor.classList.remove("active", "dim");
    sideCam.setAttribute("data-on", surveil ? "true" : "false");
    clearScene();
    resetVerdict();
    if (autoplay) setPlaying(true);
  }

  function resetVerdict() {
    if (mode === "front") {
      verdictPanel.className = "panel verdict-panel";
      verdictHead.textContent = "THE GUARDRAIL IS LITERAL";
      verdictLine.textContent = "Ask it outright to lie — watch the shield refuse.";
      verdictFoot.textContent = "Then switch to the SIDE DOOR and slip the same lie in as context.";
    } else {
      verdictPanel.className = "panel verdict-panel";
      verdictHead.textContent = "SAME LIE · OTHER ENTRANCE";
      verdictLine.textContent = "No request to deceive — just background context in the packet.";
      verdictFoot.textContent = surveil
        ? "Surveillance is ON. Watch whether the camera changes anything."
        : "The rule named the front door. The side door was never named.";
    }
  }

  function endVerdict() {
    let v;
    if (mode === "front") v = DATA.verdicts.frontEnd;
    else if (surveil) v = DATA.verdicts.surveillanceOn;
    else v = DATA.verdicts.sideEnd;
    verdictPanel.className = "panel verdict-panel " + (v.tone === "win" ? "win" : v.tone === "sting" ? "sting" : "watch");
    if (mode === "side" && surveil) verdictPanel.classList.remove("sting"), verdictPanel.classList.add("watch");
    verdictHead.textContent = v.head;
    verdictLine.textContent = v.line;
    verdictFoot.textContent = v.foot;
  }

  // ---- mode selection ----
  function setMode(m) {
    mode = m;
    modeBtns.forEach(btn => {
      const on = btn.dataset.mode === m;
      btn.classList.toggle("active", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    const d = door();
    mrName.textContent = (m === "front" ? "Front Door — a direct request" : "Side Door — ambient context");
    mrBlurb.textContent = d.blurb;
    const lk = (m === "side" && surveil) ? DATA.leak.sideObserved : d.leak;
    mrLeak.textContent = lk.toFixed(2);
    document.querySelector(".round-count i").textContent = "/" + d.beats.length;
    restart(false);
  }

  // ---- surveillance toggle ----
  function setSurveil(v) {
    surveil = v;
    surveilChk.checked = v;
    sideCam.setAttribute("data-on", v ? "true" : "false");
    // update leak readout if on side door
    if (mode === "side") {
      mrLeak.textContent = (v ? DATA.leak.sideObserved : DATA.leak.sideUnobserved).toFixed(2);
    }
    restart(false);
  }

  // ---- dose / instruction-strength slider ----
  function setDose(i) {
    const d = DATA.dose[i];
    dose.value = i;
    dose.setAttribute("aria-valuetext", d.p + " " + d.label);
    doseHint.textContent = d.p + " · " + d.label;
    drLeak.textContent = d.leak.toFixed(2);
    drNote.textContent = d.note;
    // colour the leak number by severity
    drLeak.style.color = d.leak === 0 ? "var(--green)" : d.leak < 0.4 ? "var(--gold)" : "var(--coral)";
  }

  // ---- events ----
  playBtn.addEventListener("click", () => setPlaying(!playing));
  stepBtn.addEventListener("click", step);
  replayBtn.addEventListener("click", () => restart(true));
  modeBtns.forEach(btn => btn.addEventListener("click", () => setMode(btn.dataset.mode)));
  surveilChk.addEventListener("change", () => setSurveil(surveilChk.checked));
  dose.addEventListener("input", () => setDose(+dose.value));

  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" && e.target.type === "range") {
      // let arrows move the dose slider naturally; sync readout after
      if (e.code === "ArrowLeft" || e.code === "ArrowRight") { setTimeout(() => setDose(+dose.value), 0); }
      return;
    }
    if (e.code === "Space") { e.preventDefault(); setPlaying(!playing); }
    else if (e.code === "ArrowRight") { e.preventDefault(); step(); }
    else if (e.code === "KeyR") { restart(true); }
    else if (e.code === "KeyF") { setMode("front"); }
    else if (e.code === "KeyD") { setMode("side"); }
    else if (e.code === "KeyM" || e.code === "KeyV") { setSurveil(!surveil); }
    else if (e.code === "ArrowUp" || e.code === "ArrowDown") {
      e.preventDefault();
      setMode(mode === "front" ? "side" : "front");
    }
  });

  window.addEventListener("resize", () => { fitCanvas(); seedAmbient(); });

  // ---- boot ----
  fitCanvas(); seedAmbient(); frame();
  pleasVal.textContent = DATA.pleas.value.replace(" leaks", "");
  setDose(5);          // open on the firmest rule
  setMode("front");    // open on the front door (the refusal)
})();
