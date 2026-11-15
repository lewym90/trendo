"""Znaki sklepów: prawdziwe logo z nagłówka strony sklepu (to samo, które widać na jego stronie).

Jak to działa:
1. Przeglądarka na serwerze otwiera stronę główną sklepu i wybiera znak z nagłówka: element na górze strony,
   w linku do strony głównej, opisany jako logo (obrazek, SVG albo tło CSS).
2. Gdy strona blokuje przeglądarkę: ten sam wybór na zwykłym pobraniu strony.
3. Gdy i to się nie uda: logo z Wikidanych, ale tylko gdy oficjalna strona w Wikidanych to domena sklepu.
4. Znak jest ujednolicany: przycięty, wysokość 160 px, jeden jasny kolor na przezroczystym tle,
   żeby wszystkie sklepy były tak samo ostre i pasowały do ciemnego wyglądu aplikacji. Kształt zostaje oryginalny.
Bez znaku aplikacja pokazuje nazwę sklepu zwykłym tekstem (nie używamy rozmazanych ikonek stron).
Pobieranie idzie w tle, po jednym sklepie, pamięć 30 dni. Logo służy wyłącznie do oznaczenia, z którego sklepu jest produkt.
"""
import base64, json, os, queue, re, sys, threading, time, unicodedata
from urllib.parse import quote, unquote, urljoin, urlparse
from .wspolne import DB, PRZEGLADARKA, UA, _baza_blokada, pobierz

WERSJA_ZNAKU = 2
_KAT = os.path.join(os.path.dirname(__file__), "js")
JS_WYBIERZ = open(os.path.join(_KAT, "znak_wybierz.js"), encoding="utf-8").read()
JS_PRZETWORZ = open(os.path.join(_KAT, "znak_przetworz.js"), encoding="utf-8").read()

DOMENY = {
    "zara": "zara.com", "reserved": "reserved.com", "mohito": "mohito.com", "house": "housebrand.com", "cropp": "cropp.com",
    "sinsay": "sinsay.com", "modivo": "modivo.pl", "eobuwie": "eobuwie.com.pl", "ochnik": "ochnik.com", "bialcon": "bialcon.pl",
    "born2be": "born2be.pl", "renee": "renee.pl", "bizuu": "bizuu.com", "kazar": "kazar.com", "showroom": "showroom.pl",
    "hm": "hm.com", "zalando": "zalando.pl", "answear": "answear.com", "medicine": "medicine.pl", "mango": "mango.com",
    "allegro": "allegro.pl", "decathlon": "decathlon.pl", "vistula": "vistula.pl", "wolczanka": "wolczanka.pl",
    "bytom": "bytom.com.pl", "sportano": "sportano.pl", "empik": "empik.com", "calvinklein": "calvinklein.pl",
    "calvinkleinpl": "calvinklein.pl", "tommyhilfiger": "tommy.com", "guess": "guess.eu", "vitkac": "vitkac.com",
    "lancerto": "lancerto.com", "4f": "4f.com.pl", "topsecret": "topsecret.pl", "bigstar": "bigstar.pl", "ccc": "ccc.eu",
    "deichmann": "deichmann.com", "gomez": "gomez.pl", "peekcloppenburg": "peek-cloppenburg.pl", "boozt": "boozt.com",
    "aboutyou": "aboutyou.pl", "levis": "levi.com", "diverse": "diverse.pl", "sizeer": "sizeer.com", "rylko": "rylko.pl",
    "wittchen": "wittchen.com", "monnari": "emonnari.pl", "quiosque": "quiosque.pl", "molton": "molton.pl", "tatuum": "tatuum.com",
    "pakolorente": "pakolorente.pl", "giacomoconti": "giacomoconti.com", "recman": "recman.pl", "kappahl": "kappahl.com",
    "kappahlpoland": "kappahl.com", "lidlskleponline": "lidl.pl", "ozonee": "ozonee.pl",
    "denley": "denley.pl", "moodo": "moodo.pl", "modnakiecka": "modnakiecka.pl", "greenpoint": "greenpoint.pl",
    "solarcompany": "solar.com.pl", "breuninger": "breuninger.com", "sneakerpeeker": "sneakerpeeker.pl", "vinted": "vinted.pl",
    "hugoboss": "hugoboss.com", "massimodutti": "massimodutti.com", "bershka": "bershka.com", "stradivarius": "stradivarius.com",
    "pullbear": "pullandbear.com", "cos": "cos.com", "arket": "arket.com", "nike": "nike.com", "adidas": "adidas.pl",
    "ca": "c-and-a.com", "orsay": "orsay.com", "simple": "simple.com", "liujo": "liujo.com", "ochnikpl": "ochnik.com",
}
# Strona główna, gdy sam adres domeny prowadzi do wyboru kraju.
STRONY = {
    "reserved.com": "https://www.reserved.com/pl/pl/", "cropp.com": "https://www.cropp.com/pl/pl/",
    "housebrand.com": "https://www.housebrand.com/pl/pl/", "sinsay.com": "https://www.sinsay.com/pl/pl/",
    "mohito.com": "https://www.mohito.com/pl/pl/", "zara.com": "https://www.zara.com/pl/", "mango.com": "https://shop.mango.com/pl",
    "hm.com": "https://www2.hm.com/pl_pl/index.html", "massimodutti.com": "https://www.massimodutti.com/pl/",
    "bershka.com": "https://www.bershka.com/pl/", "stradivarius.com": "https://www.stradivarius.com/pl/",
    "pullandbear.com": "https://www.pullandbear.com/pl/", "cos.com": "https://www.cos.com/pl-pl/", "arket.com": "https://www.arket.com/pl-pl/",
    "nike.com": "https://www.nike.com/pl/", "tommy.com": "https://pl.tommy.com/", "levi.com": "https://www.levi.com/PL/pl_PL/",
    "c-and-a.com": "https://www.c-and-a.com/pl/pl/shop", "kappahl.com": "https://www.kappahl.com/pl-pl/", "guess.eu": "https://www.guess.eu/pl-pl/home",
    "hugoboss.com": "https://www.hugoboss.com/pl/", "deichmann.com": "https://www.deichmann.com/pl-pl/", "boozt.com": "https://www.boozt.com/pl/pl",
    "orsay.com": "https://www.orsay.com/pl-pl/", "liujo.com": "https://www.liujo.com/pl/", "breuninger.com": "https://www.breuninger.com/pl/",
}

