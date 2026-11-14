"""Łącznik Zara: wewnętrzna wyszukiwarka sklepu (itxrest). Ceny w groszach."""
from urllib.parse import quote
from .wspolne import pobierz_json, produkt

NAZWA = "Zara"
SKLEPY = ["Zara"]
SKLEP_ID = 11725  # Zara Polska


def _stara(c):
    for k in ("oldPrice", "originalPrice", "previousPrice"):
        if c.get(k):
            return c[k]
    for kol in (c.get("detail") or {}).get("colors") or []:
        for k in ("oldPrice", "originalPrice"):
            if kol.get(k):
                return kol[k]
    return None


def szukaj(q, dzial):
    sekcja = "MAN" if dzial == "meskie" else "WOMAN"
    url = (f"https://www.zara.com/itxrest/1/search/store/{SKLEP_ID}/query?query={quote(q)}"
           f"&locale=pl_PL&section={sekcja}&limit=40")
    kod, d = pobierz_json(url)
    if not d:
        return [], f"brak odpowiedzi ({kod})"
    wyn = []
    for r in d.get("results") or []:
        c = r.get("content") or {}
        if c.get("type") not in (None, "Product") or not c.get("price"):
            continue
        seo = c.get("seo") or {}
        if not seo.get("keyword"):
            continue
        link = f"https://www.zara.com/pl/pl/{seo['keyword']}-p{seo.get('seoProductId', '')}.html"
        if seo.get("discernProductId"):
            link += f"?v1={seo['discernProductId']}"
        foto = None
        media = c.get("xmedia") or []
        if not media:
            kol = ((c.get("detail") or {}).get("colors") or [{}])[0]
            media = kol.get("xmedia") or []
        if media and media[0].get("url"):
            foto = media[0]["url"].replace("{width}", "750")
        stara = _stara(c)
        wyn.append(produkt(NAZWA, c.get("name", "").capitalize(), c["price"] / 100, link, foto,
                           stara=(stara / 100 if stara else None), zrodlo="sklep", dzial=dzial,
                           extra={"dostepnosc": c.get("availability")}))
    return wyn, "ok"
