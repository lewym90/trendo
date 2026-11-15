"""Rozmiarówka produktu.

1. Tabela ze strony produktu: wiele sklepów podaje przy produkcie jego własną tabelę (Top Secret, Moodo, Born2Be, Renee,
   Bizuu, Ochnik, Wittchen…). Serwer czyta ją przy pierwszym otwarciu produktu i pamięta 7 dni.
2. Ogólna tabela sklepu (data/rozmiary-sklepow.json): przepisana ze strony „tabele rozmiarów” sklepu, z adresem źródła i datą.
Nic nie zgadujemy: gdy sklep nie podaje tabeli, odpowiedź mówi to wprost."""
import html as _html
import json
import os
import re

from .wspolne import pamiec_czytaj, pamiec_zapisz, pobierz

_KAT = os.path.dirname(os.path.abspath(__file__))
PLIK_SKLEPOW = next((p for p in (os.path.join(_KAT, "..", "..", "data", "rozmiary-sklepow.json"),
                                 os.path.join(_KAT, "rozmiary-sklepow.json")) if os.path.exists(p)), None)
BEZ_STRONY_PRODUKTU = {"Vinted", "C&A", "Zara", "Google Shopping"}  # zapora albo tabela tylko w skrypcie strony

# Klucz pomiaru według podpisu w tabeli (kolejność ma znaczenie: dokładniejsze przed ogólnymi).
POMIARY = [
    ("pasek", r"długość paska|belt"),
    ("wkladka", r"wkładk|insole"),
    ("stopa", r"stop[ay]\b|stopy|foot"),
    ("pod_biustem", r"pod biust|pod biuś"),
    ("biust", r"biust|biuś|bust"),
    ("klatka", r"klat[kc]|chest"),
    ("talia", r"tali|w pasie|obwód pasa|\bpasa\b|waist"),
    ("biodra", r"biodr|bioder|\bhip"),
    ("nogawka", r"nogawk|inner side|inseam|wewnętrzna długość"),
    ("rekaw", r"rękaw|sleeve"),
    ("kolnierzyk", r"kołnierz|szyi|collar|\bneck"),
    ("wzrost", r"wzrost|height"),
    ("dlugosc", r"długość|length"),
    ("szerokosc", r"szerokość|width"),
    ("obcas", r"obcas|heel"),
    ("dlon", r"dłoni|hand"),
    ("glowa", r"głow|head"),
]
NIE_POMIAR = r"dostaw|kurier|paczk|płatnoś|zwrot|uk\b|us\b|\bit\b|\bfr\b|cal[ea]?\b|inch|wiek|miseczk|odpowiednik"
ROZMIAR = re.compile(r"^(?:X{0,4}S|M|X{0,4}L|[1-6]XL|XXXL|ONE ?SIZE|\d{2}(?:[.,]5)?|W?\d{2}(?:\s*/\s*L?\d{2})?|"
                     r"[XSML]{1,4}\s*/\s*[XSML]{1,4}|[XSML]{1,4}\s*/\s*\d{2}|\d{2}\s*-\s*\d{2})$", re.I)
LICZBA = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:cm)?\s*(?:[-–]\s*(\d+(?:[.,]\d+)?))?")


def _czysc(s):
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<br\s*/?>", " ", re.sub(r"<(?!br)[^>]+>", " ", s)))).strip()


def siatki(t):
    """Wszystkie tabele HTML jako prostokątne siatki tekstu (scalone komórki rowspan/colspan rozwinięte)."""
    if "&lt;table" in t:  # tabela zakodowana w opisie produktu (np. w JSON strony)
        t = t + _html.unescape(t.replace('\\"', '"').replace("\\n", "\n").replace("\\/", "/"))
    wyn = []
    for tab in re.findall(r"<table\b.*?</table>", t, re.S | re.I):
        siatka, czeka = [], {}
        for r, tr in enumerate(re.findall(r"<tr\b.*?</tr>", tab, re.S | re.I)):
            wiersz, k = [], 0
            for m in re.finditer(r"<t([dh])\b([^>]*)>(.*?)</t[dh]>", tr, re.S | re.I):
                while (r, k) in czeka:
                    wiersz.append(czeka.pop((r, k))); k += 1
                atr, txt = m.group(2), _czysc(m.group(3))
                cs = int((re.search(r'colspan="?(\d+)', atr) or [0, 1])[1])
                rs = int((re.search(r'rowspan="?(\d+)', atr) or [0, 1])[1])
                for _ in range(min(cs, 20)):
                    wiersz.append(txt)
                    for d in range(1, min(rs, 30)):
                        czeka[(r + d, k)] = txt
                    k += 1
            while (r, k) in czeka:
                wiersz.append(czeka.pop((r, k))); k += 1
            if wiersz:
                siatka.append(wiersz)
        if siatka:
            wyn.append(siatka)
    return wyn


