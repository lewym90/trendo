"""Łącznik Google Shopping. Główny dostawca: Serper (klucz ~/.trendo-serper), zapasowy: SerpApi (~/.trendo-serpapi).
Bez własnych limitów dziennych (decyzja użytkownika 15.11): granicą są kredyty na kontach dostawców.
Wyniki dzieli wspólna pamięć serwera (api.py), więc to samo hasło nie zużywa kredytów drugi raz."""
import json, os, re, time
from urllib.parse import urlencode
from .wspolne import pobierz_json, produkt, liczba, licznik

NAZWA = "Google Shopping"

NAZWY = {"zara polska": "Zara", "h&m pl": "H&M", "h&m": "H&M", "modivo": "Modivo", "shop.mango.com": "Mango",
         "zalando.pl": "Zalando", "answear.com": "Answear", "eobuwie.pl": "eobuwie", "eobuwie.com.pl": "eobuwie",
         "bonprix.pl": "bonprix", "reserved": "Reserved", "allegro": "Allegro", "cos": "COS", "mango": "Mango"}


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


def _klucz(plik, zmienna):
    k = os.environ.get(zmienna)
    if k:
        return k.strip()
    for p in (f"/root/{plik}", os.path.expanduser(f"~/{plik}")):
        try:
            return open(p).read().strip()
        except OSError:
            pass
    return None


def _fraza(q, dzial):
    return q + (" męskie" if dzial == "meskie" else " damskie")


def _serper(q, dzial, k):
    kod, d = pobierz_json("https://google.serper.dev/shopping", czas=30,
                          naglowki={"X-API-KEY": k, "Content-Type": "application/json"},
                          dane=json.dumps({"q": _fraza(q, dzial), "gl": "pl", "hl": "pl", "location": "Poland", "num": 40}))
    if not d:
        return None, f"Serper: brak odpowiedzi ({kod})"
    if d.get("message") and not d.get("shopping"):
        return None, "Serper: " + str(d["message"])[:60]
    wyn = []
    for r in d.get("shopping") or []:
        cena = liczba(r.get("price"))
        if not cena or not r.get("link"):
            continue
        wyn.append(produkt(nazwa_sklepu(r.get("source")), r.get("title", ""), cena, r["link"], r.get("imageUrl"),
                           stara=liczba(r.get("oldPrice") or r.get("originalPrice")), zrodlo="google", dzial=dzial))
    return wyn, "ok"


def _serpapi(q, dzial, k):
    url = "https://serpapi.com/search.json?" + urlencode({
        "engine": "google_shopping", "q": _fraza(q, dzial), "gl": "pl", "hl": "pl", "google_domain": "google.pl",
        "location": "Poland", "api_key": k})
    kod, d = pobierz_json(url, czas=40)
    if not d:
        return None, f"SerpApi: brak odpowiedzi ({kod})"
    if d.get("error"):
        return None, "SerpApi: " + d["error"][:60]
    wyn = []
    for r in (d.get("shopping_results") or []) + (d.get("inline_shopping_results") or []):
        cena = r.get("extracted_price") or liczba(r.get("price"))
        if not cena:
            continue
        link = r.get("link") or r.get("product_link")
        stara = r.get("extracted_old_price") or liczba(r.get("old_price"))
        wyn.append(produkt(nazwa_sklepu(r.get("source")), r.get("title", ""), cena, link, r.get("thumbnail"),
                           stara=stara, zrodlo="google", dzial=dzial))
    return wyn, "ok"


def szukaj(q, dzial):
    dzien = time.strftime("%Y-%m-%d")
    uwagi = []
    for nazwa, plik, zm, f in (("serper", ".trendo-serper", "SERPER_KEY", _serper),
                               ("serpapi", ".trendo-serpapi", "SERPAPI_KEY", _serpapi)):
        k = _klucz(plik, zm)
        if not k:
            continue
        licznik(f"{nazwa}-{dzien}", 1)
        wyn, stan = f(q, dzial, k)
        if wyn is not None:
            return wyn, "ok"
        uwagi.append(stan)
    return [], ("; ".join(uwagi) if uwagi else "brak klucza")


def stan():
    dzien = time.strftime("%Y-%m-%d")
    out = {}
    if _klucz(".trendo-serper", "SERPER_KEY"):
        out["serper"] = {"klucz": True, "dzis_uzyto": licznik(f"serper-{dzien}")}
    k = _klucz(".trendo-serpapi", "SERPAPI_KEY")
    if k:
        kod, d = pobierz_json("https://serpapi.com/account.json?" + urlencode({"api_key": k}))
        out["serpapi"] = {"klucz": True, "zostalo_w_miesiacu": (d or {}).get("plan_searches_left") or (d or {}).get("total_searches_left"),
                          "dzis_uzyto": licznik(f"serpapi-{dzien}")}
    return out or {"klucz": False}


def _domena(u):
    m = re.match(r"https?://([^/]+)", u or "")
    return (m.group(1).lower().replace("www.", "") if m else "")


def _znak(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower().replace("&", "and"))


def wybierz_link(organic, sklep):
    """Z wyników wyszukiwania wybiera stronę produktu w sklepie. Zwraca (url, pewny)."""
    s = _znak(sklep)
    kandydaci = [r.get("link") for r in organic or [] if r.get("link") and "google." not in _domena(r.get("link"))]
    for u in kandydaci:
        d = _znak(_domena(u).split(".")[0] if not _domena(u).startswith("shop.") else _domena(u).split(".")[1])
        if s and d and (s in _znak(_domena(u)) or d in s):
            return u, True
    return None, False


def link_do_sklepu(nazwa, sklep):
    """Szuka bezpośredniej strony produktu (1 wyszukiwanie Serper). Zwraca (url, pewny) albo (None, False)."""
    k = _klucz(".trendo-serper", "SERPER_KEY")
    dzien = time.strftime("%Y-%m-%d")
    if not k:
        return None, False
    licznik(f"serper-{dzien}", 1)
    kod, d = pobierz_json("https://google.serper.dev/search", czas=25,
                          naglowki={"X-API-KEY": k, "Content-Type": "application/json"},
                          dane=json.dumps({"q": f"{nazwa} {sklep}", "gl": "pl", "hl": "pl", "num": 10}))
    if not d:
        return None, False
    return wybierz_link(d.get("organic"), sklep)
