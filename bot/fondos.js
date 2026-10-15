// Fondos de arte matemático generados por código (canvas). Oscuros a propósito para que el texto se lea.
// drawFondo(motivo, semilla) dibuja en <canvas id="bg"> y, para "formulas", en <div id="bgf">.
(function () {
  const A = [255, 222, 89];            // amarillo de marca
  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
  const WHITE = [255, 255, 255];

  function rng(seed) {                  // mulberry32: aleatorio reproducible
    let t = seed >>> 0;
    return () => { t += 0x6D2B79F5; let r = Math.imul(t ^ t >>> 15, 1 | t);
      r ^= r + Math.imul(r ^ r >>> 7, 61 | r); return ((r ^ r >>> 14) >>> 0) / 4294967296; };
  }
  const between = (R, a, b) => a + (b - a) * R();
  const pick = (R, arr) => arr[Math.floor(R() * arr.length)];

  function grid(ctx, W, H, step, a) {
    ctx.strokeStyle = rgba(WHITE, a); ctx.lineWidth = 1; ctx.beginPath();
    for (let x = 0; x <= W; x += step) { ctx.moveTo(x, 0); ctx.lineTo(x, H); }
    for (let y = 0; y <= H; y += step) { ctx.moveTo(0, y); ctx.lineTo(W, y); }
    ctx.stroke();
  }
  function curve(ctx, f, x0, x1, n) {
    ctx.beginPath();
    for (let i = 0; i <= n; i++) { const t = x0 + (x1 - x0) * i / n; const [x, y] = f(t);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
    ctx.stroke();
  }

  const M = {
    funciones(ctx, W, H, R) {
      grid(ctx, W, H, 60, 0.05);
      const oy = between(R, H * 0.35, H * 0.65), ox = between(R, W * 0.3, W * 0.7);
      ctx.strokeStyle = rgba(WHITE, 0.25); ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(0, oy); ctx.lineTo(W, oy); ctx.moveTo(ox, 0); ctx.lineTo(ox, H); ctx.stroke();
      const fs = [
        x => Math.sin(x / 70) * 160, x => -Math.pow(x / 220, 3) * 120, x => -Math.exp(x / 260) * 30,
        x => -260 * Math.exp(-Math.pow(x / 180, 2)), x => Math.cos(x / 45) * 60 - x * 0.25, x => -Math.pow(x / 160, 2) * 90 + 200,
      ];
      for (let k = 0; k < 4; k++) {
        const f = fs[Math.floor(R() * fs.length)], s = between(R, 0.6, 1.4);
        ctx.strokeStyle = rgba(k % 2 ? WHITE : A, k % 2 ? 0.22 : 0.45); ctx.lineWidth = 4;
        curve(ctx, t => [t, oy + f((t - ox) * s)], 0, W, 600);
      }
      const tx = between(R, -300, 300); // recta tangente punteada a sin
      const m = Math.cos(tx / 70) * 160 / 70;
      ctx.setLineDash([14, 12]); ctx.strokeStyle = rgba(A, 0.35); ctx.lineWidth = 3;
      curve(ctx, t => [ox + t, oy + Math.sin(tx / 70) * 160 + m * (t - tx)], tx - 350, tx + 350, 2);
      ctx.setLineDash([]);
    },

    fractal(ctx, W, H, R) {
      const w = W / 2, h = H / 2, img = ctx.createImageData(w, h);
      const julia = R() < 0.5;
      const cs = [[-0.8, 0.156], [0.285, 0.01], [-0.4, 0.6], [-0.70176, -0.3842], [0.355, 0.355]];
      const spots = [[-0.745, 0.113, 0.03], [-0.16, 1.04, 0.05], [-1.25, 0.02, 0.12], [-0.5, 0, 1.6], [0.28, 0.008, 0.02]];
      const [cr, ci] = pick(R, cs); const [mx, my, mz] = pick(R, spots);
      const zoom = julia ? 1.6 : mz, cx = julia ? 0 : mx, cy = julia ? 0 : my, it = 90;
      for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
        let x = cx + (i - w / 2) / w * 2 * zoom * (w / h), y = cy + (j - h / 2) / h * 2 * zoom, ar, ai, n = 0;
        if (julia) { ar = cr; ai = ci; } else { ar = x; ai = y; x = 0; y = 0; }
        while (n < it && x * x + y * y < 16) { const t = x * x - y * y + ar; y = 2 * x * y + ai; x = t; n++; }
        let v = n >= it ? 0 : (n + 1 - Math.log(Math.log(Math.sqrt(x * x + y * y)) + 1e-9) / Math.LN2) / it;
        v = Math.pow(Math.max(0, Math.min(1, v)), 0.55);
        const p = (j * w + i) * 4;
        img.data[p] = A[0] * v; img.data[p + 1] = A[1] * v * 0.8; img.data[p + 2] = A[2] * v * 0.3; img.data[p + 3] = 255;
      }
      const off = document.createElement("canvas"); off.width = w; off.height = h;
      off.getContext("2d").putImageData(img, 0, 0);
      ctx.imageSmoothingEnabled = true; ctx.drawImage(off, 0, 0, W, H);
    },

    espiral(ctx, W, H, R) {
      // Rectángulos áureos: se corta un cuadrado por la izquierda, arriba, derecha y abajo, en ciclo.
      const phi = (1 + Math.sqrt(5)) / 2, w0 = between(R, 1500, 1750), h0 = w0 / phi;
      ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(Math.PI / 2 * Math.floor(R() * 4));
      let x = -w0 / 2 + between(R, -80, 80), y = -h0 / 2 + between(R, -80, 80), w = w0, h = h0;
      for (let k = 0; k < 12; k++) {
        const q = k % 4; let sx, sy, s, cx, cy, a0;
        if (q === 0) { s = h; sx = x; sy = y; cx = x + s; cy = y + s; a0 = Math.PI; x += s; w -= s; }
        else if (q === 1) { s = w; sx = x; sy = y; cx = x; cy = y + s; a0 = 1.5 * Math.PI; y += s; h -= s; }
        else if (q === 2) { s = h; sx = x + w - s; sy = y; cx = sx; cy = y; a0 = 0; w -= s; }
        else { s = w; sx = x; sy = y + h - s; cx = x + s; cy = sy; a0 = 0.5 * Math.PI; h -= s; }
        ctx.strokeStyle = rgba(WHITE, 0.13); ctx.lineWidth = 2; ctx.strokeRect(sx, sy, s, s);
        ctx.strokeStyle = rgba(A, 0.5); ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(cx, cy, s, a0, a0 + Math.PI / 2); ctx.stroke();
      }
      ctx.restore();
    },

    primos(ctx, W, H, R) {
      const step = 15, cx = W / 2 + between(R, -120, 120), cy = H / 2 + between(R, -160, 160);
      const isP = n => { if (n < 2) return false; for (let d = 2; d * d <= n; d++) if (n % d === 0) return false; return true; };
      let x = 0, y = 0, dx = 1, dy = 0, seg = 1, done = 0, turns = 0;
      for (let n = 1; n < 26000; n++) {
        const px = cx + x * step, py = cy + y * step;
        if (px > -10 && px < W + 10 && py > -10 && py < H + 10) {
          if (isP(n)) { ctx.fillStyle = rgba(A, 0.55); ctx.beginPath(); ctx.arc(px, py, 3.6, 0, 7); ctx.fill(); }
          else { ctx.fillStyle = rgba(WHITE, 0.06); ctx.fillRect(px - 1, py - 1, 2, 2); }
        }
        x += dx; y += dy; done++;
        if (done === seg) { done = 0; [dx, dy] = [-dy, dx]; turns++; if (turns % 2 === 0) seg++; }
      }
    },

    probabilidad(ctx, W, H, R) {
      grid(ctx, W, H, 54, 0.04);
      const base = H * between(R, 0.72, 0.85);
      // histograma tipo binomial
      const n = 24, bw = W / n;
      for (let k = 0; k < n; k++) {
        const z = (k - n / 2 + 0.5) / (n / 6), hgt = 520 * Math.exp(-z * z / 2) * between(R, 0.85, 1.1);
        ctx.fillStyle = rgba(A, 0.17); ctx.fillRect(k * bw + 3, base - hgt, bw - 6, hgt);
        ctx.strokeStyle = rgba(A, 0.32); ctx.lineWidth = 2; ctx.strokeRect(k * bw + 3, base - hgt, bw - 6, hgt);
      }
      for (let j = 0; j < 3; j++) {
        const mu = between(R, W * 0.3, W * 0.7), sg = between(R, 90, 220), amp = between(R, 300, 600);
        ctx.strokeStyle = rgba(j ? WHITE : A, j ? 0.25 : 0.75); ctx.lineWidth = j ? 2 : 5;
        curve(ctx, t => [t, base - amp * Math.exp(-Math.pow((t - mu) / sg, 2) / 2)], 0, W, 400);
      }
      for (let i = 0; i < 260; i++) { // puntos dispersos
        const u = R(), v = R(), g = Math.sqrt(-2 * Math.log(u + 1e-9)) * Math.cos(2 * Math.PI * v);
        ctx.fillStyle = rgba(WHITE, 0.18); ctx.beginPath();
        ctx.arc(W / 2 + g * 200, between(R, 120, base - 40), 2.5, 0, 7); ctx.fill();
      }
    },

    geometria(ctx, W, H, R) {
      ctx.lineWidth = 2;
      for (let i = 0; i < 9; i++) {
        const x = between(R, 0, W), y = between(R, 0, H), r = between(R, 80, 420);
        ctx.strokeStyle = rgba(i % 3 ? WHITE : A, i % 3 ? 0.13 : 0.4);
        ctx.beginPath();
        if (i % 3 === 1) ctx.ellipse(x, y, r, r * between(R, 0.35, 0.8), between(R, 0, 3), 0, 7);
        else ctx.arc(x, y, r, 0, 7);
        ctx.stroke();
        ctx.fillStyle = rgba(A, 0.5); ctx.beginPath(); ctx.arc(x, y, 5, 0, 7); ctx.fill();
      }
      ctx.strokeStyle = rgba(A, 0.4); ctx.lineWidth = 3; // parábola
      const vx = between(R, 200, W - 200), vy = between(R, 200, H - 200), a = between(R, 0.002, 0.006) * (R() < 0.5 ? 1 : -1);
      curve(ctx, t => [t, vy + a * (t - vx) * (t - vx)], 0, W, 300);
      ctx.strokeStyle = rgba(WHITE, 0.16); ctx.lineWidth = 2; // triángulo y rectas
      ctx.beginPath(); for (let k = 0; k < 3; k++) { const px = between(R, 0, W), py = between(R, 0, H); k ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }
      ctx.closePath(); ctx.stroke();
    },

    trig(ctx, W, H, R) {
      const r = between(R, 300, 380), cx = between(R, r * 0.6, W - r * 0.6), cy = between(R, H * 0.3, H * 0.7);
      ctx.strokeStyle = rgba(WHITE, 0.18); ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(W, cy); ctx.moveTo(cx, 0); ctx.lineTo(cx, H); ctx.stroke();
      ctx.strokeStyle = rgba(A, 0.5); ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.stroke();
      for (let k = 0; k < 12; k++) {
        const t = k * Math.PI / 6; ctx.strokeStyle = rgba(WHITE, 0.12); ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + r * Math.cos(t), cy - r * Math.sin(t)); ctx.stroke();
        ctx.fillStyle = rgba(A, 0.6); ctx.beginPath(); ctx.arc(cx + r * Math.cos(t), cy - r * Math.sin(t), 6, 0, 7); ctx.fill();
      }
      ctx.strokeStyle = rgba(A, 0.35); ctx.lineWidth = 4;
      curve(ctx, t => [t, cy - r * Math.sin((t - cx) / r)], 0, W, 500);
      ctx.strokeStyle = rgba(WHITE, 0.2); ctx.lineWidth = 3;
      curve(ctx, t => [t, cy - r * Math.cos((t - cx) / r)], 0, W, 500);
    },

    ondas(ctx, W, H, R) {
      const lines = 34, f = [between(R, 0.004, 0.009), between(R, 0.01, 0.02), between(R, 0.02, 0.04)];
      for (let i = 0; i < lines; i++) {
        const y0 = 80 + i * (H - 160) / lines, ph = between(R, 0, 6), amp = 30 + 50 * Math.sin(i / lines * Math.PI);
        ctx.strokeStyle = rgba(i % 5 ? WHITE : A, i % 5 ? 0.12 : 0.45); ctx.lineWidth = i % 5 ? 2 : 3;
        curve(ctx, t => [t, y0 - amp * (Math.sin(f[0] * t + ph) + 0.5 * Math.sin(f[1] * t + 2 * ph) + 0.25 * Math.sin(f[2] * t))], 0, W, 400);
      }
    },

    rejilla(ctx, W, H, R) {
      grid(ctx, W, H, 72, 0.05);
      const a = between(R, 0.7, 1.3), b = between(R, -0.6, 0.6), c = between(R, -0.5, 0.5), d = between(R, 0.7, 1.3);
      const cx = W / 2, cy = H / 2, T = (u, v) => [cx + a * u + b * v, cy - (c * u + d * v)];
      ctx.strokeStyle = rgba(A, 0.28); ctx.lineWidth = 2;
      for (let k = -14; k <= 14; k++) {
        curve(ctx, t => T(k * 72, t), -1400, 1400, 2); curve(ctx, t => T(t, k * 72), -1400, 1400, 2);
      }
      const arrow = (u, v, col) => { const [x1, y1] = T(u, v); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 6;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(x1, y1); ctx.stroke();
        const ang = Math.atan2(y1 - cy, x1 - cx); ctx.beginPath(); ctx.moveTo(x1, y1);
        ctx.lineTo(x1 - 26 * Math.cos(ang - 0.4), y1 - 26 * Math.sin(ang - 0.4)); ctx.lineTo(x1 - 26 * Math.cos(ang + 0.4), y1 - 26 * Math.sin(ang + 0.4)); ctx.fill(); };
      arrow(216, 0, rgba(A, 0.6)); arrow(0, 216, rgba(WHITE, 0.4));
    },

    red(ctx, W, H, R) {
      const pts = [];
      for (let i = 0; i < 70; i++) pts.push([between(R, -40, W + 40), between(R, -40, H + 40)]);
      ctx.lineWidth = 2;
      for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
        const dd = Math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]);
        if (dd < 210) { ctx.strokeStyle = rgba(WHITE, 0.16 * (1 - dd / 210) + 0.04); ctx.beginPath();
          ctx.moveTo(...pts[i]); ctx.lineTo(...pts[j]); ctx.stroke(); }
      }
      for (const [x, y] of pts) { const big = R() < 0.25;
        ctx.fillStyle = rgba(big ? A : WHITE, big ? 0.6 : 0.3); ctx.beginPath(); ctx.arc(x, y, big ? 9 : 5, 0, 7); ctx.fill(); }
    },

    lissajous(ctx, W, H, R) {
      const pairs = [[3, 2], [5, 4], [3, 4], [5, 6], [7, 6], [1, 2], [4, 5]];
      for (let k = 0; k < 3; k++) {
        const [p, q] = pick(R, pairs), dl = between(R, 0, Math.PI), s = between(R, 0.75, 1.05);
        ctx.strokeStyle = rgba(k ? WHITE : A, k ? 0.15 : 0.42); ctx.lineWidth = k ? 2 : 3;
        curve(ctx, t => [W / 2 + s * 470 * Math.sin(p * t + dl), H / 2 + s * 600 * Math.sin(q * t)], 0, 2 * Math.PI, 1600);
      }
    },

    formulas(ctx, W, H, R) {
      grid(ctx, W, H, 60, 0.03);
      const lay = document.getElementById("bgf"); if (!lay || !window.katex) return;
      const F = ["e^{i\\pi}+1=0", "\\int_0^1 x^2\\,dx=\\tfrac13", "\\sum_{n=1}^{\\infty}\\frac1{n^2}=\\frac{\\pi^2}{6}",
        "a^2+b^2=c^2", "x=\\frac{-b\\pm\\sqrt{b^2-4ac}}{2a}", "\\frac{d}{dx}e^x=e^x", "\\lim_{n\\to\\infty}\\left(1+\\frac1n\\right)^n=e",
        "\\sin^2\\theta+\\cos^2\\theta=1", "\\varphi=\\frac{1+\\sqrt5}{2}", "\\binom{n}{k}=\\frac{n!}{k!(n-k)!}", "\\nabla\\cdot\\vec F",
        "\\det(A-\\lambda I)=0", "i^2=-1", "\\pi\\approx3.14159", "f'(x)", "\\infty", "\\sqrt2\\notin\\mathbb Q", "P(A\\mid B)",
        "\\oint_C \\vec F\\cdot d\\vec r", "2^{10}=1024", "V-E+F=2", "\\mathbb{R}", "\\Delta x"];
      const cols = 4, rows = 7, cw = W / cols, ch = H / rows;
      for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
        if (R() < 0.5) continue;
        const el = document.createElement("div");
        el.style.cssText = `position:absolute;left:${c * cw + between(R, -60, cw * 0.4)}px;top:${r * ch + between(R, 0, ch * 0.5)}px;` +
          `font-size:${between(R, 34, 70)}px;color:${R() < 0.4 ? rgba(A, 0.22) : rgba(WHITE, 0.11)};` +
          `transform:rotate(${between(R, -14, 14)}deg);white-space:nowrap`;
        katex.render(pick(R, F), el, { throwOnError: false });
        lay.appendChild(el);
      }
    },
  };

  window.drawFondo = function (motivo, semilla) {
    const cv = document.getElementById("bg"); if (!cv) return;
    const ctx = cv.getContext("2d"), W = cv.width, H = cv.height, R = rng(semilla || 1);
    ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
    (M[motivo] || M.formulas)(ctx, W, H, R);
    // Oscurecer: velo general + viñeta, para que el texto siempre gane
    ctx.fillStyle = "rgba(0,0,0,0.12)"; ctx.fillRect(0, 0, W, H);
    const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.15, W / 2, H / 2, H * 0.75);
    g.addColorStop(0, "rgba(0,0,0,0.30)"); g.addColorStop(1, "rgba(0,0,0,0.62)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  };
  window.MOTIVOS = Object.keys(M);
})();
