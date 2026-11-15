"""Łącznik sklepów, które w wynikach wyszukiwania podają listę produktów w danych strukturalnych (ld+json ItemList)
albo w atrybutach kafelków (data-dl-*). Jeden łącznik, wiele sklepów."""
import html, json, re
from urllib.parse import quote, urljoin
from .wspolne import pobierz, pobierz_json, produkt, pasuje_dzial, rownolegle, liczba, MESKIE

NAZWA = "Sklepy (strony wyszukiwania)"
# (sklep, adres wyszukiwania dla damskich, dla męskich (None = brak), sposób odczytu)
SKLEPY_KONF = [
    ("Ochnik", "https://ochnik.com/products/search?query={q}", "https://ochnik.com/products/search?query={q}", "itemlist"),
    ("Bialcon", "https://bialcon.pl/products/search?query={q}", None, "itemlist"),
    ("Born2Be", "https://born2be.pl/kobiety?q={q}", "https://born2be.pl/mezczyzni?q={q}", "kafle"),
    ("Renee", "https://www.renee.pl/kobiety?q={q}", None, "kafle"),
    ("Bizuu", "searchanise:1r4h1n5E9I:https://bizuu.com", None, "searchanise"),
    ("Kazar", "https://kazar.com/catalogsearch/result/?q={q}", "https://kazar.com/catalogsearch/result/?q={q}", "magento"),
    ("Showroom", "https://www.showroom.pl/search?q={q}", "https://www.showroom.pl/search?q={q}", "showroom"),
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


def _magento(sklep, url, dzial):
    kod, b = pobierz(url)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    wyn = []
    for blok in t.split('class="item product product-item"')[1:]:
        blok = blok[:12000]
        m = re.search(r'class="product-item-link"\s*href="([^"]+)"[^>]*>\s*([^<]+?)\s*</a>', blok)
        c = re.search(r'data-price-amount="([\d.]+)"\s*data-price-type="finalPrice"', blok)
        if not m or not c:
            continue
        stara = re.search(r'data-price-amount="([\d.]+)"\s*data-price-type="oldPrice"', blok)
        img = re.search(r'class="product-image-photo[^"]*"\s*src="([^"]+)"', blok)
        nazwa = html.unescape(m.group(2))
        alt = re.search(r'alt="([^"]+)"', blok)
        pelna = html.unescape(alt.group(1)) if alt else nazwa
        if not pasuje_dzial(pelna, dzial):
            continue
        if dzial == "meskie" and sklep in TYLKO_JAWNIE_MESKIE and not MESKIE.search(pelna):
            continue
        cena, st = float(c.group(1)), (float(stara.group(1)) if stara else None)
        wyn.append(produkt(sklep, pelna, cena, m.group(1), img.group(1) if img else None,
                           stara=(st if st and st > cena else None), zrodlo="sklep", dzial=dzial))
    return wyn, "ok"


TYLKO_JAWNIE_MESKIE = {"Kazar"}  # sklep głównie damski: w dziale męskim tylko rzeczy opisane jako męskie
MESKIE_KAT = ("Shirts", "Suits", "Blazers > Suit", "Ties")
DAMSKIE_KAT = ("Blouses", "Dresses", "Skirts", "Jumpsuits", "Bras", "Lingerie")


def _showroom(sklep, url, dzial):
    kod, b = pobierz(url)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    znak = "__PLP_PRELOADED_STATE__ = JSON.stringify("
    i = t.find(znak)
    if i < 0:
        return [], "brak danych na stronie"
    try:
        d, _ = json.JSONDecoder().raw_decode(t[i + len(znak):])
    except Exception:
        return [], "nieczytelne dane"
    wyn = []
    for x in d.get("products") or []:
        kat = x.get("category") or ""
        if kat.startswith("Pre-owned"):
            continue
        if dzial == "damskie" and kat.startswith(MESKIE_KAT):
            continue
        if dzial == "meskie" and kat.startswith(DAMSKIE_KAT):
            continue
        cena = (x.get("price") or {}).get("price")
        if not cena or not x.get("url"):
            continue
        stara = (x.get("price") or {}).get("originalPrice")
        nazwa = f"{x.get('brand', '')} {x.get('title', '')}".strip()
        foto = ((x.get("photo") or {}).get("url") or "").replace("width=268&height=402", "width=600&height=900")
        wyn.append(produkt(sklep, nazwa[:1].upper() + nazwa[1:], cena / 100, urljoin(url, x["url"]), foto,
                           stara=(stara / 100 if stara and stara > cena else None), zrodlo="sklep", dzial=dzial,
                           extra={"rozmiary": x.get("sizes") or None}))
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
            lista, stan = {"itemlist": _itemlist, "kafle": _kafle, "magento": _magento, "showroom": _showroom}[sposob](sklep, url, dzial)
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
