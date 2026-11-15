/* Ikony i rysunki zastępcze ubrań (do czasu prawdziwych zdjęć ze sklepów) */
(function () {
  const s = (d, w) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${w || 1.6}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
  const IK = {
    szukaj: s('<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>'),
    dom: s('<path d="M4 11l8-7 8 7v9a1 1 0 0 1-1 1h-4v-6h-6v6H5a1 1 0 0 1-1-1z"/>'),
    trend: s('<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>'),
    okazje: s('<path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0l-7.2-7.2A2 2 0 0 1 2.8 12V4.8A2 2 0 0 1 4.8 2.8H12a2 2 0 0 1 1.4.6l7.2 7.2a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/>'),
    torba: s('<path d="M5 8h14l-1 12H6z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>'),
    dzwonek: s('<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 21h4"/>'),
    profil: s('<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>'),
    wstecz: s('<path d="M15 5l-7 7 7 7"/>', 1.8),
    dalej: s('<path d="M9 5l7 7-7 7"/>', 1.8),
    serce: s('<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>'),
    sercePelne: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z" fill="#EBBBA7"/></svg>',
    aparat: s('<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>'),
    iskra: s('<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/>'),
    wieszak: s('<path d="M12 8V7a2 2 0 1 0-2-2"/><path d="M12 8l-8.4 6.5A1 1 0 0 0 4.2 16h15.6a1 1 0 0 0 .6-1.5z"/>'),
    outfit: s('<path d="M8 3l4 3 4-3 4 3-2 4h-2v11H8V10H6L4 6z"/>'),
    dodatki: s('<path d="M6 9h12l-1 11H7z"/><path d="M9 9a3 3 0 0 1 6 0"/><path d="M10 13h4"/>'),
    zdjecie: s('<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-8 9"/>'),
    filtr: s('<path d="M4 7h16M7 12h10M10 17h4"/>'),
    ok: s('<path d="M5 12l5 5 9-10"/>', 2.4),
    uwaga: s('<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/>', 2),
    info: s('<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>', 2),
    link: s('<path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>'),
    gora: s('<path d="M12 19V5M6 11l6-6 6 6"/>', 2.6),
    dol: s('<path d="M12 5v14M6 13l6 6 6-6"/>', 2.6),
    poziom: s('<path d="M5 12h14"/>', 2.6),
    plus: s('<path d="M12 5v14M5 12h14"/>', 2),
    kosz: s('<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>'),
    zamknij: s('<path d="M6 6l12 12M18 6L6 18"/>', 1.8),
    second: s('<path d="M4 12a8 8 0 0 1 14-5.3L20 9"/><path d="M20 4v5h-5"/><path d="M20 12a8 8 0 0 1-14 5.3L4 15"/><path d="M4 20v-5h5"/>')
  };

  /* Sylwetki ubrań: kolor główny, kolor wykończenia */
  function ubranie(typ, k1, k2) {
    k1 = k1 || '#1F1B1D'; k2 = k2 || shade(k1, 14);
    const blask = '<path d="M30 30c-3 30-6 66-9 96" stroke="#fff" stroke-opacity=".13" stroke-width="3" fill="none"/>';
    const T = {
      spodnie: `<svg viewBox="0 0 100 140" aria-hidden="true"><path d="M27 6h46l4 18 5 110H59L51.5 50h-3L41 134H18l5-110z" fill="${k1}"/><path d="M27 6h46v9H27z" fill="${k2}"/><path d="M33 24c-2 30-5 70-8 104" stroke="#fff" stroke-opacity=".14" stroke-width="3" fill="none"/><path d="M66 24c2 30 6 70 9 104" stroke="#fff" stroke-opacity=".08" stroke-width="3" fill="none"/><path d="M50 15v22" stroke="#000" stroke-opacity=".4" stroke-width=".8"/></svg>`,
      flare: `<svg viewBox="0 0 100 140" aria-hidden="true"><path d="M27 6h46l3 18 2 70 10 40H60L51.5 50h-3L40 134H14l10-40V24z" fill="${k1}"/><path d="M27 6h46v9H27z" fill="${k2}"/><path d="M32 26c-1 30-2 60-11 102" stroke="#fff" stroke-opacity=".13" stroke-width="3" fill="none"/></svg>`,
      szerokie: `<svg viewBox="0 0 100 140" aria-hidden="true"><path d="M27 6h46l6 18 9 110H58L51.5 50h-3L42 134H12l9-110z" fill="${k1}"/><path d="M27 6h46v9H27z" fill="${k2}"/><path d="M30 26c-3 30-7 70-12 102" stroke="#fff" stroke-opacity=".13" stroke-width="3" fill="none"/></svg>`,
      koszula: `<svg viewBox="0 0 140 140" aria-hidden="true"><defs><pattern id="kr-${k1.slice(1)}" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="16" height="16" fill="${k1}"/><rect y="5" width="16" height="5" fill="${k2}" opacity=".85"/><rect x="5" width="5" height="16" fill="${k2}" opacity=".6"/><rect y="13" width="16" height="1" fill="#E8D9B5" opacity=".8"/><rect x="13" width="1" height="16" fill="#E8D9B5" opacity=".8"/></pattern></defs><path d="M45 10l13-4 12 10 12-10 13 4 33 24-10 26-16-10v82H38V50l-16 10-10-26z" fill="url(#kr-${k1.slice(1)})"/><path d="M58 6l12 10-6 9zM82 6L70 16l6 9z" fill="${k2}"/><path d="M70 16v116" stroke="#000" stroke-opacity=".35" stroke-width="1.2"/></svg>`,
      bluzka: `<svg viewBox="0 0 140 140" aria-hidden="true"><path d="M45 10l13-4 12 10 12-10 13 4 33 24-10 26-16-10v82H38V50l-16 10-10-26z" fill="${k1}"/><path d="M58 6l12 10-6 9zM82 6L70 16l6 9z" fill="${k2}"/><path d="M70 16v116" stroke="#000" stroke-opacity=".18" stroke-width="1.2"/><path d="M48 40c-2 30-2 60 0 88" stroke="#fff" stroke-opacity=".12" stroke-width="3" fill="none"/></svg>`,
      plaszcz: `<svg viewBox="0 0 140 150" aria-hidden="true"><path d="M48 8L62 4l8 22 8-22 14 4 30 22 8 82-14 2-6-56-2 88H32l-2-88-6 56-14-2 8-82z" fill="${k1}"/><path d="M62 4l8 22-6 34-10-30zM78 4l-8 22 6 34 10-30z" fill="${k2}"/><circle cx="70" cy="80" r="2.6" fill="#000" fill-opacity=".45"/><circle cx="70" cy="100" r="2.6" fill="#000" fill-opacity=".45"/><path d="M44 104h18M78 104h18" stroke="#000" stroke-opacity=".25" stroke-width="1.5"/></svg>`,
      marynarka: `<svg viewBox="0 0 140 150" aria-hidden="true"><path d="M48 10L62 6l8 20 8-20 14 4 28 22 6 66-13 2-5-44v70H32V56l-5 44-13-2 6-66z" fill="${k1}"/><path d="M62 6l8 20-5 30-10-26zM78 6l-8 20 5 30 10-26z" fill="${k2}"/><circle cx="70" cy="84" r="2.6" fill="#000" fill-opacity=".45"/><path d="M42 96h16" stroke="#000" stroke-opacity=".25" stroke-width="1.5"/></svg>`,
      sweter: `<svg viewBox="0 0 140 140" aria-hidden="true"><path d="M46 12q24 12 48 0l32 22-10 30-14-8v72H38V56l-14 8-10-30z" fill="${k1}"/><path d="M46 12q24 12 48 0l-4 8q-20 10-40 0z" fill="${k2}"/><path d="M38 124h64v4H38zM24 64l-4-6M116 64l4-6" stroke="${k2}" stroke-width="4"/><path d="M50 40v80M62 40v80M78 40v80M90 40v80" stroke="#000" stroke-opacity=".12" stroke-width="2"/></svg>`,
      botki: `<svg viewBox="0 0 140 90" aria-hidden="true"><path d="M14 4h30v48q2 10 20 12l18 3q10 2 10 11v6H10Q8 50 14 4z" fill="${k1}"/><path d="M36 14h8v34h-8z" fill="${k2}"/><path d="M10 84h82v4H10z" fill="#0d0b0b"/><g transform="translate(40 2)"><path d="M14 4h30v48q2 10 20 12l18 3q10 2 10 11v6H10Q8 50 14 4z" fill="${shade(k1, 8)}"/><path d="M36 14h8v34h-8z" fill="${k2}"/><path d="M10 84h82v4H10z" fill="#0d0b0b"/></g></svg>`,
      torebka: `<svg viewBox="0 0 100 90" aria-hidden="true"><path d="M30 34C30 6 70 6 70 34" stroke="${k2}" stroke-width="5" fill="none"/><path d="M12 32h76l-6 54H18z" fill="${k1}"/><path d="M12 32h76l-8 20H20z" fill="${k2}"/><circle cx="50" cy="52" r="3.2" fill="#E8C9A0"/></svg>`,
      pasek: `<svg viewBox="0 0 140 60" aria-hidden="true"><path d="M6 24h128v12H6z" fill="${k1}" rx="3"/><rect x="58" y="18" width="24" height="24" rx="3" fill="none" stroke="#D8B48E" stroke-width="4"/><path d="M70 30h12" stroke="#D8B48E" stroke-width="3"/></svg>`,
      kolczyki: `<svg viewBox="0 0 100 100" aria-hidden="true"><g fill="none" stroke="${k1}" stroke-width="5"><circle cx="32" cy="58" r="18"/><circle cx="72" cy="58" r="18"/></g><circle cx="32" cy="36" r="4" fill="${k1}"/><circle cx="72" cy="36" r="4" fill="${k1}"/></svg>`,
      okulary: `<svg viewBox="0 0 140 70" aria-hidden="true"><path d="M10 26h50v6q0 22-24 22T10 32zM80 26h50v6q0 22-24 22T80 32z" fill="${k1}"/><path d="M60 30q10-8 20 0" stroke="${k2}" stroke-width="4" fill="none"/></svg>`,
      sukienka: `<svg viewBox="0 0 120 150" aria-hidden="true"><path d="M44 6h32l2 26-8 14 34 98H16l34-98-8-14z" fill="${k1}"/><path d="M44 6h6v24h20V6h6l2 26-8 14H50l-8-14z" fill="${k2}"/></svg>`,
      kurtka: `<svg viewBox="0 0 140 140" aria-hidden="true"><path d="M48 8L62 4l8 16 8-16 14 4 30 22 6 72-14 2-6-50v78H34V54l-6 50-14-2 6-72z" fill="${k1}"/><path d="M62 4l8 16-8 26-8-30zM78 4l-8 16 8 26 8-30z" fill="${k2}"/><path d="M70 20v112" stroke="#C9A27E" stroke-width="1.6" stroke-dasharray="3 2"/></svg>`
    };
    return T[typ] || T.spodnie;
  }

  function shade(hex, amt) {
    const n = parseInt(hex.slice(1), 16);
    const c = (v) => Math.max(0, Math.min(255, v + amt));
    const r = c(n >> 16), g = c((n >> 8) & 255), b = c(n & 255);
    return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  }

  /* Próbka tkaniny/koloru do listy trendów */
  function probka(kind, k1, k2) {
    if (kind === 'krata') return `<svg viewBox="0 0 76 88" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><rect width="76" height="88" fill="${k1}"/><path d="M0 22h76M0 58h76" stroke="${k2}" stroke-width="12"/><path d="M20 0v88M54 0v88" stroke="${k2}" stroke-opacity=".6" stroke-width="12"/><path d="M0 40h76M38 0v88" stroke="#E8D9B5" stroke-width="1.5"/></svg>`;
    if (kind === 'metal') return `<svg viewBox="0 0 76 88" aria-hidden="true"><rect width="76" height="88" fill="${k1}"/><circle cx="38" cy="44" r="17" fill="none" stroke="${k2}" stroke-width="6"/><circle cx="38" cy="44" r="17" fill="none" stroke="#fff" stroke-opacity=".6" stroke-width="1.5" stroke-dasharray="6 40"/></svg>`;
    if (kind === 'zamsz') return `<svg viewBox="0 0 76 88" aria-hidden="true"><rect width="76" height="88" fill="${k1}"/><path d="M0 14h76M0 30h76M0 46h76M0 62h76M0 78h76" stroke="#000" stroke-opacity=".09" stroke-width="7"/></svg>`;
    return `<svg viewBox="0 0 76 88" aria-hidden="true"><rect width="76" height="88" fill="${k1}"/><path d="M-6 62C16 36 34 70 82 26" stroke="#fff" stroke-opacity=".16" stroke-width="7" fill="none"/><path d="M-6 80C20 60 40 84 82 50" stroke="#fff" stroke-opacity=".07" stroke-width="5" fill="none"/></svg>`;
  }

  /* ---------- wykresy ---------- */
  let nrWykresu = 0;
  // kolory ze świata (damski: różowe złoto, męski: mosiądz)
  const kol = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  // Gładka krzywa bez przestrzeleń (monotoniczna, Fritsch–Carlson): nie rysuje wzrostu, którego nie było.
  function krzywa(p) {
    if (p.length < 2) return '';
    if (p.length === 2) return `M${p[0][0]} ${p[0][1]}L${p[1][0]} ${p[1][1]}`;
    const n = p.length, dx = [], dy = [], m = [], t = [];
    for (let i = 0; i < n - 1; i++) { dx[i] = p[i + 1][0] - p[i][0]; dy[i] = p[i + 1][1] - p[i][1]; m[i] = dy[i] / dx[i]; }
    t[0] = m[0]; t[n - 1] = m[n - 2];
    for (let i = 1; i < n - 1; i++) t[i] = m[i - 1] * m[i] <= 0 ? 0 : (m[i - 1] + m[i]) / 2;
    for (let i = 0; i < n - 1; i++) {
      if (m[i] === 0) { t[i] = 0; t[i + 1] = 0; continue; }
      const a = t[i] / m[i], b = t[i + 1] / m[i], h = a * a + b * b;
      if (h > 9) { const k = 3 / Math.sqrt(h); t[i] = k * a * m[i]; t[i + 1] = k * b * m[i]; }
    }
    let d = `M${p[0][0].toFixed(1)} ${p[0][1].toFixed(1)}`;
    for (let i = 0; i < n - 1; i++) {
      const c = dx[i] / 3;
      d += `C${(p[i][0] + c).toFixed(1)} ${(p[i][1] + t[i] * c).toFixed(1)} ${(p[i + 1][0] - c).toFixed(1)} ${(p[i + 1][1] - t[i + 1] * c).toFixed(1)} ${p[i + 1][0].toFixed(1)} ${p[i + 1][1].toFixed(1)}`;
    }
    return d;
  }

  /* Mały wykres w karcie trendu: krzywa, mgiełka koloru pod nią, kropka „teraz”. Luki w danych zostają lukami. */
  function wykresTrendu(wartosci, kolor, opcje) {
    const o = Object.assign({ w: 84, h: 42, os: false }, opcje || {});
    const id = 'wt' + (++nrWykresu);
    const zn = wartosci.map((v, i) => [i, v]).filter((x) => x[1] != null);
    // Zakres od najmniejszej do największej wartości: liczy się kształt (rośnie, spada), nie odległość od zera.
    const vmax = Math.max(...zn.map((x) => x[1])), vmin = Math.min(...zn.map((x) => x[1]));
    const zap = (vmax - vmin) * 0.15 || Math.max(1, vmax * 0.2);
    const max = vmax + zap, min = Math.max(0, vmin - zap);
    const z = max - min || 1, gora = 7, dol = o.h - 5, lewo = 3, prawo = o.w - 6;
    const X = (i) => lewo + (i / (wartosci.length - 1)) * (prawo - lewo), Y = (v) => dol - ((v - min) / z) * (dol - gora);
    // odcinki bez luk
    const odc = []; let akt = [];
    wartosci.forEach((v, i) => { if (v == null) { if (akt.length) odc.push(akt); akt = []; } else akt.push([X(i), Y(v)]); });
    if (akt.length) odc.push(akt);
    const linie = odc.map((p) => krzywa(p)).join('');
    const mgla = odc.filter((p) => p.length > 1).map((p) => `${krzywa(p)}L${p[p.length - 1][0].toFixed(1)} ${dol}L${p[0][0].toFixed(1)} ${dol}Z`).join('');
    const ost = zn[zn.length - 1];
    return `<svg class="wykres-trendu" width="${o.w}" height="${o.h}" viewBox="0 0 ${o.w} ${o.h}" aria-hidden="true">
      <defs><linearGradient id="${id}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${kolor}" stop-opacity=".34"/><stop offset=".75" stop-color="${kolor}" stop-opacity="0"/></linearGradient></defs>
      ${o.os ? `<line x1="${lewo}" x2="${prawo}" y1="${dol + .5}" y2="${dol + .5}" stroke="rgba(${kol('--linia-rgb')},.16)" stroke-width="1"/>` : ''}
      <path d="${mgla}" fill="url(#${id})"/>
      <path d="${linie}" fill="none" stroke="${kolor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="${X(ost[0]).toFixed(1)}" cy="${Y(ost[1]).toFixed(1)}" r="7" fill="${kolor}" opacity=".16"/>
      <circle cx="${X(ost[0]).toFixed(1)}" cy="${Y(ost[1]).toFixed(1)}" r="3.4" fill="${kolor}" stroke="${kol('--tlo2')}" stroke-width="2"/></svg>`;
  }

  /* Znak statusu, gdy danych jest za mało na wykres (mniej niż 3 tygodnie): pierścień w różowym złocie i strzałka w kolorze statusu. */
  function znakStatusu(status, kolor) {
    const id = 'zs' + (++nrWykresu);
    const strzalka = {
      rosnie: '<path d="M21 31l6-6 4 4 7-8"/><path d="M33 21h5v5"/>',
      nadchodzi: '<path d="M28 18l1.6 4.6L34 24l-4.4 1.4L28 30l-1.6-4.6L22 24l4.4-1.4z"/><path d="M34.5 29l.6 1.6 1.6.6-1.6.6-.6 1.6-.6-1.6-1.6-.6 1.6-.6z"/>',
      szczyt: '<path d="M20 30c3-7 5-10 8-10s5 3 8 10"/><circle cx="28" cy="20" r="1.2" fill="currentColor"/>',
      wygasa: '<path d="M21 21l6 6 4-4 7 8"/><path d="M33 31h5v-5"/>'
    }[status] || '';
    return `<svg class="znak-statusu" width="56" height="56" viewBox="0 0 56 56" aria-hidden="true" style="color:${kolor}">
      <defs><radialGradient id="${id}g" cx=".5" cy=".42" r=".6"><stop offset="0" stop-color="${kolor}" stop-opacity=".22"/><stop offset="1" stop-color="${kolor}" stop-opacity="0"/></radialGradient>
      <linearGradient id="${id}r" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F8DACB"/><stop offset=".5" stop-color="#E7AE98"/><stop offset="1" stop-color="#9C5F4D"/></linearGradient></defs>
      <circle cx="28" cy="28" r="26" fill="url(#${id}g)"/>
      <circle cx="28" cy="28" r="22.5" fill="none" stroke="url(#${id}r)" stroke-width="1.2" opacity=".85"/>
      <circle cx="28" cy="28" r="19" fill="none" stroke="rgba(240,196,182,.12)" stroke-width="1"/>
      <g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" transform="translate(0 -1)">${strzalka}</g></svg>`;
  }

  /* Historia ceny: wykres schodkowy (cena obowiązuje do następnej zmiany), dotyk pokazuje cenę z danego dnia. */
  function wykresCeny(punkty, zl) {
    const id = 'wc' + (++nrWykresu);
    const W = 340, H = 132, l = 8, p = 8, g = 22, d = 104;
    const t0 = punkty[0][1], t1 = Math.max(punkty[punkty.length - 1][1], Date.now() / 1000), dt = t1 - t0 || 1;
    const ceny = punkty.map((x) => x[0]), max = Math.max(...ceny), min = Math.min(...ceny);
    const zakres = max - min || max * 0.1 || 1, pmax = max + zakres * 0.25, pmin = Math.max(0, min - zakres * 0.6), z = pmax - pmin || 1;
    const X = (t) => l + ((t - t0) / dt) * (W - l - p), Y = (v) => d - ((v - pmin) / z) * (d - g);
    let s = `M${X(t0).toFixed(1)} ${Y(ceny[0]).toFixed(1)}`;
    punkty.forEach((x, i) => { if (i) s += `H${X(x[1]).toFixed(1)}V${Y(x[0]).toFixed(1)}`; });
    s += `H${X(t1).toFixed(1)}`;
    const ost = punkty[punkty.length - 1];
    const naj = punkty.reduce((a, x) => (x[0] < a[0] ? x : a), punkty[0]);
    const data = (t) => new Date(t * 1000).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short' });
    return `<div class="wykres-ceny" data-wykres-ceny='${JSON.stringify({ t0, t1, l, p, W, g, d, pmin, pmax, punkty })}'>
      <svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Cena ${data(t0)}: ${zl(ceny[0])}, dziś: ${zl(ost[0])}, najniższa: ${zl(min)}">
      <defs><linearGradient id="${id}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${kol('--roz')}" stop-opacity=".26"/><stop offset="1" stop-color="${kol('--roz')}" stop-opacity="0"/></linearGradient></defs>
      <line x1="${l}" x2="${W - p}" y1="${d + .5}" y2="${d + .5}" stroke="rgba(${kol('--linia-rgb')},.16)"/>
      ${min !== max ? `<line x1="${l}" x2="${W - p}" y1="${Y(min).toFixed(1)}" y2="${Y(min).toFixed(1)}" stroke="rgba(158,217,180,.35)" stroke-width="1"/>
      <text x="${l}" y="${(Y(min) - 6).toFixed(1)}" class="opis-wykresu">najniższa ${zl(min)} · ${data(naj[1])}</text>` : ''}
      <path d="${s}V${d}H${X(t0).toFixed(1)}Z" fill="url(#${id})"/>
      <path d="${s}" fill="none" stroke="${kol('--roz')}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="${X(t1).toFixed(1)}" cy="${Y(ost[0]).toFixed(1)}" r="7" fill="${kol('--roz')}" opacity=".18"/>
      <circle cx="${X(t1).toFixed(1)}" cy="${Y(ost[0]).toFixed(1)}" r="4" fill="${kol('--akcent-jasny')}" stroke="${kol('--tlo2')}" stroke-width="2"/>
      <text x="${l}" y="${H - 6}" class="os-wykresu">${data(t0)}</text><text x="${W - p}" y="${H - 6}" text-anchor="end" class="os-wykresu">dziś</text>
      <g class="celownik" visibility="hidden"><line y1="${g - 6}" y2="${d}" stroke="rgba(${kol('--jasny-rgb')},.35)"/><circle r="4" fill="${kol('--akcent-jasny')}" stroke="${kol('--tlo2')}" stroke-width="2"/></g>
      </svg><div class="dymek" hidden></div></div>`;
  }
  // Dotyk lub kursor nad wykresem ceny: pionowa linia i cena z tego dnia.
  function podpnijWykresCeny(el, zl) {
    const o = JSON.parse(el.dataset.wykresCeny), svg = el.querySelector('svg'), cel = el.querySelector('.celownik'), dym = el.querySelector('.dymek');
    const pokaz = (e) => {
      const r = svg.getBoundingClientRect(), x = ((e.clientX - r.left) / r.width) * o.W;
      const t = o.t0 + ((Math.min(Math.max(x, o.l), o.W - o.p) - o.l) / (o.W - o.l - o.p)) * (o.t1 - o.t0);
      let c = o.punkty[0]; o.punkty.forEach((pk) => { if (pk[1] <= t) c = pk; });
      const skala = r.width / o.W, px = Math.min(Math.max(x, o.l), o.W - o.p);
      const y = o.d - ((c[0] - o.pmin) / (o.pmax - o.pmin || 1)) * (o.d - o.g);
      cel.setAttribute('visibility', 'visible'); cel.setAttribute('transform', `translate(${px.toFixed(1)} 0)`);
      cel.querySelector('circle').setAttribute('cy', y.toFixed(1));
      dym.hidden = false;
      dym.textContent = `${zl(c[0])} · ${new Date(t * 1000).toLocaleDateString('pl-PL', { day: 'numeric', month: 'long' })}`;
      dym.style.left = Math.min(Math.max(px * skala, 60), r.width - 60) + 'px';
    };
    const ukryj = () => { cel.setAttribute('visibility', 'hidden'); dym.hidden = true; };
    el.addEventListener('pointermove', pokaz); el.addEventListener('pointerdown', pokaz);
    el.addEventListener('pointerleave', ukryj); el.addEventListener('pointerup', (e) => { if (e.pointerType !== 'mouse') setTimeout(ukryj, 1600); });
  }

  window.G = { IK, ubranie, probka, wykresTrendu, znakStatusu, wykresCeny, podpnijWykresCeny };
})();
