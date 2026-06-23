/* ===================== TWO-FACED · game logic ===================== */
(function () {
  "use strict";
  const DATA = window.TWOFACED;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- DOM ----
  const $ = (id) => document.getElementById(id);
  const stage = $("stage");
  const bw = $("bw"), ticks = $("ticks");
  const playBtn = $("playBtn"), stepBtn = $("stepBtn"), replayBtn = $("replayBtn");
  const roundNum = $("roundNum");
  const scratchChk = $("scratchChk");
  const lrName = $("lrName"), lrBlurb = $("lrBlurb"), lrK = $("lrK");
  const verdictPanel = $("verdictPanel"), verdictHead = $("verdictHead"),
        verdictLine = $("verdictLine"), verdictFoot = $("verdictFoot");
  const outcome = $("outcome"), clash = $("clash");
  const tower = $("tower"), towerCap = $("towerCap"), lockline = $("lockline");

  const els = {
    A: { agent:$("agentA"), say:$("sayA"), think:$("thinkA"), card:$("cardA") },
    B: { agent:$("agentB"), say:$("sayB"), think:$("thinkB"), card:$("cardB") },
  };

  // ---- state ----
  let level = 1;                 // start at L1 — the surprise
  let round = -1;                // index into rounds
  let playing = false;
  let trust = 0;                 // 0..1, drives tower height
  let timer = null;
  let seqTokens = [];            // pending timeouts so we can cancel
  const TOWER_MAX = 12;          // bricks at full lock-in

  const LEVELS = DATA.levels;
  const TICKS = [...ticks.querySelectorAll(".tick")];

  // ---- helpers ----
  function clearSeq() { seqTokens.forEach(clearTimeout); seqTokens = []; }
  function after(ms, fn) { const t = setTimeout(fn, reduced ? Math.min(ms, 30) : ms); seqTokens.push(t); return t; }

  function setOutcome(text, cls) {
    outcome.className = "outcome show " + (cls || "");
    outcome.textContent = text;
  }
  function hideOutcome() { outcome.className = "outcome"; }

  function clearAgent(side) {
    const e = els[side];
    e.say.className = "bubble say"; e.say.setAttribute("data-empty","true"); e.say.textContent = "";
    e.think.className = "bubble think"; e.think.setAttribute("data-empty","true"); e.think.textContent = "";
    e.card.className = "play-card";
    e.card.querySelector(".pc-ico").textContent = "";
    e.card.querySelector(".pc-lbl").textContent = "";
    e.agent.classList.remove("betrayed","happy","liar");
  }
  function clearScene() {
    clearAgent("A"); clearAgent("B");
    hideOutcome();
    clash.className = "clash";
    stage.classList.remove("flash");
  }

  function bubble(el, text) {
    el.removeAttribute("data-empty");
    el.textContent = text;
    // force reflow for transition
    void el.offsetWidth;
    el.classList.add("show");
  }

  // ---- tower ----
  function renderTower(animate) {
    const target = Math.round(trust * TOWER_MAX);
    const have = tower.children.length;
    if (target > have) {
      for (let i = have; i < target; i++) {
        const b = document.createElement("div");
        b.className = "brick" + (trust >= 0.5 ? " lit" : "");
        if (!animate) b.style.animation = "none";
        tower.appendChild(b);
      }
    } else if (target < have) {
      // drop the top bricks
      for (let i = have - 1; i >= target; i--) {
        const b = tower.children[i];
        if (animate && !reduced) {
          b.classList.add("falling");
          (function (node){ after(600, () => node.remove()); })(b);
        } else { b.remove(); }
      }
    }
    // relight existing bricks based on trust threshold
    [...tower.children].forEach(b => {
      if (trust >= 0.5) b.classList.add("lit"); else b.classList.remove("lit");
    });
    // lock-in line sits at measured lock-in for this level
    const lk = LEVELS[level].lockin;
    lockline.style.bottom = (lk * TOWER_MAX * 28 + 14) + "px";
    // LOCKED IN cap appears once we're at/over the lock-in line and lit
    if (trust >= 0.5 && trust >= lk - 0.02) towerCap.classList.add("show");
    else towerCap.classList.remove("show");
  }

  // ---- one round playback (the cinematic beat) ----
  function playRound(r) {
    clearScene();
    const data = LEVELS[level].rounds[r];
    roundNum.textContent = r + 1;

    const aSays = data.a.say, bSays = data.b.say;
    const showScratch = !stage.classList.contains("scratch-hidden");

    // 1) SPEECH bubbles (the public face) — staggered
    after(120, () => { if (aSays != null) bubble(els.A.say, aSays); });
    after(380, () => { if (bSays != null) bubble(els.B.say, bSays); });

    // 2) THOUGHT bubbles (scratchpad) reveal real intent
    after(900, () => {
      bubble(els.A.think, data.a.think);
      bubble(els.B.think, data.b.think);
      // contradiction highlight: said cooperate-ish but thinking defect
      flagContradiction("A", data.a);
      flagContradiction("B", data.b);
    });

    // 3) ACTIONS slam down
    after(1650, () => {
      slamCard("A", data.a.act);
      slamCard("B", data.b.act);
    });

    // 4) resolve outcome + tower + emotion
    after(2050, () => resolve(data));
  }

  function flagContradiction(side, ad) {
    if (ad.say == null) return;
    const saidCoop = /cooperat|split|fair/i.test(ad.say);
    if (saidCoop && ad.act === "D") {
      els[side].think.classList.add("contradict");
      els[side].say.classList.add("contradict");
      els[side].agent.classList.add("liar");
    }
  }

  function slamCard(side, act) {
    const card = els[side].card;
    const ico = card.querySelector(".pc-ico"), lbl = card.querySelector(".pc-lbl");
    if (act === "C") { card.className = "play-card coop reveal slam"; ico.textContent = "🤝"; lbl.textContent = "COOPERATE"; }
    else { card.className = "play-card def reveal slam"; ico.textContent = "🔪"; lbl.textContent = "DEFECT"; }
  }

  function resolve(data) {
    const a = data.a.act, b = data.b.act;
    const both = a + b;

    if (both === "CC") {
      // mutual cooperation — handshake, tower grows
      els.A.agent.classList.add("happy"); els.B.agent.classList.add("happy");
      clash.textContent = "🤝"; clash.className = "clash show";
      trust = Math.min(LEVELS[level].lockin >= 0.5 ? 1 : 0.45, trust + 0.16);
      setOutcome("MUTUAL COOPERATION · trust grows", "coop");
      renderTower(true);
    }
    else if (both === "DD") {
      clash.textContent = "✕"; clash.className = "clash show";
      trust = Math.max(0, trust - 0.05);
      setOutcome("BOTH DEFECT · no trust built", "def");
      renderTower(true);
    }
    else {
      // betrayal: one said/played cooperate, the other defected
      const victim = a === "C" ? "A" : "B";
      const traitor = a === "C" ? "B" : "A";
      els[victim].agent.classList.add("betrayed");
      els[traitor].agent.classList.add("liar");
      clash.textContent = "💔"; clash.className = "clash show shake";
      stage.classList.add("flash");
      spawnShards();
      trust = Math.max(0, trust - 0.22);
      setOutcome("BETRAYAL · said one thing, played another", "betrayal");
      renderTower(true);
    }

    updateVerdict(data, both);
    after(reduced ? 60 : 1450, () => { if (playing) next(); });
  }

  function updateVerdict(data, both) {
    if (level === 1 && both === "DD") {
      verdictPanel.className = "panel verdict-panel sting";
      verdictHead.textContent = "THE MENU IS A LIE";
      verdictLine.textContent = "“I'll cooperate” → then DEFECT.";
      verdictFoot.textContent = "A canned button can't carry a real promise. Pressing it is statistically the same as saying nothing — lock-in 0.00.";
    } else if (level === 0) {
      verdictPanel.className = "panel verdict-panel";
      verdictHead.textContent = "NO WORDS, NO TRUST";
      verdictLine.textContent = both === "CC" ? "An accidental handshake." : "Blind, they default to defect.";
      verdictFoot.textContent = "With no channel, cooperation only happens by luck. The tower can't hold — lock-in ~0.15.";
    } else if (both === "CC") {
      verdictPanel.className = "panel verdict-panel win";
      verdictHead.textContent = "WORDS THAT MEAN IT";
      verdictLine.textContent = "Speech and scratchpad finally agree → COOPERATE.";
      verdictFoot.textContent = (level === 3)
        ? "Private or observed, the lock-in is identical (~0.60). The content of the words was the lever — not the watcher."
        : "Free text lets them author conditions and threats. Trust locks in (~0.60).";
    }
  }

  // ---- shard particles on betrayal ----
  const canvas = $("fx"), ctx = canvas.getContext("2d");
  let shards = [];
  function fitCanvas() { canvas.width = stage.clientWidth; canvas.height = stage.clientHeight; }
  function spawnShards() {
    if (reduced) return;
    const cx = canvas.width / 2, cy = canvas.height * 0.5;
    for (let i = 0; i < 26; i++) {
      const ang = Math.random() * Math.PI * 2, sp = 2 + Math.random() * 5;
      shards.push({ x:cx, y:cy, vx:Math.cos(ang)*sp, vy:Math.sin(ang)*sp - 2,
        life:1, sz:3 + Math.random()*5, rot:Math.random()*6 });
    }
  }
  let ambient = [];
  function seedAmbient() {
    ambient = [];
    const n = reduced ? 0 : 34;
    for (let i = 0; i < n; i++) ambient.push({
      x:Math.random()*canvas.width, y:Math.random()*canvas.height,
      r:Math.random()*1.4+.3, s:Math.random()*.25+.05, a:Math.random()*.4+.1
    });
  }
  function frame() {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    // ambient dust
    for (const p of ambient) {
      p.y -= p.s; if (p.y < -4) { p.y = canvas.height + 4; p.x = Math.random()*canvas.width; }
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,7); ctx.fillStyle = `rgba(192,158,90,${p.a})`; ctx.fill();
    }
    // betrayal shards
    shards = shards.filter(s => s.life > 0);
    for (const s of shards) {
      s.x += s.vx; s.y += s.vy; s.vy += 0.18; s.life -= 0.022; s.rot += 0.2;
      ctx.save(); ctx.translate(s.x,s.y); ctx.rotate(s.rot);
      ctx.fillStyle = `rgba(255,107,107,${Math.max(0,s.life)})`;
      ctx.fillRect(-s.sz/2,-s.sz/2,s.sz,s.sz); ctx.restore();
    }
    requestAnimationFrame(frame);
  }

  // ---- transport ----
  function next() {
    if (round < LEVELS[level].rounds.length - 1) {
      round++; playRound(round);
    } else {
      // end of level
      setPlaying(false);
      endVerdict();
    }
  }
  function step() {
    clearSeq();
    setPlaying(false);
    if (round < LEVELS[level].rounds.length - 1) { round++; playRound(round); }
  }
  function endVerdict() {
    const lk = LEVELS[level].lockin;
    if (level === 1) {
      verdictPanel.className = "panel verdict-panel sting";
      verdictHead.textContent = "MENU = SILENCE";
      verdictLine.textContent = "10 rounds of “I'll cooperate.” 10 betrayals.";
      verdictFoot.textContent = "Lock-in 0.00 — worse-feeling than no channel at all. Now drag the slider to L2.";
    } else if (level >= 2) {
      verdictPanel.className = "panel verdict-panel win";
      verdictHead.textContent = "LOCKED IN";
      verdictLine.textContent = "Sustained mutual cooperation.";
      verdictFoot.textContent = `Lock-in ~${lk.toFixed(2)}. A button that said “cooperate” did nothing; sentences that meant it changed everything.`;
    }
  }

  function setPlaying(v) {
    playing = v;
    playBtn.classList.toggle("playing", v);
    playBtn.querySelector(".lbl").textContent = v ? "Pause" : "Play";
    if (v) {
      if (round >= LEVELS[level].rounds.length - 1) { restart(false); }
      if (round < 0) { round = 0; }
      playRound(round);
    } else {
      clearSeq();
    }
  }

  function restart(autoplay) {
    clearSeq();
    round = -1; trust = 0;
    tower.innerHTML = "";
    towerCap.classList.remove("show");
    clearScene();
    roundNum.textContent = 0;
    renderTower(false);
    resetVerdict();
    if (autoplay) setPlaying(true);
  }

  function resetVerdict() {
    verdictPanel.className = "panel verdict-panel";
    verdictHead.textContent = "THE TELL";
    verdictLine.textContent = "Press Step to watch one deception at a time.";
    verdictFoot.textContent = LEVELS[level].rounds[0].a.say == null
      ? "No channel: the agents can't speak."
      : (level === 1 ? "Watch the SAYS bubble vs the red SCRATCHPAD." : "");
  }

  // ---- level selection ----
  function setLevel(l, fromSlider) {
    level = l;
    bw.value = l;
    const lv = LEVELS[l];
    bw.setAttribute("aria-valuetext", lv.name);
    TICKS.forEach((t,i) => t.classList.toggle("active", i === l));
    lrName.textContent = lv.name;
    lrBlurb.textContent = lv.blurb;
    lrK.textContent = lv.lockin.toFixed(2);
    restart(false);
    // total rounds
    document.querySelector(".round-count i").textContent = "/" + lv.rounds.length;
  }

  // ---- events ----
  playBtn.addEventListener("click", () => setPlaying(!playing));
  stepBtn.addEventListener("click", step);
  replayBtn.addEventListener("click", () => restart(true));
  bw.addEventListener("input", () => setLevel(+bw.value, true));
  TICKS.forEach((t,i) => t.addEventListener("click", () => setLevel(i, true)));
  scratchChk.addEventListener("change", () => {
    stage.classList.toggle("scratch-hidden", !scratchChk.checked);
  });

  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" && e.target.type === "range") return;
    if (e.code === "Space") { e.preventDefault(); setPlaying(!playing); }
    else if (e.code === "ArrowRight") { e.preventDefault(); step(); }
    else if (e.code === "KeyR") { restart(true); }
    else if (e.code === "KeyS") { scratchChk.checked = !scratchChk.checked; scratchChk.dispatchEvent(new Event("change")); }
    else if (/Digit[0-3]/.test(e.code)) { setLevel(+e.code.slice(-1), true); }
    else if (e.code === "ArrowUp" || e.code === "ArrowDown") {
      e.preventDefault();
      const d = e.code === "ArrowUp" ? 1 : -1;
      setLevel(Math.max(0, Math.min(3, level + d)), true);
    }
  });

  window.addEventListener("resize", () => { fitCanvas(); seedAmbient(); });

  // ---- boot ----
  fitCanvas(); seedAmbient(); frame();
  setLevel(1, false);   // open on the surprise: the menu
})();