def _klucz(etykieta):
    e = etykieta.lower()
    if not e or re.search(NIE_POMIAR, e) and not re.search(r"obwód|długość|wzrost", e):
        return None
    for k, wz in POMIARY:
        if re.search(wz, e):
            return k
    return None


def _wartosc(s):
    m = LICZBA.search((s or "").replace(",", "."))
    if not m or not re.search(r"\d", s or ""):
        return None
    a = float(m.group(1))
    b = float(m.group(2)) if m.group(2) else None
    return [a, b] if b and b != a else [a]


def _rozmiar(s):
    s = (s or "").strip()
    return bool(s) and len(s) <= 9 and bool(ROZMIAR.match(s))


def _scal(t):
    """Scalone komórki dublują kolumny: sąsiednie kolumny z tym samym rozmiarem i tymi samymi wartościami łączymy."""
    zostaw = [0] if t["rozmiary"] else []
    for j in range(1, len(t["rozmiary"])):
        if t["rozmiary"][j] == t["rozmiary"][j - 1] and all(
                v["wartosci"][j] == v["wartosci"][j - 1] for v in list(t["wymiary"].values()) + t["inne"]):
            continue
        zostaw.append(j)
    t["rozmiary"] = [t["rozmiary"][j] for j in zostaw]
    for v in list(t["wymiary"].values()) + t["inne"]:
        v["wartosci"] = [v["wartosci"][j] for j in zostaw]
    for a in t.get("aliasy", []):
        a["rozmiary"] = [a["rozmiary"][j] for j in zostaw]
    return t


def _z_siatki(g):
    """Rozpoznaje tabelę rozmiarów w dowolnym z dwóch układów. Zwraca słownik albo None."""
    najl = None
    # układ A: rozmiary w wierszu (pierwsza komórka to podpis); bierzemy wiersz z największą liczbą rozmiarów
    kand = []
    for i, w in enumerate(g[:7]):
        if not w or _klucz(w[0]):
            continue  # wiersz pomiaru (np. talia 62, 66…) nie jest wierszem rozmiarów
        n = sum(1 for c in w[1:] if _rozmiar(c))
        if n >= 2 and n >= len([c for c in w[1:] if c]) - 1:
            ocena = n + (5 if re.search(r"rozmiar|size|^eu", w[0].lower()) else 0) \
                + (2 if any(re.search(r"[SMLX]", c) for c in w[1:] if _rozmiar(c)) else 0) - i * 0.01
            kand.append((ocena, i))
    if kand:
        _, i = max(kand)
        w = g[i]
        idx = [j for j in range(1, len(w)) if _rozmiar(w[j])]
        aliasy = []
        for i2, w2 in enumerate(g[:7]):
            if i2 != i and w2 and not _klucz(w2[0]) and all(j < len(w2) and _rozmiar(w2[j]) for j in idx) \
                    and re.search(r"^$|rozmiar|size|^eur?\b|^it\b|^uk\b|^us\b|spodnie|jeans|garnitur|marynark|numer", w2[0].lower()):
                aliasy.append({"nazwa": w2[0], "rozmiary": [w2[j] for j in idx]})
        wym, inne = {}, []
        for w2 in g[i + 1:]:
            k = _klucz(w2[0]) if w2 else None
            if not k:
                continue
            wart = [_wartosc(w2[j]) if j < len(w2) else None for j in idx]
            if sum(1 for x in wart if x) >= max(2, len(idx) - 1):
                if k not in wym:
                    wym[k] = {"nazwa": w2[0], "wartosci": wart}
                else:
                    inne.append({"nazwa": w2[0], "wartosci": wart})
        if wym:
            najl = _scal({"rozmiary": [w[j] for j in idx], "wymiary": wym, "inne": inne, "aliasy": aliasy})
    # układ B: rozmiary w pierwszej kolumnie, pomiary w nagłówku
    for i, w in enumerate(g):
        klucze = [(j, _klucz(c), c) for j, c in enumerate(w) if j > 0 and _klucz(c)]
        if len(klucze) >= 1:
            wiersze = [w2 for w2 in g[i + 1:] if w2 and _rozmiar(w2[0])]
            if len(wiersze) >= 2:
                wym = {}
                for j, k, naz in klucze:
                    wart = [_wartosc(w2[j]) if j < len(w2) else None for w2 in wiersze]
                    if k not in wym and sum(1 for x in wart if x) >= max(2, len(wiersze) - 1):
                        wym[k] = {"nazwa": naz, "wartosci": wart}
                if wym and (not najl or len(wym) > len(najl["wymiary"])):
                    najl = _scal({"rozmiary": [w2[0] for w2 in wiersze], "wymiary": wym, "inne": []})
            break
    return najl


