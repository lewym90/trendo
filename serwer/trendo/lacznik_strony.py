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
    ("Top Secret", "https://www.topsecret.pl/wszystkie-produkty?q={q}", None, "kafle2"),
    ("Molton", "https://molton.pl/pl/search.html?text={q}", None, "idosell"),
    ("Moodo", "https://moodo.pl/pl/search.html?text={q}", None, "idosell"),
    # Kappahl miesza w wynikach dzieci, kobiety i mężczyzn; słowo działu w zapytaniu zawęża wyniki do niego
    # Grupa Monnari: wyszukiwarka przyjmuje tylko formularz (POST), dane produktu są w atrybucie data-product
    ("Quiosque", "https://www.quiosque.pl/szukaj.html", None, "monnari"),
    ("Monnari", "https://emonnari.pl/szukaj.html", None, "monnari"),
    # Grupa VRG: ten sam szablon, płeć w atrybucie data-filter-gender, Omnibus pod ceną
    ("Vistula", "https://vistula.pl/search?query={q}", "https://vistula.pl/search?query={q}", "vrg"),
    ("Wólczanka", "https://wolczanka.pl/search?query={q}", "https://wolczanka.pl/search?query={q}", "vrg"),
    ("Bytom", "https://bytom.com.pl/search?query={q}", "https://bytom.com.pl/search?query={q}", "vrg"),
    # Deichmann: wyniki renderowane na serwerze sklepu, spakowane (base64 + gzip) w <script id="ng-state">
    ("Deichmann", "https://www.deichmann.com/pl-pl/search/{q}?gendersFilter=1887164", "https://www.deichmann.com/pl-pl/search/{q}?gendersFilter=1887165", "deichmann"),
    ("Big Star", "https://bigstar.pl/api/v2/products/?q={q}", "https://bigstar.pl/api/v2/products/?q={q}", "bigstar"),
    ("Kappahl", "https://www.kappahl.com/pl-pl/szukaj/?q={q}%20damska", "https://www.kappahl.com/pl-pl/szukaj/?q={q}%20m%C4%99ska", "kappahl"),
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
    """Kafle z atrybutami data-dl-* na linku do produktu (Born2Be, Renee). Klasa linku bywa różna
    („main-img dl-product-click”, „d-flex r-main-img r-dl-product-click”), więc szukamy po atrybutach."""
    kod, b = pobierz(url)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    wyn = []
    for m in re.finditer(r'<a\s[^>]*class="[^"]*dl-product-click[^"]*"[^>]*>', t):
        tag = m.group(0)
        href = re.search(r'href="([^"]+)"', tag)
        a = dict(re.findall(r'data-dl-([a-z0-9]+)="([^"]*)"', tag))
        cena = liczba(a.get("price"))
        nazwa = html.unescape(a.get("name", ""))
        if not href or not cena or not nazwa or not pasuje_dzial(nazwa + " " + a.get("category", ""), dzial):
            continue
        dalej = t[m.end():m.end() + 4000]
        img = re.search(r'<img[^>]*?\s(?:data-src|src)="(https?://[^"]+\.(?:jpe?g|png|webp)[^"]*)"', dalej)
        rozm = [r for r in (a.get("dimension11") or "").split("|") if r] or None
        wyn.append(produkt(sklep, nazwa, cena, urljoin(url, href.group(1)), img.group(1) if img else None,
                           zrodlo="sklep", dzial=dzial, extra={"rozmiary": rozm, "material": a.get("dimension16") or None}))
    return wyn, "ok"


def _zl(t):
    return liczba(t) if t else None


def _kafle2(sklep, url, dzial):
    """Kafle z atrybutami data-dl-* na całym bloku produktu (Top Secret)."""
    kod, b = pobierz(url)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    wyn = []
    for blok in t.split('class="product dl-product-click"')[1:]:
        blok = blok[:9000]
        a = dict(re.findall(r'data-dl-([a-z0-9]+)="([^"]*)"', blok[:800]))
        link = re.search(r'<a href="([^"]+)" class="product__link"', blok)
        img = re.search(r'class="product__img[^"]*"[^>]*?\ssrc="([^"]+)"', blok)
        cena = liczba(a.get("price"))
        nazwa = html.unescape(a.get("name", "")).strip()
        if not cena or not nazwa or not link or not pasuje_dzial(nazwa + " " + a.get("category", ""), dzial):
            continue
        st = re.search(r'product__price-old">.*?<b>([^<]+)</b>', blok, re.S)
        om = re.search(r'Najniższa cena z 30 dni[^0-9]*([\d\s,.]+zł)', blok)
        stara = _zl(st.group(1)) if st else None
        rozm = re.findall(r'class="product__variant-value">\s*([^<\s][^<]*?)\s*<', blok)
        wyn.append(produkt(sklep, nazwa, cena, urljoin(url, link.group(1)), img.group(1) if img else None,
                           stara=(stara if stara and stara > cena else None), zrodlo="sklep", dzial=dzial,
                           extra={"rozmiary": rozm or None, "omnibus": _zl(om.group(1)) if om else None}))
    return wyn, "ok"


