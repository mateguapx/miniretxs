// Ilustraciones de portada: UNA figura de arte matemático, centrada y protagonista (como la ilustración de una portada).
// Sin texto ni números: solo líneas, puntos y formas. Paleta de marca: amarillo y blanco sobre negro.
// drawIlustracion(canvas, motivo, semilla). window.ILUSTRACIONES = lista de motivos.
(function () {
  const A = [255, 222, 89], WHITE = [255, 255, 255];
  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
  function rng(seed) {
    let t = seed >>> 0;
    return () => { t += 0x6D2B79F5; let r = Math.imul(t ^ t >>> 15, 1 | t);
      r ^= r + Math.imul(r ^ r >>> 7, 61 | r); return ((r ^ r >>> 14) >>> 0) / 4294967296; };
  }
  const between = (R, a, b) => a + (b - a) * R();
  const pick = (R, arr) => arr[Math.floor(R() * arr.length)];
  const TAU = Math.PI * 2;
  function poly(ctx, pts, close) {
    ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    if (close) ctx.closePath(); ctx.stroke();
  }
  function glow(ctx, c, blur) { ctx.shadowColor = rgba(c, 0.55); ctx.shadowBlur = blur; }
  function noGlow(ctx) { ctx.shadowBlur = 0; }

  // Cada motivo dibuja centrado en (cx, cy) dentro de un radio útil r.
  const M = {
    // Cardioide / nefroide con cuerdas (string art): punto i unido con el punto k·i en un círculo.
    cuerdas(ctx, cx, cy, r, R) {
      const n = pick(R, [180, 220, 240]), k = pick(R, [2, 3, 4, 5]);
      ctx.lineWidth = 1.4;
      for (let i = 0; i < n; i++) {
        const a = TAU * i / n - Math.PI / 2, b = TAU * ((k * i) % n) / n - Math.PI / 2;
        ctx.strokeStyle = rgba(i % 3 ? A : WHITE, i % 3 ? 0.55 : 0.28);
        ctx.beginPath(); ctx.moveTo(cx + r * Math.cos(a), cy + r * Math.sin(a));
        ctx.lineTo(cx + r * Math.cos(b), cy + r * Math.sin(b)); ctx.stroke();
      }
      glow(ctx, A, 18); ctx.strokeStyle = rgba(A, 0.95); ctx.lineWidth = 5;
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, TAU); ctx.stroke(); noGlow(ctx);
    },

    // Espiral áurea dentro de sus rectángulos áureos.
    espiral(ctx, cx, cy, r, R) {
      const phi = (1 + Math.sqrt(5)) / 2, w0 = r * 2.1, h0 = w0 / phi;
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(Math.PI / 2 * Math.floor(R() * 2) * 2);
      let x = -w0 / 2, y = -h0 / 2, w = w0, h = h0;
      const arcs = [];
      for (let k = 0; k < 13; k++) {
        const q = k % 4; let sx, sy, s, ax, ay, a0;
        if (q === 0) { s = h; sx = x; sy = y; ax = x + s; ay = y + s; a0 = Math.PI; x += s; w -= s; }
        else if (q === 1) { s = w; sx = x; sy = y; ax = x; ay = y + s; a0 = 1.5 * Math.PI; y += s; h -= s; }
        else if (q === 2) { s = h; sx = x + w - s; sy = y; ax = sx; ay = y; a0 = 0; w -= s; }
        else { s = w; sx = x; sy = y + h - s; ax = x + s; ay = sy; a0 = 0.5 * Math.PI; h -= s; }
        ctx.strokeStyle = rgba(WHITE, 0.45); ctx.lineWidth = 2.5; ctx.strokeRect(sx, sy, s, s);
        arcs.push([ax, ay, s, a0]);
      }
      glow(ctx, A, 22); ctx.strokeStyle = rgba(A, 1); ctx.lineWidth = 7; ctx.lineCap = "round";
      for (const [ax, ay, s, a0] of arcs) { ctx.beginPath(); ctx.arc(ax, ay, s, a0, a0 + Math.PI / 2); ctx.stroke(); }
      noGlow(ctx); ctx.restore();
    },

    // Árbol fractal (cada rama se divide en dos, más corta).
    arbol(ctx, cx, cy, r, R) {
      const ang = between(R, 0.42, 0.52), f = between(R, 0.72, 0.76), depth = 11;
      ctx.lineCap = "round";
      function rama(x, y, len, a, d) {
        if (d === 0) return;
        const x2 = x + len * Math.cos(a), y2 = y + len * Math.sin(a);
        const t = d / depth;
        ctx.strokeStyle = t > 0.35 ? rgba(A, 0.95) : rgba(WHITE, 0.75);
        ctx.lineWidth = Math.max(1.2, 16 * t * t);
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x2, y2); ctx.stroke();
        if (d === 1) { ctx.fillStyle = rgba(A, 0.85); ctx.beginPath(); ctx.arc(x2, y2, 3, 0, TAU); ctx.fill(); }
        rama(x2, y2, len * f, a - ang, d - 1); rama(x2, y2, len * f, a + ang, d - 1);
      }
      glow(ctx, A, 10); rama(cx, cy + r * 1.02, r * 0.42, -Math.PI / 2, depth); noGlow(ctx);
    },

    // Triángulo de Sierpinski.
    sierpinski(ctx, cx, cy, r, R) {
      const d = 6, top = [cx, cy - r * 1.05], L = r * 2.1, hh = L * Math.sqrt(3) / 2;
      const p0 = [cx - L / 2, top[1] + hh], p1 = [cx + L / 2, top[1] + hh];
      const shift = (cy - r * 1.05 + hh / 2) - cy; // centrar verticalmente
      const T = p => [p[0], p[1] - shift];
      ctx.lineJoin = "round";
      function tri(a, b, c, n) {
        if (n === 0) {
          ctx.fillStyle = rgba(A, 0.18); ctx.strokeStyle = rgba(A, 0.95); ctx.lineWidth = 1.6;
          ctx.beginPath(); ctx.moveTo(...T(a)); ctx.lineTo(...T(b)); ctx.lineTo(...T(c)); ctx.closePath(); ctx.fill(); ctx.stroke();
          return;
        }
        const ab = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], bc = [(b[0] + c[0]) / 2, (b[1] + c[1]) / 2], ca = [(c[0] + a[0]) / 2, (c[1] + a[1]) / 2];
        tri(a, ab, ca, n - 1); tri(ab, b, bc, n - 1); tri(ca, bc, c, n - 1);
      }
      tri(top, p1, p0, d);
      glow(ctx, A, 20); ctx.strokeStyle = rgba(WHITE, 0.9); ctx.lineWidth = 4;
      poly(ctx, [T(top), T(p1), T(p0)], true); noGlow(ctx);
    },

    // Copo de nieve de Koch, con copos más pequeños anidados.
    koch(ctx, cx, cy, r, R) {
      function copo(rad, n, rot) {
        let pts = [0, 1, 2].map(i => [cx + rad * Math.cos(rot + TAU * i / 3), cy + rad * Math.sin(rot + TAU * i / 3)]);
        for (let k = 0; k < n; k++) {
          const nx = [];
          for (let i = 0; i < pts.length; i++) {
            const [x1, y1] = pts[i], [x2, y2] = pts[(i + 1) % pts.length];
            const dx = (x2 - x1) / 3, dy = (y2 - y1) / 3;
            const a = [x1 + dx, y1 + dy], b = [x1 + 2 * dx, y1 + 2 * dy];
            const px = a[0] + dx * Math.cos(-Math.PI / 3) - dy * Math.sin(-Math.PI / 3);
            const py = a[1] + dx * Math.sin(-Math.PI / 3) + dy * Math.cos(-Math.PI / 3);
            nx.push([x1, y1], a, [px, py], b);
          }
          pts = nx;
        }
        return pts;
      }
      const rot = -Math.PI / 2;
      [[1, 0.95, A, 6], [0.62, 0.6, WHITE, 3], [0.38, 0.75, A, 2.5], [0.23, 0.5, WHITE, 2]].forEach(([s, al, c, lw], i) => {
        if (i === 0) glow(ctx, A, 24); else noGlow(ctx);
        ctx.strokeStyle = rgba(c, al); ctx.lineWidth = lw; ctx.lineJoin = "round";
        poly(ctx, copo(r * s, 4 - Math.min(i, 2), rot + (i % 2) * Math.PI / 3), true);
      });
      noGlow(ctx);
    },

    // Espirógrafo (hipotrocoide).
    espirografo(ctx, cx, cy, r, R) {
      const opts = [[5, 3, 2.2], [7, 4, 3], [8, 5, 4.2], [9, 4, 3.4], [11, 7, 5], [7, 3, 2.6]];
      const [Rr, rr, d] = pick(R, opts), s = r / (Rr - rr + d);
      const g = (a, b) => { let x = a, y = b; while (y) [x, y] = [y, x % y]; return x; };
      const turns = rr / g(Rr, rr), N = 4000 * turns;
      const P = t => [cx + s * ((Rr - rr) * Math.cos(t) + d * Math.cos((Rr - rr) / rr * t)),
                      cy + s * ((Rr - rr) * Math.sin(t) - d * Math.sin((Rr - rr) / rr * t))];
      const pts = []; for (let i = 0; i <= N; i++) pts.push(P(TAU * turns * i / N));
      ctx.strokeStyle = rgba(WHITE, 0.25); ctx.lineWidth = 10; poly(ctx, pts);
      glow(ctx, A, 16); ctx.strokeStyle = rgba(A, 0.95); ctx.lineWidth = 3; poly(ctx, pts); noGlow(ctx);
    },

    // Conjunto de Julia dentro de un círculo.
    julia(ctx, cx, cy, r, R) {
      const cs = [[-0.8, 0.156], [0.285, 0.01], [-0.4, 0.6], [-0.70176, -0.3842], [-0.835, -0.2321], [0.355, 0.355]];
      const [cr, ci] = pick(R, cs), size = Math.round(r * 2), img = ctx.createImageData(size, size), it = 160;
      for (let j = 0; j < size; j++) for (let i = 0; i < size; i++) {
        const p = (j * size + i) * 4, u = (i - size / 2) / (size / 2), v = (j - size / 2) / (size / 2);
        if (u * u + v * v > 1) { img.data[p + 3] = 0; continue; }
        let x = u * 1.6, y = v * 1.6, n = 0;
        while (n < it && x * x + y * y < 16) { const t = x * x - y * y + cr; y = 2 * x * y + ci; x = t; n++; }
        let val = n >= it ? 0 : (n + 1 - Math.log(Math.log(Math.sqrt(x * x + y * y)) + 1e-9) / Math.LN2) / 40;
        val = Math.pow(Math.max(0, Math.min(1, val)), 0.6);
        const wv = Math.max(0, val - 0.75) * 4; // los bordes más intensos tiran a blanco
        img.data[p] = A[0] * val + (255 - A[0]) * wv; img.data[p + 1] = A[1] * val + (255 - A[1]) * wv;
        img.data[p + 2] = A[2] * val * 0.6 + (255 - A[2] * 0.6) * wv; img.data[p + 3] = 255;
      }
      const off = document.createElement("canvas"); off.width = size; off.height = size;
      off.getContext("2d").putImageData(img, 0, 0); ctx.drawImage(off, cx - size / 2, cy - size / 2);
      glow(ctx, A, 18); ctx.strokeStyle = rgba(A, 0.9); ctx.lineWidth = 4;
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, TAU); ctx.stroke(); noGlow(ctx);
    },

    // Girasol: filotaxis con el ángulo áureo.
    girasol(ctx, cx, cy, r, R) {
      const n = 900, ga = Math.PI * (3 - Math.sqrt(5)), c = r / Math.sqrt(n);
      for (let i = 1; i <= n; i++) {
        const rad = c * Math.sqrt(i), a = i * ga, t = i / n;
        ctx.fillStyle = (i % 13 === 0 || i % 21 === 0) ? rgba(WHITE, 0.95) : rgba(A, 0.35 + 0.6 * t);
        ctx.beginPath(); ctx.arc(cx + rad * Math.cos(a), cy + rad * Math.sin(a), 2 + 7 * Math.sqrt(t), 0, TAU); ctx.fill();
      }
    },

    // Teseracto (hipercubo 4D) proyectado en el plano.
    teseracto(ctx, cx, cy, r, R) {
      const V = []; for (let i = 0; i < 16; i++) V.push([0, 1, 2, 3].map(b => (i >> b & 1) ? 1 : -1));
      const a1 = between(R, 0.25, 0.45), a2 = between(R, 0.2, 0.4), a3 = between(R, 0.35, 0.55);
      const rot = (p, i, j, a) => { const q = p.slice(); q[i] = p[i] * Math.cos(a) - p[j] * Math.sin(a); q[j] = p[i] * Math.sin(a) + p[j] * Math.cos(a); return q; };
      const P = V.map(p => {
        let q = rot(rot(rot(p, 0, 3, a1), 1, 3, a2), 0, 2, a3);
        q = rot(q, 1, 2, 0.5);
        const w = 1 / (3 - q[3]);
        return [cx + q[0] * w * r * 1.5, cy + q[1] * w * r * 1.5, q[3]];
      });
      ctx.lineCap = "round";
      for (let i = 0; i < 16; i++) for (let b = 0; b < 4; b++) {
        const j = i ^ (1 << b); if (j < i) continue;
        const inner = P[i][2] < 0 && P[j][2] < 0;
        ctx.strokeStyle = b === 3 ? rgba(WHITE, 0.55) : rgba(A, inner ? 0.55 : 0.95);
        ctx.lineWidth = b === 3 ? 2.5 : (inner ? 3 : 6);
        if (!inner && b !== 3) glow(ctx, A, 16); else noGlow(ctx);
        ctx.beginPath(); ctx.moveTo(P[i][0], P[i][1]); ctx.lineTo(P[j][0], P[j][1]); ctx.stroke();
      }
      noGlow(ctx);
      for (const [x, y] of P) { ctx.fillStyle = rgba(WHITE, 1); ctx.beginPath(); ctx.arc(x, y, 7, 0, TAU); ctx.fill(); }
    },

    // Rosa polar r = cos(kθ), varias capas.
    rosa(ctx, cx, cy, r, R) {
      const k = pick(R, [[5, 1], [7, 1], [4, 1], [7, 3], [5, 2], [8, 3]]), kk = k[0] / k[1];
      const per = k[1] * ((k[0] * k[1]) % 2 ? 1 : 2) * Math.PI, N = 3000;
      [[1, A, 0.95, 4], [0.7, WHITE, 0.55, 2.5], [0.42, A, 0.7, 2]].forEach(([s, c, al, lw], i) => {
        const pts = []; for (let n = 0; n <= N; n++) { const t = per * n / N, rr = r * s * Math.cos(kk * t + i * 0.3);
          pts.push([cx + rr * Math.cos(t), cy + rr * Math.sin(t)]); }
        if (i === 0) glow(ctx, A, 18); else noGlow(ctx);
        ctx.strokeStyle = rgba(c, al); ctx.lineWidth = lw; poly(ctx, pts);
      });
      noGlow(ctx);
    },

    // Superficie de onda en alambre (z = sin(r)/r) en perspectiva.
    onda3d(ctx, cx, cy, r, R) {
      const n = 46, f = between(R, 1.1, 1.6), tilt = 0.55;
      const pr = (x, y) => { const d = Math.hypot(x, y) * 9 * f + 0.0001, z = Math.sin(d) / d * 1.6;
        return [cx + (x - y) * r * 0.78, cy + (x + y) * r * 0.78 * tilt - z * r * 0.55 + r * 0.05]; };
      for (let pass = 0; pass < 2; pass++) for (let i = 0; i <= n; i++) {
        const pts = []; for (let j = 0; j <= n; j++) { const u = -1 + 2 * i / n, v = -1 + 2 * j / n; pts.push(pass ? pr(v, u) : pr(u, v)); }
        ctx.strokeStyle = (i % 5 === 0) ? rgba(A, 0.95) : rgba(WHITE, 0.32); ctx.lineWidth = i % 5 === 0 ? 3 : 1.5;
        poly(ctx, pts);
      }
    },

    // Lissajous en una sola línea gruesa con brillo.
    lissajous(ctx, cx, cy, r, R) {
      const [p, q] = pick(R, [[3, 2], [5, 4], [3, 4], [5, 6], [7, 6]]), dl = Math.PI / (2 * q), N = 4000;
      const pts = []; for (let i = 0; i <= N; i++) { const t = TAU * i / N; pts.push([cx + r * Math.sin(p * t + dl), cy + r * Math.sin(q * t)]); }
      ctx.strokeStyle = rgba(WHITE, 0.2); ctx.lineWidth = 14; poly(ctx, pts);
      glow(ctx, A, 18); ctx.strokeStyle = rgba(A, 1); ctx.lineWidth = 4; poly(ctx, pts); noGlow(ctx);
    },
  };

  window.drawIlustracion = function (cv, motivo, semilla) {
    // Se dibuja en un lienzo auxiliar grande y luego se recorta y escala para que la figura llene el espacio
    // (todas las figuras quedan del mismo tamaño visual, centradas y sin cortarse).
    const W = cv.width, H = cv.height, R = rng(semilla || 1), S = 1400;
    const off = document.createElement("canvas"); off.width = S; off.height = S;
    const octx = off.getContext("2d");
    (M[motivo] || M.cuerdas)(octx, S / 2, S / 2, S * 0.36, R);
    const d = octx.getImageData(0, 0, S, S).data;
    let x0 = S, y0 = S, x1 = 0, y1 = 0;
    for (let y = 0; y < S; y += 2) for (let x = 0; x < S; x += 2) {
      if (d[(y * S + x) * 4 + 3] > 40) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    }
    if (x1 <= x0 || y1 <= y0) return;
    const pad = 24; x0 = Math.max(0, x0 - pad); y0 = Math.max(0, y0 - pad); x1 = Math.min(S, x1 + pad); y1 = Math.min(S, y1 + pad);
    const bw = x1 - x0, bh = y1 - y0, k = Math.min(W * 0.84 / bw, H * 0.86 / bh);
    const ctx = cv.getContext("2d");
    ctx.drawImage(off, x0, y0, bw, bh, (W - bw * k) / 2, (H - bh * k) / 2 - H * 0.02, bw * k, bh * k);
  };
  window.ILUSTRACIONES = Object.keys(M);
})();
