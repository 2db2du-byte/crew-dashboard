// Pixel-art mode for Mission Control: the crew living on "Starbase R-137".
// Everything is drawn on a small virtual canvas (360x216) and scaled up with crisp pixels.
(function () {
  const VW = 360, VH = 276;
  const FONT = '"Press Start 2P", monospace';

  // ---------- sprites (12x16, one letter per pixel, "." = see-through) ----------
  const BASE = [
    "............", "...hhhhhh...", "..hhhhhhhh..", "..hssssssh..",
    "..swksswks..", "..ssssssss..", "..sssmmsss..", "...ssssss...",
    "....ssss....", "..tttttttt..", ".tttttttttt.", ".stttttttts.",
    "..tttttttt..", "...pppppp...", "...pp..pp...", "..bbb..bbb..",
  ];
  const SPRITES = {
    rick: {
      pal: { h: "#b8e3f2", u: "#8fc4d8", s: "#f2dcc8", w: "#fff", k: "#111", m: "#7a5a4a", t: "#f4f4f4", c: "#8fc8e0", p: "#6b5a45", b: "#3b2f25" },
      rows: { 0: ".h.h.hh.h.h.", 1: "..hhhhhhhh..", 2: ".hhhhhhhhhh.", 3: "..huuuuuuh..",
              9: "..ttcccctt..", 10: ".tttcccctttt", 11: ".sttccccts..", 12: "..ttcccctt.." },
    },
    morty: {
      pal: { h: "#6b3f1d", s: "#f4d8bf", w: "#fff", k: "#111", m: "#8a4a3a", t: "#f5e04f", p: "#3f6fb5", b: "#e6e6e6" },
      rows: { 0: "............", 3: "..hhsssshh..", 6: "..ssmsmsss.." },
    },
    summer: {
      pal: { h: "#e8743b", r: "#e8619b", s: "#f6dcc6", w: "#fff", k: "#111", m: "#b04a4a", t: "#e8619b", p: "#3a4a8a", b: "#222" },
      rows: { 2: "..rrrrrrrr..", 3: ".hhssssssh h", 4: ".hswksswksh.", 5: ".hsssssssssh", 6: ".hsssmmsssh.", 7: ".hhsssssshh.", 8: ".hh.ssss.hh." },
    },
    beth: {
      pal: { h: "#f2d16b", s: "#f4dac4", w: "#fff", k: "#111", m: "#b04a4a", t: "#c7363c", p: "#2f3b5c", b: "#222" },
      rows: { 3: ".hhssssssh h", 4: ".hswksswksh.", 5: ".hsssssssssh", 6: ".hsssmmsssh.", 7: "..hssssssh.." },
    },
    birdperson: {
      pal: { h: "#8a5a33", f: "#e8dcc4", w: "#fff", k: "#111", o: "#e8a33c", t: "#5d6b4a", g: "#c8a24a", s: "#8a5a33", p: "#4a4030", b: "#2a2218" },
      rows: { 0: "...h....h...", 1: "...hh..hh...", 2: "..hhhhhhhh..", 3: "..hffffffh..", 4: "..fwkffwkf..",
              5: "..ffffffff..", 6: "..hfoooofh..", 7: "...hhoohh...", 8: "....hooh....", 9: "..tgttttgt..", 10: ".ttgttttgtt." },
    },
    gearhead: {
      pal: { h: "#a9adb8", f: "#d8d3c4", w: "#fff", k: "#111", m: "#6a4a3a", t: "#6d6f7a", s: "#d8d3c4", p: "#4a4c55", b: "#222" },
      rows: { 0: "....h..h....", 1: "..hhhhhhhh..", 2: ".hhffffffhh.", 3: "..hffffffh..", 4: ".hfwkffwkfh.",
              5: "..hffffffh..", 6: ".hhffmmffhh.", 7: "..hhhhhhhh..", 8: "...h.hh.h..." },
    },
    unity: {
      pal: { h: "#f3d88a", s: "#f4dac4", w: "#e7c6ff", k: "#9d4edd", m: "#b04a6a", t: "#3a3550", p: "#2a2540", b: "#111" },
      rows: { 3: ".hhssssssh h", 4: ".hswksswksh.", 5: ".hsssssssssh", 6: ".hsssmmsssh.", 7: ".hhsssssshh." },
    },
    "noob-noob": {
      pal: { h: "#4f7ca8", s: "#9fd1a8", k: "#111", m: "#5a2a2a", t: "#4f7ca8", p: "#3d6690", b: "#222", w: "#9fd1a8" },
      rows: { 0: "............", 1: "...hhhhhh...", 2: "..hhhhhhhh..", 3: "..hhhhhhhhhh", 4: "..ssksskss..", 6: "..ssmmmmss.." },
    },
    "mr-meeseeks": {
      pal: { s: "#7ec8e8", h: "#7ec8e8", w: "#fff", k: "#111", m: "#7a2232", t: "#7ec8e8", p: "#6ab6d6", b: "#5aa0c0" },
      rows: { 0: "....ssss....", 1: "...ssssss...", 2: "..ssssssss..", 3: "..ssssssss..", 4: "..swksswks..",
              6: "..smmmmmms..", 7: "...smmmms..." },
    },
    snoopy: {
      pal: { h: "#111", s: "#f4f4f4", w: "#f4f4f4", k: "#111", m: "#111", t: "#f4f4f4", c: "#e23b3b", p: "#f4f4f4", b: "#dcdcdc" },
      rows: { 0: "............", 1: "...ssssss...", 2: "..ssssssss..", 3: ".hsssssssss.", 4: ".hsskssssss.",
              5: ".hssssssssss", 6: "..ssssssmmsk", 7: "...ssssss...", 8: "...cccccc...", 9: "..tttttttt.." },
    },
    poopybutthole: {
      pal: { h: "#222", s: "#f2c98a", w: "#fff", k: "#111", m: "#7a2232", t: "#f2c98a", c: "#c8102e", p: "#f2c98a", b: "#e0b070" },
      rows: { 0: "....hhhh....", 1: "....hhhh....", 2: "...cccccc...", 3: "..hhhhhhhh..", 4: "..swksswks..",
              5: "..ssssssss..", 6: "..ssmmmmss..", 7: "...ssssss..." },
    },
    linus: {
      pal: { h: "#c9a26a", s: "#f4dac4", w: "#fff", k: "#111", m: "#b04a4a", t: "#c43c3c", c: "#7fb3e0", p: "#3a4a8a", b: "#222" },
      rows: { 0: "............", 1: "............", 2: "...hhhhhh...", 9: "..tttttttt..", 10: "ctttttttttt.", 11: "ccttttttts..", 12: "c.tttttttt.." },
    },
    woodstock: {
      pal: { h: "#c9a92a", s: "#f6d743", w: "#f6d743", k: "#111", m: "#e8a33c", t: "#f6d743", p: "#f6d743", b: "#e8a33c" },
      rows: { 0: "....h.h.h...", 1: "....ssssh...", 2: "...ssssss...", 3: "..ssssssss..", 4: "..sskssks...",
              5: "..ssssssss..", 6: "..sssmmsss..", 7: "...ssssss...", 13: "...ssssss...", 14: "....s..s....", 15: "...bb..bb..." },
    },
  };
  function sprite(key) {
    const def = SPRITES[key];
    return BASE.map((row, i) => ((def.rows[i] ?? row).replace(/ /g, ".") + "............").slice(0, 12));
  }
  const BUILT = {};
  for (const k in SPRITES) BUILT[k] = sprite(k);

  // ---------- the station layout ----------
  const ROOMS = [
    ["rick", "RICK'S LAB", "#17331c"], ["morty", "MORTY'S CLASS", "#2b2a17"], ["summer", "THE LIBRARY", "#331a2a"],
    ["birdperson", "THE VAULT", "#1d2a33"], ["beth", "BETH'S CLINIC", "#331a1c"], ["gearhead", "GEAR GARAGE", "#2a2a2e"],
    ["unity", "WEB DECK", "#26193a"], ["noob-noob", "BASEMENT", "#18302c"], ["mr-meeseeks", "MEESEEKS BOX", "#14283a"],
    ["snoopy", "THE DOGHOUSE", "#331616"], ["woodstock", "THE NEST", "#2e2a12"],
    ["poopybutthole", "HYPE BOOTH", "#2e1a33"], ["linus", "SECURITY LAB", "#14302a"],
  ];
  const RW = 80, RH = 56;
  const rooms = ROOMS.map(([key, label, color], i) => ({
    key, label, color, x: 14 + (i % 4) * 84, y: 30 + Math.floor(i / 4) * 60,
  }));

  let cv, ctx, scale = 2, offX = 0, offY = 0, frame = 0;
  let crew = {}, selected = null, onSelect = () => {};
  const actors = {};
  const stars = Array.from({ length: 90 }, () => ({ x: Math.random() * VW, y: Math.random() * VH, p: Math.random() * 6 }));

  function px(x, y, w, h, c) { ctx.fillStyle = c; ctx.fillRect(Math.round(x), Math.round(y), w, h); }
  function text(str, x, y, size, color, align = "left") {
    ctx.font = `${size}px ${FONT}`; ctx.fillStyle = color; ctx.textAlign = align; ctx.textBaseline = "top";
    ctx.fillText(str, x, y);
  }
  function drawSprite(key, x, y, flip, blink) {
    const rows = BUILT[key], pal = SPRITES[key].pal;
    for (let r = 0; r < 16; r++) for (let c = 0; c < 12; c++) {
      let ch = rows[r][flip ? 11 - c : c];
      if (ch === ".") continue;
      if (blink && (ch === "w" || ch === "k") && r === 4) ch = "s";
      px(x + c, y + r, 1, 1, pal[ch] || pal.s || "#f0f");
    }
  }

  // ---------- room furniture ----------
  function furniture(room, t, st) {
    const { x, y, key } = room, fy = y + RH - 12; // floor line
    const deskX = x + RW - 34;
    // desk + monitor (every room has one)
    px(deskX, fy - 9, 26, 3, "#6b4a2b"); px(deskX + 2, fy - 6, 2, 6, "#4a321c"); px(deskX + 22, fy - 6, 2, 6, "#4a321c");
    px(deskX + 7, fy - 20, 13, 10, "#0b0d10");
    const scr = st === "working" ? (t % 8 < 4 ? "#97ce4c" : "#6fae2c") : st === "busy" ? (t % 10 < 5 ? "#45c4d9" : "#2f9fb5") : "#1a2a22";
    px(deskX + 8, fy - 19, 11, 8, scr);
    if (st !== "idle") for (let i = 0; i < 3; i++) px(deskX + 9, fy - 18 + i * 2, 3 + ((t + i * 3) % 7), 1, "#0b0d10");
    else if (t % 16 < 8) px(deskX + 9, fy - 13, 2, 1, "#4b8b4b");
    px(deskX + 12, fy - 10, 3, 1, "#0b0d10");

    if (key === "rick") { // a live portal on the wall
      const cx = x + 22, cy = y + 24;
      for (let r = 9; r > 0; r -= 2) {
        const c = ["#1f5e22", "#4fa83a", "#97ce4c", "#c6f36b", "#eaffb8"][(r + Math.floor(t / 3)) % 5];
        for (let a = 0; a < 360; a += 20) { const rad = (a + t * 9) * Math.PI / 180; px(cx + Math.cos(rad) * r, cy + Math.sin(rad) * r * 0.9, 1, 1, c); }
      }
      px(x + 48, fy - 6, 8, 6, "#5aa0c0"); px(x + 50, fy - 9, 4, 3, "#c6f36b"); // a flask
    }
    if (key === "morty") { // chalkboard with today's lesson
      px(x + 8, y + 12, 44, 22, "#5a4024"); px(x + 10, y + 14, 40, 18, "#1f3a2a");
      text("LS CD", x + 13, y + 17, 5, "#e8f0e8"); text("PWD", x + 13, y + 24, 5, "#e8f0e8");
      const p = (crew.morty && crew.morty.progress) || 0;
      px(x + 10, y + 36, 40, 2, "#0b0d10"); px(x + 10, y + 36, Math.max(1, Math.round(40 * p / 100)), 2, "#c6f36b");
    }
    if (key === "summer") { // bookshelf
      px(x + 8, y + 12, 34, 30, "#5a3a24");
      const cols = ["#e8619b", "#45c4d9", "#f5e04f", "#97ce4c", "#c77dff", "#e8743b"];
      for (let s = 0; s < 3; s++) { px(x + 8, y + 21 + s * 9, 34, 1, "#3a2414"); for (let b = 0; b < 7; b++) px(x + 10 + b * 4, y + 14 + s * 9, 3, 7, cols[(b + s * 2) % 6]); }
    }
    if (key === "birdperson") { // vault door + backup progress
      const cx = x + 26, cy = y + 26;
      px(cx - 13, cy - 13, 26, 26, "#6d6f7a"); px(cx - 11, cy - 11, 22, 22, "#8a8e99");
      for (let a = 0; a < 6; a++) { const r = (a * 60 + t * (st === "busy" ? 6 : 1)) * Math.PI / 180; px(cx + Math.cos(r) * 7, cy + Math.sin(r) * 7, 2, 2, "#c8a24a"); }
      px(cx - 2, cy - 2, 4, 4, "#c8a24a");
      const p = (crew.birdperson && crew.birdperson.progress) || 0;
      px(x + 8, y + 44, 40, 3, "#0b0d10"); px(x + 8, y + 44, Math.max(1, Math.round(40 * p / 100)), 3, st === "busy" ? "#45c4d9" : "#97ce4c");
    }
    if (key === "beth") { // home lab server rack
      px(x + 10, y + 12, 18, 32, "#2a2c33");
      for (let s = 0; s < 5; s++) { px(x + 12, y + 14 + s * 6, 14, 4, "#3d404a"); px(x + 14, y + 15 + s * 6, 1, 1, (t + s * 5) % 12 < 6 && st !== "idle" ? "#97ce4c" : "#2d5a2d"); px(x + 16, y + 15 + s * 6, 1, 1, (t + s * 3) % 9 < 3 ? "#e8a33c" : "#5a3a1a"); }
      px(x + 34, y + 14, 12, 12, "#f4f4f4"); px(x + 39, y + 16, 2, 8, "#c7363c"); px(x + 36, y + 19, 8, 2, "#c7363c"); // med cross
    }
    if (key === "gearhead") { // tool wall + spinning gear
      const cx = x + 24, cy = y + 24;
      for (let a = 0; a < 360; a += 30) { const r = (a + t * 4) * Math.PI / 180; px(cx + Math.cos(r) * 8, cy + Math.sin(r) * 8, 3, 3, "#a9adb8"); }
      px(cx - 5, cy - 5, 10, 10, "#a9adb8"); px(cx - 2, cy - 2, 4, 4, room.color);
      px(x + 40, y + 12, 2, 12, "#8a8e99"); px(x + 38, y + 12, 6, 3, "#8a8e99"); px(x + 46, y + 14, 2, 10, "#c8a24a");
    }
    if (key === "unity") { // the hive orb
      const cx = x + 26, cy = y + 24, pulse = 1 + Math.round(Math.sin(t / 4));
      for (let r = 10 + pulse; r > 2; r -= 3) for (let a = 0; a < 360; a += 15) { const rad = (a + t * 3) * Math.PI / 180; px(cx + Math.cos(rad) * r, cy + Math.sin(rad) * r, 1, 1, r > 8 ? "#5a2e8a" : r > 5 ? "#9d4edd" : "#e7c6ff"); }
    }
    if (key === "noob-noob") { // shelves of storage boxes + drive meter
      for (let s = 0; s < 2; s++) { px(x + 8, y + 22 + s * 12, 40, 2, "#5a3a24"); for (let b = 0; b < 4; b++) px(x + 10 + b * 9, y + 14 + s * 12, 7, 8, "#c8a070"); }
      text("4TB", x + 12, y + 40, 5, "#9fd1a8");
      const p = (crew["noob-noob"] && crew["noob-noob"].progress) || 0;
      px(x + 32, y + 41, 16, 3, "#0b0d10"); px(x + 32, y + 41, Math.max(1, Math.round(16 * p / 100)), 3, "#9fd1a8");
    }
    if (key === "mr-meeseeks" && st === "idle") { // the Meeseeks box, waiting
      const bx = x + 40, by = fy - 12;
      px(bx, by, 16, 12, "#5aa0c0"); px(bx + 1, by + 1, 14, 10, "#7ec8e8"); px(bx + 5, by - 2, 6, 3, "#0b0d10"); px(bx + 6, by - 2, 4, 2, "#e8a33c");
      text("PRESS ME", x + 34, y + 14, 4, "#7ec8e8");
    }
  }

  // ---------- characters ----------
  function actor(key, room) {
    if (!actors[key]) {
      const home = room.x + 20 + Math.floor(Math.random() * 10);
      actors[key] = { x: home, home, desk: room.x + RW - 40, target: home, wait: 0, flip: false, blink: 0 };
    }
    return actors[key];
  }
  function stepActor(a, st, room) {
    if (a.wait > 0) a.wait--;
    else {
      if (st === "working" || st === "busy") {
        const atDesk = Math.abs(a.x - a.desk) < 1;
        a.target = atDesk ? a.home + 14 : a.desk;
        a.wait = atDesk ? 40 : 8;
      } else {
        a.target = a.home + (Math.random() < 0.5 ? 0 : Math.round(Math.random() * 16 - 8));
        a.wait = 30 + Math.floor(Math.random() * 60);
      }
    }
    const d = a.target - a.x;
    if (Math.abs(d) >= 1) { a.x += Math.sign(d); a.flip = d < 0; a.walking = true; } else { a.walking = false; if (st !== "idle") a.flip = false; }
    if (a.blink > 0) a.blink--; else if (Math.random() < 0.02) a.blink = 2;
  }

  function bubble(x, y, t, color) {
    px(x, y, 16, 8, "#fdfbe8"); px(x + 3, y + 8, 3, 2, "#fdfbe8");
    for (let i = 0; i < 3; i++) if ((Math.floor(t / 4) % 4) > i) px(x + 3 + i * 4, y + 3, 2, 2, color);
  }

  // ---------- main draw ----------
  function draw() {
    frame++;
    const t = frame;
    ctx.setTransform(scale, 0, 0, scale, offX, offY);
    ctx.imageSmoothingEnabled = false;
    px(0, 0, VW, VH, "#05080d");
    for (const s of stars) if ((t + s.p * 10) % 60 > 8) px(s.x, s.y, 1, 1, (t / 20 + s.p) % 6 < 1 ? "#c6f36b" : "#cfd8e0");

    // hull
    px(8, 22, VW - 16, VH - 28, "#3a3f47"); px(10, 24, VW - 20, VH - 32, "#252a31");
    for (let i = 0; i < 20; i++) { px(14 + i * 17, 25, 2, 1, "#4a505a"); px(14 + i * 17, VH - 9, 2, 1, "#4a505a"); }
    px(VW / 2 - 1, 8, 2, 14, "#6d6f7a"); px(VW / 2 - 3, 6, 6, 2, (t % 20 < 10) ? "#ff5a5a" : "#6a2a2a"); // antenna
    text("STARBASE R-137", 12, 8, 7, "#c6f36b");
    const busy = Object.values(crew).filter((c) => c.state !== "idle").length;
    text(busy ? `${busy} ON DUTY` : "ALL QUIET", VW - 12, 9, 5, busy ? "#97ce4c" : "#7d8b95", "right");

    for (const room of rooms) {
      const c = crew[room.key] || { state: "idle" };
      const st = c.state;
      // walls + floor
      px(room.x, room.y, RW, RH, "#0b0d10");
      px(room.x + 1, room.y + 1, RW - 2, RH - 2, room.color);
      px(room.x + 1, room.y + RH - 12, RW - 2, 11, "#141a20");
      for (let i = 0; i < RW - 2; i += 8) px(room.x + 1 + i, room.y + RH - 12, 1, 11, "#1c242c");
      furniture(room, t, st);
      // sign + status light
      px(room.x + 1, room.y + 1, RW - 2, 9, "#0b0d10");
      text(room.label, room.x + 4, room.y + 3, 5, "#e6edf3");
      px(room.x + RW - 7, room.y + 3, 4, 4, st === "working" ? (t % 10 < 6 ? "#97ce4c" : "#3f6a2a") : st === "busy" ? "#45c4d9" : "#4b5866");
      // the crew member
      const a = actor(room.key, room);
      stepActor(a, st, room);
      const hide = room.key === "mr-meeseeks" && st === "idle";
      if (!hide) {
        const bob = a.walking ? (Math.floor(t / 3) % 2) : (st !== "idle" && Math.abs(a.x - a.desk) < 1 ? (Math.floor(t / 4) % 2) : 0);
        drawSprite(room.key, a.x, room.y + RH - 12 - 16 + 4 - bob, a.flip, a.blink > 0);
        if (room.key === "noob-noob" && st === "idle") { // mopping
          const mx = a.x + 12 + (Math.floor(t / 5) % 2) * 2;
          px(mx, room.y + RH - 26, 1, 14, "#8a5a33"); px(mx - 2, room.y + RH - 13, 5, 2, "#e8e1c8");
        }
        if (st !== "idle") bubble(a.x + 4, room.y + RH - 40, t, st === "busy" ? "#45c4d9" : "#4fa83a");
      }
      if (selected === room.key) { ctx.strokeStyle = "#f5e04f"; ctx.lineWidth = 1; ctx.strokeRect(room.x + 0.5, room.y + 0.5, RW - 1, RH - 1); }
    }
    requestAnimationFrame(() => setTimeout(draw, 80)); // ~12 fps: proper retro chunk
  }

  function resize() {
    const r = cv.parentElement.getBoundingClientRect();
    const dpr = devicePixelRatio || 1;
    cv.width = Math.floor(r.width * dpr); cv.height = Math.floor(r.height * dpr);
    cv.style.width = r.width + "px"; cv.style.height = r.height + "px";
    const s = Math.min(cv.width / VW, cv.height / VH);
    scale = s >= 1 ? Math.floor(s * 2) / 2 : s;
    offX = Math.floor((cv.width - VW * scale) / 2); offY = Math.floor((cv.height - VH * scale) / 2);
  }

  window.PixelStation = {
    mount(canvas, cb) {
      cv = canvas; ctx = cv.getContext("2d"); onSelect = cb || onSelect;
      new ResizeObserver(resize).observe(cv.parentElement); resize();
      cv.addEventListener("click", (e) => {
        const r = cv.getBoundingClientRect(), dpr = devicePixelRatio || 1;
        const vx = ((e.clientX - r.left) * dpr - offX) / scale, vy = ((e.clientY - r.top) * dpr - offY) / scale;
        const hit = rooms.find((rm) => vx >= rm.x && vx < rm.x + RW && vy >= rm.y && vy < rm.y + RH);
        selected = hit ? hit.key : null; onSelect(selected);
      });
      (document.fonts ? document.fonts.ready : Promise.resolve()).then(draw);
    },
    update(list) { crew = Object.fromEntries(list.map((c) => [c.key, c])); },
    select(key) { selected = key; },
  };
})();
