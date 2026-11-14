"""Łącznik Google Shopping przez SerpApi. Obejmuje sklepy, których nie czytamy bezpośrednio.
Klucz: plik ~/.trendo-serpapi albo zmienna SERPAPI_KEY. Dzienny limit chroni darmowy plan."""
import os, re, time
from urllib.parse import urlencode
from .wspolne import pobierz_json, produkt, liczba, licznik

NAZWA = "Google Shopping"
LIMIT_DZIENNY = int(os.environ.get("SERPAPI_LIMIT_DZIENNY", "8"))


NAZWY = {"zara polska": "Zara", "h&m pl": "H&M", "h&m": "H&M", "modivo": "Modivo", "shop.mango.com": "Mango",
         "zalando.pl": "Zalando", "answear.com": "Answear", "eobuwie.pl": "eobuwie", "eobuwie.com.pl": "eobuwie",
         "bonprix.pl": "bonprix", "reserved": "Reserved", "allegro": "Allegro", "cos": "COS"}


def nazwa_sklepu(n):
    n = (n or "Inny sklep").strip()
    k = n.lower()
    if k in NAZWY:
        return NAZWY[k]
    k = re.sub(r"^(www\.|shop\.|sklep\.)", "", k)
    k = re.sub(r"\.(com\.pl|pl|com|eu|store|shop)$", "", k)
    if k != n.lower():
        return NAZWY.get(k, k[:1].upper() + k[1:])
    return n


def klucz():
    k = os.environ.get("SERPAPI_KEY")
    if k:
        return k.strip()
    for p in ("/root/.trendo-serpapi", os.path.expanduser("~/.trendo-serpapi")):
        try:
            return open(p).read().strip()
        except OSError:
            pass
    return None


def szukaj(q, dzial):
    k = klucz()
    if not k:
        return [], "brak klucza"
    dzien = time.strftime("serpapi-%Y-%m-%d")
    if licznik(dzien) >= LIMIT_DZIENNY:
        return [], "dzienny limit wyczerpany"
    fraza = q + (" męskie" if dzial == "meskie" else " damskie")
    url = "https://serpapi.com/search.json?" + urlencode({
        "engine": "google_shopping", "q": fraza, "gl": "pl", "hl": "pl", "google_domain": "google.pl",
        "location": "Poland", "api_key": k})
    licznik(dzien, 1)
    kod, d = pobierz_json(url, czas=40)
    if not d:
        return [], f"brak odpowiedzi ({kod})"
    if d.get("error"):
        return [], d["error"][:80]
    wyn = []
    for r in (d.get("shopping_results") or []) + (d.get("inline_shopping_results") or []):
        cena = r.get("extracted_price") or liczba(r.get("price"))
        if not cena:
            continue
        link = r.get("link") or r.get("product_link")
        sklep = nazwa_sklepu(r.get("source"))
        stara = r.get("extracted_old_price") or liczba(r.get("old_price"))
        wyn.append(produkt(sklep, r.get("title", ""), cena, link, r.get("thumbnail"), stara=stara,
                           zrodlo="google", dzial=dzial))
    return wyn, "ok"


def stan():
    k = klucz()
    if not k:
        return {"klucz": False}
    kod, d = pobierz_json("https://serpapi.com/account.json?" + urlencode({"api_key": k}))
    if not d:
        return {"klucz": True, "konto": f"brak odpowiedzi ({kod})"}
    return {"klucz": True, "plan": d.get("plan_name"), "zostalo_w_miesiacu": d.get("plan_searches_left") or d.get("total_searches_left"),
            "dzis_uzyto": licznik(time.strftime("serpapi-%Y-%m-%d")), "limit_dzienny": LIMIT_DZIENNY}
