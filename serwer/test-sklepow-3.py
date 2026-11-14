#!/usr/bin/env python3
"""Trendo: trzeci test sklepów - przez przeglądarkę na serwerze (Chromium, Playwright).
Dla każdego sklepu przeglądarka próbuje dojść do strony produktu i odczytać nazwę, cenę i zdjęcie.
Kolejność: produkt z mapy strony -> produkty widoczne na stronie głównej -> produkty z kategorii.
Jedna karta naraz, przeglądarka zamyka się na końcu. Wynik: ~/trendo-test3.txt
Uruchomienie: ~/trendo-scraper/bin/python ~/test3.py
"""
import asyncio, importlib.util, json, os, re, sys, time

TU = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("t2", os.path.join(TU, "test2.py") if os.path.exists(os.path.join(TU, "test2.py")) else os.path.join(TU, "test-sklepow-2.py"))
t2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t2)

from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
BLOKADA = re.compile(r"(captcha|access denied|verify you are human|pardon our interruption|request unsuccessful|are you a robot|robot check|zablokowan|blocked|unusual traffic|just a moment)", re.I)
TYLKO = sys.argv[1:]  # opcjonalnie: nazwy sklepów do sprawdzenia

ODCZYT = r"""() => {
  const o = {};
  for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
    try {
      let j = JSON.parse(s.textContent);
      const lista = Array.isArray(j) ? j : (j['@graph'] || [j]);
      for (const x of lista) {
        const t = x && x['@type'];
        if (t === 'Product' || (Array.isArray(t) && t.includes('Product')) || t === 'ProductGroup') {
          o.nazwa = o.nazwa || x.name;
          let of = x.offers; if (Array.isArray(of)) of = of[0];
          if (of && of.offers) { let q = of.offers; if (Array.isArray(q)) q = q[0]; of = q || of; }
          if (of) { o.cena = o.cena || of.price || of.lowPrice; o.waluta = o.waluta || of.priceCurrency; }
          let im = x.image; if (Array.isArray(im)) im = im[0]; if (im && typeof im === 'object') im = im.url || im.contentUrl;
          o.zdjecie = o.zdjecie || im;
        }
      }
    } catch (e) {}
  }
  const meta = (p) => { const m = document.querySelector(`meta[property="${p}"],meta[name="${p}"],meta[itemprop="${p}"]`); return m && m.content; };
  o.cena = o.cena || meta('product:price:amount') || meta('og:price:amount') || meta('price');
  o.zdjecie = o.zdjecie || meta('og:image');
  o.nazwa = o.nazwa || meta('og:title') || document.title;
  if (!o.cena) {
    const t = document.body ? document.body.innerText : '';
    const m = t.match(/(\d{1,5}(?:[  .]\d{3})*,\d{2})\s*(zł|PLN)/) || t.match(/(\d{1,5})\s*(zł|PLN)/);
    if (m) o.cena = m[1] + ' (z tekstu strony)';
  }
  if (!o.zdjecie) {
    let best = null, ba = 0;
    for (const i of document.images) { const a = (i.naturalWidth || i.width) * (i.naturalHeight || i.height); if (a > ba) { ba = a; best = i.currentSrc || i.src; } }
    o.zdjecie = best;
  }
  return o;
}"""

LINKI_PRODUKTOW = r"""() => {
  const re = /\d+(?:[  .]\d{3})*(?:,\d{2})?\s*(zł|PLN)/i;
  const out = [];
  for (const a of document.querySelectorAll('a[href]')) {
    if (!a.querySelector('img,picture')) continue;
    let k = a; let ok = false;
    for (let i = 0; i < 5 && k; i++) { if (re.test(k.innerText || '')) { ok = true; break; } k = k.parentElement; }
    if (ok && a.href.startsWith('http') && !out.includes(a.href)) out.push(a.href);
    if (out.length >= 8) break;
  }
  return out;
}"""

LINKI_KATEGORII = r"""() => {
  const re = /(spodnie|kobiet|damsk|ona\b|nowości|nowosci|odzież|odziez|women|woman|buty|sukienk)/i;
  const out = [];
  for (const a of document.querySelectorAll('a[href]')) {
    const t = (a.innerText || a.getAttribute('aria-label') || '').trim();
    if (t && t.length < 40 && re.test(t) && a.href.startsWith('http') && !out.includes(a.href)) out.push(a.href);
    if (out.length >= 4) break;
  }
  return out;
}"""