with _baza_blokada:
    DB.execute("CREATE TABLE IF NOT EXISTS logo_domeny (sklep TEXT PRIMARY KEY, domena TEXT)")
    DB.execute("CREATE TABLE IF NOT EXISTS znak (domena TEXT PRIMARY KEY, wersja INTEGER, png BLOB, proporcja REAL, zrodlo TEXT, czas INTEGER)")
    DB.commit()
_poznane = set()
_kolejka = queue.Queue()
_w_kolejce = set()
_kolejka_blokada = threading.Lock()


def _znak(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s.replace("&", ""))


def _host(u):
    h = urlparse(u or "").netloc.lower()
    return h[4:] if h.startswith("www.") else h


def poznaj(p):
    """Zapamiętuje domenę sklepu z adresu produktu (tylko sklepy podłączone bezpośrednio)."""
    if p.get("zrodlo") == "google":
        return
    k = _znak(p.get("sklep"))
    h = _host(p.get("url"))
    if not k or not h or k in _poznane or "google." in h:
        return
    _poznane.add(k)
    with _baza_blokada:
        DB.execute("INSERT OR REPLACE INTO logo_domeny VALUES (?,?)", (k, h)); DB.commit()


def domena(sklep):
    """Domena sklepu albo None. Nie zgadujemy domen sprzedawców z Google Shopping."""
    k = _znak(sklep)
    if not k:
        return None
    with _baza_blokada:
        r = DB.execute("SELECT domena FROM logo_domeny WHERE sklep=?", (k,)).fetchone()
    if r:
        return r[0]
    return DOMENY.get(k)


def strona(d):
    if d in STRONY:
        return STRONY[d]
    return f"https://www.{d}/" if d.count(".") == 1 else f"https://{d}/"


def _typ(b):
    if not b or len(b) < 60:
        return None
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[8:12] == b"WEBP":
        return "image/webp"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if b"<svg" in b[:3000].lower() and b"<html" not in b[:3000].lower():
        return "image/svg+xml"
    return None


def _z_data(u):
    naglowek, _, dane = u.partition(",")
    return base64.b64decode(dane) if ";base64" in naglowek else unquote(dane).encode()


def _przetworz(pusta, b, typ):
    """Ujednolica znak w pustej karcie przeglądarki. Zwraca (png, proporcja) albo None."""
    if not typ:
        return None
    if typ == "image/svg+xml":
        t = b.decode("utf-8", "ignore")
        if "xmlns=" not in t[:2000]:
            t = t.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        b = t.encode()
    url = f"data:{typ};base64," + base64.b64encode(b).decode()
    try:
        w = pusta.evaluate(JS_PRZETWORZ, [url, "svg" if "svg" in typ else "raster"])
    except Exception:
        return None
    if not w or w.get("blad"):
        return None
    # Pełny prostokąt (zdjęcie, baner) albo pionowa ikonka to nie znak firmowy.
    if w["pokrycie"] > 0.62 or w["proporcja"] < 0.8 or w["proporcja"] > 16:
        return None
    return base64.b64decode(w["png"].split(",", 1)[1]), round(w["proporcja"], 3)


