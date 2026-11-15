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
POLA_MODIVO = {"klatka_piersiowa": "klatka", "talia": "talia", "biodra": "biodra", "pas_cm_": "talia",
               "dlugosc_wkladki_wewnatrz_buta_cm": "wkladka", "max_dlugosc_stopy_kupujacego_cm": "stopa",
               "dlugosc_nogawki": "nogawka", "dl__wew__nogawki": "nogawka", "dlugosc_rekawa": "rekaw",
               "obwod_kolnierzyka_cm": "kolnierzyk", "wzrost_cm_": "wzrost", "szerokosc_pod_biustem": "pod_biustem", "udo_cm_": "udo"}
NAZWY_MODIVO = {"stopa": "Maks. długość stopy", "wkladka": "Długość wkładki", "klatka": "Klatka piersiowa", "talia": "Talia",
                "biodra": "Biodra", "nogawka": "Długość nogawki", "rekaw": "Długość rękawa", "kolnierzyk": "Obwód kołnierzyka",
                "wzrost": "Wzrost", "pod_biustem": "Obwód pod biustem", "udo": "Udo"}

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


def _bez_dubla(txt):
    """Strony z dwiema wersjami etykiety w jednej komórce („S S”, „XXL 2XL”: na telefon i na komputer) → jedna etykieta."""
    c = txt.split(" ")
    if len(c) == 2 and _rozmiar(c[0]) and _rozmiar(c[1]) and (c[0] == c[1] or not re.search(r"\d", c[0])):
        return c[0]
    return txt


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
                atr, txt = m.group(2), _bez_dubla(_czysc(m.group(3)))
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
            eu = len(w) > 1 and re.fullmatch(r"(ue|eu|eur|rozmiar eu|eu size)", w[1].strip().lower() or "x") \
                and all(len(w2) > 1 and _rozmiar(w2[1]) for w2 in wiersze)
            if len(wiersze) >= 2:
                wym = {}
                for j, k, naz in klucze:
                    wart = [_wartosc(w2[j]) if j < len(w2) else None for w2 in wiersze]
                    if k not in wym and sum(1 for x in wart if x) >= max(2, len(wiersze) - 1):
                        wym[k] = {"nazwa": naz, "wartosci": wart}
                if wym and (not najl or len(wym) > len(najl["wymiary"])):
                    najl = _scal({"rozmiary": [f"{w2[0]}/{w2[1]}" if eu else w2[0] for w2 in wiersze], "wymiary": wym, "inne": []})
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


