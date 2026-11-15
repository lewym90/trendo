(nazwa) => {
  const norm = (s) => (s || '').toLowerCase().normalize('NFKD').replace(/[^a-z0-9]/g, '');
  const N = norm(nazwa);
  const ZLE = /visa|mastercard|blik|paypal|payu|inpost|dpd|dhl|facebook|instagram|tiktok|youtube|pinterest|appstore|googleplay|trusted|opineo|ceneo|klarna|cookie|onetrust|flag|search|szukaj|koszyk|cart|basket|wishlist|ulubion|account|konto|user|hamburger|close|zamknij|arrow|chevron|heart|bag/i;
  const host = location.hostname.replace(/^www\./, '');
  const doDomu = (a) => {
    try {
      const u = new URL(a.href, location.href);
      return u.hostname.replace(/^www\./, '') === host && u.pathname.split('/').filter(Boolean).length <= 2 && !u.search;
    } catch (e) { return false; }
  };
  const opis = (el) => [el.id, el.getAttribute('class'), el.getAttribute('alt'), el.getAttribute('aria-label'), el.getAttribute('title'), el.getAttribute('data-testid'), el.getAttribute('src')].join(' ');
  const kand = [];
  const tlo = (cs) => { for (const v of [cs.backgroundImage, cs.maskImage, cs.webkitMaskImage]) { const m = /url\(["']?([^"')]+)/.exec(v || ''); if (m) return m[1]; } return null; };
  document.querySelectorAll('svg, img, a *, header *, [class*="logo" i], [id*="logo" i]').forEach((el) => {
    const tag = el.tagName.toLowerCase();
    if (tag === 'svg' && el.parentElement && el.parentElement.closest('svg')) return;
    if (tag !== 'svg' && tag !== 'img' && el.closest('svg')) return;
    const r = el.getBoundingClientRect();
    if (r.top < -5 || r.top > 220 || r.width < 40 || r.width > 900 || r.height < 8 || r.height > 260) return;
    const cs = getComputedStyle(el);
    if (cs.display === 'none') return;
    const url = tag === 'img' ? null : tag === 'svg' ? null : tlo(cs);
    if (tag !== 'img' && tag !== 'svg' && !url) return;
    let pkt = (cs.visibility === 'hidden' || +cs.opacity === 0) ? -1 : 0, tekst = opis(el);
    let p = el.parentElement, d = 0;
    while (p && d < 6) { tekst += ' ' + opis(p); if (p.tagName === 'A' && doDomu(p)) pkt += 5; if (p.tagName === 'HEADER') pkt += 2; p = p.parentElement; d++; }
    if (/logo|brand|wordmark/i.test(tekst)) pkt += 3;
    if (N && (norm(el.getAttribute('alt')) + norm(el.getAttribute('aria-label')) + norm(el.closest('a') ? el.closest('a').getAttribute('aria-label') + el.closest('a').getAttribute('title') : '')).includes(N)) pkt += 3;
    if (N && el.tagName.toLowerCase() === 'svg' && norm(el.textContent).includes(N)) pkt += 2;
    const blisko = opis(el) + ' ' + (el.closest('a') ? opis(el.closest('a')) : '') + ' ' + (el.closest('button') ? 'button ' + opis(el.closest('button')) : '');
    if (ZLE.test(blisko.replace(/logo/ig, ''))) pkt -= 6;
    const prop = r.width / r.height;
    if (prop >= 1.8) pkt += 2;
    if (r.top < 120) pkt += 1;
    kand.push({ el, pkt, url, r: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  });
  if (!kand.some((k) => k.pkt >= 8)) {
    document.querySelectorAll('a svg, a img').forEach((el) => {
      if (el.tagName.toLowerCase() === 'svg' && el.parentElement.closest('svg')) return;
      const a = el.closest('a');
      if (!a || !doDomu(a) || el.closest('footer')) return;
      let tekst = opis(el) + ' ' + opis(a) + ' ' + opis(a.parentElement || a);
      if (!/logo|brand|strona główna|strony głównej|home/i.test(tekst) || ZLE.test((opis(el) + ' ' + opis(a)).replace(/logo/ig, ''))) return;
      const vb = (el.getAttribute('viewBox') || '').split(/[\s,]+/).map(Number);
      const w = vb.length === 4 ? vb[2] : el.naturalWidth || 0, h = vb.length === 4 ? vb[3] : el.naturalHeight || 0;
      if (!w || !h || w / h < 1) return;
      kand.push({ el, pkt: 8, url: null, r: [0, 0, Math.round(w), Math.round(h)] });
    });
  }
  kand.sort((a, b) => b.pkt - a.pkt || a.r[1] - b.r[1]);
  const widziane = new Set();
  const wyn = [];
  for (const k of kand) {
    if (wyn.length >= 3) break;
    const el = k.el;
    const klucz = k.url || el.currentSrc || el.src || el.outerHTML.length;
    if (widziane.has(klucz)) continue; widziane.add(klucz);
    el.setAttribute('data-trendo-znak', String(wyn.length));
    if (el.tagName.toLowerCase() === 'img' || k.url) {
      wyn.push({ nr: wyn.length, pkt: k.pkt, typ: 'img', url: k.url ? new URL(k.url, location.href).href : (el.currentSrc || el.src), r: k.r });
      continue;
    }
    const kopia = el.cloneNode(true);
    kopia.querySelectorAll('use').forEach((u) => {
      const ref = u.getAttribute('href') || u.getAttribute('xlink:href') || '';
      if (!ref.startsWith('#')) return;
      const s = document.getElementById(ref.slice(1));
      if (!s) return;
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.innerHTML = s.innerHTML;
      if (s.getAttribute('viewBox') && !kopia.getAttribute('viewBox')) kopia.setAttribute('viewBox', s.getAttribute('viewBox'));
      u.replaceWith(g);
    });
    // Przenosimy wyliczone kolory, bo style strony nie pojadą z plikiem.
    const zrodla = [el, ...el.querySelectorAll('*')], cele = [kopia, ...kopia.querySelectorAll('*')];
    zrodla.forEach((z, i) => {
      const c = cele[i]; if (!c || !c.setAttribute) return;
      const s = getComputedStyle(z);
      if (s.fill && s.fill !== 'none' && !c.getAttribute('fill')) c.setAttribute('fill', s.fill);
      if (s.stroke && s.stroke !== 'none' && !c.getAttribute('stroke')) c.setAttribute('stroke', s.stroke);
    });
    if (!kopia.getAttribute('viewBox')) { const b = el.getBBox ? el.getBBox() : null; if (b && b.width) kopia.setAttribute('viewBox', `${b.x} ${b.y} ${b.width} ${b.height}`); }
    kopia.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    ['class', 'style', 'aria-hidden', 'focusable', 'role', 'data-trendo-znak'].forEach((a) => kopia.removeAttribute(a));
    kopia.setAttribute('width', k.r[2]); kopia.setAttribute('height', k.r[3]);
    wyn.push({ nr: wyn.length, pkt: k.pkt, typ: 'svg', svg: kopia.outerHTML, r: k.r });
  }
  return wyn;
}
