"""Łącznik grupy LPP (Reserved, Mohito, House, Cropp, Sinsay).
Sklepy szukają przez Algolię; publiczny klucz tylko do wyszukiwania sklep podaje na swojej stronie.
Algolia zwraca też najniższą cenę z 30 dni (history_price), więc promocje weryfikujemy od razu."""
import re
from urllib.parse import urlencode
from .wspolne import pobierz, pobierz_json, produkt, pamiec_czytaj, pamiec_zapisz, rownolegle

NAZWA = "LPP"
MARKI = [("Reserved", "https://www.reserved.com/pl/pl/"), ("Mohito", "https://www.mohito.com/pl/pl/"),
         ("House", "https://www.housebrand.com/pl/pl/"), ("Cropp", "https://www.cropp.com/pl/pl/"),
         ("Sinsay", "https://www.sinsay.com/pl/pl/")]
SKLEPY = [m for m, _ in MARKI]
TYLKO_DAMSKIE = {"Mohito"}


def _konfiguracja(marka, adres):
    k = f"lpp-konf|{marka}"
    c = pamiec_czytaj(k, 24 * 3600)
    if c:
        return c
    kod, b = pobierz(adres)
    t = b.decode("utf-8", "ignore")
    app = re.search(r"applicationId:\s*'([A-Z0-9]+)'", t)
    key = re.search(r"searchApiKey:\s*'([a-f0-9]+)'", t)
    idx = re.search(r"productPrimaryIndex:\s*'([A-Z0-9_]+)'", t)
    if not (app and key and idx):
        return None
    c = {"app": app.group(1), "key": key.group(1), "idx": idx.group(1)}
    pamiec_zapisz(k, c)
    return c


def _marka(arg):
    (marka, adres), q, dzial = arg
    if dzial == "meskie" and marka in TYLKO_DAMSKIE:
        return marka, [], "tylko damskie"
    c = _konfiguracja(marka, adres)
    if not c:
        return marka, [], "brak konfiguracji wyszukiwarki"
    url = f"https://{c['app']}-dsn.algolia.net/1/indexes/{c['idx']}?" + urlencode(
        {"query": q, "hitsPerPage": 40, "x-algolia-application-id": c["app"], "x-algolia-api-key": c["key"]})
    kod, d = pobierz_json(url)
    if not d:
        return marka, [], f"brak odpowiedzi ({kod})"
    wyn = []
    for h in d.get("hits") or []:
        if h.get("blocked") or h.get("sellable") is False:
            continue
        plec = (h.get("sex") or "").lower()
        if dzial == "damskie" and plec.startswith("mężczy"):
            continue
        if dzial == "meskie" and plec.startswith("kobiet"):
            continue
        if plec and not (plec.startswith("kobiet") or plec.startswith("mężczy") or "unisex" in plec):
            continue  # dziecięce itp.
        cena = h.get("final_price") or h.get("regular_price")
        if not cena or not h.get("url"):
            continue
        stara = h.get("regular_price") if (h.get("regular_price") or 0) > cena else None
        omnibus = h.get("history_price") or None
        foto = (h.get("photos") or {}).get("categoryPhoto")
        wyn.append(produkt(marka, h.get("name", ""), cena, h["url"], foto, stara=stara, zrodlo="sklep", dzial=dzial,
                           extra={"omnibus": omnibus, "rozmiary": h.get("sizes") or None,
                                  "plec_sklepu": "damskie" if plec.startswith("kobiet") else "meskie" if plec.startswith("mężczy")
                                  else "unisex" if "unisex" in plec else None,
                                  "material": ", ".join((h.get("features") or {}).get("Materiał", [])) or None}))
    return marka, wyn, "ok"


def szukaj(q, dzial):
    wyniki = rownolegle(_marka, [(m, q, dzial) for m in MARKI], watki=5)
    wszystkie, stany = [], []
    for w in wyniki:
        if not w:
            continue
        marka, lista, stan = w
        wszystkie += lista
        if stan not in ("ok", "tylko damskie"):
            stany.append(f"{marka}: {stan}")
    return wszystkie, ("ok" if not stany else "; ".join(stany))