async def otworz(strona, url):
    try:
        odp = await strona.goto(url, wait_until="domcontentloaded", timeout=30000)
        await strona.wait_for_timeout(3500)
        kod = odp.status if odp else 0
        tekst = await strona.evaluate("() => (document.body ? document.body.innerText : '').slice(0, 3000)")
        tytul = await strona.title()
        zablok = kod in (403, 429) or (len(tekst) < 400 and BLOKADA.search(tekst + " " + tytul) is not None) or bool(BLOKADA.search(tytul))
        return kod, zablok, tytul
    except Exception as e:
        return 0, False, str(e)[:60]

def dobry(o):
    return bool(o and o.get("cena") and o.get("zdjecie"))

async def sklep(strona, nazwa, adresy):
    baza = adresy[0]
    proba = []
    # 1. produkty z mapy strony
    try:
        rob, ile, prod = t2.mapa(baza)
        for b in adresy[1:]:
            if rob: break
            baza = b; rob, ile, prod = t2.mapa(b)
    except Exception:
        prod = []
    proba += prod[:2]
    # 2. strona główna
    kod, zablok, tytul = await otworz(strona, baza)
    if zablok:
        return "BLOKADA (strona główna %s)" % (kod or "-"), None
    if not kod:
        return "BRAK POLACZENIA", None
    try:
        proba += await strona.evaluate(LINKI_PRODUKTOW)
        if len(proba) < 2:
            for k in (await strona.evaluate(LINKI_KATEGORII))[:2]:
                kk, zb, _ = await otworz(strona, k)
                if not zb:
                    proba += await strona.evaluate(LINKI_PRODUKTOW)
                if len(proba) >= 3: break
    except Exception:
        pass
    widzial = False
    for u in proba[:4]:
        kod, zablok, _ = await otworz(strona, u)
        if zablok:
            widzial = True; continue
        try:
            o = await strona.evaluate(ODCZYT)
        except Exception:
            o = None
        if dobry(o):
            return "TAK", o
    if widzial:
        return "BLOKADA (strona produktu)", None
    return "CZESC (sklep otwiera się, nie znaleziono produktu)" if proba else "CZESC (sklep otwiera się, brak linków do produktów)", None

async def main():
    wyniki = []
    async with async_playwright() as p:
        sciezka = os.environ.get("CHROME")
        przegl = await p.chromium.launch(headless=True, executable_path=sciezka or None,
                                         args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"])
        kontekst = await przegl.new_context(user_agent=UA, locale="pl-PL", timezone_id="Europe/Warsaw",
                                            viewport={"width": 1366, "height": 900},
                                            extra_http_headers={"Accept-Language": "pl-PL,pl;q=0.9,en;q=0.7"})
        await kontekst.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        async def filtr(route):
            if route.request.resource_type in ("media", "font"):
                await route.abort()
            else:
                await route.continue_()
        await kontekst.route("**/*", filtr)
        strona = await kontekst.new_page()
        print("Przeglądarka sprawdza sklepy, to potrwa 15-30 minut...\n", flush=True)
        for nazwa, adresy in t2.SKLEPY:
            if TYLKO and nazwa not in TYLKO: continue
            t0 = time.time()
            try:
                wynik, o = await asyncio.wait_for(sklep(strona, nazwa, adresy), timeout=150)
            except asyncio.TimeoutError:
                wynik, o = "CZESC (za długo)", None
                await strona.close(); strona = await kontekst.new_page()
            if o:
                cena = str(o.get("cena"))[:24]
                znak = "TAK*" if "z tekstu" in cena else "TAK "
                linia = "%-16s %s cena: %s | zdjęcie: tak | %s" % (nazwa[:16], znak, cena.replace(" (z tekstu strony)", ""), str(o.get("nazwa") or "")[:40].replace("\n", " "))
            else:
                linia = "%-16s %s" % (nazwa[:16], wynik)
            print(linia + "  (%ds)" % (time.time() - t0), flush=True)
            wyniki.append(linia)
        await przegl.close()
    tak = sum(1 for w in wyniki if " TAK" in w)
    bl = sum(1 for w in wyniki if "BLOKADA" in w)
    pod = "---\n* cena odczytana z tekstu strony (łącznik to dopracuje)\nRAZEM: %d | TAK: %d | BLOKADA: %d | INNE: %d" % (len(wyniki), tak, bl, len(wyniki) - tak - bl)
    print(pod)
    with open(os.path.expanduser("~/trendo-test3.txt"), "w") as f:
        f.write("\n".join(wyniki) + "\n" + pod + "\n")

asyncio.run(main())