def z_html(t):
    """Najlepsza tabela rozmiarów na stronie (najwięcej rozpoznanych pomiarów)."""
    najl = None
    for g in siatki(t):
        x = _z_siatki(g)
        if x and (not najl or (len(x["wymiary"]), len(x["rozmiary"])) > (len(najl["wymiary"]), len(najl["rozmiary"]))):
            najl = x
    return najl


def _sklepy():
    if not PLIK_SKLEPOW:
        return {}
    try:
        return json.load(open(PLIK_SKLEPOW, encoding="utf-8")).get("sklepy", {})
    except Exception:
        return {}


GRUPA = {"buty": "buty", "botki": "buty", "kozaki": "buty", "sneakersy": "buty", "półbuty": "buty", "szpilki": "buty", "czółenka": "buty",
         "mokasyny": "buty", "baleriny": "buty", "sandały": "buty", "klapki": "buty", "kapcie": "buty",
         "spodnie": "dol", "szorty": "dol", "legginsy": "dol", "spódnica": "dol", "jeansy": "jeansy",
         "marynarka": "marynarki", "garnitur": "marynarki", "pasek": "paski"}


def grupa(rodzaj, nazwa=""):
    if rodzaj in GRUPA:
        return GRUPA[rodzaj]
    n = (nazwa or "").lower()
    for slowo, g in (("jeans", "jeansy"), ("spodni", "dol"), ("spódnic", "dol"), ("szort", "dol"), ("marynark", "marynarki"),
                     ("garnitur", "marynarki"), ("pasek", "paski"), ("botk", "buty"), ("kozak", "buty"), ("sneaker", "buty"),
                     ("półbut", "buty"), ("szpilk", "buty"), ("czółen", "buty"), ("mokasyn", "buty"), ("balerin", "buty"),
                     ("sandał", "buty"), ("klapk", "buty"), ("trzewik", "buty"), ("buty", "buty")):
        if slowo in n:
            return g
    return "ubrania"


def tabela_sklepu(sklep, dzial, gr, rozmiary_produktu=None):
    """Ogólna tabela sklepu: najpierw ta dla grupy, potem ogólna dla ubrań; przy kilku wybiera najlepiej pasującą do rozmiarów produktu."""
    s = _sklepy().get(sklep)
    if not s:
        return None
    d = "m" if dzial == "meskie" else "d"
    kand = [t for t in s.get("tabele", []) if t["dzial"] == d and t["grupa"] == gr]
    if not kand and gr in ("dol", "jeansy", "marynarki"):
        kand = [t for t in s.get("tabele", []) if t["dzial"] == d and t["grupa"] in (("dol",) if gr == "jeansy" else ()) + ("ubrania",)]
    if not kand and gr == "ubrania":
        kand = [t for t in s.get("tabele", []) if t["dzial"] == d and t["grupa"] in ("gora",)]
    if not kand:
        return None
    rp = {str(r).upper().replace(" ", "") for r in rozmiary_produktu or []}
    kand.sort(key=lambda t: -len(rp & {str(r).upper().replace(" ", "") for r in t["rozmiary"]}))
    t = dict(kand[0])
    t.update({"zrodlo_url": s.get("url"), "sprawdzono": s.get("sprawdzono")})
    return t


def dla_produktu(p):
    """p: produkt z bazy (sklep, url, dzial, nazwa, rodzaj, rozmiary). Zwraca odpowiedź dla aplikacji."""
    gr = grupa(p.get("rodzaj"), p.get("nazwa"))
    wyn = {"grupa": gr, "dzial": p.get("dzial"), "tabela": None, "zrodlo": None}
    if p.get("sklep") not in BEZ_STRONY_PRODUKTU and p.get("zrodlo") == "sklep" and p.get("url"):
        klucz = "rozm|" + p["url"]
        z = pamiec_czytaj(klucz, 7 * 86400)
        if z is None:
            kod, b = pobierz(p["url"], czas=20)
            z = {"t": z_html(b.decode("utf-8", "ignore")) if kod == 200 else None}
            if kod == 200:
                pamiec_zapisz(klucz, z)
        if z and z.get("t"):
            wyn.update({"tabela": z["t"], "zrodlo": "produkt", "zrodlo_url": p["url"]})
            return wyn
    t = tabela_sklepu(p.get("sklep"), p.get("dzial"), gr, p.get("rozmiary"))
    if t:
        wyn.update({"tabela": {"rozmiary": t["rozmiary"], "wymiary": t["wymiary"], "inne": t.get("inne", [])},
                    "zrodlo": "sklep", "zrodlo_url": t.get("zrodlo_url"), "sprawdzono": t.get("sprawdzono"), "nazwa_tabeli": t.get("nazwa")})
    return wyn
