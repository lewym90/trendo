/* Trendo 0.1.0: interfejs. Do czasu podłączenia serwera działa na danych przykładowych (js/demo.js). */
(function () {
  'use strict';
  const WERSJA = '0.11.4';
  const IK = G.IK;
  const E = document.getElementById('ekran');
  const MENU = document.getElementById('menu');
  const ARK = document.getElementById('arkusz');
  const KOM = document.getElementById('komunikat');

  /* ---------- stan zapisany na telefonie ---------- */
  const DOMYSLNE = {
    witaj: false, dzial: 'damskie', zapytanie: 'Skórzane spodnie', b1: 300, b2: 500,
    okazja: 'codzien', tryb: 'outfit', koszyk: [], ulubione: [], zapisane: [], alerty: [],
    ostatnie: [], rozmiar: {}, ust: { gora: '', dol: '', buty: '' }, znane: {}
  };
  let st;
  try { st = Object.assign({}, DOMYSLNE, JSON.parse(localStorage.getItem('trendo') || '{}')); } catch (e) { st = Object.assign({}, DOMYSLNE); }
  const zapisz = () => { try { localStorage.setItem('trendo', JSON.stringify(st)); } catch (e) { /* tryb prywatny */ } };

  /* ---------- pomocnicze ---------- */
  const zl = (n) => n.toLocaleString('pl-PL', { minimumFractionDigits: n % 1 ? 2 : 0, maximumFractionDigits: 2 }) + ' zł';
  const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const API = (() => { try { return localStorage.getItem('trendo-api'); } catch (e) { return null; } })() || 'https://188-68-247-201.sslip.io/trendo-api';
  let wynik = null; // ostatni prawdziwy wynik z serwera
  try { wynik = JSON.parse(sessionStorage.getItem('trendo-wynik') || 'null'); } catch (e) { wynik = null; }
  const prod = (id) => DEMO.P.find((p) => p.id === id) || (wynik && wynik.produkty.find((p) => p.id === id)) || (st.znane || {})[id];
  function zapamietaj(p) {
    if (!p || !p.zrodlo) return;
    st.znane = st.znane || {}; st.znane[p.id] = p;
    const k = Object.keys(st.znane);
    if (k.length > 300) k.slice(0, k.length - 300).forEach((x) => { if (!st.koszyk.includes(x) && !st.ulubione.includes(x)) delete st.znane[x]; });
  }
  const prawdziwy = (p) => !!(p && p.zrodlo);
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
  const foto = (p) => (p.zdjecie ? `<img class="zdj" src="${esc(p.zdjecie)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">`
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
        <div class="kropki" role="tablist" aria-label="Slajdy">${SLAJDY.map((_, i) => `<button role="tab" aria-label="Slajd ${i + 1}" data-akcja="witajSlajd" data-i="${i}" class="${i ? '' : 'tak'}"></button>`).join('')}</div>
      </div></section>`,
    po: () => {
      const sl = document.getElementById('slajdy');
      const nr = () => Math.round(sl.scrollLeft / sl.clientWidth);
      sl.addEventListener('scroll', () => {
        const i = nr();
        document.querySelectorAll('.kropki button').forEach((k, j) => k.classList.toggle('tak', j === i));
        const b = document.getElementById('witaj-btn');
        b.innerHTML = (i === SLAJDY.length - 1 ? 'Zacznijmy ' : 'Dalej ') + IK.dalej;
        b.dataset.akcja = i === SLAJDY.length - 1 ? 'zacznij' : 'witajDalej';
      }, { passive: true });
    }
  });

  EKRANY.start = () => {
    const g = new Date().getHours();
    const pow = g < 5 ? 'Dobry wieczór' : g < 18 ? 'Dzień dobry' : 'Dobry wieczór';
    const s = sezon();
    const zap = st.zapisane.map((id) => DEMO.S.find((x) => x.id === id)).filter(Boolean);
    const ost = st.ostatnie.slice(0, 6);
    return {
      akt: 'start',
      html: `<div class="powitanie-dnia">
        <div><p class="szary maly">${pow}</p><h1>Czego dziś<br>szukasz?</h1></div>
        <div class="akcje">
          <a class="ikonka" href="#/alerty" aria-label="Alerty cenowe${st.alerty.length ? ', ' + st.alerty.length : ''}">${IK.dzwonek}${st.alerty.length ? '<span class="kropka"></span>' : ''}</a>
          <a class="ikonka" href="#/profil" aria-label="Profil i ustawienia">${IK.profil}</a>
        </div></div>
      <a href="#/szukaj" class="pole-szukaj" style="text-decoration:none">${IK.szukaj}<span style="flex:1;color:var(--szary2);font-size:17px">Np. skórzane spodnie, płaszcz…</span><span class="ikonka" aria-hidden="true">${IK.aparat}</span></a>
      <div class="sekcja" style="margin-top:22px"><div class="sekcja-tytul"><h2>Kategorie</h2>
        <div class="przelacznik" role="radiogroup" aria-label="Dział" style="width:190px;padding:3px"><button role="radio" style="height:32px;font-size:13.5px" aria-checked="${st.dzial === 'damskie'}" data-akcja="dzial" data-v="damskie">Damskie</button><button role="radio" style="height:32px;font-size:13.5px" aria-checked="${st.dzial === 'meskie'}" data-akcja="dzial" data-v="meskie">Męskie</button></div></div>
        <div class="karuzela kategorie">${kategorie(st.dzial).map((k) => `<button class="kategoria" data-akcja="kategoria" data-q="${esc(k.zapytanie)}"><span class="kat-foto"><img src="img/wzorce/${k.id}.webp" alt="" loading="lazy"></span><span>${esc(k.katNazwa)}</span></button>`).join('')}</div></div>
      ${ost.length ? `<div class="sekcja" style="margin-top:16px"><div class="chipy">${ost.map((q) => `<button class="chip" data-akcja="szukajOstatnie" data-q="${esc(q)}">${esc(q)}</button>`).join('')}</div></div>` : ''}

      <div class="sekcja">
        <a href="#/trendy" class="okladka" style="--foto:url('img/${s.plik}.jpg');text-decoration:none;color:var(--tekst)">
          <div><p class="maly" style="color:#E7CFC6;margin:0 0 6px">Raport trendów</p><h2>${s.nazwa}<br>${s.rok}</h2><p>Co jest teraz w modzie i dokąd to zmierza.</p></div>
        </a>
      </div>

      ${zap.length ? `<div class="sekcja"><div class="sekcja-tytul"><h2>Zapisane stylizacje</h2></div><div class="karuzela">${zap.map(kartaStylizacji).join('')}</div></div>` : ''}

      <div class="sekcja">
        <div class="sekcja-tytul"><h2>Okazje dnia</h2><a class="link" href="#/okazje">Wszystkie</a></div>
        ${DEMO.OK.filter((o) => o.weryf === 'ok').slice(0, 3).map(kartaOkazji).join('')}
        <p class="maly szary" style="margin-top:10px">Wersja próbna: okazje są przykładowe.</p>
      </div>`
    };
  };

  EKRANY.szukaj = () => {
    const tryby = [['outfit', 'outfit', 'Cały outfit'], ['rzecz', 'wieszak', 'Jedna rzecz'], ['dodatki', 'dodatki', 'Dodatki'], ['zdjecie', 'zdjecie', 'Ze zdjęcia']];
    const okazje = [['codzien', 'Na co dzień'], ['smartcasual', 'Smart casual'], ['praca', 'Do pracy'], ['randka', 'Randka'], ['wesele', 'Wesele'], ['wieczor', 'Wieczór'], ['sylwester', 'Sylwester'], ['wyjazd', 'Wyjazd']];
    const p1 = (st.b1 - 30) / (3000 - 30) * 100, p2 = st.b2 / 5000 * 100;
    return {
      akt: 'szukaj',
      po: () => { const z = document.querySelector('.okazja-kafel[aria-pressed="true"]'); if (z) z.parentElement.scrollLeft = Math.max(0, z.offsetLeft - 20); },
      html: `<div class="naglowek"><a class="ikonka bez" href="#/start" aria-label="Wróć">${IK.wstecz}</a><h1>Nowe wyszukiwanie</h1><span class="puste"></span></div>
      <h2 class="wejscie" style="font-size:34px;margin:4px 0 16px">Czego dziś szukasz?</h2>
      <label class="ukryj" for="q">Czego szukasz</label>
      <div class="pole-szukaj">${IK.szukaj}<input id="q" value="${esc(st.zapytanie)}" placeholder="Np. skórzane spodnie i koszula w kratę" autocomplete="off" enterkeyhint="search">
        <button class="ikonka" data-akcja="zdjecie" aria-label="Szukaj ze zdjęcia">${IK.aparat}</button></div>

      <div class="przelacznik" role="radiogroup" aria-label="Dział" style="margin-top:14px">
        <button role="radio" aria-checked="${st.dzial === 'damskie'}" data-akcja="dzial" data-v="damskie">Damskie</button>
        <button role="radio" aria-checked="${st.dzial === 'meskie'}" data-akcja="dzial" data-v="meskie">Męskie</button>
      </div>

      <div class="sekcja" style="margin-top:22px">
        <p style="text-align:center;margin-bottom:12px;font-size:15px">Ustal swój cel budżetowy</p>
        <div class="budzet">
          <div class="budzet-wiersz"><div class="budzet-gora"><label for="b1">Na szukaną rzecz<span class="opis">np. spodnie, koszula</span></label><span class="budzet-kwota" id="b1v">~ ${zl(st.b1)}</span></div>
            <input id="b1" type="range" min="30" max="3000" step="10" value="${st.b1}" style="--p:${p1}%"></div>
          <div class="budzet-wiersz"><div class="budzet-gora"><label for="b2">Na resztę stylizacji<span class="opis">razem z dodatkami</span></label><span class="budzet-kwota" id="b2v">~ ${zl(st.b2)}</span></div>
            <input id="b2" type="range" min="0" max="5000" step="10" value="${st.b2}" style="--p:${p2}%"></div>
        </div>
        <p class="maly szary" style="margin-top:10px;text-align:center">To kwota, w którą celujesz. Gdy warto dołożyć, pokażemy też rzeczy trochę droższe.</p>
      </div>

      <button class="btn" style="margin-top:20px" data-akcja="szukaj">${st.tryb === 'rzecz' ? 'Znajdź w sklepach' : 'Znajdź stylizacje'} ${IK.iskra}</button>

      <div class="sekcja">
        <p style="text-align:center;margin-bottom:12px;font-size:15px">Lub wybierz, czego potrzebujesz</p>
        <div class="tryby">${tryby.map(([v, , n]) => `<button class="tryb" aria-pressed="${st.tryb === v}" data-akcja="tryb" data-v="${v}"><img class="tryb-ikona" src="img/ikony/tryb-${v}.webp" alt="">${n}</button>`).join('')}</div>
      </div>

      <div class="sekcja">
        <p style="margin-bottom:10px;font-size:15px">Okazja</p>
        <div class="karuzela okazje-kafle">${okazje.map(([v, n]) => `<button class="okazja-kafel" aria-pressed="${st.okazja === v}" data-akcja="okazja" data-v="${v}"><span class="okazja-foto"><img src="img/okazje/okazja-${st.dzial === 'meskie' ? 'm' : 'd'}-${v}.webp" alt="" loading="lazy"></span><span>${n}</span></button>`).join('')}</div>
      </div>
      <input type="file" id="plik" accept="image/*" hidden>`
    };
  };

  EKRANY.analiza = () => {
    const s = sezon();
    const kroki = [
      ['Aktualne trendy', `sezon ${s.nazwa.toLowerCase()} ${s.rok}`],
      ['Ceny i dostępność w sklepach', 'sklepy internetowe i Google Shopping'],
      ['Promocje i wyprzedaże', 'porównanie z najniższą ceną z 30 dni'],
      ['Dobór stylizacji i dodatków', 'w ramach Twojego budżetu']
    ];
    return {
      menu: false, klasa: 'bez-menu',
      html: `<section class="analiza">
        <div class="pierscien"><img src="icons/icon-192.png" alt=""></div>
        <h1 style="font-size:34px;font-weight:400">Analizuję dla Ciebie…</h1>
        <ol class="kroki" id="kroki">${kroki.map(([a, b], i) => `<li data-i="${i}"><span class="znak"></span><div><b>${a}</b><span>${b}</span></div></li>`).join('')}</ol>
      </section>`,
      po: () => {
        const li = [...document.querySelectorAll('#kroki li')];
        let i = 0, gotowe = false;
        const ctrl = new AbortController();
        const czas = setTimeout(() => ctrl.abort(), 150000);
        fetch(`${API}/szukaj?q=${encodeURIComponent(st.zapytanie)}&dzial=${st.dzial}&okazja=${st.okazja || ''}`, { signal: ctrl.signal })
          .then((r) => r.json())
          .then((d) => { wynik = d && d.produkty ? d : null; if (wynik) wynik.kodOkazji = st.okazja || ''; })
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
          li[i].classList.add('aktywny'); i++;
          EKRANY.analiza.timer = setTimeout(krok, 700);
        };
        krok();
      }
    };
  };

  let zakladka = 'stylizacje', strefa = 'budzet', tylkoPrawdziwe = false;
  EKRANY.wyniki = () => {
    const q = st.zapytanie || 'Skórzane spodnie';
    if (wynik && wynik.zapytanie.toLowerCase() === q.trim().replace(/\s+/g, ' ').toLowerCase().slice(0, 80) && wynik.dzial === st.dzial && (wynik.kodOkazji || '') === (st.okazja || '')) return wynikiPrawdziwe(q);
    const baza = DEMO.P.filter((p) => p.id.startsWith('p'));
    let lista;
    if (strefa === 'tanio') lista = baza.filter((p) => p.strefa !== 'second').slice().sort((a, b) => a.cena - b.cena);
    else lista = baza.filter((p) => p.strefa === strefa);
    if (tylkoPrawdziwe) lista = lista.filter((p) => p.weryf === 'ok');
    const ile = (z) => baza.filter((p) => p.strefa === z).length;
    const inne = q.trim().toLowerCase() !== 'skórzane spodnie';
    return {
      akt: 'szukaj',
      html: `<div class="naglowek"><a class="ikonka bez" href="#/szukaj" aria-label="Zmień wyszukiwanie">${IK.wstecz}</a><h1>${esc(q)}</h1><span class="puste"></span></div>
      ${demoZnak()}
      ${inne ? `<div class="info uwaga" style="margin-bottom:14px">${IK.uwaga}<p>W wersji próbnej zawsze pokazujemy przykład dla skórzanych spodni. Prawdziwe wyszukiwanie zadziała po podłączeniu serwera.</p></div>` : ''}
      <div class="przelacznik" role="tablist" aria-label="Wyniki">
        <button role="tab" aria-selected="${zakladka === 'stylizacje'}" data-akcja="zakladka" data-v="stylizacje">Stylizacje (${DEMO.S.length})</button>
        <button role="tab" aria-selected="${zakladka === 'sklepy'}" data-akcja="zakladka" data-v="sklepy">W sklepach (${baza.length})</button>
      </div>
      ${zakladka === 'stylizacje' ? `
        <p class="szary maly" style="margin:14px 0 12px">Trzy gotowe zestawy z rzeczy dostępnych dziś w sklepach. Dotknij, żeby zobaczyć szczegóły i ceny.</p>
        <div class="karuzela">${DEMO.S.map(kartaStylizacji).join('')}</div>` : `
        <div class="chipy" style="margin-top:14px">
          <button class="chip" aria-pressed="${strefa === 'budzet'}" data-akcja="strefa" data-v="budzet">W budżecie <span class="ile">${ile('budzet')}</span></button>
          <button class="chip" aria-pressed="${strefa === 'wiecej'}" data-akcja="strefa" data-v="wiecej">Warto dołożyć <span class="ile">${ile('wiecej')}</span></button>
          <button class="chip" aria-pressed="${strefa === 'tanio'}" data-akcja="strefa" data-v="tanio">Najtaniej</button>
          <button class="chip" aria-pressed="${strefa === 'second'}" data-akcja="strefa" data-v="second">${ikonaW('second', 15)} Z drugiej ręki <span class="ile">${ile('second')}</span></button>
        </div>
        <div class="chipy" style="margin-top:8px"><button class="chip" aria-pressed="${tylkoPrawdziwe}" data-akcja="tylkoPrawdziwe">${ikonaW('ok', 14)} Tylko potwierdzone promocje</button></div>
        <p class="szary maly" style="margin:12px 0">${strefa === 'wiecej' ? 'Trochę ponad Twój cel, ale z wyraźnie lepszym materiałem albo dobrą obniżką.' : strefa === 'second' ? 'Ogłoszenia z serwisów z używaną odzieżą. Stan opisuje sprzedający.' : strefa === 'tanio' ? 'Wszystkie nowe produkty od najtańszego.' : 'Produkty w okolicy Twojej kwoty.'}</p>
        ${lista.length ? `<div class="siatka">${lista.map(kartaProduktu).join('')}</div>` : `<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/pusty-okazje.webp" alt=""><p>Brak potwierdzonych promocji w tej grupie. Wyłącz filtr, żeby zobaczyć wszystkie produkty.</p></div>`}`}`
    };
  };

  const SECOND = /vinted|olx|allegro lokalnie|sprzedajemy|depop|remixshop/i;
  function strefaProduktu(p) {
    if (SECOND.test(p.sklep)) return 'second';
    if (p.cena <= st.b1 * 1.15) return 'budzet';
    if (p.cena <= st.b1 * 1.8) return 'wiecej';
    return 'drozej';
  }
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

  function wynikiPrawdziwe(q) {
    const P = wynik.produkty;
    const ile = (z) => P.filter((p) => strefaProduktu(p) === z).length;
    const nowe = P.filter((p) => strefaProduktu(p) !== 'second');
    let lista = strefa === 'tanio' ? nowe.slice().sort((a, b) => a.cena - b.cena) : P.filter((p) => strefaProduktu(p) === strefa).sort((a, b) => (b.punkty || 0) - (a.punkty || 0) || (b.stara ? 1 : 0) - (a.stara ? 1 : 0) || a.cena - b.cena);
    if (tylkoPrawdziwe) lista = lista.filter((p) => p.stara);
    let zamiast = '';
    if (!lista.length && strefa === 'budzet' && !tylkoPrawdziwe && nowe.length) {
      const min = Math.min(...nowe.map((p) => p.cena));
      zamiast = `<div class="info neutral" style="margin-bottom:14px">${IK.info}<p>W okolicy ${zl(st.b1)} nic nie znaleźliśmy. Najtańsza sensowna opcja kosztuje ${zl(min)}, poniżej pokazujemy wszystko od najtańszego.</p></div>`;
      lista = nowe.slice().sort((a, b) => a.cena - b.cena);
    }
    const ileSklepow = new Set(P.map((p) => p.sklep)).size;
    const kiedy = new Date(wynik.sprawdzono * 1000).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
    const uwagi = (wynik.sklepy || []).filter((x) => x.stan !== 'ok').map((x) => `${x.nazwa}: ${x.stan}`).join(', ');
    return {
      akt: 'szukaj',
      html: `<div class="naglowek"><a class="ikonka bez" href="#/szukaj" aria-label="Zmień wyszukiwanie">${IK.wstecz}</a><h1>${esc(q)}</h1><span class="puste"></span></div>
      <p class="szary maly" style="text-align:center;margin:-6px 0 14px">${P.length} produktów z ${ileSklepow} ${ileSklepow === 1 ? 'sklepu' : 'sklepów'}, sprawdzone o ${kiedy}${uwagi ? `<br>${esc(uwagi)}` : ''}</p>
      ${wynik.okazja ? `<div class="info neutral" style="margin:-4px 0 14px">${IK.iskra}<p><b>Pod okazję: ${esc(wynik.okazja)}.</b> ${wynik.klasyfikacja === 'ai' ? 'Każdą rzecz sprawdził stylista AI na zdjęciu, a potem nasze stałe zasady (np. bez dużych nadruków, bluz i dresów). Małe logo marki na piersi nie jest przeszkodą.' : 'Stylista AI jest chwilowo niedostępny, więc pokazujemy tylko rzeczy, które według opisu sklepu są jednoznacznie eleganckie.'}${wynik.pominiete ? ` Pominęliśmy ${wynik.pominiete} ${wynik.pominiete === 1 ? 'rzecz, która' : 'rzeczy, które'} na tę okazję się nie nadają.` : ''} Coś nie pasuje? Otwórz produkt i dotknij „Nie pasuje”.</p></div>` : ''}
      <div class="przelacznik" role="tablist" aria-label="Wyniki">
        <button role="tab" aria-selected="${zakladka === 'sklepy'}" data-akcja="zakladka" data-v="sklepy">W sklepach (${P.length})</button>
        <button role="tab" aria-selected="${zakladka === 'stylizacje'}" data-akcja="zakladka" data-v="stylizacje">Stylizacje</button>
      </div>
      ${zakladka === 'stylizacje' ? `
        <div class="info uwaga" style="margin:14px 0">${IK.info}<p>Stylizacje z prawdziwych produktów to następny etap budowy. Poniżej przykład, jak będą wyglądać.</p></div>
        <div class="karuzela">${DEMO.S.map(kartaStylizacji).join('')}</div>` : `
        <div class="chipy" style="margin-top:14px">
          <button class="chip" aria-pressed="${strefa === 'budzet'}" data-akcja="strefa" data-v="budzet">W budżecie <span class="ile">${ile('budzet')}</span></button>
          <button class="chip" aria-pressed="${strefa === 'wiecej'}" data-akcja="strefa" data-v="wiecej">Warto dołożyć <span class="ile">${ile('wiecej')}</span></button>
          <button class="chip" aria-pressed="${strefa === 'tanio'}" data-akcja="strefa" data-v="tanio">Najtaniej</button>
          <button class="chip" aria-pressed="${strefa === 'second'}" data-akcja="strefa" data-v="second">${ikonaW('second', 15)} Z drugiej ręki <span class="ile">${ile('second')}</span></button>
        </div>
        <div class="chipy" style="margin-top:8px"><button class="chip" aria-pressed="${tylkoPrawdziwe}" data-akcja="tylkoPrawdziwe">${ikonaW('okazje', 14)} Tylko promocje</button></div>
        <p class="szary maly" style="margin:12px 0">${strefa === 'wiecej' ? `Od ${zl(Math.round(st.b1 * 1.15))} do ${zl(Math.round(st.b1 * 1.8))}: trochę ponad Twój cel.` : strefa === 'second' ? 'Ogłoszenia z serwisów z używaną odzieżą. Stan opisuje sprzedający.' : strefa === 'tanio' ? 'Wszystkie nowe produkty od najtańszego.' : `Do ${zl(Math.round(st.b1 * 1.15))}, czyli w okolicy Twojej kwoty.`}</p>
        ${zamiast}
        ${lista.length ? siatkaWynikow(lista, q) : `<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/${tylkoPrawdziwe ? 'pusty-okazje' : 'pusty-wyniki'}.webp" alt=""><p>${strefa === 'second' ? 'Tym razem nie znaleźliśmy ogłoszeń z drugiej ręki.' : tylkoPrawdziwe ? 'Brak promocji w tej grupie. Wyłącz filtr, żeby zobaczyć wszystko.' : 'Brak produktów w tej grupie. Zajrzyj do „Najtaniej”.'}</p></div>`}`}`
    };
  }

  EKRANY.stylizacja = (id) => {
    const s = DEMO.S.find((x) => x.id === id) || DEMO.S[0];
    const el = s.el.map(prod);
    const suma = el.reduce((a, p) => a + p.cena, 0);
    const plan = st.b1 + st.b2;
    const roznica = suma - plan;
    const zapisana = st.zapisane.includes(s.id);
    return {
      akt: 'szukaj', po: () => document.body.classList.add('z-paskiem'),
      html: `<div class="naglowek"><a class="ikonka bez" href="#/wyniki" aria-label="Wróć do wyników">${IK.wstecz}</a><h1>Stylizacja ${esc(s.nazwa.toLowerCase())}</h1>
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
  EKRANY.produkt = (id) => {
    const p = prod(id) || DEMO.P[0];
    const r = rabat(p);
    const ul = st.ulubione.includes(p.id);
    const alert = st.alerty.find((a) => a.id === p.id);
    const wybr = st.rozmiar[p.id];
    const rozm = listaRozmiarow(p.rozmiary);
    let werInfo = '';
    if (p.weryf === 'ok') werInfo = `<div class="info ok">${IK.ok}<p><b>Obniżka jest prawdziwa.</b> Najniższa cena z 30 dni przed obniżką: ${zl(p.omnibus)}.</p></div>`;
    else if (p.weryf === 'pozorna') werInfo = `<div class="info uwaga">${IK.uwaga}<p><b>Promocja pozorna.</b> Przez ostatnie 30 dni produkt kosztował tyle samo (${zl(p.omnibus)}). Przekreślona cena nie była aktualna.</p></div>`;
    else if (p.weryf === 'second') werInfo = `<div class="info neutral">${IK.info}<p>Ogłoszenie z drugiej ręki. Stan i opis podaje sprzedający, sprawdź zdjęcia przed zakupem.</p></div>`;
    else if (p.weryf === 'sklep') werInfo = `<div class="info neutral">${IK.info}<p><b>Obniżkę podaje sklep</b> (wcześniej ${zl(p.stara)}). Historię ceny tego produktu zbieramy od ${new Date(p.sprawdzono * 1000).toLocaleDateString('pl-PL')}. Po 30 dniach ocenimy, czy obniżka jest prawdziwa.</p></div>`;
    if (p.weryf === 'pozorna' && prawdziwy(p)) werInfo = `<div class="info uwaga">${IK.uwaga}<p><b>Promocja pozorna.</b> ${p.omnibus ? `Najniższa cena z 30 dni przed obniżką, podana przez sklep, to ${zl(p.omnibus)}, czyli tyle samo albo mniej niż teraz.` : 'W ostatnich 30 dniach ten produkt kosztował już tyle samo albo mniej.'} Przekreślona cena nie była aktualna.</p></div>`;
    return {
      akt: 'szukaj', menu: false, klasa: 'bez-menu',
      po: () => {
        const wc = document.querySelector('#hist .wykres-ceny'); if (wc) G.podpnijWykresCeny(wc, zl);
        if (!prawdziwy(p)) return;
        fetch(`${API}/historia?id=${encodeURIComponent(p.id)}`).then((r) => r.json()).then((d) => {
          const el = document.getElementById('hist'); if (!el) return;
          const c = (d.ceny || []).filter((x) => Date.now() / 1000 - x[1] < 31 * 86400);
          if (c.length >= 2 && (c[c.length - 1][1] - c[0][1]) > 86400) {
            el.innerHTML = G.wykresCeny(c, zl);
            G.podpnijWykresCeny(el.querySelector('.wykres-ceny'), zl);
            document.getElementById('hist-opis').textContent = c.every((x) => x[0] === c[0][0]) ? 'bez zmian' : 'zmieniała się';
          } else {
            el.innerHTML = `<p class="maly szary">Historię ceny tego produktu zbieramy od ${new Date((c[0] ? c[0][1] : p.sprawdzono) * 1000).toLocaleDateString('pl-PL')}. Wykres pojawi się po kilku dniach, a ocena promocji po 30 dniach.</p>`;
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
        <div class="karta"><div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px"><b style="font-weight:500">Cena przez 30 dni</b><span class="maly szary" id="hist-opis">${p.historia ? (p.historia.every((v) => v === p.historia[0]) ? 'bez zmian' : 'zmieniała się') : ''}</span></div>
          <div id="hist">${p.historia ? G.wykresCeny(p.historia.map((v, i) => [v, Date.now() / 1000 - (p.historia.length - 1 - i) * 86400]), zl) : '<p class="maly szary">Sprawdzam historię ceny…</p>'}</div></div>
        ${rozm.length ? `<div><div style="display:flex;justify-content:space-between;margin-bottom:10px"><b style="font-weight:500">Rozmiar</b><span class="maly szary">${esc(p.material || '')}</span></div>
          <div class="rozmiary">${rozm.map((r) => `<button aria-pressed="${wybr === r}" ${(p.brak || []).includes(r) ? 'disabled aria-label="' + r + ', brak"' : ''} data-akcja="rozmiar" data-id="${p.id}" data-v="${r}">${r}</button>`).join('')}</div></div>` : ''}
        <div style="display:flex;flex-direction:column;gap:10px;margin-top:4px">
          <a class="btn" href="${p.url}" target="_blank" rel="noopener" ${viaGoogle(p) ? `data-akcja="doSklepu" data-id="${p.id}"` : ''}>Kup w sklepie ${esc(p.sklep)}</a>
          ${viaGoogle(p) ? '<p class="maly szary" style="margin:-4px 2px 0">Ten produkt znaleźliśmy przez Google Shopping. Po dotknięciu wyszukamy jego stronę w sklepie.</p>' : ''}
          <button class="btn drugi" data-akcja="alert" data-id="${p.id}">${IK.dzwonek} ${alert ? `Alert ustawiony: ${zl(alert.cel)}` : 'Powiadom, gdy stanieje'}</button>
          <button class="btn drugi" data-akcja="dodajProdukt" data-id="${p.id}">${IK.torba} ${st.koszyk.includes(p.id) ? 'Jest w zakupach' : 'Dodaj do zakupów'}</button>
          ${prawdziwy(p) ? '' : `<a class="btn drugi" href="#/wyniki" data-akcja="dobierz">${IK.iskra} Dobierz do tego stylizację</a>`}
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
      <div class="okladka wejscie" style="--foto:url('img/${s.plik}.jpg');margin-top:14px"><div><p class="maly" style="color:#E7CFC6;margin:0 0 6px">Kluczowe trendy</p><h2>${s.nazwa}<br>${s.rok}</h2></div></div>
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
    let lista = DEMO.OK.filter((o) => o.typ === zakladkaOkazji);
    const obs = st.ulubione.map(prod).filter(Boolean);
    return {
      akt: 'okazje',
      html: `<div class="naglowek"><span class="puste"></span><h1>Najlepsze okazje</h1><span class="puste"></span></div>
      ${demoZnak()}
      <div class="przelacznik trzy" role="tablist" aria-label="Rodzaj okazji">
        ${[['promocje', 'Promocje'], ['wyprzedaze', 'Wyprzedaże'], ['obserwowane', 'Obserwowane']].map(([v, n]) => `<button role="tab" aria-selected="${zakladkaOkazji === v}" data-akcja="zakladkaOkazji" data-v="${v}">${n}</button>`).join('')}</div>
      <div style="margin-top:16px">
      ${zakladkaOkazji === 'obserwowane'
        ? (obs.length ? `<div class="elementy">${obs.map(wierszElementu).join('')}</div>` : `<div class="pusty"><img class="ilustracja-pusta" src="img/ikony/pusty-obserwowane.webp" alt=""><p>Dotknij serca przy produkcie, żeby go obserwować. Gdy stanieje, zobaczysz to tutaj.</p><a class="btn maly" href="#/szukaj">Szukaj produktów</a></div>`)
        : lista.map(kartaOkazji).join('')}
      </div>
      ${zakladkaOkazji !== 'obserwowane' ? '<p class="maly szary" style="margin-top:14px">Każdą promocję porównujemy z najniższą ceną z 30 dni przed obniżką. Pozorne oznaczamy na pomarańczowo.</p>' : ''}`
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
    return {
      akt: 'start',
      html: `<div class="naglowek"><a class="ikonka bez" href="#/start" aria-label="Wróć">${IK.wstecz}</a><h1>Alerty cenowe</h1><span class="puste"></span></div>
      ${al.length ? `<div class="elementy">${al.map(({ a, p }) => `<div class="element"><a class="miniatura" href="#/produkt/${p.id}" aria-label="${esc(p.nazwa)}">${foto(p)}</a>
        <div class="opis"><div class="nazwa">${esc(p.nazwa)}</div><div class="sklep">${esc(p.sklep)}, teraz ${zl(p.cena)}</div><div class="maly" style="color:var(--roz);margin-top:3px">Powiadom poniżej ${zl(a.cel)}</div></div>
        <button class="ikonka bez" data-akcja="usunAlert" data-id="${p.id}" aria-label="Usuń alert">${IK.kosz}</button></div>`).join('')}</div>
        <div class="info uwaga" style="margin-top:18px">${IK.uwaga}<p>Powiadomienia na telefon zaczną przychodzić po podłączeniu serwera, który codziennie sprawdza ceny.</p></div>`
      : `<div class="pusty"><img class="ilustracja-pusta" src="img/puste/pusty-alerty.webp" alt=""><p>Nie masz jeszcze alertów. Na stronie produktu dotknij „Powiadom, gdy stanieje”.</p></div>`}`
    };
  };

  EKRANY.profil = () => ({
    akt: 'start',
    html: `<div class="naglowek"><a class="ikonka bez" href="#/start" aria-label="Wróć">${IK.wstecz}</a><h1>Ustawienia</h1><span class="puste"></span></div>
    <img class="ilustracja-ustawien" src="img/ikony/rozmiary.webp" alt="">
    <p class="szary" style="text-align:center;margin:0 0 16px">Twoje rozmiary pomagają dobrać rzeczy. Zapisują się tylko na tym telefonie.</p>
    <div class="karta" style="padding:4px 16px">
      <div class="ustawienie"><label for="u-dzial">Dział na start</label><select id="u-dzial" data-ust="dzial"><option value="damskie" ${st.dzial === 'damskie' ? 'selected' : ''}>Damskie</option><option value="meskie" ${st.dzial === 'meskie' ? 'selected' : ''}>Męskie</option></select></div>
      <div class="ustawienie"><label for="u-gora">Rozmiar góry</label><select id="u-gora" data-ust="gora">${['', 'XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL'].map((r) => `<option value="${r}" ${st.ust.gora === r ? 'selected' : ''}>${r || 'nie podano'}</option>`).join('')}</select></div>
      <div class="ustawienie"><label for="u-dol">Rozmiar spodni</label><select id="u-dol" data-ust="dol">${['', '32', '34', '36', '38', '40', '42', '44', '46', '48', '50', '52', '54'].map((r) => `<option value="${r}" ${st.ust.dol === r ? 'selected' : ''}>${r || 'nie podano'}</option>`).join('')}</select></div>
      <div class="ustawienie"><label for="u-buty">Rozmiar butów</label><select id="u-buty" data-ust="buty">${['', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47'].map((r) => `<option value="${r}" ${st.ust.buty === r ? 'selected' : ''}>${r || 'nie podano'}</option>`).join('')}</select></div>
    </div>
    <div class="karta" style="padding:4px 16px;margin-top:14px">
      <div class="ustawienie"><span>Pokaż ekran powitalny</span><button class="link" data-akcja="pokazPowitanie">Pokaż</button></div>
      <div class="ustawienie"><span>Usuń wszystkie dane z telefonu</span><button class="link" data-akcja="wyczyscWszystko">Usuń</button></div>
    </div>
    <p class="maly szary" style="text-align:center;margin-top:20px">Trendo ${WERSJA}, wersja próbna</p>`
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
      <div class="podpis"><p class="maly" style="color:#E7CFC6">Stylizacja ${DEMO.S.indexOf(s) + 1} z ${DEMO.S.length}</p><h3>${esc(s.nazwa)}</h3>
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
      : p.weryf === 'pozorna' ? `<div class="weryf uwaga">${IK.uwaga}Promocja pozorna: przez 30 dni było ${zl(p.omnibus)}</div>`
      : p.weryf === 'second' ? `<div class="weryf" style="color:var(--szary)">${IK.second}Z drugiej ręki</div>`
      : p.weryf === 'sklep' ? `<div class="weryf" style="color:var(--promo)">${IK.okazje}Promocja według sklepu</div>` : '';
    return `<div class="produkt"><a href="#/produkt/${p.id}" class="foto" aria-label="${esc(p.sklep + ', ' + p.nazwa)}">${foto(p)}${r ? `<span class="rabat">−${r}%</span>` : ''}</a>
      <button class="serce" style="position:relative;margin:-50px 8px 14px auto;width:36px;height:36px;border-radius:18px;background:rgba(14,9,12,.6);border:none;display:flex;align-items:center;justify-content:center" data-akcja="ulubiony" data-id="${p.id}" aria-pressed="${ul}" aria-label="${ul ? 'Usuń z obserwowanych' : 'Obserwuj'}">${(ul ? IK.sercePelne : IK.serce).replace('<svg', '<svg width="18" height="18"')}</button>
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
      <p class="maly szary" style="margin:10px 0 18px">Damy znać także wtedy, gdy wróci Twój rozmiar.</p>
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
    const ok = wynik && wynik.okazja ? wynik.okazja : '';
    const pow = [ok ? ['okazja', `Nie pasuje na okazję: ${ok}`] : null, ['rzecz', 'To inna rzecz, niż szukałam / szukałem'],
      ['plec', 'Nie ten dział (damskie / męskie)'], ['zdjecie', 'Zdjęcie nie zgadza się z opisem'], ['inne', 'Inny powód']].filter(Boolean);
    ARK.innerHTML = `<div class="panel" role="dialog" aria-modal="true" aria-labelledby="ark-t"><div class="uchwyt"></div>
      <h2 id="ark-t">Co jest nie tak?</h2><p class="szary" style="margin:6px 0 18px">${esc(p.sklep)}, ${esc(p.nazwa)}.</p>
      <div style="display:flex;flex-direction:column;gap:10px">${pow.map(([v, t]) => `<button class="btn drugi" data-akcja="wyslijZgloszenie" data-id="${p.id}" data-v="${v}">${esc(t)}</button>`).join('')}</div>
      <p class="maly szary" style="margin:14px 0 4px">${ok ? 'Po zgłoszeniu ta rzecz od razu zniknie z wyników na tę okazję. ' : ''}Zgłoszenie pomaga nam poprawić zasady dla wszystkich.</p>
      <button class="link" style="margin:10px auto 0;display:flex" data-akcja="zamknijArkusz">Anuluj</button></div>`;
    ARK.hidden = false;
  }
  ARK.addEventListener('click', (e) => { if (e.target === ARK) ARK.hidden = true; });

  /* ---------- akcje ---------- */
  const A = {
    zacznij() { st.witaj = true; zapisz(); location.hash = '#/start'; },
    witajDalej() { const sl = document.getElementById('slajdy'); sl.scrollTo({ left: (Math.round(sl.scrollLeft / sl.clientWidth) + 1) * sl.clientWidth, behavior: 'smooth' }); },
    witajSlajd(el) { const sl = document.getElementById('slajdy'); sl.scrollTo({ left: Number(el.dataset.i) * sl.clientWidth, behavior: 'smooth' }); },
    dzial(el) { st.dzial = el.dataset.v; zapisz(); render(); },
    tryb(el) {
      if (el.dataset.v === 'zdjecie') return A.zdjecie();
      st.tryb = el.dataset.v; zapisz(); render();
    },
    okazja(el) {
      st.okazja = el.dataset.v; zapisz();
      // bez przerysowania ekranu (zostajemy w tym samym miejscu przewinięcia)
      document.querySelectorAll('[data-akcja="okazja"]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === st.okazja)));
    },
    zdjecie() { const f = document.getElementById('plik'); if (f) f.click(); },
    szukaj() {
      const q = (document.getElementById('q').value || '').trim();
      if (!q && st.tryb !== 'outfit') { komunikat('Wpisz, czego szukasz.'); document.getElementById('q').focus(); return; }
      st.zapytanie = q || 'Cały outfit';
      st.ostatnie = [st.zapytanie].concat(st.ostatnie.filter((x) => x.toLowerCase() !== st.zapytanie.toLowerCase())).slice(0, 8);
      zakladka = 'sklepy'; strefa = 'budzet'; tylkoPrawdziwe = false;
      zapisz(); location.hash = '#/analiza';
    },
    kategoria(el) { st.zapytanie = el.dataset.q; st.tryb = 'rzecz'; zapisz(); location.hash = '#/szukaj'; },
    szukajOstatnie(el) { st.zapytanie = el.dataset.q; zapisz(); location.hash = '#/szukaj'; },
    szukajTrendu(el, e) { e.preventDefault(); ARK.hidden = true; st.zapytanie = el.dataset.q; zapisz(); location.hash = '#/szukaj'; },
    zakladka(el) { zakladka = el.dataset.v; render(); },
    strefa(el) { strefa = el.dataset.v; render(); },
    tylkoPrawdziwe() { tylkoPrawdziwe = !tylkoPrawdziwe; render(); },
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
      if (i >= 0) { st.ulubione.splice(i, 1); komunikat('Usunięto z obserwowanych'); } else { st.ulubione.push(id); komunikat('Obserwujesz ten produkt'); }
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
    rozmiar(el) { st.rozmiar[el.dataset.id] = el.dataset.v; zapisz(); render(true); },
    alert(el) { arkuszAlertu(el.dataset.id); },
    zapiszAlert(el) {
      const id = el.dataset.id, cel = +document.getElementById('cel').value;
      st.alerty = st.alerty.filter((a) => a.id !== id).concat([{ id, cel }]);
      if (!st.ulubione.includes(id)) st.ulubione.push(id);
      zapamietaj(prod(id));
      zapisz(); ARK.hidden = true; render(true);
      komunikat(`Alert ustawiony na ${zl(cel)}`);
    },
    usunAlert(el) { st.alerty = st.alerty.filter((a) => a.id !== el.dataset.id); zapisz(); ARK.hidden = true; render(true); },
    zamknijArkusz() { ARK.hidden = true; },
    niePasuje(el) { arkuszZgloszenia(el.dataset.id); },
    zrodlaTrendu(el) { arkuszZrodel(+el.dataset.i); },
    wyslijZgloszenie(el) {
      const p = prod(el.dataset.id); if (!p) return;
      const okazja = el.dataset.v === 'okazja' && wynik ? (wynik.kodOkazji || '') : '';
      const par = new URLSearchParams({ id: p.id, okazja, q: (wynik && wynik.zapytanie) || st.zapytanie || '', dzial: st.dzial, powod: el.dataset.v, nazwa: p.nazwa, sklep: p.sklep, zdjecie: p.zdjecie || '' });
      ARK.hidden = true;
      fetch(`${API}/zglos?${par}`).then((r) => {
        if (!r.ok) throw new Error();
        if (okazja && wynik) { wynik.produkty = wynik.produkty.filter((x) => x.id !== p.id); try { sessionStorage.setItem('trendo-wynik', JSON.stringify(wynik)); } catch (e) {} }
        komunikat(okazja ? 'Dziękujemy. Ta rzecz zniknęła z wyników na tę okazję.' : 'Dziękujemy, zgłoszenie zapisane.');
      }).catch(() => komunikat('Nie udało się wysłać zgłoszenia. Spróbuj za chwilę.'));
    },
    wstecz() { if (history.length > 1) history.back(); else location.hash = '#/wyniki'; },
    dobierz() { zakladka = 'stylizacje'; },
    dzialTrendow(el) { dzialTrendow = el.dataset.v; render(); },
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
      const p = t.id === 'b1' ? (t.value - 30) / (3000 - 30) * 100 : t.value / 5000 * 100;
      t.style.setProperty('--p', p + '%');
      document.getElementById(t.id + 'v').textContent = '~ ' + zl(+t.value);
    }
    if (t.id === 'q') { st.zapytanie = t.value; zapisz(); }
  });
  document.addEventListener('change', (e) => {
    const t = e.target;
    if (t.dataset.ust) {
      if (t.dataset.ust === 'dzial') { st.dzial = t.value; dzialTrendow = null; } else st.ust[t.dataset.ust] = t.value;
      zapisz(); komunikat('Zapisano');
    }
    if (t.id === 'plik' && t.files && t.files[0]) {
      komunikat('Szukanie po zdjęciu zadziała po podłączeniu serwera.');
      t.value = '';
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.id === 'q') { e.preventDefault(); A.szukaj(); }
    if (e.key === 'Escape' && !ARK.hidden) ARK.hidden = true;
  });

  /* ---------- router ---------- */
  function render(zachowajPozycje) {
    clearTimeout(EKRANY.analiza.timer);
    document.body.classList.remove('z-paskiem');
    let [nazwa, arg] = location.hash.replace(/^#\/?/, '').split('/');
    if (!nazwa) nazwa = st.witaj ? 'start' : 'witaj';
    if (nazwa === 'witaj' && st.witaj && !location.hash.includes('witaj')) nazwa = 'start';
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
    if (ekran.menu === false) MENU.hidden = true; else { MENU.hidden = false; rysujMenu(ekran.akt); }
    if (zachowajPozycje) window.scrollTo(0, y); else window.scrollTo(0, 0);
    if (ekran.po) { try { ekran.po(); } catch (e) { console.error(e); } }
    document.title = nazwa === 'start' || nazwa === 'witaj' ? 'Trendo' : 'Trendo: ' + (E.querySelector('h1') ? E.querySelector('h1').textContent.replace(/\s+/g, ' ') : '');
  }
  window.addEventListener('hashchange', () => { ARK.hidden = true; render(); });
  render();

  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
})();
