"""Łącznik Modivo i eobuwie (wspólna wyszukiwarka grupy). Zwraca też cenę Omnibus."""
from urllib.parse import urlencode
from .wspolne import pobierz_json, produkt, rownolegle

NAZWA = "Modivo i eobuwie"
KANALY = [("Modivo", "modivo", "https://modivo.pl/p/", {"damskie": "kobiety", "meskie": "mezczyzni"}),
          ("eobuwie", "eobuwie", "https://eobuwie.com.pl/p/", {"damskie": "damskie", "meskie": "meskie"})]
SKLEPY = ["Modivo", "eobuwie"]


def _kwota(v):
    try:
        return float(v["value"]["pl_PL"]["PLN"]["amount"])
    except Exception:
        return None


def _kanal(arg):
    (sklep, kanal, adres, kat), q, dzial = arg
    url = "https://search-service.modivo.io/search?" + urlencode([
        ("channel", kanal), ("currency", "PLN"), ("locale", "pl_PL"), ("limit", 40), ("page", 1),
        ("query", q), ("categories[]", kat[dzial]), ("engine", "SYNERISE")])
    kod, d = pobierz_json(url)
    if not d:
        return sklep, [], f"brak odpowiedzi ({kod})"
    wyn = []
    for p in d.get("products") or []:
        v = p.get("values") or {}
        cena = _kwota(v.get("final_price"))
        stara = _kwota(v.get("price"))
        if not cena:
            continue
        try:
            nazwa = v["nazwa_wyswietlana"]["value"]["pl_PL"]
            klucz = v["url_key"]["value"]["pl_PL"]
        except Exception:
            continue
        zdj = None
        try:
            zdj = f"https://img.modivo.cloud/product({v['images']['value'][0]['url']},jpg)"
        except Exception:
            pass
        rozm = [r.get("size") for r in (p.get("variants") or {}).values() if r.get("size")] or None
        wyn.append(produkt(sklep, nazwa, cena, adres + klucz, zdj, stara=(stara if stara and stara > cena else None),
                           zrodlo="sklep", dzial=dzial, extra={"omnibus": _kwota(v.get("omnibus_price")), "rozmiary": rozm}))
    return sklep, wyn, "ok"


def szukaj(q, dzial):
    out, stany = [], []
    for w in rownolegle(_kanal, [(k, q, dzial) for k in KANALY], watki=2):
        if w:
            out += w[1]
            if w[2] != "ok":
                stany.append(f"{w[0]}: {w[2]}")
    return out, ("ok" if not stany else "; ".join(stany))
