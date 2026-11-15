"""Ostatnio widziane produkty i obserwowane ceny.

Każdy produkt z wyszukiwania trafia do tabeli `produkty` (ostatni stan). Z niej powstają:
- okazje dnia: tylko obniżki sprawdzone (Omnibus albo własna historia z 30 dni), z ostatnich 48 godzin,
- alerty cenowe: produkty, które ktoś obserwuje, serwer odświeża sam co 12 godzin w ich własnym sklepie.
Produkty z Google Shopping nie są odświeżane (każde zapytanie zużywa płatny limit)."""
import json
import re
import time
import traceback

from .wspolne import DB, _baza_blokada, zapisz_cene, weryfikuj

with _baza_blokada:
    DB.execute("CREATE TABLE IF NOT EXISTS produkty (id TEXT PRIMARY KEY, dzial TEXT, czas INTEGER, dane TEXT)")
    DB.execute("CREATE INDEX IF NOT EXISTS produkty_czas ON produkty(czas)")
    DB.execute("CREATE TABLE IF NOT EXISTS obserwowane (id TEXT PRIMARY KEY, dodano INTEGER, sprawdzono INTEGER)")
    DB.commit()

POLA = ("id", "sklep", "nazwa", "cena", "stara", "stara_sklepu", "omnibus", "url", "zdjecie", "zrodlo", "dzial", "plec_sklepu",
        "weryf", "rozmiary", "sprawdzono", "dostepnosc", "uzywany", "stan", "kolor", "material")
ODSWIEZ_CO = 12 * 3600


def _okrojony(p):
    d = {k: p[k] for k in POLA if p.get(k) is not None}
    if (p.get("klasa") or {}).get("r"):
        d["rodzaj"] = p["klasa"]["r"]  # rodzaj rzeczy z oceny AI: dobór tabeli rozmiarów i szkicu
    elif p.get("rodzaj"):
        d["rodzaj"] = p["rodzaj"]
    return d


def zapamietaj(produkty):
    teraz = int(time.time())
    wiersze = [(p["id"], p.get("dzial") or "", teraz, json.dumps(_okrojony(p), ensure_ascii=False)) for p in produkty if p.get("id")]
    if not wiersze:
        return
    with _baza_blokada:
        DB.executemany("INSERT OR REPLACE INTO produkty VALUES (?,?,?,?)", wiersze)
        DB.commit()


def dane(ids):
    ids = [i for i in ids if i][:200]
    if not ids:
        return {}
    with _baza_blokada:
        r = DB.execute(f"SELECT id, czas, dane FROM produkty WHERE id IN ({','.join('?' * len(ids))})", ids).fetchall()
    wyn = {}
    for i, czas, d in r:
        p = json.loads(d)
        p["widziany"] = czas
        wyn[i] = p
    return wyn


def obserwuj(ids):
    teraz = int(time.time())
    ids = [i for i in ids if i and re.fullmatch(r"[A-Za-z0-9_-]{4,40}", i)][:200]
    with _baza_blokada:
        DB.executemany("INSERT OR IGNORE INTO obserwowane VALUES (?,?,0)", [(i, teraz) for i in ids])
        DB.commit()
    return len(ids)


def okazje(dzial, limit=60):
    """Sprawdzone obniżki z ostatnich 48 godzin, od największej. Jedna pozycja na nazwę produktu w sklepie."""
    od = int(time.time()) - 48 * 3600
    with _baza_blokada:
        r = DB.execute("SELECT dane FROM produkty WHERE czas>? AND dzial=?", (od, dzial)).fetchall()
    lista, byly = [], set()
    for (d,) in r:
        p = json.loads(d)
        if p.get("weryf") != "ok" or not p.get("stara") or p["stara"] <= p["cena"]:
            continue
        if p.get("plec_sklepu") and p["plec_sklepu"] != dzial:
            continue
        k = (p["sklep"].lower(), p["nazwa"].lower())
        if k in byly:
            continue
        byly.add(k)
        p["rabat"] = round((1 - p["cena"] / p["stara"]) * 100)
        if p["rabat"] >= 5:
            lista.append(p)
    lista.sort(key=lambda p: -p["rabat"])
    # nie więcej niż 6 pozycji z jednego sklepu, żeby jedna wyprzedaż nie zasłoniła reszty
    wyn, ile = [], {}
    for p in lista:
        if ile.get(p["sklep"], 0) < 6:
            wyn.append(p); ile[p["sklep"]] = ile.get(p["sklep"], 0) + 1
        if len(wyn) >= limit:
            break
    return wyn


def _bez_parametrow(u):
    return (u or "").split("?")[0].split("#")[0].rstrip("/").lower()


def _szukaj_w_sklepie(p, laczniki):
    """Szuka produktu po nazwie w jego własnym sklepie. Zwraca świeżą wersję albo None."""
    from . import lacznik_strony
    sklep, dzial = p["sklep"], p.get("dzial") or "damskie"
    lista = None
    konf = next((k for k in lacznik_strony.SKLEPY_KONF if k[0] == sklep), None)
    if konf:
        _, lista, _ = lacznik_strony._sklep((konf, p["nazwa"], dzial))
    else:
        for l in laczniki:
            if l.NAZWA != "Google Shopping" and sklep in getattr(l, "SKLEPY", [l.NAZWA]) and l is not lacznik_strony:
                lista, _ = l.szukaj(p["nazwa"], dzial)
                break
    if not lista:
        return None
    url = _bez_parametrow(p.get("url"))
    for x in lista:
        if x["id"] == p["id"] or (url and _bez_parametrow(x.get("url")) == url):
            return x
    return None


def odswiez(laczniki, maks=120):
    """Odświeża obserwowane produkty, których nie sprawdzano od 12 godzin."""
    teraz = int(time.time())
    with _baza_blokada:
        ids = [r[0] for r in DB.execute("SELECT id FROM obserwowane WHERE sprawdzono<? ORDER BY sprawdzono LIMIT ?",
                                        (teraz - ODSWIEZ_CO, maks)).fetchall()]
    znane = dane(ids)
    for i in ids:
        p = znane.get(i)
        stan = teraz
        try:
            if p and p.get("zrodlo") == "sklep":
                nowy = _szukaj_w_sklepie(p, laczniki)
                if nowy:
                    nowy["id"] = i
                    for k in ("plec_sklepu",):
                        nowy.setdefault(k, p.get(k))
                    zapisz_cene(nowy)
                    nowy["weryf"] = weryfikuj(nowy)
                    zapamietaj([nowy])
                else:
                    p["brak_w_sklepie"] = teraz  # nie znaleziono: mógł zejść ze sprzedaży
                    with _baza_blokada:
                        DB.execute("UPDATE produkty SET dane=? WHERE id=?", (json.dumps(p, ensure_ascii=False), i))
                        DB.commit()
        except Exception:
            traceback.print_exc()
        with _baza_blokada:
            DB.execute("UPDATE obserwowane SET sprawdzono=? WHERE id=?", (stan, i))
            DB.commit()
        time.sleep(2)  # sklepy odpytujemy spokojnie, po jednym produkcie


def sprzataj():
    """Produkty niewidziane od 60 dni znikają, chyba że ktoś je obserwuje."""
    od = int(time.time()) - 60 * 86400
    with _baza_blokada:
        DB.execute("DELETE FROM produkty WHERE czas<? AND id NOT IN (SELECT id FROM obserwowane)", (od,))
        DB.commit()
