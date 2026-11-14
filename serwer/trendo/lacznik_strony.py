"""Łącznik sklepów, które w wynikach wyszukiwania podają listę produktów w danych strukturalnych (ld+json ItemList)
albo w atrybutach kafelków (data-dl-*). Jeden łącznik, wiele sklepów."""
import html, json, re
from urllib.parse import quote, urljoin
from .wspolne import pobierz, pobierz_json, produkt, pasuje_dzial, rownolegle, liczba

NAZWA = "Sklepy (strony wyszukiwania)"
# (sklep, adres wyszukiwania dla damskich, dla męskich (None = brak), sposób odczytu)
SKLEPY_KONF = [
    ("Ochnik", "https://ochnik.com/products/search?query={q}", "https://ochnik.com/products/search?query={q}", "itemlist"),
    ("Bialcon", "https://bialcon.pl/products/search?query={q}", None, "itemlist"),
    ("Born2Be", "https://born2be.pl/kobiety?q={q}", "https://born2be.pl/mezczyzni?q={q}", "kafle"),
    ("Renee", "https://www.renee.pl/kobiety?q={q}", None, "kafle"),
    ("Bizuu", "searchanise:1r4h1n5E9I:https://bizuu.com", None, "searchanise"),
]
SKLEPY = [s[0] for s in SKLEPY_KONF]


def _itemlist(sklep, url, dzial):
    kod, b = pobierz(url)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    wyn = []
    for blok in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', t, re.S | re.I):
        try:
            j = json.loads(blok)
        except Exception:
            continue
        lista = j.get("@graph", [j]) if isinstance(j, dict) else j
        for x in lista:
            if not isinstance(x, dict) or x.get("@type") != "ItemList":
                continue
            for el in x.get("itemListElement") or []:
                it = el.get("item") or el
                of = it.get("offers") or {}
                if isinstance(of, list):
                    of = of[0] if of else {}
                cena = liczba(of.get("price") or of.get("lowPrice"))
                nazwa = it.get("name") or ""
                if not cena or not it.get("url") or not pasuje_dzial(nazwa, dzial):
                    continue
                im = it.get("image")
                if isinstance(im, list):
                    im = im[0] if im else None
                wyn.append(produkt(sklep, html.unescape(nazwa), cena, urljoin(url, it["url"]), im, zrodlo="sklep", dzial=dzial))
    return wyn, "ok"


def _kafle(sklep, url, dzial):
    kod, b = pobierz(url)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    wyn = []
    for m in re.finditer(r'<a href="([^"]+)"[^>]*class="main-img dl-product-click"([^>]*)>\s*<img src="([^"]+)"', t):
        href, atr, img = m.groups()
        a = dict(re.findall(r'data-dl-([a-z0-9]+)="([^"]*)"', atr))
        cena = liczba(a.get("price"))
        nazwa = html.unescape(a.get("name", ""))
        if not cena or not nazwa or not pasuje_dzial(nazwa + " " + a.get("category", ""), dzial):
            continue
        rozm = [r for r in (a.get("dimension11") or "").split("|") if r] or None
        wyn.append(produkt(sklep, nazwa, cena, urljoin(url, href), img, zrodlo="sklep", dzial=dzial,
                           extra={"rozmiary": rozm, "material": a.get("dimension16") or None}))
    return wyn, "ok"


def _searchanise(sklep, konf, q, dzial):
    _, klucz, baza = konf.split(":", 2)
    kod, d = pobierz_json(f"https://searchserverapi.com/getresults?api_key={klucz}&q={quote(q)}&items=true&maxResults=40&output=json")
    if not d:
        return [], f"brak odpowiedzi ({kod})"
    wyn = []
    for it in d.get("items") or []:
        cena = liczba(it.get("price"))
        if not cena or not it.get("link"):
            continue
        stara = liczba(it.get("list_price"))
        wyn.append(produkt(sklep, it.get("title", ""), cena, urljoin(baza, it["link"]), it.get("image_link"),
                           stara=(stara if stara and stara > cena else None), zrodlo="sklep", dzial=dzial))
    return wyn, "ok"


def _sklep(arg):
    (sklep, dam, mes, sposob), q, dzial = arg
    wzor = dam if dzial == "damskie" else mes
    if not wzor:
        return sklep, [], "pomijam"
    try:
        if sposob == "searchanise":
            lista, stan = _searchanise(sklep, wzor, q, dzial)
        else:
            url = wzor.format(q=quote(q))
            lista, stan = (_itemlist if sposob == "itemlist" else _kafle)(sklep, url, dzial)
        return sklep, lista, stan
    except Exception as e:
        return sklep, [], "błąd: " + str(e)[:40]


def szukaj(q, dzial):
    out, stany = [], []
    for w in rownolegle(_sklep, [(k, q, dzial) for k in SKLEPY_KONF], watki=5):
        if w:
            out += w[1]
            if w[2] not in ("ok", "pomijam"):
                stany.append(f"{w[0]}: {w[2]}")
    return out, ("ok" if not stany else "; ".join(stany))
