"""Loga sklepów: oficjalna ikona ze strony sklepu (apple-touch-icon albo ikona strony), pamiętana 14 dni.
Logo służy wyłącznie do oznaczenia, z którego sklepu jest produkt."""
import re, time, unicodedata
from urllib.parse import urljoin, urlparse
from .wspolne import DB, _baza_blokada, pobierz

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
    "kappahlpoland": "kappahl.com", "lidlsklep online": "lidl.pl", "lidlskleponline": "lidl.pl", "ozonee": "ozonee.pl",
    "denley": "denley.pl", "moodo": "moodo.pl", "modnakiecka": "modnakiecka.pl", "greenpoint": "greenpoint.pl",
    "solarcompany": "solar.com.pl", "breuninger": "breuninger.com", "sneakerpeeker": "sneakerpeeker.pl", "vinted": "vinted.pl",
    "hugoboss": "hugoboss.com", "massimodutti": "massimodutti.com", "bershka": "bershka.com", "stradivarius": "stradivarius.com",
    "pullbear": "pullandbear.com", "cos": "cos.com", "arket": "arket.com", "nike": "nike.com", "adidas": "adidas.pl",
    "ca": "c-and-a.com", "orsay": "orsay.com", "simple": "simple.com", "liujo": "liujo.com", "ochnikpl": "ochnik.com",
}

with _baza_blokada:
    DB.execute("CREATE TABLE IF NOT EXISTS logo (domena TEXT PRIMARY KEY, typ TEXT, dane BLOB, czas INTEGER)")
    DB.execute("CREATE TABLE IF NOT EXISTS logo_domeny (sklep TEXT PRIMARY KEY, domena TEXT)")
    DB.commit()
_poznane = set()


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
    k = _znak(sklep)
    if not k:
        return None
    with _baza_blokada:
        r = DB.execute("SELECT domena FROM logo_domeny WHERE sklep=?", (k,)).fetchone()
    if r:
        return r[0]
    if k in DOMENY:
        return DOMENY[k]
    if re.fullmatch(r"[a-z0-9]{3,30}", k):
        return k + ".pl"
    return None


def _obraz(b):
    if not b or len(b) < 100:
        return None
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[:4] == b"\x00\x00\x01\x00":
        return "image/x-icon"
    if b[8:12] == b"WEBP":
        return "image/webp"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if b"<svg" in b[:600].lower():
        return "image/svg+xml"
    return None


def _rozmiar(typ, b):
    """Szerokość obrazka w pikselach (SVG traktujemy jak duży)."""
    try:
        if typ == "image/svg+xml":
            return 512
        if typ == "image/png":
            return int.from_bytes(b[16:20], "big")
        if typ == "image/x-icon":
            return max(b[6 + 16 * i] or 256 for i in range(min(int.from_bytes(b[4:6], "little"), 8)))
        if typ == "image/gif":
            return int.from_bytes(b[6:8], "little")
    except Exception:
        pass
    return 64


def _kandydaci(d):
    adres = f"https://www.{d}/" if d.count(".") == 1 else f"https://{d}/"
    kod, b = pobierz(adres, czas=15, limit=2_500_000)
    lista = []
    if kod == 200 and b:
        html = b.decode("utf-8", "ignore")
        for tag in re.findall(r"<link\b[^>]*>", html, re.I):
            rel = (re.search(r'rel=["\']([^"\']+)', tag, re.I) or [None, ""])[1].lower()
            href = (re.search(r'href=["\']([^"\']+)', tag, re.I) or [None, ""])[1]
            if "icon" not in rel or not href:
                continue
            rozm = max([int(x) for x in re.findall(r"(\d+)x\d+", tag)] or [0])
            waga = (2000 if "apple-touch" in rel else 0) + (500 if href.lower().endswith(".svg") else 0) + rozm
            lista.append((waga, urljoin(adres, href.replace("&amp;", "&"))))
    lista.sort(reverse=True)
    wyn = [u for _, u in lista]
    wyn += [urljoin(adres, "/apple-touch-icon.png"), f"https://www.google.com/s2/favicons?domain={d}&sz=128",
            f"https://icons.duckduckgo.com/ip3/{d}.ico", urljoin(adres, "/favicon.ico")]
    return wyn


def logo(sklep):
    """Zwraca (typ, bajty) albo (None, None)."""
    d = domena(sklep)
    if not d:
        return None, None
    with _baza_blokada:
        r = DB.execute("SELECT typ, dane, czas FROM logo WHERE domena=?", (d,)).fetchone()
    if r and (time.time() - r[2] < (14 * 86400 if r[1] else 86400)):
        return (r[0], bytes(r[1])) if r[1] else (None, None)
    typ, dane, najl = None, None, -1
    for u in _kandydaci(d)[:8]:
        kod, b = pobierz(u, czas=12, limit=600_000)
        t = _obraz(b) if kod == 200 else None
        if not t:
            continue
        w = _rozmiar(t, b)
        if w > najl:
            typ, dane, najl = t, b, w
        if w >= 120:
            break
    with _baza_blokada:
        DB.execute("INSERT OR REPLACE INTO logo VALUES (?,?,?,?)", (d, typ, dane, int(time.time()))); DB.commit()
    return typ, dane
