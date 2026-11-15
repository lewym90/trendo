async ([dane, typ]) => {
  // Znak sklepu jako jasny napis na przezroczystym tle: przycięty, wysokość 160 px, jeden kolor.
  const img = new Image();
  img.src = dane;
  try { await img.decode(); } catch (e) { return { blad: 'nie da się otworzyć obrazu' }; }
  let w = img.naturalWidth, h = img.naturalHeight;
  if (!w || !h) { w = 600; h = 150; }
  const WYS = 160;
  const skala = typ === 'svg' ? Math.max(1, (WYS * 2.2) / h) : Math.min(6, Math.max(1, (WYS * 1.2) / h));
  const W = Math.min(4000, Math.round(w * skala)), H = Math.min(2000, Math.round(h * skala));
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const x = c.getContext('2d');
  x.drawImage(img, 0, 0, W, H);
  const d = x.getImageData(0, 0, W, H).data;
  const px = (i, j) => { const k = (j * W + i) * 4; return [d[k], d[k + 1], d[k + 2], d[k + 3]]; };
  // Tło: rogi. Gdy są nieprzezroczyste i podobne, to kolor tła do wycięcia (logo na białym albo w ramce).
  const rogi = [px(1, 1), px(W - 2, 1), px(1, H - 2), px(W - 2, H - 2)];
  const nieprzezr = rogi.filter((r) => r[3] > 200);
  let tlo = null;
  if (nieprzezr.length >= 3) {
    const sr = [0, 1, 2].map((i) => nieprzezr.reduce((s, r) => s + r[i], 0) / nieprzezr.length);
    if (nieprzezr.every((r) => Math.abs(r[0] - sr[0]) + Math.abs(r[1] - sr[1]) + Math.abs(r[2] - sr[2]) < 60)) tlo = sr;
  }
  // Znak na przezroczystym tle z białymi wycięciami w ciemnym kształcie (np. litera w kolorowym kwadracie):
  // białe piksele traktujemy jako wycięcia, chyba że cały znak jest biały.
  let wyciecia = false;
  if (!tlo) {
    let n = 0, biale = 0; const lumy = [];
    for (let k = 0; k < d.length; k += 16) {
      if (d[k + 3] < 200) continue;
      n++;
      const r = d[k], g = d[k + 1], b = d[k + 2], l = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
      if (l > 0.9 && Math.max(r, g, b) - Math.min(r, g, b) < 25) biale++; else lumy.push(l);
    }
    lumy.sort((a, b) => a - b);
    const med = lumy.length ? lumy[lumy.length >> 1] : 1;
    wyciecia = n > 0 && biale / n > 0.02 && biale / n < 0.6 && med < 0.75;
  }
  // Najdalszy kolor od tła daje pełną siłę znaku.
  const sila = new Float32Array(W * H);
  let maks = 0;
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
    const k = (j * W + i) * 4, a = d[k + 3] / 255;
    let s;
    if (tlo) {
      const roz = Math.sqrt((d[k] - tlo[0]) ** 2 + (d[k + 1] - tlo[1]) ** 2 + (d[k + 2] - tlo[2]) ** 2) / 441.7;
      s = a * roz;
    } else if (wyciecia) {
      const doBieli = Math.sqrt((255 - d[k]) ** 2 + (255 - d[k + 1]) ** 2 + (255 - d[k + 2]) ** 2) / 441.7;
      s = a * Math.min(1, doBieli / 0.35);
    } else s = a;
    sila[j * W + i] = s; if (s > maks) maks = s;
  }
  if (maks < 0.15) return { blad: 'pusty obraz' };
  const prog = maks * 0.12;
  let x0 = W, y0 = H, x1 = -1, y1 = -1;
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) if (sila[j * W + i] > prog) { if (i < x0) x0 = i; if (i > x1) x1 = i; if (j < y0) y0 = j; if (j > y1) y1 = j; }
  if (x1 < 0) return { blad: 'pusty obraz' };
  const bw = x1 - x0 + 1, bh = y1 - y0 + 1;
  let suma = 0;
  for (let j = y0; j <= y1; j++) for (let i = x0; i <= x1; i++) suma += Math.min(1, sila[j * W + i] / maks);
  const pokrycie = suma / (bw * bh);
  // Wynik: wysokość WYS, kolor jasny, przezroczystość = siła znaku.
  const sk2 = WYS / bh;
  const OW = Math.max(1, Math.round(bw * sk2)), OH = WYS;
  const m = document.createElement('canvas'); m.width = bw; m.height = bh;
  const mx = m.getContext('2d'), md = mx.createImageData(bw, bh);
  for (let j = 0; j < bh; j++) for (let i = 0; i < bw; i++) {
    const k = (j * bw + i) * 4, s = Math.min(1, sila[(j + y0) * W + (i + x0)] / maks);
    md.data[k] = 255; md.data[k + 1] = 255; md.data[k + 2] = 255; md.data[k + 3] = Math.round(s * 255);
  }
  mx.putImageData(md, 0, 0);
  const o = document.createElement('canvas'); o.width = OW + 8; o.height = OH + 8;
  const ox = o.getContext('2d'); ox.imageSmoothingQuality = 'high';
  ox.drawImage(m, 4, 4, OW, OH);
  return { png: o.toDataURL('image/png'), proporcja: bw / bh, pokrycie, tlo: !!tlo, wyciecia, zrodlo: [w, h] };
}