def _idosell(sklep, url, dzial):
    """Sklepy na platformie IdoSell: wspólny szablon listy wyników (product__name, product__prices)."""
    kod, b = pobierz(url)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    wyn = []
    for blok in t.split('data-product_id="')[1:]:
        blok = blok[:7000]
        m = re.search(r'class="product__name" href="([^"]+)"[^>]*>([^<]+)</a>', blok)
        c = re.search(r'<strong class="price">([^<]+)</strong>', blok)
        if not m or not c:
            continue
        cena = _zl(c.group(1))
        nazwa = html.unescape(m.group(2)).strip()
        if not cena or not pasuje_dzial(nazwa, dzial):
            continue
        st = re.search(r'<del class="price --max">([^<]+)</del>', blok)
        stara = _zl(st.group(1)) if st else None
        om = re.search(r'data-omniprice="([\d,.]+)"', blok)
        img = re.search(r'data-src="(/hpeciai/[^"]+)"', blok) or re.search(r'<img src="(/hpeciai/[^"]+)"', blok)
        rozm = re.findall(r'<span class="product__size">([^<]+)</span>', blok)
        wyn.append(produkt(sklep, nazwa, cena, urljoin(url, m.group(1).split("?")[0]), urljoin(url, img.group(1)) if img else None,
                           stara=(stara if stara and stara > cena else None), zrodlo="sklep", dzial=dzial,
                           extra={"rozmiary": rozm or None, "omnibus": _zl(om.group(1)) if om else None}))
    return wyn, "ok"


def _kappahl(sklep, url, dzial):
    kod, b = pobierz(url)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    i = t.find('"products": [')
    if i < 0:
        return [], "brak danych na stronie"
    try:
        lista, _ = json.JSONDecoder().raw_decode(t[i + len('"products": '):])
    except Exception:
        return [], "nieczytelne dane"
    obszar = "Man" if dzial == "meskie" else "Woman"
    wyn = []
    for x in lista:
        if x.get("businessArea") != obszar or not x.get("url"):
            continue
        cen = x.get("price") or {}
        cena = ((cen.get("current") or {}).get("inclVat"))
        if not cena:
            continue
        stara = ((cen.get("previous") or {}).get("inclVat")) or ((cen.get("original") or {}).get("inclVat"))
        stara = round(stara, 2) if stara and stara > cena + 0.01 else None
        zdj = next((z.get("url") for z in x.get("images") or [] if z.get("imageType") == "modelImage"), None) \
            or next((z.get("url") for z in x.get("images") or []), None)
        nazwa = x.get("displayName") or ""
        if x.get("brandName") and x["brandName"].lower() not in ("kappahl",):
            nazwa = f"{x['brandName']} {nazwa}"
        wyn.append(produkt(sklep, nazwa, cena, urljoin(url, x["url"]), urljoin(url, zdj.split("?")[0]) if zdj else None,
                           stara=stara, zrodlo="sklep", dzial=dzial,
                           extra={"plec_sklepu": "meskie" if obszar == "Man" else "damskie", "kolor": x.get("color")}))
    return wyn, "ok"


def _monnari(sklep, url, q, dzial):
    kod, b = pobierz(url, {"Content-Type": "application/x-www-form-urlencoded"}, dane="search_phrase=" + quote(q))
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    i = t.find("product-list-search")
    if i < 0:  # brak wyników: sklep pokazuje wtedy polecane produkty, nie trafienia
        return [], "ok"
    t = t[i:]
    wyn, byly = [], set()
    for blok in t.split("<div class=\"product-brick\" data-product='")[1:]:
        try:
            d = json.loads(html.unescape(blok[:blok.index("'")]))
        except Exception:
            continue
        link = re.search(r'<a href="([^"]+)" class="product-brick__link', blok)
        if not link or link.group(1) in byly:
            continue
        byly.add(link.group(1))
        img = re.search(r'data-original="\s*(https?://[^"\s]+)', blok)
        cena = liczba(d.get("price"))
        nazwa = d.get("item_name") or ""
        if not cena or not link or not pasuje_dzial(nazwa + " " + (d.get("item_category2") or ""), dzial):
            continue
        st = re.search(r'product-brick__price-regular--new[^>]*>\s*([^<]+)<', blok[:8000])
        stara = liczba(html.unescape(st.group(1))) if st else None
        wyn.append(produkt(sklep, nazwa, cena, link.group(1), img.group(1) if img else None,
                           stara=(stara if stara and stara > cena else None), zrodlo="sklep", dzial=dzial))
    return wyn, "ok"