def _kandydaci_statyczni(html, adres, nazwa):
    """Zapasowy wybór bez renderowania: obrazki i SVG w nagłówku, w linku do strony głównej, opisane jako logo."""
    wyn = []
    zle = re.compile(r"visa|mastercard|blik|paypal|payu|inpost|dpd|dhl|facebook|instagram|tiktok|youtube|pinterest|app-?store|"
                     r"google-?play|trusted|opineo|ceneo|cookie|onetrust|flag|banner|baner|product|catalog|media/catalog", re.I)
    naglowek = re.search(r"<header\b.*?</header>", html, re.S | re.I)
    obszar = naglowek.group(0) if naglowek else html[:400_000]
    for m in re.finditer(r"<img\b[^>]*>", obszar, re.I):
        tag = m.group(0)
        if not re.search(r"logo", tag, re.I) or zle.search(tag):
            continue
        src = re.search(r'\b(?:src|data-src)=["\']([^"\']+)', tag, re.I)
        if src:
            wyn.append(("img", urljoin(adres, src.group(1).replace("&amp;", "&"))))
    for m in re.finditer(r"<a\b[^>]*>(?:(?!</a>).){0,6000}?</a>", obszar, re.S | re.I):
        a = m.group(0)
        if not re.search(r"logo|strona główna|strony głównej|home", a[:600], re.I):
            continue
        s = re.search(r"<svg\b.*?</svg>", a, re.S | re.I)
        if s and "<use" not in s.group(0):
            wyn.append(("svg", s.group(0)))
    return wyn[:4]


def _wiki(u):
    ua = {"User-Agent": "TrendoLogo/1.0 (https://lewym90.github.io/trendo/)"}
    for proba in range(3):
        kod, b = pobierz(u, naglowki=ua, czas=20)
        if kod != 429:
            return kod, b
        time.sleep(4 + 6 * proba)
    return kod, b