def _z_kolumn(rozmiary, pomiary, aliasy=None, **dodatki):
    """pomiary: {klucz: (nazwa, [tekst dla każdego rozmiaru])} -> tabela w formacie aplikacji."""
    wym = {}
    for k, (naz, wart) in pomiary.items():
        w = [_wartosc(str(x)) if x not in (None, "", "-") else None for x in wart]
        if sum(1 for x in w if x) >= max(1, len(w) // 2):
            wym[k] = {"nazwa": naz, "wartosci": w}
    if not rozmiary or not wym:
        return None
    t = {"rozmiary": [str(r) for r in rozmiary], "wymiary": wym, "inne": [], "aliasy": aliasy or []}
    t.update(dodatki)
    return t


def _vrg(p):
    """Vistula, Wólczanka, Bytom: tabela produktu z okienka „TABELA ROZMIARÓW” (POST /product/sizeTable/{id} z tokenem CSRF)."""
    import subprocess, tempfile
    from .wspolne import UA
    baza = re.match(r"https?://[^/]+", p["url"]).group(0)
    with tempfile.NamedTemporaryFile(suffix=".txt") as ck:
        r = subprocess.run(["curl", "-sSL", "--compressed", "--max-time", "20", "-A", UA, "-c", ck.name, "-b", ck.name, p["url"]],
                           capture_output=True)
        t = r.stdout.decode("utf-8", "ignore")
        tok = re.search(r'name="csrf-token" content="([^"]+)"', t)
        idp = re.search(r'product-size-info"\s+data-id="(\d+)"', t)
        if not tok or not idp:
            return None
        r = subprocess.run(["curl", "-sS", "--compressed", "--max-time", "20", "-A", UA, "-c", ck.name, "-b", ck.name, "-X", "POST",
                            "-H", "X-CSRF-TOKEN: " + tok.group(1), "-H", "X-Requested-With: XMLHttpRequest", "-H", "Referer: " + p["url"],
                            f"{baza}/product/sizeTable/{idp.group(1)}"], capture_output=True)
    try:
        widok = json.loads(r.stdout.decode("utf-8", "ignore")).get("view") or ""
    except Exception:
        return None
    m = re.search(r"dataSizes\s*=\s*(\[.*?\]);", widok, re.S)
    if not m:
        return None
    try:
        dane = json.loads(m.group(1))
    except Exception:
        return None
    wiersze = []
    for x in dane:
        if isinstance(x, dict) and "result_size" in x:
            wiersze.append((None, x))
        elif isinstance(x, dict):
            for wzrost, lista in x.items():
                wiersze += [(wzrost, y) for y in lista if isinstance(y, dict)]
    if not wiersze:
        return None
    kl = "biust" if p.get("dzial") == "damskie" else "klatka"
    mapa = {"chest": (kl, "Klatka piersiowa" if kl == "klatka" else "Biust"), "waist": ("talia", "Talia"), "hips": ("biodra", "Biodra"),
            "neck": ("kolnierzyk", "Obwód szyi"), "collar": ("kolnierzyk", "Obwód kołnierzyka")}
    pom = {}
    for pole, (k, naz) in mapa.items():
        if any(pole in y for _, y in wiersze):
            pom[k] = (naz, [y.get(pole) for _, y in wiersze])
    if any(w for w, _ in wiersze):
        pom["wzrost"] = ("Wzrost", [w for w, _ in wiersze])
    alias = [{"nazwa": "", "rozmiary": [y.get("result_size_alternative") or "" for _, y in wiersze]}]
    t = _z_kolumn([y["result_size"] for _, y in wiersze], pom, alias, rodzaj="cialo")
    if t:
        t["dostepne"] = [y["result_size"] for _, y in wiersze if y.get("available")]
        pref = [r.split("/")[0] for r in t["rozmiary"]]
        if any(w for w, _ in wiersze) and all("/" in r for r in t["rozmiary"]) and 1 < len(set(pref)) < len(pref):
            t["grupy"] = {"nazwa": "Wzrost", "lista": list(dict.fromkeys(pref))}
    return t


def _ccc(p):
    from . import lacznik_ccc
    slug = p["url"].rstrip("/").rsplit("/", 1)[-1]
    ck = lacznik_ccc._ciasteczka()
    if not ck:
        return None
    gl = {"x-api-version": "5.0", "x-frontend-id": "44", "x-source-name": "WWW", "Accept": "application/json",
          "Cookie": "; ".join(f"{k}={v}" for k, v in ck.items())}
    kod, b = pobierz(f"https://ccc.eu/pl/api/Product/GetProduct?slug={slug}&language=pl_PL", gl)
    if kod != 200:
        return None
    try:
        d = json.loads(b.decode("utf-8", "ignore"))["data"]
    except Exception:
        return None
    rows = d.get("tableSize") or []
    rozm = next((r["values"] for r in rows if r.get("rowHeaderCode") == "sizes"), None)
    pom = {}
    for r in rows:
        k = _klucz(r.get("rowHeaderLabel", "")) if r.get("rowHeaderCode") != "sizes" else None
        if k and k not in pom:
            pom[k] = (r["rowHeaderLabel"], r.get("values") or [])
    t = _z_kolumn(rozm, pom, rodzaj="cialo")
    if t:
        t["dostepne"] = [s["size"] for s in d.get("itemSizes") or [] if (s.get("onlineStock") or 0) > 0]
    return t


def _bigstar(p):
    ref = p.get("rozm_ref") or {}
    if not ref.get("war"):
        return None
    from .wspolne import pobierz_json
    kod, d = pobierz_json(f"https://bigstar.pl/api/v2/product/sizedetails/{ref['war']}")
    if not isinstance(d, dict):
        return None
    mapa = ref.get("mapa") or {}
    war = [v for v in mapa if v in d]
    if not war:
        return None
    etyk = []
    for v in war:
        for x in (d[v].get("product_dimensions") or []):
            if x.get("label") and x["label"] not in etyk:
                etyk.append(x["label"])
    pom = {}
    for e in etyk:
        k = "udo" if re.search(r"\bud(a|o)\b", e.lower()) else (_klucz(e) or re.sub(r"\W+", "_", e.lower()))
        if k in pom:
            continue
        pom[k] = (e, [next((x.get("value") for x in d[v].get("product_dimensions") or [] if x.get("label") == e), None) for v in war])
    t = _z_kolumn([mapa[v] for v in war], pom, rodzaj="rzecz")
    if t:  # „W29 L32”: najpierw długość nogawki, potem obwód w pasie
        m = [re.fullmatch(r"(W\d+)\s*(L\d+)", r.strip()) for r in t["rozmiary"]]
        if all(m) and len({x.group(2) for x in m}) > 1:
            t["grupy"] = {"nazwa": "Długość", "lista": sorted({x.group(2) for x in m}, key=lambda z: int(z[1:])),
                          "klucze": [x.group(2) for x in m], "etykiety": [x.group(1) for x in m]}
    return t


def _drzewo_html(n):
    if isinstance(n, str):
        return _html.escape(n)
    if isinstance(n, list):
        return "".join(_drzewo_html(x) for x in n)
    if isinstance(n, dict):
        tag = n.get("tag")
        if not tag:
            return "".join(_drzewo_html(v) for v in n.values() if isinstance(v, (dict, list)))
        a = n.get("attr") or {}
        at = "".join(f' {k.lower()}="{v}"' for k, v in a.items() if k.lower() in ("colspan", "rowspan"))
        return f"<{tag}{at}>{_drzewo_html(n.get('children') or [])}</{tag}>"
    return ""


def _kappahl(p):
    kod, b = pobierz(p["url"], czas=20)
    if kod != 200:
        return None
    t = b.decode("utf-8", "ignore")
    i = t.find('"sizeGuide": {')
    if i < 0:
        return None
    try:
        o, _ = json.JSONDecoder().raw_decode(t[i + len('"sizeGuide": '):])
    except Exception:
        return None
    x = z_html(_drzewo_html(o))
    if x:
        x["rodzaj"] = "cialo"
        x["nazwa_tabeli"] = o.get("header")
    return x


def _modivo(p):
    """Modivo i eobuwie: tabela producenta (marki) z API produktu, a gdy jej nie ma, domyślna tabela kategorii sklepu."""
    kanal = "eobuwie" if "eobuwie" in p["url"] else "modivo"
    slug = p["url"].split("/p/", 1)[-1].split("?")[0].strip("/")
    from .wspolne import pobierz_json
    kod, d = pobierz_json(f"https://searchgcp.modivo.io/api/v5/products/{slug}?channel={kanal}&currency=PLN&locale=pl_PL&select_locales[]=pl_PL")
    if not isinstance(d, dict):
        return None
    v = d.get("values") or {}
    lista, nazwa, zrodlo = None, None, "produkt"
    tp = ((v.get("tabela_producent") or {}).get("value") or {})
    if tp.get("values", {}).get("tabela_rozmiarow"):
        lista, nazwa = tp["values"]["tabela_rozmiarow"], "tabela producenta: " + (tp.get("label") or "").split("–")[0].strip()
    else:
        for kat in ((v.get("kategorie_filtr_b") or {}).get("value") or {}).values():
            if isinstance(kat, dict) and (kat.get("values") or {}).get("wymiary"):
                lista = kat["values"]["wymiary"]
                pl = ((kat["values"].get("plec") or {}).get("label") or "").lower()
                nazwa = ((kat.get("label") or "rzeczy") + (" " + {"kobieta": "damska", "mężczyzna": "męska"}.get(pl, pl) if pl else "")).lower()
                break
        zrodlo = "sklep"
    if not lista:
        return None

    def etyk(w, pole):
        x = w.get(pole)
        return x.get("label") if isinstance(x, dict) else x
    wiersze = [x.get("values") or {} for x in lista]
    wiersze = [w for w in wiersze if etyk(w, "rozmiar") or etyk(w, "rozmiar_karta_produktu")]
    try:
        wiersze.sort(key=lambda w: float(str(etyk(w, "rozmiar") or etyk(w, "rozmiar_karta_produktu")).replace(",", ".").split("/")[0]))
    except Exception:
        pass
    rozm = [str(etyk(w, "rozmiar") or etyk(w, "rozmiar_karta_produktu")) for w in wiersze]
    pom = {}
    for pole, k in POLA_MODIVO.items():
        if k not in pom and any(w.get(pole) for w in wiersze):
            pom[k] = (NAZWY_MODIVO[k], [w.get(pole) for w in wiersze])
    alias = [{"nazwa": "INT", "rozmiary": [str(etyk(w, "rozmiar_filtr") or "") for w in wiersze]}] if any(etyk(w, "rozmiar_filtr") for w in wiersze) else []
    t = _z_kolumn(rozm, pom, alias, rodzaj="cialo")
    if t:
        t["nazwa_tabeli"], t["zrodlo"] = nazwa, zrodlo
    return t


def _showroom(p):
    """Showroom podaje tylko przelicznik rozmiarów (EU, IT, FR, UK, US), bez centymetrów."""
    kod, b = pobierz(p["url"], czas=20)
    if kod != 200:
        return None
    t = b.decode("utf-8", "ignore")
    i = t.find('"sizeGuide":{')
    if i < 0:
        return None
    try:
        o, _ = json.JSONDecoder().raw_decode(t[i + len('"sizeGuide":'):])
        tabele = o["body"]["tables"]
    except Exception:
        return None
    gr = grupa((p.get("klasa") or {}).get("r") or p.get("rodzaj"), p.get("nazwa", ""))
    slowo = {"dol": "spodn", "jeansy": "spodn", "buty": "but"}.get(gr, "top")
    tab = next((x for x in tabele if slowo in (x.get("groupName") or "").lower()), tabele[0] if tabele else None)
    kol = [c for c in (tab or {}).get("columns") or [] if c.get("sizes")]
    if len(kol) < 2:
        return None
    return {"rozmiary": [str(x) for x in kol[0]["sizes"]], "wymiary": {}, "inne": [], "rodzaj": "przelicznik",
            "aliasy": [{"nazwa": re.sub(r"\s*/\s*", " / ", (c.get("header") or "").strip()).split(" / ")[-1], "rozmiary": [str(x) for x in c["sizes"]]} for c in kol[1:] if "numer" not in (c.get("header") or "").lower()],
            "nazwa_tabeli": "przelicznik rozmiarów Showroom: " + (tab.get("groupName") or "").lower()}


ADAPTERY = {"Vistula": _vrg, "Wólczanka": _vrg, "Bytom": _vrg, "CCC": _ccc, "Big Star": _bigstar, "Kappahl": _kappahl,
            "Modivo": _modivo, "eobuwie": _modivo, "Showroom": _showroom}


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
    if p.get("sklep") in ADAPTERY and p.get("url"):
        klucz = "rozmA|" + p["url"]
        z = pamiec_czytaj(klucz, 7 * 86400)
        if z is None:
            try:
                z = {"t": ADAPTERY[p["sklep"]](p)}
            except Exception:
                z = {"t": None}
            if z["t"]:
                pamiec_zapisz(klucz, z)
        if z.get("t"):
            t = z["t"]
            wyn.update({"tabela": t, "zrodlo": t.get("zrodlo") or "produkt", "zrodlo_url": p["url"], "nazwa_tabeli": t.get("nazwa_tabeli"),
                        "rodzaj_wymiarow": t.get("rodzaj")})
            return wyn
    if p.get("sklep") not in BEZ_STRONY_PRODUKTU and p.get("zrodlo") == "sklep" and p.get("url"):
        klucz = "rozm2|" + p["url"]  # tabela pamiętana 7 dni, jej brak tylko dobę (sklep mógł zmienić stronę)
        z = pamiec_czytaj(klucz, 7 * 86400) or pamiec_czytaj("rozm2n|" + p["url"], 86400)
        if z is None:
            kod, b = pobierz(p["url"], czas=20)
            z = {"t": z_html(b.decode("utf-8", "ignore")) if kod == 200 else None}
            if kod == 200:
                pamiec_zapisz(klucz if z["t"] else "rozm2n|" + p["url"], z)
        if z and z.get("t"):
            wyn.update({"tabela": z["t"], "zrodlo": "produkt", "zrodlo_url": p["url"]})
            return wyn
    t = tabela_sklepu(p.get("sklep"), p.get("dzial"), gr, p.get("rozmiary"))
    if t:
        wyn.update({"tabela": {"rozmiary": t["rozmiary"], "wymiary": t["wymiary"], "inne": t.get("inne", [])},
                    "zrodlo": "sklep", "zrodlo_url": t.get("zrodlo_url"), "sprawdzono": t.get("sprawdzono"), "nazwa_tabeli": t.get("nazwa")})
    return wyn