def _vrg(sklep, url, dzial):
    kod, b = pobierz(url)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    wyn = []
    for m in re.finditer(r'data-filter-gender="([^"]*)"[^>]*>\s*<div class="product-tag-details"([^>]*)>', t):
        plec, atr = m.group(1).lower(), m.group(2)
        blok = t[m.end():m.end() + 6000]
        a = dict(re.findall(r'data-([a-z]+)="([^"]*)"', atr))
        if plec.startswith("m") and dzial == "damskie" or plec.startswith("d") and dzial == "meskie":
            continue
        link = re.search(r'<a href="([^"]+)"', blok)
        nazwa = html.unescape(re.sub(r"\s+", " ", (re.search(r'class="product-title">([^<]+)<', blok) or [None, a.get("name", "")])[1])).strip()
        cena_b = re.search(r'class="product-price">\s*<span class="([^"]+)">([^<]+)<', blok)
        if not link or not nazwa or not cena_b:
            continue
        if nazwa.isupper():  # Bytom pisze nazwy wielkimi literami
            nazwa = nazwa.capitalize()
        cena = liczba(cena_b.group(2))
        if not cena or not pasuje_dzial(nazwa, dzial):
            continue
        stara = om = None
        if cena_b.group(1) != "reg":
            st = re.search(r'Cena regularna:\s*([^<]+)<', blok)
            on = re.search(r'Najniższa cena:\s*([^<]+)<', blok)
            stara, om = (liczba(st.group(1)) if st else None), (liczba(on.group(1)) if on else None)
        img = re.search(r'<img class="thumb[^"]*"[^>]*data-src="([^"]+)"', blok)
        mat = re.search(r'class="product-line">\s*([^<]+?)\s*<', blok)
        wyn.append(produkt(sklep, nazwa, cena, link.group(1), img.group(1) if img else None,
                           stara=(stara if stara and stara > cena else None), zrodlo="sklep", dzial=dzial,
                           extra={"omnibus": om, "material": mat.group(1) if mat else None,
                                  "plec_sklepu": "damskie" if plec.startswith("d") else "meskie" if plec.startswith("m") else None}))
    return wyn, "ok"


def _grosze(c):
    return round(c / 100, 2) if isinstance(c, (int, float)) and c > 0 else None


def _deichmann_strona(url):
    import base64, gzip
    kod, b = pobierz(url)
    if kod != 200:
        return None, f"brak odpowiedzi ({kod})"
    t = b.decode("utf-8", "ignore")
    m = re.search(r'<script id="ng-state" type="application/json">(.*?)</script>', t, re.S)
    if not m:
        return None, "brak danych na stronie"
    try:
        stan = json.loads(m.group(1))
        sur = next(v for k, v in stan.items() if "search%2F" in k)
        d = json.loads(gzip.decompress(base64.b64decode(sur))) if isinstance(sur, str) else sur
        return (d.get("body") or d).get("products") or [], "ok"
    except Exception:
        return None, "nieczytelne dane"


def _deichmann(sklep, url, dzial):
    """Sklep podaje 24 produkty na stronę (płeć wybrana w adresie); bierzemy dwie strony."""
    lista, stan = _deichmann_strona(url)
    if lista is None:
        return [], stan
    if len(lista) >= 24:
        dalej, _ = _deichmann_strona(url + "&page=2")
        widziane = {x.get("id") for x in lista}
        lista += [x for x in dalej or [] if x.get("id") not in widziane]
    chce = "Mężczyźni" if dzial == "meskie" else "Kobiety"
    wyn = []
    for x in lista:
        at = x.get("attributes") or {}
        plcie = [v.get("label") for v in _wartosci(at.get("genders"))]
        if plcie and chce not in plcie and "Unisex" not in plcie:
            continue
        wiek = [v.get("label") for v in _wartosci(at.get("phasesOfLife"))]
        if wiek and "Dorośli" not in wiek:
            continue
        cena = _grosze((((x.get("priceRange") or {}).get("min") or {}).get("withTax")))
        if not cena or not x.get("url"):
            continue
        stara = _grosze(((x.get("variants") or [{}])[0].get("price") or {}).get("beforeSaleWithTax")) or liczba(x.get("wasPrice"))
        om = _grosze((x.get("lowestPriorPrice") or {}).get("withTax"))
        marka = ((at.get("brand") or {}).get("values") or {}).get("label") or ""
        kolor = ((at.get("color") or {}).get("values") or {}).get("label") or ""
        nazwa = " ".join(w for w in (x.get("displayName") or "", marka, kolor) if w)
        zdj = (x.get("images") or [{}])[0].get("public_id")
        wyn.append(produkt(sklep, nazwa, cena, "https://www.deichmann.com/pl-pl" + x["url"],
                           f"https://asset.deichmann.com/images/f_auto,q_auto/w_600/{zdj}/zdjecie" if zdj else None,
                           stara=(stara if stara and stara > cena else None), zrodlo="sklep", dzial=dzial,
                           extra={"omnibus": om, "kolor": kolor or None,
                                  "plec_sklepu": None if (not plcie or "Unisex" in plcie) else dzial}))
    return wyn, "ok"