def _z_wikidanych(sklep, d):
    """Logo z Wikidanych, tylko gdy oficjalna strona tego hasła to domena sklepu."""
    api = "https://www.wikidata.org/w/api.php?format=json&"
    kod, b = _wiki(api + "action=wbsearchentities&type=item&limit=8&language=pl&uselang=pl&search=" + quote(sklep))
    try:
        ids = [x["id"] for x in json.loads(b)["search"]] if kod == 200 else []
    except Exception:
        ids = []
    if not ids:
        return []
    kod, b = _wiki(api + "action=wbgetentities&props=claims&ids=" + "|".join(ids))
    try:
        enc = json.loads(b)["entities"] if kod == 200 else {}
    except Exception:
        enc = {}
    rdzen = d.split(".")[0]
    wyn = []
    for i in ids:
        cl = (enc.get(i) or {}).get("claims", {})
        strony = [((c.get("mainsnak") or {}).get("datavalue") or {}).get("value", "") for c in cl.get("P856", [])]
        if not any(_host(s) == d or _host(s).endswith("." + d) or _host(s).split(".")[0] == rdzen for s in strony if isinstance(s, str)):
            continue
        for c in cl.get("P154", []):
            plik = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
            if plik:
                wyn.append(("img", "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(plik.replace(" ", "_"))))
    return wyn[:2]


def _pobierz_obraz(ctx, u, adres):
    if u.startswith("data:"):
        try:
            return _z_data(u)
        except Exception:
            return b""
    try:
        r = ctx.request.get(u, headers={"Referer": adres}, timeout=20000)
        if r.ok:
            return r.body()
    except Exception:
        pass
    kod, b = pobierz(u, naglowki={"Referer": adres}, czas=20, limit=3_000_000)
    return b if kod == 200 else b""


def wyszukaj(sklep, d, log=None):
    """Szuka znaku sklepu. Zwraca (png, proporcja, źródło) albo (None, None, powód)."""
    loguj = log or (lambda *a: None)
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None, None, "brak przeglądarki na serwerze"
    adres = strona(d)
    with PRZEGLADARKA, sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"],
                              executable_path=os.environ.get("TRENDO_CHROME") or None)
        try:
            ctx = b.new_context(viewport={"width": 1280, "height": 900}, locale="pl-PL", user_agent=UA, device_scale_factor=3)
            pusta = ctx.new_page()
            s = ctx.new_page()
            # 1. Strona wyrenderowana w przeglądarce.
            try:
                s.goto(adres, timeout=45000, wait_until="domcontentloaded")
                s.wait_for_timeout(4500)
                kand = s.evaluate(JS_WYBIERZ, sklep) or []
            except Exception as e:
                kand = []
                loguj("  przeglądarka:", str(e)[:120])
            loguj("  kandydaci z przeglądarki:", [(k["pkt"], k["typ"], k["r"]) for k in kand])
            for k in kand:
                if k["pkt"] < 7:
                    continue
                if k["typ"] == "svg":
                    dane = k["svg"].encode()
                else:
                    dane = _pobierz_obraz(ctx, k["url"], adres)
                w = _przetworz(pusta, dane, _typ(dane))
                if not w:
                    # Plik zablokowany albo nieczytelny: zrzut samego elementu w potrójnej rozdzielczości.
                    try:
                        el = s.locator(f'[data-trendo-znak="{k["nr"]}"]').first
                        if el.bounding_box() and el.bounding_box()["width"] > 10:
                            w = _przetworz(pusta, el.screenshot(omit_background=True, timeout=10000), "image/png")
                    except Exception:
                        pass
                if w:
                    return w[0], w[1], "strona sklepu"
            # 2. Zwykłe pobranie strony (gdy przeglądarka jest blokowana).
            kod, h = pobierz(adres, czas=20, limit=4_000_000)
            for typ, x in (_kandydaci_statyczni(h.decode("utf-8", "ignore"), adres, sklep) if kod == 200 else []):
                dane = x.encode() if typ == "svg" else _pobierz_obraz(ctx, x, adres)
                w = _przetworz(pusta, dane, _typ(dane))
                if w:
                    return w[0], w[1], "kod strony sklepu"
            # 3. Wikidane (oficjalne logo przypisane do domeny sklepu).
            for typ, x in _z_wikidanych(sklep, d):
                dane = _pobierz_obraz(ctx, x, adres)
                w = _przetworz(pusta, dane, _typ(dane))
                if w:
                    return w[0], w[1], "Wikidane"
            return None, None, "nie znaleziono znaku"
        finally:
            b.close()


def _zapisz(d, png, prop, zrodlo):
    with _baza_blokada:
        DB.execute("INSERT OR REPLACE INTO znak VALUES (?,?,?,?,?,?)", (d, WERSJA_ZNAKU, png, prop, zrodlo, int(time.time())))
        DB.commit()


def _z_pamieci(d):
    with _baza_blokada:
        r = DB.execute("SELECT wersja, png, proporcja, zrodlo, czas FROM znak WHERE domena=?", (d,)).fetchone()
    if not r or r[0] != WERSJA_ZNAKU:
        return None
    swiezy = time.time() - r[4] < (30 * 86400 if r[1] else 3 * 86400)
    return {"png": bytes(r[1]) if r[1] else None, "proporcja": r[2], "zrodlo": r[3], "swiezy": swiezy}


def _pracownik():
    while True:
        sklep, d = _kolejka.get()
        try:
            png, prop, zr = wyszukaj(sklep, d)
            _zapisz(d, png, prop, zr)
        except Exception as e:
            _zapisz(d, None, None, "błąd: " + str(e)[:80])
        finally:
            with _kolejka_blokada:
                _w_kolejce.discard(d)
            time.sleep(2)


def _dodaj(sklep, d):
    with _kolejka_blokada:
        if d in _w_kolejce:
            return
        _w_kolejce.add(d)
    _kolejka.put((sklep, d))


threading.Thread(target=_pracownik, daemon=True).start()


def logo(sklep):
    """(typ, bajty) gotowego znaku albo (None, None). Brakujący znak trafia do kolejki w tle."""
    d = domena(sklep)
    if not d:
        return None, None
    z = _z_pamieci(d)
    if not z or not z["swiezy"]:
        _dodaj(sklep, d)
    if z and z["png"]:
        return "image/png", z["png"]
    return None, None


def rozgrzej():
    """Kolejkuje znaki znanych sklepów (po jednym, w tle)."""
    with _baza_blokada:
        znane = DB.execute("SELECT sklep, domena FROM logo_domeny").fetchall()
    for k, d in list(znane) + [(k, d) for k, d in DOMENY.items()]:
        z = _z_pamieci(d)
        if not z or not z["swiezy"]:
            _dodaj(k, d)


if __name__ == "__main__":
    # python -m trendo.logo Reserved Zara "H&M"  — sprawdzenie od ręki (zapisuje wynik)
    for n in sys.argv[1:]:
        d = domena(n)
        if not d:
            print(f"{n}: nieznana domena sklepu"); continue
        t0 = time.time()
        png, prop, zr = wyszukaj(n, d, log=print if os.environ.get("TRENDO_GADATLIWIE") else None)
        _zapisz(d, png, prop, zr)
        print(f"  {n:12} {'OK ' if png else 'BRAK'} {zr}{f', proporcje {prop}:1, {len(png)//1024} KB' if png else ''} ({time.time() - t0:.0f} s)")
