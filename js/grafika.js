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

  function wykresLinii(punkty, kolor, w, h) {
    w = w || 70; h = h || 30;
    const max = Math.max(...punkty), min = Math.min(...punkty), z = max - min || 1;
    const d = punkty.map((p, i) => `${i ? 'L' : 'M'}${(i / (punkty.length - 1) * (w - 2) + 1).toFixed(1)} ${(h - 3 - (p - min) / z * (h - 6)).toFixed(1)}`).join('');
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><path d="${d}" fill="none" stroke="${kolor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }

  window.G = { IK, ubranie, probka, wykresLinii };
})();