def _wartosci(a):
    v = (a or {}).get("values")
    return v if isinstance(v, list) else [v] if isinstance(v, dict) else []


def _bigstar(sklep, url, dzial):
    kod, d = pobierz_json(url)
    if not d:
        return [], f"brak odpowiedzi ({kod})"
    wyn = []
    for x in d.get("list") or []:
        kat = " ".join(x.get("category_path") or []).lower()
        if re.search(r"dzie[cć]|dziewcz|chłop", kat):
            continue
        if dzial == "meskie" and "damsk" in kat or dzial == "damskie" and "męsk" in kat:
            continue
        cena = liczba(x.get("price"))
        nazwa = x.get("display_name") or ""
        if not cena or not x.get("slug") or not pasuje_dzial(nazwa, dzial):
            continue
        stara, om = liczba(x.get("regular_price")), liczba(x.get("omnibus_price"))
        im = (x.get("product_images") or [{}])[0]
        plik = ((im.get("sizes") or {}).get("image_normal") or {}).get("filename")
        rozm = [r.get("label") for r in x.get("size_variants") or [] if (r.get("stock_level") or 0) > 0]
        wyn.append(produkt(sklep, nazwa, cena, "https://bigstar.pl/p-" + x["slug"], (im.get("base_path") or "") + plik if plik else None,
                           stara=(stara if stara and stara > cena else None), zrodlo="sklep", dzial=dzial,
                           extra={"omnibus": om if stara and stara > cena else None, "rozmiary": rozm or None,
                                  "plec_sklepu": "meskie" if "męsk" in kat else "damskie" if "damsk" in kat else None}))
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


def _showroom(sklep, url, dzial, ponow=True):
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
    if not d.get("products") and ponow:  # np. „sukienka” daje pustą stronę, „sukienka damska” już nie
        return _showroom(sklep, url + ("%20damska" if dzial == "damskie" else "%20m%C4%99ska"), dzial, ponow=False)
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
        foto = ((x.get("photo") or {}).get("url") or "").split("?")[0]  # pełny obraz; inne rozmiary niż 268x402 dają 404
        wyn.append(produkt(sklep, nazwa[:1].upper() + nazwa[1:], cena / 100, urljoin(url, x["url"]), foto,
                           stara=(stara / 100 if stara and stara > cena else None), zrodlo="sklep", dzial=dzial,
                           extra={"rozmiary": x.get("sizes") or None,
                                  "plec_sklepu": "damskie" if kat.startswith(DAMSKIE_KAT) else "meskie" if kat.startswith(MESKIE_KAT) else None}))
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
        elif sposob == "monnari":
            lista, stan = _monnari(sklep, wzor, q, dzial)
        else:
            url = wzor.format(q=quote(q))
            lista, stan = {"itemlist": _itemlist, "kafle": _kafle, "kafle2": _kafle2, "idosell": _idosell,
                            "kappahl": _kappahl, "vrg": _vrg, "deichmann": _deichmann, "bigstar": _bigstar, "magento": _magento, "showroom": _showroom}[sposob](sklep, url, dzial)
        return sklep, lista, stan
    except Exception as e:
        return sklep, [], "błąd: " + str(e)[:40]


def szukaj(q, dzial):
    out, stany = [], []
    for w in rownolegle(_sklep, [(k, q, dzial) for k in SKLEPY_KONF], watki=6):
        if w:
            out += w[1]
            if w[2] not in ("ok", "pomijam"):
                stany.append(f"{w[0]}: {w[2]}")
    return out, ("ok" if not stany else "; ".join(stany))
