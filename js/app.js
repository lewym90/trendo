/* Trendo: interfejs. Produkty, ceny, okazje, alerty i trendy pochodzą z serwera; js/demo.js zostaje tylko jako zapas,
   gdy serwer nie odpowiada, oraz dla stylizacji, które są jeszcze przykładowe. */
(function () {
  'use strict';
  const WERSJA = '0.20.0';
  const IK = G.IK;
  const E = document.getElementById('ekran');
  const MENU = document.getElementById('menu');
  const ARK = document.getElementById('arkusz');
  const KOM = document.getElementById('komunikat');

  /* ---------- stan zapisany na telefonie ---------- */
  const DOMYSLNE = {
    witaj: false, dzial: 'damskie', zapytanie: 'Skórzane spodnie', b1: 3000, b2: 800,
    okazja: 'codzien', stylTryb: 'outfit', stylStart: null, stylQ: '', koszyk: [], ulubione: [], zapisane: [], alerty: [],
    ostatnie: [], rozmiar: {}, ust: { gora: '', dol: '', buty: '' }, rozm: { d: {}, m: {} }, hist: { produkty: [], szukania: [], styl: [] }, stylRozm: null, znane: {}
  };
  let st;
  try { st = Object.assign({}, DOMYSLNE, JSON.parse(localStorage.getItem('trendo') || '{}')); } catch (e) { st = Object.assign({}, DOMYSLNE); }
  const zapisz = () => { try { localStorage.setItem('trendo', JSON.stringify(st)); } catch (e) { /* tryb prywatny */ } };

  /* ---------- pomocnicze ---------- */
  const zl = (n) => (typeof n === 'number' && isFinite(n) ? n : 0).toLocaleString('pl-PL', { minimumFractionDigits: n % 1 ? 2 : 0, maximumFractionDigits: 2 }) + ' zł';
  const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const API = (() => { try { return localStorage.getItem('trendo-api'); } catch (e) { return null; } })() || 'https://188-68-247-201.sslip.io/trendo-api';
  let wynik = null; // ostatni prawdziwy wynik z serwera
  try { wynik = JSON.parse(sessionStorage.getItem('trendo-wynik') || 'null'); } catch (e) { wynik = null; }
  const OKZ = { damskie: null, meskie: null }; // okazje dnia z serwera: { czas, lista, trwa, blad }
  const OKZ_ID = {};
  // Ten sam produkt może być w ostatnim wyniku, w zapamiętanych i w okazjach: bierzemy najświeżej sprawdzony.
  const prod = (id) => DEMO.P.find((p) => p.id === id) || [wynik && wynik.produkty.find((p) => p.id === id), (st.znane || {})[id], OKZ_ID[id], STYL_ID[id]]
    .filter(Boolean).sort((a, b) => (b.sprawdzono || 0) - (a.sprawdzono || 0))[0];
  function zapamietaj(p) {
    if (!p || !p.zrodlo) return;
    st.znane = st.znane || {}; st.znane[p.id] = p;
    const k = Object.keys(st.znane);
    if (k.length > 300) { const chron = idsHistorii(); k.slice(0, k.length - 300).forEach((x) => { if (!st.koszyk.includes(x) && !st.ulubione.includes(x) && !chron.has(x)) delete st.znane[x]; }); }
  }
  const prawdziwy = (p) => !!(p && p.zrodlo);

  /* ---------- historia (0.20.0, prośba użytkownika): oglądane produkty, wyszukiwania i stylizacje, tylko na tym telefonie ---------- */
  const HIST = () => (st.hist = Object.assign({ produkty: [], szukania: [], styl: [] }, st.hist || {}));
  const idsHistorii = () => new Set(HIST().produkty.map((x) => x.id).concat(...HIST().styl.map((e) => ((e.m || {}).el || []).map((x) => x.id))));
  function kiedyTemu(t) {
    const m = Math.round((Date.now() - t) / 60000);
    if (m < 2) return 'przed chwilą';
    if (m < 60) return m + ' min temu';
    if (m < 24 * 60) return Math.round(m / 60) + ' godz. temu';
    if (m < 48 * 60) return 'wczoraj';
    return new Date(t).toLocaleDateString('pl-PL', { day: 'numeric', month: 'long' });
  }
  function dopiszOgladany(p) {
    if (!prawdziwy(p)) return;
    const h = HIST(), byl = h.produkty.find((x) => x.id === p.id);
    h.produkty = [{ id: p.id, t: Date.now(), cena: byl ? byl.cena : p.cena }].concat(h.produkty.filter((x) => x.id !== p.id)).slice(0, 30);
    zapamietaj(p); zapisz();
  }
  function dopiszSzukanie(q) {
    const h = HIST();
    h.szukania = [{ q, dzial: st.dzial, b1: st.b1, t: Date.now(), n: null }].concat(h.szukania.filter((x) => !(x.q.toLowerCase() === q.toLowerCase() && x.dzial === st.dzial))).slice(0, 20);
  }
  let zapisStylT;
  function zapiszStylHistorie(teraz) {
    clearTimeout(zapisStylT);
    const zrob = () => {
      const d = STYL && STYL.dane; if (!d) return;
      const { wyn, suma } = stylWybor(d, stylWidok.tryb, stylWidok.z), P = d.produkty;
      const el = d.miejsca.filter(({ k }) => wyn[k] && wyn[k].id && !wyn[k].s.wyl).map(({ k, nazwa }) => {
        const p = P[wyn[k].id]; zapamietaj(STYL_ID[p.id] || p);
        return { id: p.id, nazwa: p.nazwa, sklep: p.sklep, cena: p.cena, zdjecie: p.zdjecie, slot: nazwa };
      });
      const h = HIST(), byl = h.styl.find((e) => e.k === STYL.klucz);
      const wpis = { k: STYL.klucz, t: Date.now(), przypiety: !!(byl && byl.przypiety),
        p: { dzial: d.dzial, okazja: d.okazja, stylTryb: d.tryb, stylStart: (d.baza && d.baza.id) || null, stylQ: d.baza && !d.baza.id ? d.baza.nazwa : '', rozm: rozmSwiata() },
        widok: Object.assign({}, stylWidok), wyb: JSON.parse(JSON.stringify(stylWyb)),
        m: { baza: d.baza, el, zestaw: d.tryby[stylWidok.tryb].zestawy[stylWidok.z].nazwa, sklep: stylWidok.tryb === 'sklep' ? d.tryby.sklep.sklep : '',
          suma: Math.round((suma + (d.baza && d.baza.cena ? d.baza.cena : 0)) * 100) / 100 } };
      const reszta = h.styl.filter((e) => e.k !== STYL.klucz);
      const przyp = reszta.filter((e) => e.przypiety), zwykle = reszta.filter((e) => !e.przypiety);
      h.styl = [wpis].concat(przyp, zwykle.slice(0, wpis.przypiety ? 20 : 19)).sort((a, b) => b.t - a.t);
      zapisz();
    };
    if (teraz) zrob(); else zapisStylT = setTimeout(zrob, 500);
  }
  let stylDoPrzywrocenia = null;
  function odswiezHistorie() {
    const ids = HIST().produkty.map((x) => x.id).filter((id) => prawdziwy(prod(id)));
    if (!ids.length) return;
    fetch(`${API}/produkty?ids=${ids.map(encodeURIComponent).join(',')}`).then((r) => r.json()).then((d) => {
      const P = d.produkty || {};
      let zmiana = false;
      Object.keys(P).forEach((id) => {
        const s0 = st.znane[id]; if (!s0) return;
        if (s0.cena !== P[id].cena || s0.brak_w_sklepie !== P[id].brak_w_sklepie) zmiana = true;
        st.znane[id] = Object.assign({}, s0, P[id]);
      });
      if (zmiana) { zapisz(); odswiezJesliNa(['historia', 'start']); }
    }).catch(() => {});
  }
  const viaGoogle = (p) => !!(p && p.zrodlo === 'google' && /google\./.test(p.url || ''));
  const rabat = (p) => (p.stara ? Math.round((1 - p.cena / p.stara) * 100) : 0);
  const demoZnak = () => `<div class="demo">${IK.info.replace('<svg', '<svg width="15" height="15"')}Wersja próbna: dane przykładowe</div>`;
  const sezon = () => {
    const d = new Date(), m = d.getMonth() + 1, r = d.getFullYear();
    if (m >= 9) return { nazwa: 'Jesień–zima', rok: `${r}/${String(r + 1).slice(2)}`, plik: 'sezon-jz' };
    if (m <= 2) return { nazwa: 'Jesień–zima', rok: `${r - 1}/${String(r).slice(2)}`, plik: 'sezon-jz' };
    return { nazwa: 'Wiosna–lato', rok: String(r), plik: 'sezon-wl' };
  };
  function komunikat(t) {
    KOM.textContent = t; KOM.classList.add('widac');
    clearTimeout(komunikat.t); komunikat.t = setTimeout(() => KOM.classList.remove('widac'), 3200);
  }
  /* ---------- okazje dnia, obserwowane i alerty (dane z serwera) ---------- */
  const trasa = () => location.hash.replace(/^#\/?/, '').split('/')[0] || 'start';
  const odswiezJesliNa = (ekrany) => { if (ekrany.includes(trasa()) && ARK.hidden) render(true); };
  function wczytajOkazje(dz) {
    const o = OKZ[dz];
    if (o && (o.trwa || Date.now() - o.czas < 15 * 60e3)) return;
    OKZ[dz] = { czas: Date.now(), trwa: true, lista: o ? o.lista : null };
    fetch(`${API}/okazje?dzial=${dz}`).then((r) => r.json()).then((d) => {
      const l = Array.isArray(d.okazje) ? d.okazje : [];
      l.forEach((p) => { OKZ_ID[p.id] = p; });
      OKZ[dz] = { czas: Date.now(), lista: l };
      odswiezJesliNa(['start', 'okazje']);
    }).catch(() => { OKZ[dz] = { czas: Date.now(), lista: (o && o.lista) || [], blad: true }; odswiezJesliNa(['start', 'okazje']); });
  }
  const obserwowaneIds = () => [...new Set(st.ulubione.concat(st.alerty.map((a) => a.id)))].filter((id) => prawdziwy(prod(id)));
  function zglosObserwowane(ids) {
    ids = (ids || obserwowaneIds()).filter((id) => prawdziwy(prod(id)));
    if (ids.length) fetch(`${API}/obserwuj?ids=${ids.map(encodeURIComponent).join(',')}`).catch(() => {});
  }
  function powiadom(p) {
    const tresc = { body: `${p.nazwa} (${p.sklep}) kosztuje teraz ${zl(p.cena)}.`, icon: 'icons/icon-192.png', tag: 'trendo-' + p.id };
    try {
      if (!('Notification' in window) || Notification.permission !== 'granted') return;
      if (navigator.serviceWorker && navigator.serviceWorker.controller) navigator.serviceWorker.ready.then((r) => r.showNotification('Cena spadła', tresc)).catch(() => {});
      else new Notification('Cena spadła', tresc);
    } catch (e) { /* przeglądarka bez powiadomień */ }
  }
  let sprawdzonoObs = 0;
  function odswiezObserwowane(wymus) {
    const ids = obserwowaneIds();
    if (!ids.length || (!wymus && Date.now() - sprawdzonoObs < 10 * 60e3)) return;
    sprawdzonoObs = Date.now();
    fetch(`${API}/produkty?ids=${ids.map(encodeURIComponent).join(',')}`).then((r) => r.json()).then((d) => {
      const P = d.produkty || {};
      let zmiana = false;
      Object.keys(P).forEach((id) => {
        const s0 = st.znane[id], n = P[id];
        if (!s0) return;
        if (s0.cena !== n.cena || s0.stara !== n.stara || s0.weryf !== n.weryf || s0.brak_w_sklepie !== n.brak_w_sklepie) zmiana = true;
        st.znane[id] = Object.assign({}, s0, n);
      });
      const spadki = [];
      st.alerty.forEach((a) => {
        const p = st.znane[a.id];
        if (!p) return;
        if (p.cena <= a.cel && !a.osiagniety) { a.osiagniety = Date.now(); spadki.push(p); zmiana = true; }
        if (p.cena > a.cel && a.osiagniety) { a.osiagniety = null; zmiana = true; }
      });
      if (spadki.length) {
        komunikat(spadki.length === 1 ? `Cena spadła: ${spadki[0].nazwa}, teraz ${zl(spadki[0].cena)}` : `Cena spadła w ${spadki.length} obserwowanych rzeczach`);
        spadki.forEach(powiadom);
      }
      if (zmiana) { zapisz(); odswiezJesliNa(['start', 'alerty', 'okazje', 'koszyk', 'produkt']); }
    }).catch(() => {});
  }
  const foto = (p) => (p.zdjecie ? `<img class="zdj" src="${esc(p.zdjecie)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="TrendoBezZdjecia(this)">`
    : p.img ? `<img src="img/wzorce/${p.img}.webp" alt="" loading="lazy" decoding="async">`
    : p.k ? G.ubranie(p.typ, p.k[0], p.k[1]) : `<span style="color:var(--szary2);width:40%">${IK.wieszak}</span>`);
  const ikonaW = (n, w) => IK[n].replace('<svg', `<svg width="${w}" height="${w}"`);

  /* ---------- menu ---------- */
  function rysujMenu(akt) {
    const ile = st.koszyk.length;
    const poz = (h, n, ik, nazwa) => `<a href="#/${h}" ${akt === h ? 'aria-current="page"' : ''}>${IK[ik]}${nazwa}${h === 'koszyk' && ile ? `<span class="ukryj">, ${ile} w koszyku</span>` : ''}</a>`;
    MENU.innerHTML =
      poz('start', 0, 'dom', 'Start') + poz('trendy', 0, 'trend', 'Trendy') +
      `<a href="#/szukaj" class="srodek" aria-label="Nowe wyszukiwanie" ${akt === 'szukaj' ? 'aria-current="page"' : ''}><span class="moneta"><img src="icons/icon-192.png" alt=""></span></a>` +
      poz('okazje', 0, 'okazje', 'Okazje') + poz('koszyk', 0, 'torba', ile ? `Zakupy (${ile})` : 'Zakupy');
  }

  /* ---------- ekrany ---------- */
  const EKRANY = {};

  const SLAJDY = [
    ['img/hero.jpg', 'Moda\nTrendy\nStylizacje\nZakupy', 'Znajdzie to, czego szukasz, w dziesiątkach sklepów, sprawdzi, czy promocja jest prawdziwa, i dobierze resztę stylizacji zgodnie z trendami.'],
    ['img/powitanie-2.jpg', 'Prawdziwe\npromocje', 'Szukamy w wielu sklepach naraz i porównujemy każdą obniżkę z najniższą ceną z 30 dni. Pozorne promocje oznaczamy od razu.'],
    ['img/powitanie-3.jpg', 'Trendy\nna każdą\nokazję', 'Trendy z magazynów i raportów, każdy potwierdzony w co najmniej dwóch niezależnych źródłach. Dla kobiet i mężczyzn, na co dzień i na wielkie wyjścia.']
  ];
  EKRANY.witaj = () => ({
    klasa: 'pelny', menu: false,
    html: `<section class="powitanie">
      <div class="slajdy" id="slajdy">${SLAJDY.map(([foto, h, p], i) => `<div class="slajd" aria-label="Slajd ${i + 1} z ${SLAJDY.length}">
        <div class="powitanie-foto" style="--foto:url('${foto}')"></div>
        <div class="powitanie-tresc${i ? '' : ' wejscie'}"><h1>${h}</h1><p>${p}</p></div></div>`).join('')}</div>
      <div class="powitanie-znak">Trendo</div>
      <div class="powitanie-dol">
        <button class="btn" data-akcja="witajDalej" id="witaj-btn">Dalej ${IK.dalej}</button>
        <div class="wybor-swiata" id="wybor-swiata" style="display:none"><button class="btn" data-akcja="zacznijSwiat" data-v="damskie">Dla niej</button><button class="btn drugi" data-akcja="zacznijSwiat" data-v="meskie">Dla niego</button></div>
        <div class="kropki" role="tablist" aria-label="Slajdy">${SLAJDY.map((_, i) => `<button role="tab" aria-label="Slajd ${i + 1}" data-akcja="witajSlajd" data-i="${i}" class="${i ? '' : 'tak'}"></button>`).join('')}</div>
      </div></section>`,
    po: () => {
      const sl = document.getElementById('slajdy');
      const nr = () => Math.round(sl.scrollLeft / sl.clientWidth);
      sl.addEventListener('scroll', () => {
        const i = nr();
        document.querySelectorAll('.kropki button').forEach((k, j) => k.classList.toggle('tak', j === i));
        const ost = i === SLAJDY.length - 1;
        document.getElementById('witaj-btn').style.display = ost ? 'none' : '';
        document.getElementById('wybor-swiata').style.display = ost ? 'grid' : 'none';
      }, { passive: true });
    }
  });

  EKRANY.start = () => {
    const g = new Date().getHours();
    const pow = g < 5 ? 'Dobry wieczór' : g < 18 ? 'Dzień dobry' : 'Dobry wieczór';
    const s = sezon();
    const przyp = HIST().styl.filter((e) => e.przypiety);
    const ogl = HIST().produkty.map((x) => prod(x.id)).filter((p) => prawdziwy(p)).slice(0, 10);
    const ost = st.ostatnie.slice(0, 6);
    const spadly = st.alerty.filter((a) => a.osiagniety).length;
    return {
      akt: 'start',
      html: `<div class="powitanie-dnia">
        <div><p class="szary maly">${pow}</p><h1>Czego dziś<br>szukasz?</h1></div>
        <div class="akcje">
          <a class="ikonka" href="#/historia" aria-label="Historia: oglądane, wyszukiwania, stylizacje">${IK.zegar}</a>
          <a class="ikonka" href="#/alerty" aria-label="Alerty cenowe${st.alerty.length ? ', ' + st.alerty.length : ''}${spadly ? ', cena spadła w ' + spadly : ''}">${IK.dzwonek}${spadly ? '<span class="kropka"></span>' : ''}</a>
          <a class="ikonka" href="#/profil" aria-label="Profil i ustawienia">${IK.profil}</a>
        </div></div>
      <a href="#/szukaj" class="pole-szukaj" style="text-decoration:none">${IK.szukaj}<span style="flex:1;color:var(--szary2);font-size:17px">Np. skórzane spodnie, płaszcz…</span><span class="ikonka" aria-hidden="true">${IK.aparat}</span></a>
      <div class="tryby wejscia">
        <a class="tryb" href="#/szukaj"><img class="tryb-ikona" src="img/ikony/tryb-rzecz.webp" alt="">Jedna rzecz</a>
        <a class="tryb" href="#/komponuj" data-akcja="wejscieStyl" data-v="outfit"><img class="tryb-ikona" src="img/ikony/tryb-outfit.webp" alt="">Cały outfit</a>
        <a class="tryb" href="#/komponuj" data-akcja="wejscieStyl" data-v="dodatki"><img class="tryb-ikona" src="img/ikony/tryb-dodatki.webp" alt="">Dodatki</a>
        <button class="tryb" data-akcja="zdjecie"><img class="tryb-ikona" src="img/ikony/tryb-zdjecie.webp" alt="">Ze zdjęcia</button>
      </div>
      <input type="file" id="plik" accept="image/*" hidden>
      <div class="sekcja" style="margin-top:22px"><div class="sekcja-tytul"><h2>Kategorie</h2>
        <div class="przelacznik" role="radiogroup" aria-label="Dział" style="width:190px;padding:3px"><button role="radio" style="height:32px;font-size:13.5px" aria-checked="${st.dzial === 'damskie'}" data-akcja="dzial" data-v="damskie">Damskie</button><button role="radio" style="height:32px;font-size:13.5px" aria-checked="${st.dzial === 'meskie'}" data-akcja="dzial" data-v="meskie">Męskie</button></div></div>
        <div class="karuzela kategorie">${kategorie(st.dzial).map((k) => `<button class="kategoria" data-akcja="kategoria" data-q="${esc(k.zapytanie)}"><span class="kat-foto"><img src="img/wzorce/${k.id}.webp" alt="" loading="lazy"></span><span>${esc(k.katNazwa)}</span></button>`).join('')}</div></div>
      ${ost.length ? `<div class="sekcja" style="margin-top:16px"><div class="chipy">${ost.map((q) => `<button class="chip" data-akcja="szukajOstatnie" data-q="${esc(q)}">${esc(q)}</button>`).join('')}</div></div>` : ''}

      <div class="sekcja">
        <a href="#/trendy" class="okladka" style="--foto:url('${obrazSwiata(s.plik + '.jpg')}');text-decoration:none;color:var(--tekst)">
          <div><p class="maly" style="color:var(--tekst2);margin:0 0 6px">Raport trendów</p><h2>${s.nazwa}<br>${s.rok}</h2><p>Co jest teraz w modzie i dokąd to zmierza.</p></div>
        </a>
      </div>

      ${ogl.length ? `<div class="sekcja"><div class="sekcja-tytul"><h2>Ostatnio oglądane</h2><a class="link" href="#/historia" data-akcja="histTab" data-v="produkty">Historia</a></div>
        <div class="karuzela">${ogl.map((p) => `<a class="mini-produkt" href="#/produkt/${p.id}"><span class="foto">${foto(p)}</span><span class="sklep">${esc(p.sklep)}</span><span class="nazwa">${esc(p.nazwa)}</span><b>${zl(p.cena)}</b></a>`).join('')}</div></div>` : ''}

      ${przyp.length ? `<div class="sekcja"><div class="sekcja-tytul"><h2>Zapisane stylizacje</h2></div><div class="elementy">${przyp.map(kartaHistStyl).join('')}</div></div>` : ''}

      ${sekcjaOkazjiDnia()}`,
      po: () => { wczytajOkazje(st.dzial); odswiezObserwowane(); }
    };
  };

  /* Droga 1: szukam konkretnej rzeczy. Wyniki zawsze pełne; cena to jedyny filtr ustawiany tutaj (można go zdjąć w wynikach). */
  const OKAZJE_LISTA = [['codzien', 'Na co dzień'], ['smartcasual', 'Smart casual'], ['praca', 'Do pracy'], ['randka', 'Randka'], ['wesele', 'Wesele'], ['wieczor', 'Wieczór'], ['sylwester', 'Sylwester'], ['wyjazd', 'Wyjazd']];
  const NAZWA_OKAZJI = Object.fromEntries(OKAZJE_LISTA);
  const BEZ_LIMITU = 3000;
  const opisCeny = (v) => (v >= BEZ_LIMITU ? 'bez limitu' : 'do ' + zl(v));
  EKRANY.szukaj = () => {
    const p1 = (Math.min(st.b1, BEZ_LIMITU) - 30) / (BEZ_LIMITU - 30) * 100;
    return {
      akt: 'szukaj',
      html: `<div class="naglowek"><a class="ikonka bez" href="#/start" aria-label="Wróć">${IK.wstecz}</a><h1>Szukaj rzeczy</h1><span class="puste"></span></div>
      <h2 class="wejscie" style="font-size:34px;margin:4px 0 16px">Czego szukasz?</h2>
      <label class="ukryj" for="q">Czego szukasz</label>
      <div class="pole-szukaj">${IK.szukaj}<input id="q" value="${esc(st.zapytanie)}" placeholder="Np. czarne skórzane spodnie" autocomplete="off" enterkeyhint="search">
        <button class="ikonka" data-akcja="zdjecie" aria-label="Szukaj ze zdjęcia">${IK.aparat}</button></div>

      <div class="przelacznik" role="radiogroup" aria-label="Dział" style="margin-top:14px">
        <button role="radio" aria-checked="${st.dzial === 'damskie'}" data-akcja="dzial" data-v="damskie">Damskie</button>
        <button role="radio" aria-checked="${st.dzial === 'meskie'}" data-akcja="dzial" data-v="meskie">Męskie</button>
      </div>

      <div class="sekcja" style="margin-top:22px">
        <div class="budzet">
          <div class="budzet-wiersz"><div class="budzet-gora"><label for="b1">Maksymalna cena<span class="opis">pokażemy rzeczy do tej kwoty</span></label><span class="budzet-kwota" id="b1v">${opisCeny(st.b1)}</span></div>
            <input id="b1" type="range" min="30" max="${BEZ_LIMITU}" step="10" value="${Math.min(st.b1, BEZ_LIMITU)}" style="--p:${p1}%"></div>
        </div>
        <p class="maly szary" style="margin-top:10px;text-align:center">Przesuń do końca, żeby szukać bez limitu. W wynikach limit możesz zdjąć jednym dotknięciem.</p>
      </div>

      <button class="btn" style="margin-top:20px" data-akcja="szukaj">Szukaj w sklepach ${IK.szukaj}</button>

      <a class="karta-wejscie" href="#/komponuj" data-akcja="wejscieStyl" data-v="outfit">
        <img src="img/ikony/tryb-outfit.webp" alt=""><span><b>Potrzebujesz całej stylizacji?</b><span>Wybierz okazję i budżet na całość, dobierzemy zestaw.</span></span>${IK.dalej}</a>
      <input type="file" id="plik" accept="image/*" hidden>`
    };
  };

  /* Droga 2: stylizacja na okazję. Okazja i budżet na całość mają sens tylko tutaj. */
  EKRANY.komponuj = () => {
    const start = st.stylStart ? prod(st.stylStart) : null;
    const p2 = st.b2 / 5000 * 100;
    return {
      akt: 'szukaj',
      po: () => { const z = document.querySelector('.okazja-kafel[aria-pressed="true"]'); if (z) z.parentElement.scrollLeft = Math.max(0, z.offsetLeft - 20); },
      html: `<div class="naglowek"><a class="ikonka bez" href="#/start" aria-label="Wróć">${IK.wstecz}</a><h1>Stylizacja</h1><span class="puste"></span></div>
      <h2 class="wejscie" style="font-size:34px;margin:4px 0 16px">Na jaką okazję?</h2>
      <div class="przelacznik" role="radiogroup" aria-label="Dział">
        <button role="radio" aria-checked="${st.dzial === 'damskie'}" data-akcja="dzial" data-v="damskie">Damskie</button>
        <button role="radio" aria-checked="${st.dzial === 'meskie'}" data-akcja="dzial" data-v="meskie">Męskie</button>
      </div>
      <div class="sekcja" style="margin-top:18px">
        <div class="karuzela okazje-kafle">${OKAZJE_LISTA.map(([v, n]) => `<button class="okazja-kafel" aria-pressed="${st.okazja === v}" data-akcja="okazja" data-v="${v}"><span class="okazja-foto"><img src="img/okazje/okazja-${st.dzial === 'meskie' ? 'm' : 'd'}-${v}.webp" alt="" loading="lazy"></span><span>${n}</span></button>`).join('')}</div>
      </div>
      <div class="sekcja">
        <p style="margin-bottom:10px;font-size:15px">Co dobieramy</p>
        <div class="przelacznik" role="radiogroup" aria-label="Co dobieramy">
          <button role="radio" aria-checked="${st.stylTryb !== 'dodatki'}" data-akcja="stylTryb" data-v="outfit">Całą stylizację</button>
          <button role="radio" aria-checked="${st.stylTryb === 'dodatki'}" data-akcja="stylTryb" data-v="dodatki">Tylko dodatki</button>
        </div>
      </div>
      <div class="sekcja">
        <p style="margin-bottom:10px;font-size:15px">Od czego zaczynamy <span class="szary maly">(opcjonalnie)</span></p>
        ${start ? `<div class="element start-rzecz"><span class="miniatura">${foto(start)}</span><span class="opis"><span class="maly szary" style="display:block">Zaczynamy od</span><span class="nazwa" style="display:block">${esc(start.nazwa)}</span><span class="sklep">${marka(start.sklep)}</span></span><button class="ikonka bez" data-akcja="bezStartu" aria-label="Usuń">${IK.zamknij}</button></div>`
          : `<div class="pole-szukaj">${IK.wieszak}<input id="qs" value="${esc(st.stylQ || '')}" placeholder="Np. mam czarne skórzane spodnie" autocomplete="off"></div>`}
      </div>
      <button class="btn" style="margin-top:20px" data-akcja="komponuj">Skomponuj stylizacje ${IK.iskra}</button>`
    };
  };

  /* ---------- stylizacje z prawdziwych produktów (0.20.0, wariant B wybrany przez użytkownika) ----------
     Serwer zwraca dla każdego miejsca w zestawie uszeregowanych kandydatów; suwak ceny przy rzeczy podmienia ją na bieżąco
     (najlepiej pasująca rzecz do tej kwoty), suwak całości obniża zestaw tam, gdzie tańszy zamiennik traci najmniej. */
  const STYL_ID = {};
  let STYL = null; // { klucz, dane } albo { klucz, laduje } albo { klucz, blad }
  let stylWidok = { tryb: 'wszystkie', z: 0 };
  const stylWyb = {};
  const STATUS_TRENDU = { szczyt: 'szczyt', rosnie: 'rośnie', nadchodzi: 'nadchodzi', wygasa: 'wygasa' };
  const swiatLit = () => (st.dzial === 'meskie' ? 'm' : 'd');
  const rozmSwiata = () => st.stylRozm || ((st.rozm || {})[swiatLit()] || {});
  function kluczStylizacji() {
    return JSON.stringify([st.dzial, st.okazja, st.stylTryb, st.stylStart || '', st.stylStart ? '' : (st.stylQ || ''), rozmSwiata()]);
  }
  function wczytajStylizacje() {
    const k = kluczStylizacji();
    if (STYL && STYL.klucz === k && !STYL.blad) return;
    STYL = { klucz: k, laduje: true };
    const u = `${API}/stylizacja?dzial=${st.dzial}&okazja=${st.okazja}&tryb=${st.stylTryb}`
      + (st.stylStart ? `&id=${encodeURIComponent(st.stylStart)}` : st.stylQ ? `&q=${encodeURIComponent(st.stylQ)}` : '')
      + `&rozm=${encodeURIComponent(JSON.stringify(rozmSwiata()))}`;
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 180000);
    fetch(u, { signal: ctrl.signal })
      .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
      .then(({ ok, d }) => {
        if (!ok || !d || !d.tryby) throw new Error((d && d.blad) || 'blad');
        Object.values(d.produkty).forEach((p) => { p.sprawdzono = p.sprawdzono || d.sprawdzono; STYL_ID[p.id] = p; });
        Object.keys(stylWyb).forEach((x) => delete stylWyb[x]);
        stylWidok = { tryb: d.tryby.sklep ? 'sklep' : 'wszystkie', z: 0 };
        if (stylDoPrzywrocenia && stylDoPrzywrocenia.k === k) { // stylizacja z historii: ten sam zestaw, suwaki i „Mam już”
          Object.assign(stylWyb, stylDoPrzywrocenia.wyb || {});
          const w = stylDoPrzywrocenia.widok || {};
          if (d.tryby[w.tryb] && d.tryby[w.tryb].zestawy[w.z]) stylWidok = { tryb: w.tryb, z: w.z };
        }
        stylDoPrzywrocenia = null;
        STYL = { klucz: k, dane: d };
        zapiszStylHistorie();
      })
      .catch((e) => {
        STYL = { klucz: k, blad: e.name === 'AbortError' ? 'Składanie trwało za długo. Spróbuj jeszcze raz.'
          : (e.message && !/^blad$|fetch|NetworkError|JSON/i.test(e.message) ? e.message : 'Serwer nie odpowiada. Spróbuj za chwilę.') };
      })
      .finally(() => { clearTimeout(t); if (location.hash === '#/stylizacje') render(); });
  }
  function stylStan(tr, z) { const k = tr + '|' + z; return stylWyb[k] || (stylWyb[k] = { sloty: {}, suma: null }); }
  function stylWybor(d, tr, z) {
    const Z = d.tryby[tr].zestawy[z], S = stylStan(tr, z), P = d.produkty, wyn = {};
    d.miejsca.forEach(({ k }) => {
      const ids = (Z.sloty[k] || []).filter((id) => P[id]);
      if (!ids.length) return;
      const s = S.sloty[k] || (S.sloty[k] = { limit: null, skok: 0, wyl: false });
      const dost = ids.filter((id) => s.limit == null || P[id].cena <= s.limit + 0.001);
      wyn[k] = { ids, dost, id: dost.length ? dost[s.skok % dost.length] : null, s };
    });
    const suma = () => Object.values(wyn).reduce((a, w) => a + (w.id && !w.s.wyl ? P[w.id].cena : 0), 0);
    let ponad = false;
    if (S.suma != null) {
      for (let g = 0; g < 80 && suma() > S.suma + 0.001; g++) {
        let naj = null;
        Object.entries(wyn).forEach(([k, w]) => {
          if (!w.id || w.s.wyl) return;
          const c = P[w.id].cena, i = w.dost.indexOf(w.id), j = w.dost.findIndex((id) => P[id].cena < c - 0.001);
          if (j >= 0 && (!naj || j - i < naj.strata)) naj = { k, j, strata: j - i };
        });
        if (!naj) { ponad = true; break; }
        wyn[naj.k].id = wyn[naj.k].dost[naj.j];
      }
    }
    return { wyn, suma: suma(), ponad };
  }
  const stylCeny = (ids, P) => [...new Set(ids.map((id) => P[id].cena))].sort((a, b) => a - b);
  function stylPlansza(d, tr, z) {
    const { wyn, suma } = stylWybor(d, tr, z), P = d.produkty, Z = d.tryby[tr].zestawy[z];
    const kafle = [];
    if (d.baza && d.baza.zdjecie) kafle.push({ p: d.baza, et: 'Twoja rzecz', baza: true });
    d.miejsca.forEach(({ k, nazwa }) => { const w = wyn[k]; if (w && w.id) kafle.push({ p: P[w.id], et: nazwa, wyl: w.s.wyl }); });
    const sklepy = new Set(kafle.filter((x) => !x.baza && !x.wyl).map((x) => x.p.sklep));
    const zBaza = d.baza && d.baza.cena && d.baza.zdjecie ? d.baza.cena : 0;
    // pierwsza rzecz (Twoja albo pierwsza dobrana) na dwa rzędy; gdy zostałoby puste pole, ostatnia na całą szerokość
    const n = kafle.length, duza = n >= 3, szeroka = duza ? (n + 1) % 2 === 1 : n === 1;
    return `<div class="plansza${duza ? ' duza' : ''}${szeroka ? ' szeroka' : ''}" data-z="${z}">
      <img class="plansza-tlo" src="img/stylizacja/plansza-${swiatLit()}.webp" alt="">
      <div class="plansza-siatka">${kafle.map((x) => `<a class="kafel${x.baza ? ' baza' : ''}${x.wyl ? ' wyl' : ''}" href="#/produkt/${x.p.id || ''}" ${x.baza && !x.p.id ? 'onclick="return false"' : ''}>${foto(x.p)}<span class="metka">${esc(x.et)}</span></a>`).join('')}</div>
      <div class="plansza-podpis"><div><small>Zestaw ${z + 1} z ${d.tryby[tr].zestawy.length}</small><h2>${esc(Z.nazwa)}</h2></div>
        <div style="text-align:right"><small>${sklepy.size === 1 ? '1 sklep' : sklepy.size + ' sklepy'}</small><b>${zl(Math.round((suma + zBaza) * 100) / 100)}</b></div></div></div>`;
  }
  function stylWiersz(d, k, nazwa, w, tr) {
    const p = d.produkty[w.id], ceny = stylCeny(w.ids, d.produkty), n = ceny.length;
    const v = w.s.limit == null ? n : Math.max(0, ceny.indexOf(w.s.limit));
    return `<div class="styl-el${w.s.wyl ? ' wyl' : ''}" id="se-${k}">
      <div class="styl-tresc">${stylTresc(p, nazwa, w)}</div>
      <div class="styl-suwak"><span id="sl-${k}">${w.s.limit == null ? 'Bez limitu' : 'Do <b>' + zl(w.s.limit) + '</b>'}</span>
        <input type="range" class="suwak-rzeczy" data-k="${k}" min="0" max="${n}" step="1" value="${v}" style="--p:${n ? v / n * 100 : 100}%" aria-label="Cena: ${esc(nazwa)}"></div>
      <div class="styl-akcje"><button class="link" data-akcja="stylInna" data-k="${k}">${IK.iskra.replace('<svg', '<svg width="14" height="14"')} Inna propozycja</button>
        <button class="mam" data-akcja="stylWl" data-k="${k}" aria-pressed="${!w.s.wyl}"><span>${w.s.wyl ? 'Mam już' : 'Uwzględnij'}</span><i class="przel"></i></button></div>
    </div>`;
  }
  function stylTresc(p, nazwa, w) {
    if (!p) return `<div class="tx"><span class="slot">${esc(nazwa)}</span><p class="szary" style="margin:6px 0 0;font-size:14px">Nic w tej cenie. Przesuń suwak w prawo.</p></div>`;
    const r = rabat(p);
    return `<a class="fot" href="#/produkt/${p.id}">${foto(p)}${r ? `<span class="rabat">−${r}%</span>` : ''}</a>
      <div class="tx"><span class="slot">${esc(nazwa)}</span>
        <a class="nazwa" href="#/produkt/${p.id}">${esc(p.nazwa)}</a>
        <span class="sklep">${marka(p.sklep)}</span>
        <span class="ceny"><span class="cena">${zl(p.cena)}</span>${p.stara ? `<span class="stara">${zl(p.stara)}</span>` : ''}</span>
        ${p.trend ? `<a class="znacz-trend" href="#/trendy">W trendzie: ${esc(p.trend.nazwa)} · ${STATUS_TRENDU[p.trend.status] || esc(p.trend.status)}</a>` : `<span class="powod">${esc(p.powod || '')}</span>`}
        ${p.rozmiar_ok == null ? '<span class="maly szary" style="display:block;margin-top:4px">Rozmiar sprawdź w sklepie</span>' : ''}</div>`;
  }
  function stylBraki(d, tr) {
    const T = d.tryby[tr], br = T.braki || {}, sk = T.sklep;
    return d.miejsca.filter(({ k }) => br[k]).map(({ k, nazwa }) => {
      const msg = tr === 'sklep'
        ? (br[k] === 'rozmiar' ? `W ${esc(sk)} nie ma tego w Twoim rozmiarze.` : `${esc(sk)} nie ma rzeczy, która pasuje do tego zestawu.`)
        : (br[k] === 'rozmiar' ? 'Nie znaleźliśmy pasującej rzeczy w Twoim rozmiarze.' : 'Nie znaleźliśmy pasującej rzeczy na tę okazję.');
      return `<div class="styl-brak"><img src="img/stylizacja/brak-${swiatLit()}.webp" alt=""><div><b>${esc(nazwa)}</b><p>${msg}</p>
        ${tr === 'sklep' ? '<button class="link" data-akcja="stylTrybW" data-v="wszystkie">Pokaż ze wszystkich sklepów</button>' : ''}</div></div>`;
    }).join('');
  }
  function stylLista(d) {
    const tr = stylWidok.tryb, z = stylWidok.z, { wyn, ponad } = stylWybor(d, tr, z);
    const S = stylStan(tr, z), P = d.produkty;
    const wiersze = d.miejsca.filter(({ k }) => wyn[k]).map(({ k, nazwa }) => stylWiersz(d, k, nazwa, wyn[k], tr)).join('');
    const wl = Object.values(wyn).filter((w) => !w.s.wyl);
    const min = Math.floor(wl.reduce((a, w) => a + Math.min(...w.ids.map((id) => P[id].cena)), 0) / 10) * 10;
    const max = Math.ceil(wl.reduce((a, w) => a + Math.max(...(w.s.limit == null ? w.ids : w.dost).map((id) => P[id].cena)), 0) / 10) * 10 || 10;
    const v = S.suma == null ? max : Math.min(max, Math.max(min, S.suma));
    return wiersze + stylBraki(d, tr) + (wl.length ? `<div class="karta budzet" style="margin-top:14px">
      <div class="budzet-gora"><label for="styl-suma">Budżet na całość<span class="opis">dobierane rzeczy${d.baza && d.baza.cena ? ', bez Twojej' : ''}</span></label>
        <span class="budzet-kwota" id="stv">${S.suma == null ? 'Bez limitu' : '~ ' + zl(S.suma)}</span></div>
      <input id="styl-suma" type="range" min="${min}" max="${max}" step="10" value="${v}" style="--p:${max > min ? (v - min) / (max - min) * 100 : 100}%">
      <p class="maly" id="styl-ponad" style="margin:6px 0 0;color:var(--uwaga)">${ponad ? 'Taniej się nie da w Twoich rozmiarach. Odznacz którąś rzecz albo podnieś budżet.' : ''}</p></div>` : '');
  }
  function stylPasek(d) {
    const { wyn, suma } = stylWybor(d, stylWidok.tryb, stylWidok.z);
    const n = Object.values(wyn).filter((w) => w.id && !w.s.wyl).length + (d.baza && d.baza.id ? 1 : 0);
    const razem = suma + (d.baza && d.baza.cena ? d.baza.cena : 0);
    return `<div class="wnetrze"><div class="razem"><span>Zestaw: ${n} ${n === 1 ? 'rzecz' : n < 5 ? 'rzeczy' : 'rzeczy'}${d.baza && d.baza.cena ? ' z Twoją' : ''}</span><b>${zl(Math.round(razem * 100) / 100)}</b></div>
      <button class="btn maly" data-akcja="stylDoKoszyka">${IK.torba} Do zakupów</button></div>`;
  }
  // znaczki trendów tylko dla rzeczy w oglądanym zestawie
  function stylTrendy(d) {
    const { wyn } = stylWybor(d, stylWidok.tryb, stylWidok.z), byly = {};
    Object.values(wyn).forEach((w) => { const t = w.id && !w.s.wyl && d.produkty[w.id].trend; if (t) byly[t.nazwa] = t; });
    return Object.values(byly).map((t) => `<a href="#/trendy">${esc(t.nazwa)} · ${STATUS_TRENDU[t.status] || esc(t.status)}</a>`).join('');
  }
  function stylOdswiez(cale) {
    const d = STYL && STYL.dane; if (!d) return;
    const tr = stylWidok.tryb;
    const pl = document.querySelector(`.plansza[data-z="${stylWidok.z}"]`);
    if (pl) pl.outerHTML = stylPlansza(d, tr, stylWidok.z);
    document.querySelectorAll('.kropki i').forEach((x, i) => x.classList.toggle('on', i === stylWidok.z));
    if (cale) document.getElementById('styl-lista').innerHTML = stylLista(d);
    const ps = document.getElementById('styl-pasek'); if (ps) ps.innerHTML = stylPasek(d);
    const ts = document.getElementById('styl-trendy'); if (ts) ts.innerHTML = stylTrendy(d);
    zapiszStylHistorie();
    podmienGrafikiSwiata(E);
  }
  const KROKI_STYL = [['Analizuję Twoją rzecz', 'kolor, materiał, styl', 'krok-stylizacje'], ['Szukam w sklepach', 'w rozmiarach z Ustawień', 'krok-sklepy'],
    ['Sprawdzam trendy', 'tylko potwierdzone źródłami', 'krok-trendy'], ['Składam 3 zestawy', 'klasycznie, modnie, odważnie', 'krok-promocje']];

  EKRANY.stylizacje = () => {
    wczytajStylizacje();
    if (STYL.laduje) {
      return {
        menu: false, klasa: 'bez-menu',
        html: `<section class="analiza"><div class="pierscien"><img id="pierscien-img" class="pierscien-przedmiot" src="img/ikony/krok-stylizacje.webp" alt=""></div>
          <h1 style="font-size:34px;font-weight:400">Składam stylizacje…</h1>
          <ol class="kroki" id="kroki">${KROKI_STYL.map(([a, b, ik], i) => `<li data-i="${i}" data-ik="${ik}"><img class="krok-ikona" src="img/ikony/${ik}.webp" alt=""><div><b>${a}</b><span>${b}</span></div><span class="znak"></span></li>`).join('')}</ol>
          <p class="maly szary">Pierwsze złożenie trwa do minuty, następne są od razu.</p></section>`,
        po: () => {
          const li = [...document.querySelectorAll('#kroki li')];
          let i = 0;
          const krok = () => {
            if (location.hash !== '#/stylizacje' || !STYL || !STYL.laduje) return;
            if (i > 0) { li[i - 1].classList.remove('aktywny'); li[i - 1].classList.add('gotowy'); li[i - 1].querySelector('.znak').innerHTML = IK.ok; }
            if (i >= li.length) return;
            li[i].classList.add('aktywny');
            const pi = document.getElementById('pierscien-img');
            if (pi && i) { pi.classList.add('znika'); const nowy = obrazSwiata(`ikony/${li[i].dataset.ik}.webp`); setTimeout(() => { pi.src = nowy; pi.classList.remove('znika'); }, 220); }
            i++;
            if (i < li.length) EKRANY.stylizacje.timer = setTimeout(krok, i === 1 ? 2500 : 9000);
          };
          krok();
        }
      };
    }
    if (STYL.blad) {
      return { akt: 'szukaj', html: `<div class="naglowek"><a class="ikonka bez" href="#/komponuj" aria-label="Wróć">${IK.wstecz}</a><h1>Stylizacja</h1><span class="puste"></span></div>
        <div class="info uwaga">${IK.uwaga}<p>${esc(STYL.blad)}</p></div><button class="btn" style="margin-top:16px" data-akcja="stylPonow">Spróbuj jeszcze raz</button>` };
    }
    const d = STYL.dane, tr = d.tryby[stylWidok.tryb] ? stylWidok.tryb : 'wszystkie';
    stylWidok.tryb = tr;
    const R = rozmSwiata(), opisR = Object.keys(R).filter((k) => R[k]).length
      ? ROZM_POLA[swiatLit()].filter(([k]) => R[k]).slice(0, 3).map(([k, n]) => `${n.split(' (')[0].split(':')[0].toLowerCase()} <b>${esc(R[k])}</b>`).join(' · ')
      : 'nie podano, pokazujemy wszystkie';
    const zestawy = d.tryby[tr].zestawy;
    return {
      akt: 'szukaj',
      po: () => {
        document.body.classList.add('z-paskiem');
        const pl = document.getElementById('plansze');
        if (pl) {
          pl.scrollLeft = stylWidok.z * pl.clientWidth;
          let t;
          pl.addEventListener('scroll', () => {
            clearTimeout(t);
            t = setTimeout(() => { const z = Math.round(pl.scrollLeft / pl.clientWidth); if (z !== stylWidok.z) { stylWidok.z = z; stylOdswiez(true); } }, 120);
          });
        }
      },
      html: `<div class="naglowek"><a class="ikonka bez" href="javascript:history.back()" aria-label="Wróć">${IK.wstecz}</a><h1>Stylizacja</h1>${(() => { const e = HIST().styl.find((x) => x.k === STYL.klucz), on = !!(e && e.przypiety); return `<button class="ikonka bez" data-akcja="stylPrzypnij" data-k="${esc(STYL.klucz)}" aria-pressed="${on}" aria-label="${on ? 'Odepnij stylizację' : 'Zapisz stylizację na stałe'}">${on ? IK.sercePelne : IK.serce}</button>`; })()}</div>
      <p class="szary styl-pod">${esc(NAZWA_OKAZJI[d.okazja] || '')}${d.baza ? ' · do: ' + esc(d.baza.nazwa) : ''}</p>
      ${d.opis ? `<div class="styl-hero">${d.baza && d.baza.zdjecie ? `<span class="fot">${foto(d.baza)}</span>` : ''}<p>${esc(d.opis)}</p></div>` : ''}
      <div class="styl-trendy" id="styl-trendy">${stylTrendy(d)}</div>
      <div class="styl-roz"><span>Szukam w rozmiarach: ${opisR}</span><a class="link" href="#/profil">Zmień</a></div>
      ${d.tryby.sklep ? `<div class="styl-filtr"><div class="przelacznik" role="tablist">
        <button role="tab" aria-selected="${tr === 'sklep'}" data-akcja="stylTrybW" data-v="sklep">Tylko ${esc(d.tryby.sklep.sklep)}</button>
        <button role="tab" aria-selected="${tr === 'wszystkie'}" data-akcja="stylTrybW" data-v="wszystkie">Wszystkie sklepy</button></div></div>` : ''}
      <div class="plansze" id="plansze">${zestawy.map((_, z) => stylPlansza(d, tr, z)).join('')}</div>
      <div class="kropki">${zestawy.map((_, z) => `<i class="${z === stylWidok.z ? 'on' : ''}"></i>`).join('')}</div>
      <p class="szary maly" style="margin:10px 2px 0">Przesuń planszę, żeby zobaczyć inne zestawy. Suwak przy rzeczy pokazuje najlepszą propozycję do wybranej kwoty.</p>
      <div id="styl-lista">${stylLista(d)}</div>
      <div style="height:110px"></div>
      <div class="pasek-suma" id="styl-pasek">${stylPasek(d)}</div>`
    };
  };

  EKRANY.analiza = () => {
    const s = sezon();
    const kroki = [
      ['Aktualne trendy', `sezon ${s.nazwa.toLowerCase()} ${s.rok}`, 'krok-trendy'],
      ['Ceny i dostępność w sklepach', 'sklepy internetowe i Google Shopping', 'krok-sklepy'],
      ['Promocje i wyprzedaże', 'porównanie z najniższą ceną z 30 dni', 'krok-promocje'],
      ['Dobór stylizacji i dodatków', 'w ramach Twojego budżetu', 'krok-stylizacje']
    ];
    return {
      menu: false, klasa: 'bez-menu',
      html: `<section class="analiza">
        <div class="pierscien"><img id="pierscien-img" class="pierscien-przedmiot" src="img/ikony/${kroki[0][2]}.webp" alt=""></div>
        <h1 style="font-size:34px;font-weight:400">Analizuję dla Ciebie…</h1>
        <ol class="kroki" id="kroki">${kroki.map(([a, b, ik], i) => `<li data-i="${i}" data-ik="${ik}"><img class="krok-ikona" src="img/ikony/${ik}.webp" alt=""><div><b>${a}</b><span>${b}</span></div><span class="znak"></span></li>`).join('')}</ol>
      </section>`,
      po: () => {
        const li = [...document.querySelectorAll('#kroki li')];
        let i = 0, gotowe = false;
        const ctrl = new AbortController();
        const czas = setTimeout(() => ctrl.abort(), 150000);
        fetch(`${API}/szukaj?q=${encodeURIComponent(st.zapytanie)}&dzial=${st.dzial}`, { signal: ctrl.signal })
          .then((r) => r.json())
          .then((d) => {
            wynik = d && d.produkty ? d : null;
            const h = HIST().szukania.find((x) => x.q === st.zapytanie && x.dzial === st.dzial);
            if (h && wynik) { h.n = wynik.produkty.length; zapisz(); }
          })
          .catch(() => { wynik = null; komunikat('Serwer nie odpowiada. Pokazuję przykład.'); })
          .finally(() => {
            clearTimeout(czas); gotowe = true;
            try { sessionStorage.setItem('trendo-wynik', JSON.stringify(wynik)); } catch (e) { /* pełna pamięć */ }
          });
        const krok = () => {
          if (location.hash !== '#/analiza') return;
          if (i === 2 && !gotowe) { EKRANY.analiza.timer = setTimeout(krok, 300); return; }
          if (i > 0) { li[i - 1].classList.remove('aktywny'); li[i - 1].classList.add('gotowy'); li[i - 1].querySelector('.znak').innerHTML = IK.ok; }
          if (i === li.length) { setTimeout(() => { location.hash = '#/wyniki'; }, 450); return; }
          li[i].classList.add('aktywny');
          const pi = document.getElementById('pierscien-img');
          if (pi && i) { pi.classList.add('znika'); const nowy = obrazSwiata(`ikony/${li[i].dataset.ik}.webp`); setTimeout(() => { pi.src = nowy; pi.classList.remove('znika'); }, 220); }
          i++;
          EKRANY.analiza.timer = setTimeout(krok, 700);
        };
        krok();
      }
    };
  };

  // Filtry wyników (na czas jednego wyszukiwania). Domyślnie widać wszystko, poza limitem ceny ustawionym przy szukaniu.
  let filtrOkazji = 'wszystkie', budzetWl = true, tylkoPromocje = false, tylkoSecond = false, kolejnosc = 'polecane';
  const norm = (x) => (x || '').trim().replace(/\s+/g, ' ').toLowerCase().slice(0, 80);
  EKRANY.wyniki = () => {
    const q = st.zapytanie || 'Skórzane spodnie';
    if (wynik && norm(wynik.zapytanie) === norm(q) && wynik.dzial === st.dzial) return wynikiPrawdziwe(q, wynik);
    return wynikiPrawdziwe(q, { zapytanie: q, dzial: st.dzial, sprawdzono: Date.now() / 1000, sklepy: [], produkty: DEMO.P.filter((p) => p.id.startsWith('p')), demo: true });
  };
  const SECOND = /vinted|olx|allegro lokalnie|sprzedajemy|depop|remixshop/i;
  const uzywany = (p) => SECOND.test(p.sklep) || p.weryf === 'second';
  function siatkaWynikow(lista, q) {
    const dokladne = lista.filter((p) => p.trafnosc !== 1);
    const podobne = lista.filter((p) => p.trafnosc === 1);
    let h = dokladne.length ? `<div class="siatka">${dokladne.map(kartaProduktu).join('')}</div>` : '';
    if (podobne.length) {
      h += `<div class="sekcja-tytul" style="margin:${dokladne.length ? 28 : 4}px 0 12px"><h2>Podobne</h2><span class="maly szary">${podobne.length}</span></div>
        <p class="maly szary" style="margin:-6px 0 14px">Ten sam rodzaj rzeczy, ale nie każde słowo z hasła „${esc(q)}” jest w opisie sklepu.</p>
        <div class="siatka">${podobne.map(kartaProduktu).join('')}</div>`;
    }
    return h;
  }

  function wynikiPrawdziwe(q, W) {
    const P = W.produkty;
    const nowe = P.filter((p) => !uzywany(p)), uzyw = P.filter(uzywany);
    const baza = tylkoSecond ? uzyw : nowe;
    const limit = budzetWl && st.b1 < BEZ_LIMITU ? st.b1 : null;
    const wCenie = limit ? baza.filter((p) => p.cena <= limit) : baza;
    const drozsze = baza.length - wCenie.length;
    let lista = tylkoPromocje ? wCenie.filter((p) => p.stara) : wCenie;
    const przedFiltrem = lista;
    const ocenione = przedFiltrem.filter((p) => Array.isArray(p.okazje));
    const ileNa = (o) => przedFiltrem.filter((p) => (p.okazje || []).includes(o)).length;
    const przedOkazja = przedFiltrem.length;
    if (filtrOkazji !== 'wszystkie') lista = lista.filter((p) => (p.okazje || []).includes(filtrOkazji));
    const promo = (p) => (p.weryf === 'ok' ? 2 : p.stara ? 1 : 0);
    lista = lista.slice().sort(kolejnosc === 'najtaniej' ? (a, b) => a.cena - b.cena : kolejnosc === 'najdrozej' ? (a, b) => b.cena - a.cena
      : (a, b) => promo(b) - promo(a) || a.cena - b.cena);
    const ileSklepow = new Set(P.map((p) => p.sklep)).size;
    const kiedy = new Date(W.sprawdzono * 1000).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
    const uwagi = (W.sklepy || []).filter((x) => x.stan !== 'ok').map((x) => `${x.nazwa}: ${x.stan}`).join(', ');
    const inneDemo = W.demo && norm(q) !== 'skórzane spodnie';
    let komunikaty = '';
    if (limit && !wCenie.length && baza.length) {
      const min = Math.min(...baza.map((p) => p.cena));
      komunikaty += `<div class="info neutral" style="margin-bottom:14px">${IK.info}<p>Do ${zl(limit)} nic nie znaleźliśmy. Najtańsza rzecz kosztuje ${zl(min)}.</p></div>`;
    } else if (filtrOkazji !== 'wszystkie' && !lista.length && przedOkazja) {
      komunikaty += `<div class="info neutral" style="margin-bottom:14px">${IK.info}<p>Żadna z ${przedOkazja} rzeczy nie pasuje na okazję „${NAZWA_OKAZJI[filtrOkazji]}” według naszego kodeksu ubioru (np. skóra i dżins nie na wesele, sportowe rzeczy nie do pracy).</p></div>`;
    }
    if (filtrOkazji !== 'wszystkie' && ocenione.length < przedOkazja) {
      komunikaty += `<p class="maly szary" style="margin:-4px 0 12px">${przedOkazja - ocenione.length} rzeczy czeka jeszcze na ocenę stylisty, więc nie ma ich w tym filtrze.</p>`;
    }
    const pusto = !lista.length && !komunikaty;
    return {
      akt: 'szukaj',
      html: `<div class="naglowek"><a class="ikonka bez" href="#/szukaj" aria-label="Zmień wyszukiwanie">${IK.wstecz}</a><h1>${esc(q)}</h1><span class="puste"></span></div>
      ${W.demo ? demoZnak() : ''}
      ${inneDemo ? `<div class="info uwaga" style="margin-bottom:14px">${IK.uwaga}<p>Serwer nie odpowiedział, więc pokazujemy przykład dla skórzanych spodni.</p></div>` : ''}
      <div class="wyniki-meta"><p class="szary maly">${W.demo ? `${P.length} przykładowych produktów` : `${P.length} produktów z ${ileSklepow} ${ileSklepow === 1 ? 'sklepu' : 'sklepów'}, sprawdzone o ${kiedy}`}${uwagi ? `<br>${esc(uwagi)}` : ''}</p>
        <label class="ukryj" for="kolejnosc">Kolejność</label><select id="kolejnosc" class="kolejnosc">${[['polecane', 'Polecane'], ['najtaniej', 'Najtaniej'], ['najdrozej', 'Najdrożej']].map(([v, n]) => `<option value="${v}" ${kolejnosc === v ? 'selected' : ''}>${n}</option>`).join('')}</select></div>
      <div class="chipy">
        ${st.b1 < BEZ_LIMITU ? `<button class="chip" aria-pressed="${budzetWl}" data-akcja="budzetWl">${budzetWl ? `Do ${zl(st.b1)} ${IK.zamknij.replace('<svg', '<svg width="13" height="13"')}` : `Bez limitu ceny`}</button>` : `<a class="chip" href="#/szukaj">Bez limitu ceny</a>`}
        <button class="chip" aria-pressed="${tylkoPromocje}" data-akcja="tylkoPromocje">${ikonaW('okazje', 14)} Tylko promocje</button>
        ${uzyw.length ? `<button class="chip" aria-pressed="${tylkoSecond}" data-akcja="tylkoSecond">${ikonaW('second', 15)} Z drugiej ręki <span class="ile">${uzyw.length}</span></button>` : ''}
      </div>
      ${ocenione.length ? `<p class="maly szary" style="margin:12px 0 6px">Pasuje na okazję</p>
      <div class="chipy">
        <button class="chip" aria-pressed="${filtrOkazji === 'wszystkie'}" data-akcja="filtrOkazji" data-v="wszystkie">Wszystkie <span class="ile">${przedOkazja}</span></button>
        ${OKAZJE_LISTA.map(([v, n]) => `<button class="chip${ileNa(v) ? '' : ' wyblakly'}" aria-pressed="${filtrOkazji === v}" data-akcja="filtrOkazji" data-v="${v}">${n} <span class="ile">${ileNa(v)}</span></button>`).join('')}
      </div>` : ''}
      <div style="height:14px"></div>
      ${komunikaty}
      ${lista.length ? siatkaWynikow(lista, q) : pusto ? `<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/${tylkoPromocje ? 'pusty-okazje' : 'pusty-wyniki'}.webp" alt=""><p>${tylkoSecond ? 'Tym razem nie znaleźliśmy ogłoszeń z drugiej ręki.' : tylkoPromocje ? 'Brak promocji w tej grupie. Wyłącz filtr, żeby zobaczyć wszystko.' : 'Nic nie znaleźliśmy. Spróbuj innego hasła.'}</p></div>` : ''}
      ${limit && drozsze ? `<button class="btn drugi" style="margin-top:22px" data-akcja="budzetWl">Pokaż też droższe: ${drozsze} ${drozsze === 1 ? 'rzecz' : 'rzeczy'} powyżej ${zl(limit)}</button>` : ''}`
    };
  }


  EKRANY.stylizacja = (id) => {
    const s = DEMO.S.find((x) => x.id === id) || DEMO.S[0];
    const el = s.el.map(prod);
    const suma = el.reduce((a, p) => a + p.cena, 0);
    const plan = st.b2;
    const roznica = suma - plan;
    const zapisana = st.zapisane.includes(s.id);
    return {
      akt: 'szukaj', po: () => document.body.classList.add('z-paskiem'),
      html: `<div class="naglowek"><a class="ikonka bez" href="#/stylizacje" aria-label="Wróć do stylizacji">${IK.wstecz}</a><h1>Stylizacja ${esc(s.nazwa.toLowerCase())}</h1>
        <button class="ikonka bez" data-akcja="zapiszStyl" data-id="${s.id}" aria-label="${zapisana ? 'Usuń z zapisanych' : 'Zapisz stylizację'}" aria-pressed="${zapisana}">${zapisana ? IK.sercePelne : IK.serce}</button></div>
      ${demoZnak()}
      <div class="kolaz wejscie" style="height:380px;border-radius:26px;border:1px solid var(--linia2)">${kolaz(s)}</div>
      <p class="szary" style="margin:12px 2px 4px">${esc(s.opis)}</p>
      <div class="sekcja" style="margin-top:14px"><div class="sekcja-tytul"><h2>Elementy (${el.length})</h2></div>
        <div class="elementy">${el.map(wierszElementu).join('')}</div></div>
      <div class="sekcja"><div class="sekcja-tytul"><h2>Dlaczego ten zestaw</h2></div>
        <ul class="dlaczego">${s.dlaczego.map((t) => `<li>${esc(t)}</li>`).join('')}</ul>
        <a class="zrodlo-chip" href="#/trendy">${ikonaW('trend', 14)} Trendy i źródła</a></div>
      <div class="info neutral" style="margin-top:20px">${IK.info}<p>${roznica > 0 ? `Zestaw jest o ${zl(Math.round(roznica * 100) / 100)} droższy niż Twój plan (${zl(plan)}).` : `Mieścisz się w planie (${zl(plan)}), zostaje ${zl(Math.round(-roznica * 100) / 100)}.`}</p></div>
      <div style="height:96px"></div>
      <div class="pasek-suma"><div class="wnetrze"><div class="razem"><span>Cały outfit (${el.length} elementów)</span><b>~ ${zl(Math.round(suma * 100) / 100)}</b></div>
        <button class="btn maly" data-akcja="doKoszyka" data-id="${s.id}">${IK.torba} Do koszyka</button></div></div>`
    };
  };

  /* Rozmiary od sklepów przychodzą jako lista, obiekt {"1":"M"} albo napis. Zawsze robimy z nich listę napisów. */
  function listaRozmiarow(r) {
    if (!r) return [];
    if (typeof r === 'string') r = r.split(/[,;/|]/);
    else if (!Array.isArray(r) && typeof r === 'object') r = Object.values(r);
    if (!Array.isArray(r)) return [];
    const w = [];
    r.forEach((x) => { if (x && typeof x === 'object') x = x.name || x.label || x.size || x.value; x = String(x == null ? '' : x).trim(); if (x && !w.includes(x)) w.push(x); });
    return w;
  }
  /* ---------- rozmiarówka: tabela ze strony produktu albo ogólna tabela sklepu, na szkicu rzeczy ---------- */
  const ROZM = {}; // id produktu -> odpowiedź serwera (albo { laduje } / { blad })
  let SZKICE = null;
  function wczytajRozmiarowke(p) {
    const odswiez = () => { const k = document.getElementById('rozm'); if (k && location.hash.includes(p.id)) k.innerHTML = kartaRozmiarowki(p, ROZM[p.id]); };
    if (!SZKICE) fetch('data/szkice-rozmiarow.json?v=' + WERSJA).then((r) => r.json()).then((d) => { SZKICE = d; odswiez(); }).catch(() => { SZKICE = {}; });
    if (!prawdziwy(p) || ROZM[p.id]) return;
    ROZM[p.id] = { laduje: true };
    fetch(`${API}/rozmiary?id=${encodeURIComponent(p.id)}`).then((r) => r.json()).then((d) => { ROZM[p.id] = d; })
      .catch(() => { ROZM[p.id] = { blad: true }; }).finally(odswiez);
  }
  const normR = (x) => String(x || '').toUpperCase().replace(/\s+/g, '').replace(',', '.');
  // Czy rozmiar z tabeli (np. „XS/34”, z odpowiednikami w innych wierszach) to ten sam co rozmiar sklepu („34”)?
  function zgodnyRozmiar(t, i, r) {
    const n = normR(r), etyk = [t.rozmiary[i]].concat((t.aliasy || []).map((a) => a.rozmiary[i]));
    return etyk.some((e) => normR(e) === n || normR(e).split('/').includes(n) || normR(e).split('-').includes(n));
  }
  const SZKIC_RODZAJ = {
    d: { koszula: 'bluzka', bluzka: 'bluzka', top: 'bluzka', 't-shirt': 'bluzka', polo: 'bluzka', sweter: 'sweter', kardigan: 'sweter', bluza: 'sweter',
      sukienka: 'sukienka', kombinezon: 'sukienka', 'spódnica': 'spodnica', spodnie: 'spodnie', jeansy: 'spodnie', szorty: 'spodnie', legginsy: 'spodnie',
      marynarka: 'marynarka', kamizelka: 'marynarka', garnitur: 'marynarka', kurtka: 'plaszcz', 'płaszcz': 'plaszcz' },
    m: { koszula: 'koszula', 't-shirt': 'tshirt', polo: 'tshirt', top: 'tshirt', sweter: 'sweter', kardigan: 'sweter', bluza: 'sweter', marynarka: 'marynarka',
      garnitur: 'marynarka', kamizelka: 'marynarka', kurtka: 'plaszcz', 'płaszcz': 'plaszcz', spodnie: 'spodnie', szorty: 'spodnie', dres: 'spodnie', jeansy: 'jeansy' }
  };
  const SLOWA_SZKICU = [[/sukien/, 'sukienka'], [/spódnic/, 'spodnica'], [/jeans/, 'jeansy'], [/spodni|szort|chino/, 'spodnie'], [/marynark|garnitur|kamizel/, 'marynarka'],
    [/płaszcz|kurtk|parka|trencz/, 'plaszcz'], [/swet|kardigan|bluza|golf/, 'sweter'], [/t-shirt|koszulk|polo/, 'tshirt'], [/koszul|bluzk|top/, 'koszula']];
  function szkicProduktu(p, d) {
    const pl = d && d.dzial === 'meskie' || (!d && (p.plec_sklepu || p.dzial || st.dzial) === 'meskie') ? 'm' : 'd';
    if (d && d.grupa === 'buty') return pl + (pl === 'm' ? '-but' : '-botek');
    let x = SZKIC_RODZAJ[pl][(p.klasa || {}).r || (d || {}).rodzaj];
    if (!x) { const n = (p.nazwa || '').toLowerCase(); const t = SLOWA_SZKICU.find(([re]) => re.test(n)); x = t && t[1]; }
    if (x === 'jeansy' && pl === 'd') x = 'spodnie';
    if (x === 'koszula' && pl === 'd') x = 'bluzka';
    if (x === 'tshirt' && pl === 'd') x = 'bluzka';
    if (x === 'spodnica' && pl === 'm') x = 'spodnie';
    if (x === 'sukienka' && pl === 'm') x = null;
    if (!x) x = d && (d.grupa === 'dol' || d.grupa === 'jeansy') ? (pl === 'm' ? 'spodnie' : 'spodnie') : (pl === 'm' ? 'koszula' : 'bluzka');
    return pl + '-' + x;
  }
  const liczbaPl = (v) => String(Math.round(v * 10) / 10).replace('.', ',');
  const cm = (w) => (w ? (w.length > 1 ? `${liczbaPl(w[0])}–${liczbaPl(w[1])}` : liczbaPl(w[0])) + ' cm' : '–');
  const NAZWY_POM = { biust: 'Biust', klatka: 'Klatka', talia: 'Talia', biodra: 'Biodra', nogawka: 'Nogawka', stopa: 'Stopa', wkladka: 'Wkładka' };
  const czystaNazwa = (n) => {
    let t = String(n || '').replace(/^\[\d+\]\s*|^[A-Z]\s*-\s*|\s*[([]\s*(cm|CM)\s*[)\]]|\*|:$/g, '').replace(/\s+/g, ' ').trim();
    if (t === t.toUpperCase()) t = t.toLowerCase();
    return t.replace(/^./, (c) => c.toUpperCase());
  };
  function kroj(nazwa) {
    const n = (nazwa || '').toLowerCase();
    if (/oversize|relaxed|loose|boxy|luźn/.test(n)) return 'luźny (oversize)';
    if (/slim|skinny|dopasowan|fitted|taliowan/.test(n)) return 'dopasowany (slim)';
    if (/regular|straight|prosty|klasyczn/.test(n)) return 'regularny';
    return null;
  }
  function kartaRozmiarowki(p, d) {
    const rp = listaRozmiarow(p.rozmiary);
    const naglowek = (prawa) => `<div class="rozm-gora"><b>Rozmiarówka</b>${prawa ? `<span class="maly szary">${prawa}</span>` : ''}</div>`;
    const chipy = (lista) => `<div class="rozmiary">${lista.map(({ r, et, ok, wyb }) => `<button aria-pressed="${!!wyb}" ${ok ? '' : `class="niedostepny" aria-label="${esc(et || r)}, niedostępny"`} data-akcja="rozmiar" data-id="${p.id}" data-v="${esc(r)}">${esc(et || r)}</button>`).join('')}</div>`;
    if (!prawdziwy(p)) return naglowek() + (rp.length ? chipy(rp.map((r) => ({ r, ok: !(p.brak || []).includes(r), wyb: st.rozmiar[p.id] === r }))) : '');
    if (!d || d.laduje) return naglowek() + (rp.length ? chipy(rp.map((r) => ({ r, ok: true, wyb: st.rozmiar[p.id] === r }))) : '') + '<p class="maly szary" style="margin:12px 0 0">Sprawdzam tabelę rozmiarów…</p>';
    const t = d.tabela;
    if (!t || !t.rozmiary || !t.rozmiary.length) {
      const pow = p.uzywany ? 'Rozmiar podał sprzedający. Ogłoszenia z drugiej ręki nie mają tabeli rozmiarów.' : d.blad ? 'Tabela rozmiarów chwilowo niedostępna.' : 'Sklep nie podaje tabeli rozmiarów, którą możemy odczytać.';
      return naglowek() + (rp.length ? chipy(rp.map((r) => ({ r, ok: true, wyb: st.rozmiar[p.id] === r }))) : '')
        + `<p class="maly szary" style="margin:12px 0 0">${pow}${p.uzywany ? '' : ` <a class="link" href="${esc(p.url)}" target="_blank" rel="noopener">Sprawdź w sklepie</a>`}</p>`;
    }
    // sam przelicznik (Showroom): rozmiar uniwersalny i jego odpowiedniki, bez centymetrów
    if (t.rodzaj === 'przelicznik') {
      let wi = Math.max(0, t.rozmiary.findIndex((r) => normR(r) === normR(st.rozmiar[p.id])));
      if (!st.rozmiar[p.id]) wi = Math.max(0, t.rozmiary.findIndex((r) => normR(r) === 'M'));
      const odp = (t.aliasy || []).filter((a) => a.rozmiary[wi]).map((a) => `${esc(a.nazwa)} <b>${esc(a.rozmiary[wi])}</b>`).join('<span class="szary"> · </span>');
      return naglowek() + chipy(t.rozmiary.map((r, i) => ({ r, ok: true, wyb: i === wi })))
        + `<p class="rozm-odp">${odp}</p>`
        + (rp.length ? `<p class="maly" style="margin:8px 0 0"><span class="szary">Rozmiary w sklepie:</span> ${rp.map(esc).join(', ')}</p>` : '')
        + `<p class="maly szary" style="margin:10px 0 0">Sklep podaje tylko przelicznik rozmiarów, bez wymiarów w cm. Marki w Showroom mają różne rozmiarówki. ${d.zrodlo_url ? `<a class="link" href="${esc(d.zrodlo_url)}" target="_blank" rel="noopener">Źródło</a>` : ''}</p>`;
    }
    // kolumny tabeli i dostępność według rozmiarów sklepu
    const dostT = !rp.length && t.dostepne && t.dostepne.length ? t.dostepne : null;
    const kol = t.rozmiary.map((r, i) => ({ r, i, ok: dostT ? dostT.includes(r) : !rp.length || rp.some((x) => zgodnyRozmiar(t, i, x)) }));
    const pozaTabela = rp.filter((x) => !t.rozmiary.some((_, i) => zgodnyRozmiar(t, i, x)));
    const zapisany = st.rozmiar[p.id];
    let wi = kol.findIndex((k) => zapisany && (normR(k.r) === normR(zapisany) || zgodnyRozmiar(t, k.i, zapisany)));
    const G = t.grupy && t.grupy.lista && t.grupy.lista.length > 1 ? t.grupy : null;
    // grupa rozmiaru: podana przez serwer albo część przed „/” („176-182/41” → „176-182”)
    const grupaR = (r) => { const i = t.rozmiary.indexOf(r); return G && G.klucze ? G.klucze[i] : String(r).split('/')[0]; };
    const krotka = (r) => { const i = t.rozmiary.indexOf(r); return G && G.etykiety ? G.etykiety[i] : String(r).slice(grupaR(r).length + 1); };
    if (wi < 0) {
      const gr = G ? G.lista[Math.floor((G.lista.length - 1) / 2)] : null;
      const dost = kol.filter((k) => k.ok && (!gr || grupaR(k.r) === gr)), wszystkie = kol.filter((k) => !gr || grupaR(k.r) === gr);
      const m = dost.find((k) => /^M$|^38$|^50$|^41$/.test(normR(k.r).split('/').pop()) || /^M$|^38$/.test(normR(k.r).split('/')[0]));
      wi = (m || dost[Math.floor((dost.length - 1) / 2)] || wszystkie[0] || kol[0]).i;
    }
    // koszule i garnitury z grupą wzrostu: najpierw wzrost, potem rozmiar w tej grupie
    const grWyb = G ? grupaR(t.rozmiary[wi]) : null;
    const lista = kol.filter((k) => !G || grupaR(k.r) === grWyb).map((k) => ({ r: k.r, et: G ? krotka(k.r) : k.r, ok: k.ok, wyb: k.i === wi }))
      .concat(G ? [] : pozaTabela.map((r) => ({ r, ok: true, wyb: zapisany === r })));
    const wierszGrup = G ? `<div class="rozm-grupy"><span class="maly szary">${esc(G.nazwa)}</span>${G.lista.map((g) => {
      const reszta = krotka(t.rozmiary[wi]);
      const cel = t.rozmiary.find((r) => grupaR(r) === g && krotka(r) === reszta) || t.rozmiary.find((r) => grupaR(r) === g && kol[t.rozmiary.indexOf(r)].ok) || t.rozmiary.find((r) => grupaR(r) === g);
      return `<button aria-pressed="${g === grWyb}" data-akcja="rozmiar" data-id="${p.id}" data-v="${esc(cel)}">${esc(g.replace('-', '–'))}${/^\d/.test(g) ? ' cm' : ''}</button>`;
    }).join('')}</div>` : '';
    // szkic z liniami pomiarów
    const nazwaSz = szkicProduktu(p, d), sz = SZKICE && SZKICE[nazwaSz];
    const W = t.wymiary || {}, rysowane = new Set();
    const wartosc = (k) => { const z = W[k]; return z ? z.wartosci[wi] : null; };
    let linie = '';
    const poziome = [];
    if (sz) {
      Object.entries(sz.poziome || {}).forEach(([k, [y, x0, x1]]) => {
        const klucze = k === 'biust' || k === 'klatka' ? ['biust', 'klatka'] : k === 'stopa' ? ['wkladka', 'stopa'] : [k];
        const kk = klucze.find((x) => W[x] && wartosc(x)); if (!kk) return;
        rysowane.add(kk);
        const nazwa = t.rodzaj === 'rzecz' ? esc(czystaNazwa(W[kk].nazwa)) : kk === 'klatka' && nazwaSz.startsWith('d') ? 'Biust' : kk === 'biust' && nazwaSz.startsWith('m') ? 'Klatka' : kk === 'wkladka' ? 'Długość wkładki' : kk === 'stopa' ? 'Długość stopy' : NAZWY_POM[kk];
        poziome.push({ y, x0, x1, html: `${nazwa} <b>${cm(wartosc(kk))}</b>` });
      });
      // etykieta nad linią, a gdy zachodziłaby na poprzednią, pod linią (wysokość etykiety ok. 9% szkicu)
      let dol = -1;
      poziome.sort((a, b) => a.y - b.y).forEach((l) => {
        const nad = l.y - 0.1 >= dol;
        dol = nad ? l.y : l.y + 0.1;
        linie += `<div class="pom-linia" style="top:${l.y * 100}%;left:${l.x0 * 100}%;width:${(l.x1 - l.x0) * 100}%"><span class="pom-et${nad ? '' : ' pod'}">${l.html}</span></div>`;
      });
      Object.entries(sz.pionowe || {}).forEach(([k, [x, y0, y1]]) => {
        const klucze = k === 'stopa' ? ['wkladka', 'stopa'] : [k];
        const kk = klucze.find((z) => W[z] && wartosc(z)); if (!kk) return;
        rysowane.add(kk);
        linie += `<div class="pom-pion" style="left:${x * 100}%;top:${y0 * 100}%;height:${(y1 - y0) * 100}%"><span class="pom-et">${kk === 'nogawka' ? 'Nogawka' : 'Długość'} <b>${cm(wartosc(kk))}</b></span></div>`;
      });
    }
    const reszta = Object.entries(W).filter(([k]) => !rysowane.has(k)).map(([, v]) => v).concat(t.inne || [])
      .filter((v) => v.wartosci[wi]).map((v) => `<div><span class="szary">${esc(czystaNazwa(v.nazwa))}</span><b>${cm(v.wartosci[wi])}</b></div>`).join('');
    const k = kroj(p.nazwa);
    const jakie = t.rodzaj === 'rzecz' ? 'wymiary ubrania mierzone na płasko' : 'wymiary ciała';
    const opis = d.zrodlo === 'produkt' ? `Tabela dla tego produktu${d.nazwa_tabeli ? ' (' + esc(d.nazwa_tabeli.charAt(0).toLowerCase() + d.nazwa_tabeli.slice(1)) + ')' : ''}, ${jakie}`
      : `Ogólna tabela sklepu${d.nazwa_tabeli ? ': ' + esc(d.nazwa_tabeli.toLowerCase()) : ''}, ${jakie}`;
    const kiedy = d.sprawdzono ? `, sprawdzona ${new Date(d.sprawdzono).toLocaleDateString('pl-PL')}` : '';
    return naglowek('w cm') + wierszGrup + chipy(lista)
      + (rp.length || dostT ? '' : '<p class="maly szary" style="margin:8px 0 0">Dostępność rozmiarów sprawdzisz w sklepie.</p>')
      + (sz ? `<div class="pom-szkic" style="aspect-ratio:${sz.w}/${sz.h}"><img src="img/rozmiary/${nazwaSz}.webp" alt="">${linie}</div>` : '')
      + (reszta ? `<div class="pom-lista">${reszta}</div>` : '')
      + (k ? `<p class="maly" style="margin:10px 0 0">Krój: <b style="font-weight:500">${k}</b> <span class="szary">(z nazwy produktu)</span></p>` : '')
      + `<p class="maly szary" style="margin:10px 0 0">${opis}${kiedy}. ${d.zrodlo_url ? `<a class="link" href="${esc(d.zrodlo_url)}" target="_blank" rel="noopener">Źródło</a>` : ''}</p>`;
  }

  EKRANY.produkt = (id) => {
    const p = prod(id) || DEMO.P[0];
    dopiszOgladany(p);
    const r = rabat(p);
    const ul = st.ulubione.includes(p.id);
    const alert = st.alerty.find((a) => a.id === p.id);
    let werInfo = '';
    if (p.weryf === 'ok') werInfo = `<div class="info ok">${IK.ok}<p><b>Obniżka jest prawdziwa.</b> ${p.omnibus ? `Najniższa cena z 30 dni przed obniżką: ${zl(p.omnibus)}.` : 'Przez ostatnie 30 dni sprawdzaliśmy cenę sami i była wyższa niż teraz.'}${p.stara_sklepu ? ` Sklep podaje cenę regularną ${zl(p.stara_sklepu)}, ale rabat liczymy uczciwie, od najniższej ceny z 30 dni.` : ''}</p></div>`;
    else if (p.weryf === 'pozorna') werInfo = `<div class="info uwaga">${IK.uwaga}<p><b>Promocja pozorna.</b> ${p.omnibus ? `Przez ostatnie 30 dni produkt kosztował tyle samo (${zl(p.omnibus)}).` : 'Przez ostatnie 30 dni produkt kosztował tyle samo albo mniej.'} Przekreślona cena nie była aktualna.</p></div>`;
    else if (p.weryf === 'second') werInfo = `<div class="info neutral">${IK.info}<p>Ogłoszenie z drugiej ręki. Stan i opis podaje sprzedający, sprawdź zdjęcia przed zakupem.</p></div>`;
    else if (p.weryf === 'sklep') werInfo = `<div class="info neutral">${IK.info}<p><b>Obniżkę podaje sklep</b> (wcześniej ${zl(p.stara)}). Historię ceny tego produktu zbieramy od ${new Date(p.sprawdzono * 1000).toLocaleDateString('pl-PL')}. Po 30 dniach ocenimy, czy obniżka jest prawdziwa.</p></div>`;
    if (p.weryf === 'pozorna' && prawdziwy(p)) werInfo = `<div class="info uwaga">${IK.uwaga}<p><b>Promocja pozorna.</b> ${p.omnibus ? `Najniższa cena z 30 dni przed obniżką, podana przez sklep, to ${zl(p.omnibus)}, czyli tyle samo albo mniej niż teraz.` : 'W ostatnich 30 dniach ten produkt kosztował już tyle samo albo mniej.'} Przekreślona cena nie była aktualna.</p></div>`;
    return {
      akt: 'szukaj', menu: false, klasa: 'bez-menu',
      po: () => {
        const wc = document.querySelector('#hist .wykres-ceny'); if (wc) G.podpnijWykresCeny(wc, zl);
        wczytajRozmiarowke(p);
        if (!prawdziwy(p)) return;
        fetch(`${API}/historia?id=${encodeURIComponent(p.id)}`).then((r) => r.json()).then((d) => {
          const el = document.getElementById('hist'); if (!el) return;
          const c = (d.ceny || []).filter((x) => Date.now() / 1000 - x[1] < 31 * 86400);
          if (c.length >= 2 && (c[c.length - 1][1] - c[0][1]) > 86400) {
            el.innerHTML = G.wykresCeny(c, zl);
            G.podpnijWykresCeny(el.querySelector('.wykres-ceny'), zl);
            document.getElementById('hist-opis').textContent = c.every((x) => x[0] === c[0][0]) ? 'bez zmian' : 'zmieniała się';
          } else {
            el.innerHTML = `<p class="maly szary">Historię ceny tego produktu zbieramy od ${new Date((c[0] ? c[0][1] : p.sprawdzono) * 1000).toLocaleDateString('pl-PL')}. Wykres pojawi się po kilku dniach${p.omnibus || p.weryf === 'ok' || p.weryf === 'pozorna' ? '' : ', a nasza ocena promocji po 30 dniach'}.</p>`;
          }
        }).catch(() => { const el = document.getElementById('hist'); if (el) el.innerHTML = '<p class="maly szary">Historia ceny chwilowo niedostępna.</p>'; });
      },
      html: `<div class="produkt-foto">
        <div class="gora"><button class="ikonka" data-akcja="wstecz" aria-label="Wróć">${IK.wstecz}</button>
          <button class="ikonka" data-akcja="ulubiony" data-id="${p.id}" aria-pressed="${ul}" aria-label="${ul ? 'Usuń z obserwowanych' : 'Obserwuj produkt'}">${ul ? IK.sercePelne : IK.serce}</button></div>
        ${p.zdjecie ? `<img class="zdj-duze wejscie" src="${esc(p.zdjecie)}" alt="${esc(p.nazwa)}" referrerpolicy="no-referrer">`
          : `<div class="wejscie" style="width:56%;height:66%;display:flex;align-items:center;justify-content:center;filter:drop-shadow(0 22px 28px rgba(0,0,0,.6))">${foto(p)}</div>`}
      </div>
      <div class="produkt-tresc">
        ${prawdziwy(p) ? '' : demoZnak()}
        <div style="display:flex;justify-content:space-between;align-items:center"><b style="font-weight:500;display:flex;align-items:center">${marka(p.sklep, 'l')}</b><a class="link" href="${p.url}" target="_blank" rel="noopener" ${viaGoogle(p) ? `data-akcja="doSklepu" data-id="${p.id}"` : ''}>Otwórz w sklepie ${ikonaW('link', 15)}</a></div>
        <h1 style="font-size:30px;margin-top:-8px">${esc(p.nazwa)}</h1>
        <div class="ceny"><span class="cena" style="font-size:38px">${zl(p.cena)}</span>${p.stara ? `<span class="stara" style="font-size:16px">${zl(p.stara)}</span><span class="rabat">−${r}%</span>` : ''}</div>
        ${werInfo}
        <div class="karta rozmiarowka" id="rozm">${kartaRozmiarowki(p, ROZM[p.id])}</div>
        ${Array.isArray(p.okazje) ? `<div class="pasuje-na"><b>Pasuje na</b>${p.okazje.length ? `<div class="pasuje-lista">${OKAZJE_LISTA.filter(([v]) => p.okazje.includes(v)).map(([v, n]) => `<span class="pasuje-kafel"><img src="img/okazje/okazja-${st.dzial === 'meskie' ? 'm' : 'd'}-${v}.webp" alt="">${n}</span>`).join('')}</div>` : '<p class="maly szary">Według naszego kodeksu ubioru to rzecz poza okazjami z listy (np. sportowa albo domowa).</p>'}</div>` : ''}
        <div class="karta"><div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px"><b style="font-weight:500">Cena przez 30 dni</b><span class="maly szary" id="hist-opis">${p.historia ? (p.historia.every((v) => v === p.historia[0]) ? 'bez zmian' : 'zmieniała się') : ''}</span></div>
          <div id="hist">${p.historia ? G.wykresCeny(p.historia.map((v, i) => [v, Date.now() / 1000 - (p.historia.length - 1 - i) * 86400]), zl) : '<p class="maly szary">Sprawdzam historię ceny…</p>'}</div></div>
        <div style="display:flex;flex-direction:column;gap:10px;margin-top:4px">
          <a class="btn" href="${p.url}" target="_blank" rel="noopener" ${viaGoogle(p) ? `data-akcja="doSklepu" data-id="${p.id}"` : ''}>Kup w sklepie ${esc(p.sklep)}</a>
          ${viaGoogle(p) ? '<p class="maly szary" style="margin:-4px 2px 0">Ten produkt znaleźliśmy przez Google Shopping. Po dotknięciu wyszukamy jego stronę w sklepie.</p>' : ''}
          <button class="btn drugi" data-akcja="alert" data-id="${p.id}">${IK.dzwonek} ${alert ? `Alert ustawiony: ${zl(alert.cel)}` : 'Powiadom, gdy stanieje'}</button>
          <button class="btn drugi" data-akcja="dodajProdukt" data-id="${p.id}">${IK.torba} ${st.koszyk.includes(p.id) ? 'Jest w zakupach' : 'Dodaj do zakupów'}</button>
          <a class="btn drugi" href="#/komponuj" data-akcja="dobierzDo" data-id="${p.id}">${IK.iskra} Dobierz stylizację</a>
          ${prawdziwy(p) ? `<button class="link zglos" data-akcja="niePasuje" data-id="${p.id}">${IK.uwaga.replace('<svg', '<svg width="16" height="16"')}<span>Nie pasuje? Zgłoś</span></button>` : ''}
        </div>
      </div>`
    };
  };

  let dzialTrendow = null, filtrTrendow = 'wszystkie';
  const trendyDane = {}, trendyLaduje = {};
  /* Grafiki trendów: tylko te przypisane ręcznie do konkretnego trendu (img/trendy/mapa.json), bez zgadywania po kategorii. */
  let mapaGrafik = null;
  const kluczTrendu = (s) => (s || '').toLowerCase().replace(/ł/g, 'l').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  function grafikaKafla(t, d) {
    if (!mapaGrafik) return null;
    const m = mapaGrafik[d === 'meskie' ? 'm' : 'd'] || {};
    return m[kluczTrendu(t.nazwa)] || (t.kategoria === 'wzor' && t.wzor && ((mapaGrafik.cechy || {}).wzor || {})[t.wzor]) || null;
  }
  function pobierzTrendy(d) {
    if (!mapaGrafik) fetch('img/trendy/mapa.json?v=' + WERSJA).then((r) => r.json()).then((m) => { mapaGrafik = m; if (location.hash.startsWith('#/trendy')) render(); }).catch(() => { mapaGrafik = {}; });
    if (trendyDane[d] || trendyLaduje[d]) return;
    trendyLaduje[d] = true;
    fetch(`${API}/trendy?dzial=${d}`).then((r) => r.json()).then((x) => { trendyDane[d] = x; })
      .catch(() => { trendyDane[d] = { blad: true, trendy: [] }; })
      .finally(() => { trendyLaduje[d] = false; if (location.hash.startsWith('#/trendy')) render(); });
  }
  /* Ile tygodni naprawdę zbieramy dane o trendach (wcześniej: brak danych, nie zero). */
  function tygodnieDanych(t) {
    if (t.tygodni_danych) return t.tygodni_danych;
    const w = t.wzmianek_w_tygodniach || [], i = w.findIndex((x) => x > 0);
    return i < 0 ? 1 : w.length - i;
  }
  // Co da się uczciwie narysować: udział w nowościach sklepów albo liczba wzmianek, od 3 tygodni danych.
  function seriaTrendu(t) {
    const n = tygodnieDanych(t);
    const rynek = (t.seria || []).slice(-n);
    if (rynek.filter((v) => v != null).length >= 3) return { wart: rynek, opis: `udział ${String(t.udzial).replace('.', ',')}%`, rodzaj: 'rynek' };
    const wzm = (t.wzmianek_w_tygodniach || []).slice(-n);
    if (n >= 3 && wzm.some((v) => v > 0)) return { wart: wzm, opis: `${wzm[wzm.length - 1]} wzm. w tyg.`, rodzaj: 'wzmianki' };
    return null;
  }
  function grafikaTrendu(t, kol) {
    const s = seriaTrendu(t);
    if (!s) return `<div class="grafika-trendu"><img class="medalion" src="img/status/${['rosnie', 'nadchodzi', 'szczyt', 'wygasa'].includes(t.status) ? t.status : 'szczyt'}.webp" alt="" width="58" height="58" loading="lazy"></div>`;
    return `<div class="grafika-trendu">${G.wykresTrendu(s.wart, kol)}<span>${s.opis}</span></div>`;
  }
  function arkuszZrodel(i) {
    const d = dzialTrendow || st.dzial;
    const t = ((trendyDane[d] || {}).trendy || [])[i]; if (!t) return;
    ARK.innerHTML = `<div class="panel" role="dialog" aria-modal="true" aria-labelledby="ark-t"><div class="uchwyt"></div>
      <h2 id="ark-t">${esc(t.nazwa)}</h2><p class="szary" style="margin:6px 0 14px">${esc(t.opis)}</p>
      <div style="display:flex;flex-direction:column;gap:10px">${t.linki.map((l) => `<a class="karta" style="display:block;text-decoration:none;color:var(--tekst)" href="${esc(l.url)}" target="_blank" rel="noopener"><b style="font-weight:500">${esc(l.wydawca)}</b><span class="maly szary" style="display:block;margin-top:4px">${esc(l.tytul || 'Raport')} · ${new Date(l.data * 1000).toLocaleDateString('pl-PL')}</span></a>`).join('')}</div>
      ${(() => {
        const sr = seriaTrendu(t), kol = ({ rosnie: '#9ED9B4', szczyt: '#FBE3D8', wygasa: '#F3BE7E', nadchodzi: '#C9B8F0' })[t.status] || '#EBBBA7';
        if (!sr) return `<p class="maly szary" style="margin:14px 0 0">Wykres popularności pojawi się po 3 tygodniach obserwacji. Teraz mamy ${tygodnieDanych(t) === 1 ? 'pierwszy tydzień' : tygodnieDanych(t) + ' tygodnie'} danych.</p>`;
        return `<div class="karta" style="margin-top:14px"><b style="font-weight:500;font-size:14px">${sr.rodzaj === 'rynek' ? 'Udział w nowościach sklepów' : 'Wzmianki w źródłach'}, tydzień po tygodniu</b>
          <div style="margin-top:10px">${G.wykresTrendu(sr.wart, kol, { w: 300, h: 96, os: true })}</div>
          <p class="maly szary" style="margin:8px 0 0">${sr.rodzaj === 'rynek' ? `Liczymy sami: ${t.proba} produktów z naszych sklepów z ostatnich 4 tygodni.` : 'Liczba artykułów o tym trendzie w kolejnych tygodniach.'}</p></div>`;
      })()}
      <button class="btn" style="margin-top:16px" data-akcja="szukajTrendu" data-q="${esc(t.haslo)}">Znajdź w sklepach</button>
      <button class="link" style="margin:10px auto 0;display:flex" data-akcja="zamknijArkusz">Zamknij</button></div>`;
    ARK.hidden = false;
  }
  EKRANY.trendy = () => {
    const d = dzialTrendow || st.dzial;
    const s = sezon();
    pobierzTrendy(d);
    const dane = trendyDane[d];
    const prawdziwe = dane && dane.trendy && dane.trendy.length;
    let lista = prawdziwe ? dane.trendy.map((t, i) => Object.assign({ i }, t)) : [];
    if (filtrTrendow !== 'wszystkie') lista = lista.filter((t) => t.status === filtrTrendow);
    const stat = { rosnie: ['gora', 'Rośnie', '#9ED9B4'], szczyt: ['poziom', 'Na szczycie', '#FBE3D8'], wygasa: ['dol', 'Wygasa', '#F3BE7E'], nadchodzi: ['gora', 'Nadchodzi', '#C9B8F0'] };
    return {
      akt: 'trendy',
      html: `<div class="naglowek"><span class="puste"></span><h1>Trendy teraz</h1><span class="puste"></span></div>
      <div class="przelacznik" role="radiogroup" aria-label="Dział">
        <button role="radio" aria-checked="${d === 'damskie'}" data-akcja="dzialTrendow" data-v="damskie">Damskie</button>
        <button role="radio" aria-checked="${d === 'meskie'}" data-akcja="dzialTrendow" data-v="meskie">Męskie</button></div>
      <div class="okladka wejscie" style="--foto:url('${obrazSwiata(s.plik + '.jpg')}');margin-top:14px"><div><p class="maly" style="color:var(--tekst2);margin:0 0 6px">Kluczowe trendy</p><h2>${s.nazwa}<br>${s.rok}</h2></div></div>
      <div class="chipy" style="margin-top:16px">
        ${[['wszystkie', 'Wszystkie'], ['rosnie', 'Rosnące'], ['nadchodzi', 'Nadchodzące'], ['szczyt', 'Na szczycie'], ['wygasa', 'Wygasające']].map(([v, n]) => `<button class="chip" aria-pressed="${filtrTrendow === v}" data-akcja="filtrTrendow" data-v="${v}">${n}</button>`).join('')}</div>
      <div style="margin-top:4px">${!dane ? '<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/pusty-trendy.webp" alt=""><p>Sprawdzam aktualne trendy w źródłach…</p></div>'
        : !prawdziwe ? `<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/pusty-trendy.webp" alt=""><p>${dane.blad ? 'Serwer trendów chwilowo nie odpowiada.' : 'Zbieramy pierwsze potwierdzone trendy. Pokażemy je, gdy napiszą o nich co najmniej dwa niezależne źródła.'}</p></div>`
        : !lista.length ? '<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/pusty-trendy.webp" alt=""><p>W tej grupie nie ma teraz trendów.</p></div>'
        : lista.map((t) => {
          const [ik, nazwa, kol] = stat[t.status] || stat.szczyt;
          return `<div class="trend" style="cursor:pointer" data-akcja="zrodlaTrendu" data-i="${t.i}" role="button" tabindex="0">
          ${(() => { const g = grafikaKafla(t, d); return g ? `<div class="probka"><img src="img/${g}.webp" alt="" loading="lazy"></div>` : '<div class="probka bez-grafiki" aria-hidden="true"><span>T</span></div>'; })()}
          <div class="opis"><h3>${esc(t.nazwa)}</h3><p>${esc(t.opis)}</p>
            <div class="trend-meta"><span class="status ${t.status}">${IK[ik]}${nazwa}</span><span class="zrodla">${t.zrodla} ${t.zrodla < 5 ? 'źródła' : 'źródeł'}${t.polskie ? `, w tym ${t.polskie} polskie` : ''}</span></div></div>
          ${grafikaTrendu(t, kol)}</div>`;
        }).join('')}</div>
      <div class="info neutral" style="margin-top:20px">${IK.info}<p>Trend pokazujemy dopiero, gdy piszą o nim co najmniej dwa niezależne źródła${dane && dane.zrodla ? ` (sprawdzamy: ${dane.zrodla.length} magazynów i raportów, m.in. ${d === 'meskie' ? 'GQ, Esquire, Permanent Style, Tagwalk, Mr Vintage' : 'Lyst Index, Tagwalk, WGSN, Vogue, Elle'})` : ''}. Każdą wzmiankę porównujemy z tekstem artykułu. Udział w nowościach liczymy sami z produktów naszych sklepów. Dotknij trendu, żeby zobaczyć źródła.</p></div>`
    };
  };

  let zakladkaOkazji = 'promocje';
  EKRANY.okazje = () => {
    const o = OKZ[st.dzial];
    const obs = st.ulubione.map(prod).filter(Boolean);
    let tresc;
    if (zakladkaOkazji === 'obserwowane') {
      tresc = obs.length ? `<div class="elementy">${obs.map(wierszElementu).join('')}</div>
        <p class="maly szary" style="margin-top:14px">Ceny obserwowanych rzeczy sprawdzamy w sklepach co 12 godzin.</p>`
        : `<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/pusty-obserwowane.webp" alt=""><p>Dotknij serca przy produkcie, żeby go obserwować. Gdy stanieje, zobaczysz to tutaj.</p><a class="btn maly" href="#/szukaj">Szukaj produktów</a></div>`;
    } else if (!o || (o.trwa && !o.lista)) {
      tresc = '<p class="szary" style="text-align:center;margin-top:30px">Sprawdzam dzisiejsze obniżki…</p>';
    } else if (!o.lista.length) {
      tresc = `<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/pusty-obserwowane.webp" alt=""><p>${o.blad ? 'Serwer nie odpowiada. Spróbuj za chwilę.' : 'Dziś nie znaleźliśmy jeszcze sprawdzonych obniżek. Lista rośnie z każdym wyszukiwaniem i codziennym przeglądem sklepów.'}</p><a class="btn maly" href="#/szukaj">Szukaj produktów</a></div>`;
    } else {
      tresc = `<p class="szary maly" style="margin:0 0 12px">${o.lista.length} sprawdzonych obniżek z ostatnich 48 godzin, od największej.</p>
        <div class="siatka">${o.lista.map(kartaProduktu).join('')}</div>`;
    }
    return {
      akt: 'okazje',
      po: () => { wczytajOkazje(st.dzial); odswiezObserwowane(); },
      html: `<div class="naglowek"><span class="puste"></span><h1>Najlepsze okazje</h1><span class="puste"></span></div>
      <div class="przelacznik" role="tablist" aria-label="Rodzaj okazji">
        ${[['promocje', 'Sprawdzone obniżki'], ['obserwowane', 'Obserwowane']].map(([v, n]) => `<button role="tab" aria-selected="${zakladkaOkazji === v}" data-akcja="zakladkaOkazji" data-v="${v}">${n}</button>`).join('')}</div>
      <div style="margin-top:16px">${tresc}</div>
      ${zakladkaOkazji !== 'obserwowane' ? '<p class="maly szary" style="margin-top:14px">Każdą promocję porównujemy z najniższą ceną z 30 dni przed obniżką (podaną przez sklep albo z naszej historii cen). Rabat liczymy od tej ceny, nie od „ceny regularnej”.</p>' : ''}`
    };
  };

  let histTab = 'produkty';
  function kartaHistStyl(e) {
    const m = e.m || {}, fot = (m.baza && m.baza.zdjecie ? [m.baza] : []).concat(m.el || []).slice(0, 5);
    return `<div class="hist-styl"><a class="hist-styl-gora" href="#/stylizacje" data-akcja="otworzStyl" data-k="${esc(e.k)}">
        <span class="hist-fot">${fot.map((p) => `<span>${foto(p)}</span>`).join('')}</span>
        <span class="opis"><span class="nazwa">${esc(NAZWA_OKAZJI[e.p.okazja] || '')}${m.baza ? ' · do: ' + esc(m.baza.nazwa) : ''}</span>
          <span class="sklep">${esc(m.zestaw || '')}${m.sklep ? ' · ' + esc(m.sklep) : ''} · ${kiedyTemu(e.t)}</span>
          <span class="cena" style="font-size:18px">${zl(m.suma || 0)}</span></span></a>
      <span class="hist-akcje"><button class="ikonka bez" data-akcja="stylPrzypnij" data-k="${esc(e.k)}" aria-pressed="${!!e.przypiety}" aria-label="${e.przypiety ? 'Odepnij' : 'Zapisz na stałe'}">${e.przypiety ? IK.sercePelne : IK.serce}</button>
        <button class="ikonka bez" data-akcja="histUsun" data-v="styl" data-k="${esc(e.k)}" aria-label="Usuń z historii">${IK.zamknij}</button></span></div>`;
  }
  EKRANY.historia = () => {
    const h = HIST(), pusto = (t) => `<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/pusta-historia.webp" alt="" onerror="this.remove()"><p>${t}</p></div>`;
    let tresc = '';
    if (histTab === 'produkty') {
      const L = h.produkty.map((x) => ({ x, p: prod(x.id) })).filter(({ p }) => prawdziwy(p));
      tresc = L.length ? `<div class="elementy">${L.map(({ x, p }) => `<div class="element"><a class="miniatura" href="#/produkt/${p.id}" aria-label="${esc(p.nazwa)}">${foto(p)}</a>
        <a class="opis" href="#/produkt/${p.id}" style="text-decoration:none;color:var(--tekst)"><div class="nazwa">${esc(p.nazwa)}</div><div class="sklep">${esc(p.sklep)} · ${kiedyTemu(x.t)}</div>
        <div class="ceny"><span class="cena" style="font-size:19px">${zl(p.cena)}</span>${x.cena && p.cena < x.cena - 0.01 ? `<span class="maly" style="color:var(--ok);margin-left:8px">taniej o ${zl(Math.round((x.cena - p.cena) * 100) / 100)}</span>` : x.cena && p.cena > x.cena + 0.01 ? `<span class="maly" style="color:var(--uwaga);margin-left:8px">drożej o ${zl(Math.round((p.cena - x.cena) * 100) / 100)}</span>` : ''}${p.brak_w_sklepie ? '<span class="maly" style="color:var(--uwaga);margin-left:8px">zniknęło ze sklepu</span>' : ''}</div></a>
        <button class="ikonka bez" data-akcja="histUsun" data-v="produkty" data-k="${p.id}" aria-label="Usuń z historii">${IK.zamknij}</button></div>`).join('')}</div>`
        : pusto('Tu pojawią się rzeczy, które oglądasz. Wejdź w dowolny produkt, a wrócisz do niego jednym dotknięciem.');
    } else if (histTab === 'szukania') {
      tresc = h.szukania.length ? `<div class="elementy">${h.szukania.map((x, i) => `<div class="element"><span class="miniatura hist-ikona">${IK.szukaj}</span>
        <button class="opis hist-przycisk" data-akcja="histSzukaj" data-i="${i}"><div class="nazwa">${esc(x.q)}</div>
        <div class="sklep">${x.dzial === 'meskie' ? 'Męskie' : 'Damskie'}${x.b1 && x.b1 < BEZ_LIMITU ? ' · do ' + zl(x.b1) : ''}${x.n != null ? ' · ' + x.n + ' wyników' : ''} · ${kiedyTemu(x.t)}</div></button>
        <button class="ikonka bez" data-akcja="histUsun" data-v="szukania" data-k="${i}" aria-label="Usuń z historii">${IK.zamknij}</button></div>`).join('')}</div>`
        : pusto('Tu pojawią się Twoje wyszukiwania. Dotknięcie otworzy wyniki z tymi samymi ustawieniami.');
    } else {
      tresc = h.styl.length ? `<div class="elementy">${h.styl.map(kartaHistStyl).join('')}</div>
        <p class="maly szary" style="margin-top:10px">Serduszko zapisuje stylizację na stałe. Pozostałe trzymamy do 20 ostatnich.</p>`
        : pusto('Tu pojawią się Twoje stylizacje razem z tym, co w nich ustawisz.');
    }
    const ile = histTab === 'styl' ? h.styl.filter((e) => !e.przypiety).length : h[histTab].length;
    return {
      akt: 'start',
      po: () => { if (histTab === 'produkty') odswiezHistorie(); },
      html: `<div class="naglowek"><a class="ikonka bez" href="#/start" aria-label="Wróć">${IK.wstecz}</a><h1>Historia</h1><span class="puste"></span></div>
      <div class="przelacznik trzy" role="tablist" style="margin-bottom:12px">
        <button role="tab" aria-selected="${histTab === 'produkty'}" data-akcja="histTab" data-v="produkty">Oglądane</button>
        <button role="tab" aria-selected="${histTab === 'szukania'}" data-akcja="histTab" data-v="szukania">Szukane</button>
        <button role="tab" aria-selected="${histTab === 'styl'}" data-akcja="histTab" data-v="styl">Stylizacje</button></div>
      ${tresc}
      ${ile ? `<button class="link" style="margin-top:12px" data-akcja="histWyczysc">Wyczyść ${histTab === 'produkty' ? 'oglądane' : histTab === 'szukania' ? 'wyszukiwania' : 'stylizacje (bez zapisanych)'}</button>` : ''}`
    };
  };

  EKRANY.koszyk = () => {
    const el = st.koszyk.map(prod).filter(Boolean);
    if (!el.length) return { akt: 'koszyk', html: `<div class="naglowek"><span class="puste"></span><h1>Zakupy</h1><span class="puste"></span></div><div class="pusty"><img class="ilustracja-pusta" src="img/puste/pusty-koszyk.webp" alt=""><p>Koszyk jest pusty. Dodaj cały zestaw ze stylizacji albo pojedyncze rzeczy.</p><a class="btn maly" href="#/szukaj">Znajdź stylizację</a></div>` };
    const grupy = {};
    el.forEach((p) => { (grupy[p.sklep] = grupy[p.sklep] || []).push(p); });
    let sumaP = 0, sumaD = 0, nieznana = false;
    const html = Object.keys(grupy).map((sk) => {
      const ps = grupy[sk];
      const s = ps.reduce((a, p) => a + p.cena, 0); sumaP += s;
      const d = ps.find((p) => p.dostawa) ? ps.find((p) => p.dostawa).dostawa : (prawdziwy(ps[0]) ? null : { prog: 199, koszt: 12.99 });
      if (!d) nieznana = true;
      const darmo = d && s >= d.prog;
      if (d && !darmo) sumaD += d.koszt;
      return `<section class="grupa" aria-label="${esc(sk)}">
        <div class="grupa-gora"><b style="display:flex;align-items:center;font-weight:500">${marka(sk, 'l')}</b><a class="link" href="${ps[0].sklepUrl || ps[0].url}" target="_blank" rel="noopener" ${viaGoogle(ps[0]) && !ps[0].sklepUrl ? `data-akcja="doSklepu" data-id="${ps[0].id}"` : ''}>Zamów w sklepie ${ikonaW('link', 14)}</a></div>
        ${ps.map((p) => `<div class="element"><a class="miniatura" href="#/produkt/${p.id}" aria-label="${esc(p.nazwa)}">${foto(p)}</a>
          <div class="opis"><div class="nazwa">${esc(p.nazwa)}</div><div class="sklep">${st.rozmiar[p.id] ? 'Rozmiar ' + esc(st.rozmiar[p.id]) : 'Rozmiar wybierzesz w sklepie'}</div>
          <div class="ceny"><span class="cena" style="font-size:19px">${zl(p.cena)}</span>${p.stara ? `<span class="stara">${zl(p.stara)}</span>` : ''}</div></div>
          <button class="ikonka bez" data-akcja="usunZKoszyka" data-id="${p.id}" aria-label="Usuń ${esc(p.nazwa)}">${IK.kosz}</button></div>`).join('')}
        <div class="dostawa">${!d ? '<span>Koszt dostawy poda sklep przy zamówieniu.</span>' : darmo ? `<span style="color:var(--ok)">Darmowa dostawa</span>` : `<div class="pasek"><span style="width:${Math.min(100, s / d.prog * 100)}%"></span></div><span>Do darmowej dostawy brakuje ${zl(Math.round((d.prog - s) * 100) / 100)}. Dostawa ${zl(d.koszt)}.</span>`}</div>
      </section>`;
    }).join('');
    return {
      akt: 'koszyk',
      html: `<div class="naglowek"><span class="puste"></span><h1>Zakupy</h1><span class="puste"></span></div>
      ${el.some((p) => !prawdziwy(p)) ? demoZnak() : ''}
      <p class="szary" style="margin:-4px 0 14px;text-align:center">${el.length} ${el.length === 1 ? 'rzecz' : el.length < 5 ? 'rzeczy' : 'rzeczy'} z ${Object.keys(grupy).length} ${Object.keys(grupy).length === 1 ? 'sklepu' : 'sklepów'}</p>
      ${html}
      <div class="karta podsumowanie" style="margin-top:16px">
        <div><span class="szary">Produkty</span><span>${zl(Math.round(sumaP * 100) / 100)}</span></div>
        <div><span class="szary">Dostawa ze wszystkich sklepów</span><span>${nieznana ? (sumaD ? zl(Math.round(sumaD * 100) / 100) + ' + wg sklepów' : 'wg sklepów') : sumaD ? zl(Math.round(sumaD * 100) / 100) : 'gratis'}</span></div>
        <div class="razem"><span>Razem</span><b>${zl(Math.round((sumaP + sumaD) * 100) / 100)}</b></div>
      </div>
      <p class="maly szary" style="margin-top:12px">Każdy sklep zamawiasz osobno, na jego stronie. Przyciski „Zamów w sklepie” przenoszą Cię prosto do niego.</p>
      <button class="link" style="margin-top:10px" data-akcja="wyczyscKoszyk">Wyczyść koszyk</button>`
    };
  };

  EKRANY.alerty = () => {
    const al = st.alerty.map((a) => ({ a, p: prod(a.id) })).filter((x) => x.p);
    const kiedy = (t) => t ? new Date(t * 1000).toLocaleString('pl-PL', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' }) : '';
    return {
      akt: 'start',
      po: () => odswiezObserwowane(true),
      html: `<div class="naglowek"><a class="ikonka bez" href="#/start" aria-label="Wróć">${IK.wstecz}</a><h1>Alerty cenowe</h1><span class="puste"></span></div>
      ${al.length ? `<div class="elementy">${al.map(({ a, p }) => `<div class="element"><a class="miniatura" href="#/produkt/${p.id}" aria-label="${esc(p.nazwa)}">${foto(p)}</a>
        <div class="opis"><div class="nazwa">${esc(p.nazwa)}</div><div class="sklep">${esc(p.sklep)}, teraz ${zl(p.cena)}</div>
        ${a.osiagniety ? `<div class="maly" style="color:var(--ok);margin-top:3px;font-weight:500">Cena spadła poniżej ${zl(a.cel)}</div>` : `<div class="maly" style="color:var(--roz);margin-top:3px">Powiadom poniżej ${zl(a.cel)}</div>`}
        ${p.brak_w_sklepie ? '<div class="maly" style="color:var(--promo);margin-top:3px">Ostatnio nie znaleźliśmy go w sklepie. Mógł się wyprzedać.</div>' : p.sprawdzono ? `<div class="maly szary" style="margin-top:3px">Sprawdzono ${kiedy(p.sprawdzono)}</div>` : ''}</div>
        <button class="ikonka bez" data-akcja="usunAlert" data-id="${p.id}" aria-label="Usuń alert">${IK.kosz}</button></div>`).join('')}</div>
        <div class="info neutral" style="margin-top:18px">${IK.info}<p>Ceny sprawdzamy w sklepach co 12 godzin. Gdy cena spadnie poniżej progu, zobaczysz to tutaj i kropkę na dzwonku${'Notification' in window ? ', a jeśli pozwolisz, także powiadomienie po otwarciu aplikacji' : ''}. Rzeczy znalezione przez Google Shopping sprawdzamy tylko przy nowym wyszukiwaniu.</p></div>`
      : `<div class="pusty"><img class="ilustracja-pusta" src="img/puste/pusty-alerty.webp" alt=""><p>Nie masz jeszcze alertów. Na stronie produktu dotknij „Powiadom, gdy stanieje”.</p></div>`}`
    };
  };

  /* Rozmiary tylko do stylizacji (decyzja użytkownika 15.11): same oznaczenia, bez wymiarów ciała. Strona produktu działa bez zmian. */
  const NUM = (a, b, k) => Array.from({ length: Math.floor((b - a) / k) + 1 }, (_, i) => String(a + i * k));
  const ROZM_POLA = {
    d: [['gora', 'Góra (bluzki, koszule, swetry)', ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL']], ['sukienka', 'Sukienki i spódnice', NUM(32, 48, 2)],
      ['spodnie', 'Spodnie', NUM(32, 48, 2)], ['jeansyW', 'Jeansy: obwód (W)', NUM(24, 34, 1).map((x) => 'W' + x)], ['jeansyL', 'Jeansy: długość (L)', ['L30', 'L32', 'L34']],
      ['okrycie', 'Marynarki i okrycia', NUM(32, 48, 2)], ['buty', 'Buty', NUM(35, 42, 1)]],
    m: [['gora', 'Góra (t-shirty, swetry, kurtki)', ['XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL']], ['kolnierzyk', 'Koszula wizytowa: kołnierzyk', NUM(37, 46, 1)],
      ['wzrost', 'Wzrost (koszule i garnitury)', ['164-170', '170-176', '176-182', '182-188', '188-194']], ['spodnie', 'Spodnie', NUM(44, 58, 2)],
      ['jeansyW', 'Jeansy: obwód (W)', NUM(28, 40, 1).map((x) => 'W' + x)], ['jeansyL', 'Jeansy: długość (L)', ['L30', 'L32', 'L34', 'L36']],
      ['marynarka', 'Marynarki i garnitury', NUM(44, 60, 2)], ['buty', 'Buty', NUM(39, 47, 1)]]
  };
  let swiatRozm = null;
  function kartaRozmiarow() {
    const w = swiatRozm || swiatLit(), R = (st.rozm || {})[w] || {};
    return `<div class="karta" style="padding:4px 16px;margin-top:14px">
      <div style="padding:14px 0 12px;border-bottom:1px solid var(--linia)"><b style="font-weight:500">Twoje rozmiary</b>
        <p class="maly szary" style="margin:4px 0 10px">Tylko do stylizacji: dobieramy rzeczy dostępne w tych rozmiarach. Na stronie produktu dalej widzisz całą rozmiarówkę.</p>
        <div class="przelacznik" role="radiogroup" aria-label="Rozmiary"><button role="radio" aria-checked="${w === 'd'}" data-akcja="rozmSwiat" data-v="d">Damskie</button><button role="radio" aria-checked="${w === 'm'}" data-akcja="rozmSwiat" data-v="m">Męskie</button></div></div>
      ${ROZM_POLA[w].map(([k, n, opcje]) => `<div class="ustawienie"><label for="r-${k}">${n}</label><select id="r-${k}" data-rozm="${k}">${[''].concat(opcje).map((r) => `<option value="${r}" ${(R[k] || '') === r ? 'selected' : ''}>${r ? r.replace('-', '–') : 'nie podano'}</option>`).join('')}</select></div>`).join('')}
    </div>`;
  }

  EKRANY.profil = () => ({
    akt: 'start',
    html: `<div class="naglowek"><a class="ikonka bez" href="#/start" aria-label="Wróć">${IK.wstecz}</a><h1>Ustawienia</h1><span class="puste"></span></div>
    <img class="ilustracja-ustawien" src="img/ikony/rozmiary.webp" alt="">
    <p class="szary" style="text-align:center;margin:0 0 16px">Ustawienia, ulubione i alerty zapisują się tylko na tym telefonie.</p>
    <div class="karta" style="padding:4px 16px">
      <div class="ustawienie"><label for="u-dzial">Dział na start</label><select id="u-dzial" data-ust="dzial"><option value="damskie" ${st.dzial === 'damskie' ? 'selected' : ''}>Damskie</option><option value="meskie" ${st.dzial === 'meskie' ? 'selected' : ''}>Męskie</option></select></div>
    </div>
    ${kartaRozmiarow()}
    <div class="karta" style="padding:4px 16px;margin-top:14px">
      <div class="ustawienie"><span>Pokaż ekran powitalny</span><button class="link" data-akcja="pokazPowitanie">Pokaż</button></div>
      <div class="ustawienie"><span>Usuń wszystkie dane z telefonu</span><button class="link" data-akcja="wyczyscWszystko">Usuń</button></div>
    </div>
    <p class="maly szary" style="text-align:center;margin-top:20px">Trendo ${WERSJA}</p>`
  });

  /* ---------- elementy wielokrotne ---------- */
  const KAT_ZAPYTANIE = { spodnie: 'Spodnie', koszule: 'Koszula', swetry: 'Sweter', okrycia: 'Płaszcz', sukienki: 'Sukienka', buty: 'Buty', torebki: 'Torebka', dodatki: 'Dodatki' };
  const KAT_OKLADKA = { 'damskie': { spodnie: 3, koszule: 3, swetry: 5, okrycia: 1, sukienki: 2, buty: 2, torebki: 2, dodatki: 1 }, 'meskie': { spodnie: 1, koszule: 3, swetry: 2, okrycia: 2, buty: 1, dodatki: 3 } };
  function kategorie(dzial) {
    const ok = KAT_OKLADKA[dzial];
    return Object.keys(ok).map((k) => {
      const w = WZORCE.find((x) => x.dzial === dzial && x.kat === k && x.id.endsWith('-' + ok[k]));
      return { id: w.id, katNazwa: w.katNazwa, zapytanie: KAT_ZAPYTANIE[k] };
    });
  }
  function kartaStylizacji(s) {
    const el = s.el.map(prod);
    const suma = el.reduce((a, p) => a + p.cena, 0);
    return `<a class="styl-karta" href="#/stylizacja/${s.id}"><div class="kolaz">${kolaz(s)}</div>
      <div class="podpis"><p class="maly" style="color:var(--tekst2)">Stylizacja ${DEMO.S.indexOf(s) + 1} z ${DEMO.S.length}</p><h3>${esc(s.nazwa)}</h3>
        <div class="meta"><span>${el.length} elementów</span><b>~ ${zl(Math.round(suma * 100) / 100)}</b></div>
        <span class="btn maly" style="align-self:flex-start">Zobacz szczegóły ${IK.dalej}</span></div></a>`;
  }
  function kolaz(s) {
    return s.uklad.map(([id, x, y, w, h, rot]) => {
      const p = prod(id);
      return `<div class="el" style="left:${x}%;top:${y}%;width:${w}%;height:${h}%;transform:rotate(${rot}deg)">${foto(p)}</div>`;
    }).join('');
  }
  /* Znak sklepu: prawdziwe logo z nagłówka strony sklepu (serwer przygotowuje je jako jasny, przycięty napis).
     Do czasu wczytania i gdy znaku nie ma, widać nazwę sklepu tekstem. Wielkość wyrównana optycznie: długie napisy niższe, zwarte wyższe. */
  const ZNAK_POLE = { m: [940, 9, 17], l: [1700, 12, 24] };
  window.TrendoZnak = (img) => {
    const r = img.naturalWidth / img.naturalHeight || 4;
    const [pole, min, max] = ZNAK_POLE[img.dataset.r] || ZNAK_POLE.m;
    img.style.height = Math.max(min, Math.min(max, Math.sqrt(pole / r))).toFixed(1) + 'px';
    img.parentNode.classList.add('ma-znak');
  };
  function marka(nazwa, r) {
    return `<span class="marka marka-${r || 'm'}"><img src="${API}/logo?sklep=${encodeURIComponent(nazwa)}&v=2" alt="" data-r="${r || 'm'}" decoding="async" referrerpolicy="no-referrer" onload="TrendoZnak(this)" onerror="this.remove()"><span class="marka-nazwa">${esc(nazwa)}</span></span>`;
  }
  function kartaProduktu(p) {
    const r = rabat(p), ul = st.ulubione.includes(p.id);
    const wer = p.weryf === 'ok' ? `<div class="weryf ok">${IK.ok}Obniżka potwierdzona</div>`
      : p.weryf === 'pozorna' ? `<div class="weryf uwaga">${IK.uwaga}${p.omnibus ? `Promocja pozorna: przez 30 dni było ${zl(p.omnibus)}` : 'Promocja pozorna'}</div>`
      : p.weryf === 'second' ? `<div class="weryf" style="color:var(--szary)">${IK.second}Z drugiej ręki</div>`
      : p.weryf === 'sklep' ? `<div class="weryf" style="color:var(--promo)">${IK.okazje}Promocja według sklepu</div>` : '';
    return `<div class="produkt"><a href="#/produkt/${p.id}" class="foto" aria-label="${esc(p.sklep + ', ' + p.nazwa)}">${foto(p)}${r ? `<span class="rabat">−${r}%</span>` : ''}</a>
      <button class="serce" style="position:relative;margin:-50px 8px 14px auto;width:36px;height:36px;border-radius:18px;background:rgba(var(--pasek-rgb),.6);border:none;display:flex;align-items:center;justify-content:center" data-akcja="ulubiony" data-id="${p.id}" aria-pressed="${ul}" aria-label="${ul ? 'Usuń z obserwowanych' : 'Obserwuj'}">${(ul ? IK.sercePelne : IK.serce).replace('<svg', '<svg width="18" height="18"')}</button>
      <a href="#/produkt/${p.id}" style="text-decoration:none;color:var(--tekst);display:flex;flex-direction:column;gap:4px">
      <span class="sklep">${marka(p.sklep)}</span><span class="nazwa">${esc(p.nazwa)}</span>
      <span class="ceny"><span class="cena">${zl(p.cena)}</span>${p.stara ? `<span class="stara">${zl(p.stara)}</span>` : ''}</span>${wer}</a></div>`;
  }
  function wierszElementu(p) {
    const r = rabat(p);
    return `<a class="element" href="#/produkt/${p.id}"><span class="miniatura">${foto(p)}</span>
      <span class="opis"><span class="nazwa" style="display:block">${esc(p.nazwa)}</span><span class="sklep">${marka(p.sklep)}</span>
      <span class="ceny"><span class="cena">${zl(p.cena)}</span>${p.stara ? `<span class="stara">${zl(p.stara)}</span>` : ''}${r && p.weryf === 'ok' ? `<span class="rabat">−${r}%</span>` : ''}</span></span>
      <span class="zewn">${IK.dalej}</span></a>`;
  }
  function sekcjaOkazjiDnia() {
    const o = OKZ[st.dzial];
    const tytul = '<div class="sekcja-tytul"><h2>Okazje dnia</h2><a class="link" href="#/okazje">Wszystkie</a></div>';
    if (!o || (o.trwa && !o.lista)) return `<div class="sekcja">${tytul}<p class="maly szary">Sprawdzam dzisiejsze obniżki…</p></div>`;
    if (!o.lista.length) return '';
    return `<div class="sekcja">${tytul}<div class="elementy">${o.lista.slice(0, 3).map(wierszElementu).join('')}</div>
      <p class="maly szary" style="margin-top:10px">Tylko obniżki sprawdzone: cena niższa niż najniższa z 30 dni przed promocją.</p></div>`;
  }
  function kartaOkazji(o) {
    return `<div class="okazja"><div class="opis"><span class="sklep">${marka(o.sklep)}</span><b>${esc(o.tytul)}</b><p>${esc(o.opis)}</p>
      ${o.weryf === 'ok' ? `<div class="weryf ok" style="margin-top:4px">${IK.ok}Sprawdzone</div>` : `<div class="weryf uwaga" style="margin-top:4px">${IK.uwaga}Częściowo pozorna</div>`}</div>
      <span class="rabat" style="align-self:flex-start">−${o.rabat}%</span></div>`;
  }


  /* ---------- arkusz alertu ---------- */
  function arkuszAlertu(id) {
    const p = prod(id);
    const ist = st.alerty.find((a) => a.id === id);
    const cel = ist ? ist.cel : Math.round(p.cena * 0.85);
    ARK.innerHTML = `<div class="panel" role="dialog" aria-modal="true" aria-labelledby="ark-t"><div class="uchwyt"></div>
      <h2 id="ark-t">Powiadom, gdy stanieje</h2><p class="szary" style="margin:6px 0 18px">${esc(p.sklep)}, ${esc(p.nazwa)}. Teraz ${zl(p.cena)}.</p>
      <div class="budzet-wiersz"><div class="budzet-gora"><label for="cel">Cena docelowa</label><span class="budzet-kwota" id="celv">${zl(cel)}</span></div>
      <input id="cel" type="range" min="${Math.round(p.cena * 0.4)}" max="${Math.round(p.cena)}" step="1" value="${cel}"></div>
      <p class="maly szary" style="margin:10px 0 18px">Cenę sprawdzamy w sklepie co 12 godzin.</p>
      <button class="btn" data-akcja="zapiszAlert" data-id="${id}">Ustaw alert</button>
      ${ist ? `<button class="btn drugi" style="margin-top:10px" data-akcja="usunAlert" data-id="${id}">Usuń alert</button>` : ''}
      <button class="link" style="margin:10px auto 0;display:flex" data-akcja="zamknijArkusz">Anuluj</button></div>`;
    ARK.hidden = false;
    const r = document.getElementById('cel');
    const odsw = () => { r.style.setProperty('--p', ((r.value - r.min) / (r.max - r.min) * 100) + '%'); document.getElementById('celv').textContent = zl(+r.value); };
    r.addEventListener('input', odsw); odsw();
  }
  function arkuszZgloszenia(id) {
    const p = prod(id); if (!p) return;
    const ok = filtrOkazji !== 'wszystkie' ? NAZWA_OKAZJI[filtrOkazji] : '';
    const pow = [ok ? ['okazja', `Nie pasuje na okazję: ${ok}`] : null, ['rzecz', 'To inna rzecz, niż szukałam / szukałem'],
      ['plec', 'Nie ten dział (damskie / męskie)'], ['zdjecie', 'Zdjęcie nie zgadza się z opisem'], ['inne', 'Inny powód']].filter(Boolean);
    ARK.innerHTML = `<div class="panel" role="dialog" aria-modal="true" aria-labelledby="ark-t"><div class="uchwyt"></div>
      <h2 id="ark-t">Co jest nie tak?</h2><p class="szary" style="margin:6px 0 18px">${esc(p.sklep)}, ${esc(p.nazwa)}.</p>
      <div style="display:flex;flex-direction:column;gap:10px">${pow.map(([v, t]) => `<button class="btn drugi" data-akcja="wyslijZgloszenie" data-id="${p.id}" data-v="${v}">${esc(t)}</button>`).join('')}</div>
      <p class="maly szary" style="margin:14px 0 4px">${ok ? 'Po zgłoszeniu ta rzecz od razu zniknie z filtra tej okazji. ' : ''}Zgłoszenie pomaga nam poprawić zasady dla wszystkich.</p>
      <button class="link" style="margin:10px auto 0;display:flex" data-akcja="zamknijArkusz">Anuluj</button></div>`;
    ARK.hidden = false;
  }
  ARK.addEventListener('click', (e) => { if (e.target === ARK) ARK.hidden = true; });

  /* ---------- akcje ---------- */
  const A = {
    zacznij() { st.witaj = true; zapisz(); location.hash = '#/start'; },
    zacznijSwiat(el) { st.dzial = el.dataset.v; st.witaj = true; zapisz(); location.hash = '#/start'; },
    witajDalej() { const sl = document.getElementById('slajdy'); sl.scrollTo({ left: (Math.round(sl.scrollLeft / sl.clientWidth) + 1) * sl.clientWidth, behavior: 'smooth' }); },
    witajSlajd(el) { const sl = document.getElementById('slajdy'); sl.scrollTo({ left: Number(el.dataset.i) * sl.clientWidth, behavior: 'smooth' }); },
    dzial(el) { st.dzial = el.dataset.v; zapisz(); render(); },
    wejscieStyl(el) { st.stylTryb = el.dataset.v === 'dodatki' ? 'dodatki' : 'outfit'; zapisz(); },
    stylTryb(el) { st.stylTryb = el.dataset.v; zapisz(); render(true); },
    bezStartu() { st.stylStart = null; zapisz(); render(true); },
    dobierzDo(el) { st.stylRozm = null; st.stylStart = el.dataset.id; st.stylTryb = 'outfit'; if (filtrOkazji && filtrOkazji !== 'wszystkie') st.okazja = filtrOkazji; zapisz(); },
    histTab(el) { histTab = el.dataset.v; if (location.hash === '#/historia') render(true); },
    histSzukaj(el) { const x = HIST().szukania[+el.dataset.i]; if (!x) return; st.dzial = x.dzial; st.b1 = x.b1 || st.b1; zacznijSzukanie(x.q); },
    histUsun(el) {
      const h = HIST(), k = el.dataset.k;
      if (el.dataset.v === 'produkty') h.produkty = h.produkty.filter((x) => x.id !== k);
      else if (el.dataset.v === 'szukania') h.szukania.splice(+k, 1);
      else h.styl = h.styl.filter((e) => e.k !== k);
      zapisz(); render(true);
    },
    histWyczysc() {
      const h = HIST();
      if (!confirm('Wyczyścić tę część historii?')) return;
      if (histTab === 'styl') h.styl = h.styl.filter((e) => e.przypiety); else h[histTab] = [];
      zapisz(); render(true);
    },
    otworzStyl(el) {
      const e = HIST().styl.find((x) => x.k === el.dataset.k); if (!e) return;
      const [dzial, okazja, stylTryb, stylStart, stylQ, rozm] = JSON.parse(e.k); // dokładnie te same ustawienia co przy złożeniu
      Object.assign(st, { dzial, okazja, stylTryb, stylStart: stylStart || null, stylQ: stylQ || '', stylRozm: rozm || null });
      if (!(STYL && STYL.klucz === e.k && STYL.dane)) { STYL = null; stylDoPrzywrocenia = e; }
      zapisz();
    },
    stylPrzypnij(el) {
      if (STYL && STYL.dane && STYL.klucz === el.dataset.k) zapiszStylHistorie(true);
      const e = HIST().styl.find((x) => x.k === el.dataset.k); if (!e) return;
      e.przypiety = !e.przypiety; zapisz();
      komunikat(e.przypiety ? 'Stylizacja zapisana na stałe' : 'Stylizacja odpięta');
      render(true);
    },
    stylTrybW(el) { stylWidok = { tryb: el.dataset.v, z: 0 }; render(true); },
    stylWl(el) { const S = stylStan(stylWidok.tryb, stylWidok.z), s = S.sloty[el.dataset.k]; if (!s) return; s.wyl = !s.wyl; stylOdswiez(true); },
    stylInna(el) { const S = stylStan(stylWidok.tryb, stylWidok.z), s = S.sloty[el.dataset.k]; if (!s) return; s.skok++; S.suma = null; stylOdswiez(true); },
    stylPonow() { STYL = null; render(); },
    rozmSwiat(el) { swiatRozm = el.dataset.v; render(true); },
    stylDoKoszyka() {
      const d = STYL && STYL.dane; if (!d) return;
      const { wyn } = stylWybor(d, stylWidok.tryb, stylWidok.z);
      const ids = Object.values(wyn).filter((w) => w.id && !w.s.wyl).map((w) => w.id).concat(d.baza && d.baza.id ? [d.baza.id] : []);
      let dod = 0;
      ids.forEach((id) => { const p = STYL_ID[id] || prod(id); if (!p) return; zapamietaj(p); if (!st.koszyk.includes(id)) { st.koszyk.push(id); dod++; } });
      zapisz(); rysujMenu('szukaj');
      komunikat(dod ? `Dodano ${dod} ${dod === 1 ? 'rzecz' : 'rzeczy'} do zakupów` : 'Ten zestaw jest już w zakupach');
    },
    komponuj() {
      const qs = document.getElementById('qs');
      if (qs) st.stylQ = qs.value.trim();
      st.stylRozm = null;
      zapisz(); location.hash = '#/stylizacje';
    },
    okazja(el) {
      st.okazja = el.dataset.v; zapisz();
      // bez przerysowania ekranu (zostajemy w tym samym miejscu przewinięcia)
      document.querySelectorAll('[data-akcja="okazja"]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === st.okazja)));
    },
    zdjecie() { const f = document.getElementById('plik'); if (f) f.click(); },
    szukaj() {
      const q = (document.getElementById('q').value || '').trim();
      if (!q) { komunikat('Wpisz, czego szukasz.'); document.getElementById('q').focus(); return; }
      zacznijSzukanie(q);
    },
    kategoria(el) { st.zapytanie = el.dataset.q; zapisz(); location.hash = '#/szukaj'; },
    szukajOstatnie(el) { st.zapytanie = el.dataset.q; zapisz(); location.hash = '#/szukaj'; },
    szukajTrendu(el, e) { e.preventDefault(); ARK.hidden = true; st.zapytanie = el.dataset.q; zapisz(); location.hash = '#/szukaj'; },
    budzetWl() { budzetWl = !budzetWl; render(true); },
    tylkoPromocje() { tylkoPromocje = !tylkoPromocje; render(true); },
    tylkoSecond() { tylkoSecond = !tylkoSecond; render(true); },
    filtrOkazji(el) { filtrOkazji = el.dataset.v; render(true); },
    doSklepu(el, e) {
      e.preventDefault();
      const p = prod(el.dataset.id); if (!p) return;
      if (p.sklepUrl) { location.href = p.sklepUrl; return; }
      komunikat(`Szukam strony produktu w sklepie ${p.sklep}…`);
      fetch(`${API}/link?nazwa=${encodeURIComponent(p.nazwa)}&sklep=${encodeURIComponent(p.sklep)}`)
        .then((r) => r.json())
        .then((d) => {
          if (d.url && d.pewny) { p.sklepUrl = d.url; zapamietaj(p); zapisz(); }
          if (d.wyszukiwanie) komunikat('Nie znalazłem strony w sklepie. Otwieram wyszukiwanie.');
          location.href = d.url || p.url;
        })
        .catch(() => { location.href = 'https://www.google.com/search?q=' + encodeURIComponent(p.nazwa + ' ' + p.sklep); });
    },
    dodajProdukt(el) {
      const id = el.dataset.id;
      if (st.koszyk.includes(id)) { location.hash = '#/koszyk'; return; }
      zapamietaj(prod(id)); st.koszyk.push(id); zapisz(); render(true); komunikat('Dodano do zakupów');
    },
    ulubiony(el) {
      const id = el.dataset.id, i = st.ulubione.indexOf(id);
      zapamietaj(prod(id));
      if (i >= 0) { st.ulubione.splice(i, 1); komunikat('Usunięto z obserwowanych'); } else { st.ulubione.push(id); komunikat('Obserwujesz ten produkt'); zglosObserwowane([id]); }
      zapisz(); render(true);
    },
    zapiszStyl(el) {
      const id = el.dataset.id, i = st.zapisane.indexOf(id);
      if (i >= 0) { st.zapisane.splice(i, 1); komunikat('Usunięto z zapisanych'); } else { st.zapisane.push(id); komunikat('Stylizacja zapisana na ekranie Start'); }
      zapisz(); render(true);
    },
    doKoszyka(el) {
      const s = DEMO.S.find((x) => x.id === el.dataset.id);
      let dod = 0; s.el.forEach((id) => { if (!st.koszyk.includes(id)) { st.koszyk.push(id); dod++; } });
      zapisz(); rysujMenu('szukaj');
      komunikat(dod ? `Dodano ${dod} ${dod === 1 ? 'rzecz' : dod < 5 ? 'rzeczy' : 'rzeczy'} do zakupów` : 'Ten zestaw jest już w zakupach');
    },
    usunZKoszyka(el) { st.koszyk = st.koszyk.filter((x) => x !== el.dataset.id); zapisz(); render(true); },
    wyczyscKoszyk() { st.koszyk = []; zapisz(); render(); },
    rozmiar(el) {
      st.rozmiar[el.dataset.id] = el.dataset.v; zapisz();
      const k = document.getElementById('rozm'), p = prod(el.dataset.id);
      if (k && p) k.innerHTML = kartaRozmiarowki(p, ROZM[p.id]); else render(true);
    },
    alert(el) { arkuszAlertu(el.dataset.id); },
    zapiszAlert(el) {
      const id = el.dataset.id, cel = +document.getElementById('cel').value;
      st.alerty = st.alerty.filter((a) => a.id !== id).concat([{ id, cel }]);
      if (!st.ulubione.includes(id)) st.ulubione.push(id);
      zapamietaj(prod(id));
      zapisz(); ARK.hidden = true; render(true);
      komunikat(`Alert ustawiony na ${zl(cel)}`);
      zglosObserwowane([id]);
      try { if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission().catch(() => {}); } catch (e) { /* stara przeglądarka */ }
    },
    usunAlert(el) { st.alerty = st.alerty.filter((a) => a.id !== el.dataset.id); zapisz(); ARK.hidden = true; render(true); },
    zamknijArkusz() { ARK.hidden = true; },
    niePasuje(el) { arkuszZgloszenia(el.dataset.id); },
    zrodlaTrendu(el) { arkuszZrodel(+el.dataset.i); },
    wyslijZgloszenie(el) {
      const p = prod(el.dataset.id); if (!p) return;
      const okazja = el.dataset.v === 'okazja' && filtrOkazji !== 'wszystkie' ? filtrOkazji : '';
      const par = new URLSearchParams({ id: p.id, okazja, q: (wynik && wynik.zapytanie) || st.zapytanie || '', dzial: st.dzial, powod: el.dataset.v, nazwa: p.nazwa, sklep: p.sklep, zdjecie: p.zdjecie || '' });
      ARK.hidden = true;
      fetch(`${API}/zglos?${par}`).then((r) => {
        if (!r.ok) throw new Error();
        if (okazja && Array.isArray(p.okazje)) { p.okazje = p.okazje.filter((o) => o !== okazja); try { sessionStorage.setItem('trendo-wynik', JSON.stringify(wynik)); } catch (e) {} }
        komunikat(okazja ? 'Dziękujemy. Ta rzecz nie będzie już pokazywana na tę okazję.' : 'Dziękujemy, zgłoszenie zapisane.');
      }).catch(() => komunikat('Nie udało się wysłać zgłoszenia. Spróbuj za chwilę.'));
    },
    wstecz() { if (history.length > 1) history.back(); else location.hash = '#/wyniki'; },
    dzialTrendow(el) { dzialTrendow = null; st.dzial = el.dataset.v; zapisz(); render(); },
    filtrTrendow(el) { filtrTrendow = el.dataset.v; render(); },
    zakladkaOkazji(el) { zakladkaOkazji = el.dataset.v; render(); },
    pokazPowitanie() { st.witaj = false; zapisz(); location.hash = '#/witaj'; },
    wyczyscWszystko() {
      if (!confirm('Usunąć zapisane stylizacje, koszyk, alerty i ustawienia z tego telefonu?')) return;
      localStorage.removeItem('trendo'); st = Object.assign({}, DOMYSLNE); location.hash = '#/witaj';
    }
  };

  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-akcja]');
    if (!el || !A[el.dataset.akcja]) return;
    A[el.dataset.akcja](el, e);
  });
  document.addEventListener('input', (e) => {
    const t = e.target;
    if (t.id === 'b1' || t.id === 'b2') {
      st[t.id] = +t.value; zapisz();
      const p = t.id === 'b1' ? (t.value - 30) / (BEZ_LIMITU - 30) * 100 : t.value / 5000 * 100;
      t.style.setProperty('--p', p + '%');
      document.getElementById(t.id + 'v').textContent = t.id === 'b1' ? opisCeny(+t.value) : '~ ' + zl(+t.value);
    }
    if (t.id === 'q') { st.zapytanie = t.value; zapisz(); }
    const d = STYL && STYL.dane;
    if (d && (t.classList.contains('suwak-rzeczy') || t.id === 'styl-suma')) {
      const S = stylStan(stylWidok.tryb, stylWidok.z), Z = d.tryby[stylWidok.tryb].zestawy[stylWidok.z];
      if (t.id === 'styl-suma') {
        const v = +t.value, max = +t.max, min = +t.min;
        S.suma = v >= max ? null : v;
        t.style.setProperty('--p', (max > min ? (v - min) / (max - min) * 100 : 100) + '%');
        document.getElementById('stv').textContent = S.suma == null ? 'Bez limitu' : '~ ' + zl(S.suma);
      } else {
        const k = t.dataset.k, s = S.sloty[k], ceny = stylCeny((Z.sloty[k] || []).filter((id) => d.produkty[id]), d.produkty), n = ceny.length, v = +t.value;
        s.limit = v >= n ? null : ceny[v]; s.skok = 0;
        t.style.setProperty('--p', (n ? v / n * 100 : 100) + '%');
        document.getElementById('sl-' + k).innerHTML = s.limit == null ? 'Bez limitu' : 'Do <b>' + zl(s.limit) + '</b>';
      }
      const { wyn, ponad } = stylWybor(d, stylWidok.tryb, stylWidok.z);
      d.miejsca.forEach(({ k, nazwa }) => { const el = document.querySelector('#se-' + k + ' .styl-tresc'); if (el && wyn[k]) el.innerHTML = stylTresc(d.produkty[wyn[k].id], nazwa, wyn[k]); });
      const pn = document.getElementById('styl-ponad'); if (pn) pn.textContent = ponad ? 'Taniej się nie da w Twoich rozmiarach. Odznacz którąś rzecz albo podnieś budżet.' : '';
      stylOdswiez(false);
    }
  });
  document.addEventListener('change', (e) => {
    const t = e.target;
    if (t.id === 'kolejnosc') { kolejnosc = t.value; render(true); return; }
    if (t.dataset.rozm) {
      const w = swiatRozm || swiatLit();
      st.rozm = st.rozm || {}; st.rozm[w] = Object.assign({}, st.rozm[w] || {}, { [t.dataset.rozm]: t.value });
      zapisz(); komunikat('Zapisano');
    }
    if (t.dataset.ust) {
      if (t.dataset.ust === 'dzial') { st.dzial = t.value; dzialTrendow = null; } else st.ust[t.dataset.ust] = t.value;
      zapisz(); komunikat('Zapisano');
      if (t.dataset.ust === 'dzial') render(true);
    }
    if (t.id === 'plik' && t.files && t.files[0]) {
      szukajZeZdjecia(t.files[0]);
      t.value = '';
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.id === 'q') { e.preventDefault(); A.szukaj(); }
    if (e.key === 'Escape' && !ARK.hidden) ARK.hidden = true;
  });

  /* Dwa światy w jednej aplikacji: dział zmienia cały wygląd (kolory, akcenty, grafiki).
     Grafiki świata męskiego leżą w img/m/ pod tą samą ścieżką co damskie. Do czasu ich przygotowania
     damskie przedmioty w różowym złocie są w świecie męskim przemalowywane filtrem na mosiądz (styles.css, --przemaluj). */
  const GOTOWE_M = new Set([ // ścieżki względem img/ (pliki leżą w img/m/)
    'ikony/krok-promocje.webp',
    'ikony/krok-sklepy.webp',
    'ikony/krok-stylizacje.webp',
    'ikony/krok-trendy.webp',
    'ikony/pusty-obserwowane.webp',
    'ikony/pusta-historia.webp',
    'ikony/pusty-okazje.webp',
    'ikony/pusty-trendy.webp',
    'ikony/pusty-wyniki.webp',
    'ikony/rozmiary.webp',
    'ikony/tryb-dodatki.webp',
    'ikony/tryb-outfit.webp',
    'ikony/tryb-rzecz.webp',
    'ikony/tryb-zdjecie.webp',
    'puste/pusty-alerty.webp',
    'puste/pusty-koszyk.webp',
    'sezon-jz.jpg',
    'sezon-wl.jpg',
    'status/nadchodzi.webp',
    'status/rosnie.webp',
    'status/szczyt.webp',
    'status/wygasa.webp'
  ]);
  const swiatM = () => document.documentElement.dataset.swiat === 'm';
  const obrazSwiata = (r) => 'img/' + (swiatM() && GOTOWE_M.has(r) ? 'm/' + r : r);
  function podmienGrafikiSwiata(root) {
    if (!swiatM() || !GOTOWE_M.size) return;
    root.querySelectorAll('img[src^="img/"]').forEach((im) => {
      const r = im.getAttribute('src').slice(4);
      if (GOTOWE_M.has(r)) { im.src = 'img/m/' + r; im.classList.add('wlasna-m'); }
    });
  }
  const META_KOLOR = document.querySelector('meta[name="theme-color"]');
  function ustawSwiat(dzial) {
    const sw = dzial === 'meskie' ? 'm' : 'd';
    if (document.documentElement.dataset.swiat === sw) return;
    document.documentElement.dataset.swiat = sw;
    if (META_KOLOR) META_KOLOR.setAttribute('content', sw === 'm' ? '#0C0B0A' : '#0E090C');
  }

  /* ---------- szukanie: z hasła albo ze zdjęcia ---------- */
  function zacznijSzukanie(q) {
    st.zapytanie = q;
    st.ostatnie = [q].concat(st.ostatnie.filter((x) => x.toLowerCase() !== q.toLowerCase())).slice(0, 8);
    dopiszSzukanie(q);
    filtrOkazji = 'wszystkie'; budzetWl = true; tylkoPromocje = false; tylkoSecond = false; kolejnosc = 'polecane';
    zapisz(); location.hash = '#/analiza';
  }
  // Zdjęcie zmniejszamy na telefonie (dłuższy bok 1280 px, JPEG), żeby wysyłka była szybka także na komórkowym internecie.
  function zmniejsz(plik) {
    return new Promise((ok, zle) => {
      const u = URL.createObjectURL(plik), im = new Image();
      im.onload = () => {
        const k = Math.min(1, 1280 / Math.max(im.naturalWidth, im.naturalHeight));
        const c = document.createElement('canvas');
        c.width = Math.max(1, Math.round(im.naturalWidth * k)); c.height = Math.max(1, Math.round(im.naturalHeight * k));
        c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
        URL.revokeObjectURL(u);
        c.toBlob((b) => (b ? ok(b) : zle(new Error('zdjecie'))), 'image/jpeg', 0.85);
      };
      im.onerror = () => { URL.revokeObjectURL(u); zle(new Error('zdjecie')); };
      im.src = u;
    });
  }
  let rozpoznaje = false;
  function szukajZeZdjecia(plik) {
    if (rozpoznaje) return;
    rozpoznaje = true;
    komunikat('Rozpoznaję rzecz ze zdjęcia…');
    zmniejsz(plik)
      .then((b) => fetch(`${API}/zdjecie`, { method: 'POST', headers: { 'Content-Type': 'image/jpeg' }, body: b }))
      .then((r) => r.json().then((d) => ({ ok: r.ok, d })))
      .then(({ ok, d }) => {
        if (!ok) { komunikat(d.blad || 'Nie udało się rozpoznać zdjęcia. Spróbuj jeszcze raz.'); return; }
        if (!d.rzecz || !d.q) { komunikat('Nie widzę na zdjęciu ubrania ani dodatku. Spróbuj innego zdjęcia.'); return; }
        komunikat(`Szukam: ${d.q}`);
        zacznijSzukanie(d.q);
      })
      .catch(() => komunikat('Nie udało się wysłać zdjęcia. Sprawdź internet albo wpisz, czego szukasz.'))
      .finally(() => { rozpoznaje = false; });
  }


  /* ---------- router ---------- */
  function render(zachowajPozycje) {
    clearTimeout(EKRANY.analiza.timer); clearTimeout(EKRANY.stylizacje.timer);
    document.body.classList.remove('z-paskiem');
    let [nazwa, arg] = location.hash.replace(/^#\/?/, '').split('/');
    if (!nazwa) nazwa = st.witaj ? 'start' : 'witaj';
    if (nazwa === 'witaj' && st.witaj && !location.hash.includes('witaj')) nazwa = 'start';
    ustawSwiat(nazwa === 'witaj' ? 'damskie' : st.dzial); // przed budową ekranu: grafiki i okładki zależą od świata
    const f = EKRANY[nazwa] || EKRANY.start;
    let ekran;
    try { ekran = f(arg); } catch (e) {
      console.error(e);
      ekran = { akt: 'start', menu: false, klasa: 'bez-menu', html: `<div class="naglowek"><a class="ikonka bez" href="javascript:history.back()" aria-label="Wróć">${IK.wstecz}</a><h1>Coś poszło nie tak</h1><span class="puste"></span></div>
        <div class="info uwaga">${IK.uwaga}<p>Nie udało się otworzyć tego ekranu. Wróć i spróbuj jeszcze raz. Jeśli to się powtarza, zgłoś to przy produkcie przyciskiem „Nie pasuje? Zgłoś”.</p></div>` };
    }
    const y = window.scrollY;
    E.className = ekran.klasa || '';
    E.innerHTML = ekran.html;
    podmienGrafikiSwiata(E);
    if (ekran.menu === false) MENU.hidden = true; else { MENU.hidden = false; rysujMenu(ekran.akt); }
    if (zachowajPozycje) window.scrollTo(0, y); else window.scrollTo(0, 0);
    if (ekran.po) { try { ekran.po(); } catch (e) { console.error(e); } }
    document.title = nazwa === 'start' || nazwa === 'witaj' ? 'Trendo' : 'Trendo: ' + (E.querySelector('h1') ? E.querySelector('h1').textContent.replace(/\s+/g, ' ') : '');
  }
  // Zdjęcie, które się nie wczytało (sklep je usunął albo blokuje): wieszak zamiast pustego pola.
  window.TrendoBezZdjecia = (im) => { const s = document.createElement('span'); s.style.cssText = 'color:var(--szary2);width:40%;display:flex'; s.innerHTML = IK.wieszak; im.replaceWith(s); };

  /* iPhone, aplikacja z ekranu początkowego: po schowaniu klawiatury iOS potrafi zostawić zmniejszony obszar strony
     i przyczepione do dołu paski (menu, suma zestawu) wiszą w połowie ekranu. Dół liczymy z faktycznie widocznej części. */
  const poleAktywne = () => document.activeElement && /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
  function dopasujDol() {
    const vv = window.visualViewport;
    let p = 0;
    if (vv && !poleAktywne()) p = Math.round(window.innerHeight - (vv.offsetTop + vv.height));
    document.documentElement.style.setProperty('--przes', Math.min(0, p) + 'px');
  }
  function poKlawiaturze() {
    [80, 400, 900].forEach((t) => setTimeout(() => {
      if (poleAktywne()) return;
      window.scrollBy(0, 1); window.scrollBy(0, -1); // wymusza przeliczenie widoku w Safari
      dopasujDol();
    }, t));
  }
  document.addEventListener('focusout', (e) => { if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) poKlawiaturze(); });
  if (window.visualViewport) { window.visualViewport.addEventListener('resize', dopasujDol); window.visualViewport.addEventListener('scroll', dopasujDol); }
  window.addEventListener('pageshow', poKlawiaturze);

  window.addEventListener('hashchange', () => { ARK.hidden = true; render(); });
  render();
  setTimeout(() => { zglosObserwowane(); odswiezObserwowane(); }, 1500);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') odswiezObserwowane(); });

  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
})();
