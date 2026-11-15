"""Silnik stylizacji (0.19.0, decyzje użytkownika 15.11.2026).

Do rzeczy wyjściowej (produkt albo opis „mam czarne skórzane spodnie”) i okazji dobiera resztę zestawu z prawdziwych
produktów ze sklepów podłączonych bezpośrednio (bez Google Shopping i Vinted: tam nie da się sprawdzić rozmiaru).
- Miejsca w zestawie (góra, dół, sukienka, okrycie, buty, dodatki) wynikają z kodeksu ubioru (kontrola/kodeks.md).
- Kandydat musi pasować na okazję według nadzoru (te same zasady co w wynikach), mieć właściwy rodzaj i rozmiar z Ustawień.
- Trzy zestawy o różnym charakterze: Klasycznie, Modnie (trendy z potwierdzonej listy), Odważnie (jeden mocny akcent).
- Dwa tryby: tylko sklep rzeczy wyjściowej i wszystkie sklepy.
- Zamiast jednej rzeczy na miejsce serwer zwraca uszeregowanych kandydatów: aplikacja podmienia rzecz na bieżąco suwakiem ceny.
- Znaczek trendu tylko wtedy, gdy cechy rzeczy (rodzaj, kolor, materiał, wzór ze zdjęcia) spełniają definicję trendu z listy
  potwierdzonej przez co najmniej dwa źródła (ta sama reguła co udziały trendów w sklepach). Opis stylisty pisze AI wyłącznie
  z podanych faktów; opis wspominający modę bez trendu z zestawu jest odrzucany i zastępowany opisem z reguł.
- AI ocenia tylko wybranych kandydatów (każdy produkt raz na zawsze); koszt liczony osobno (licznik styl-koszt)."""
import hashlib, json, math, re, time, traceback
from concurrent.futures import ThreadPoolExecutor

from . import klasyfikator as K, nadzor, trendy
from .wspolne import licznik, lista_rozmiarow, pamiec_czytaj, pamiec_zapisz

WIEK = 12 * 3600
WERSJA_DOBORU = 2  # zmiana zasad doboru = nowe stylizacje zamiast zapamiętanych
NA_MIEJSCE = 24        # ilu kandydatów z wszystkich sklepów oceniamy na jedno miejsce w zestawie
ZE_SKLEPU = 10         # i ilu dodatkowo ze sklepu rzeczy wyjściowej
W_RANKINGU = 16        # ilu kandydatów na miejsce wraca do aplikacji (dla suwaków)
POMIJANE_SKLEPY = {"Vinted", "Google Shopping"}

GORA = {"koszula", "bluzka", "t-shirt", "polo", "top", "sweter", "kardigan", "bluza"}
DOL = {"spodnie", "jeansy", "spódnica", "szorty"}
SUKIENKA = {"sukienka", "kombinezon"}
OKRYCIE = {"marynarka", "kurtka", "płaszcz", "kamizelka"}
BUTY = set(K.BUTY)
FORMALNE = {"wieczor", "wesele", "sylwester"}

NAZWY_OKAZJI = {"codzien": "na co dzień", "smartcasual": "smart casual", "praca": "do pracy", "randka": "na randkę",
                "wieczor": "na wieczór", "wesele": "na wesele", "sylwester": "na sylwestra", "wyjazd": "na wyjazd"}
# Poziom elegancji (f) według kodeksu ubioru.
ELEGANCJA = {"codzien": (1, 2), "smartcasual": (2, 3), "praca": (3, 3), "randka": (2, 4), "wieczor": (3, 4),
             "wesele": (4, 5), "sylwester": (3, 5), "wyjazd": (1, 2)}
NEUTRALNE = {"czarny", "bialy_ecru", "szary", "granatowy", "bezowy_brazowy"}
KOLOR_NAZWA = {"czarny": "czerń", "bialy_ecru": "biel", "szary": "szarość", "granatowy": "granat", "niebieski": "błękit",
               "bezowy_brazowy": "beż i brąz", "zielony": "zieleń", "czerwony_bordo": "czerwień", "rozowy": "róż",
               "fioletowy": "fiolet", "zolty_pomaranczowy": "żółć", "zloty_srebrny": "metaliczny połysk", "wielokolorowy": "wiele kolorów"}
SKORA = nadzor.SKORA



def miejsca(dzial, okazja, tryb, r_bazy):
    """Lista miejsc w zestawie. r_bazy: rodzaj rzeczy wyjściowej albo None."""
    d = dzial == "damskie"
    formalnie = okazja in FORMALNE
    dodatek = {"k": "dodatek", "rodzaje": {"torebka"} if d else {"pasek"}}
    if tryb == "dodatki":
        return [dodatek, {"k": "bizuteria", "rodzaje": {"biżuteria", "szal"} if d else {"zegarek", "szal", "krawat"}}]
    gora = {"k": "gora", "rodzaje": ({"koszula"} if formalnie and not d else {"bluzka", "koszula", "top"} if formalnie else
                                     {"koszula", "bluzka", "sweter", "kardigan", "polo"} if okazja in ("smartcasual", "praca", "randka") else GORA)}
    dol = {"k": "dol", "rodzaje": ({"spodnie"} if formalnie and not d else {"spodnie", "spódnica"} if formalnie else
                                   {"spodnie", "jeansy", "spódnica"} if okazja != "codzien" else DOL)}
    okrycie = {"k": "okrycie", "rodzaje": {"marynarka"} if (formalnie or okazja == "praca") and not d else
               {"marynarka", "płaszcz"} if formalnie else OKRYCIE}
    buty = {"k": "buty", "rodzaje": BUTY - {"klapki", "kapcie"}}
    sukienka = {"k": "sukienka", "rodzaje": SUKIENKA}
    krawat = {"k": "krawat", "rodzaje": {"krawat"}}
    if not d and okazja == "wesele":  # kodeks 15: garnitur, koszula, krawat lub mucha, skórzane buty
        lista = [gora, buty, krawat, dodatek] if r_bazy == "garnitur" else None
        if lista:
            return lista
    if r_bazy == "garnitur":
        return [gora, buty, dodatek]
    if d and r_bazy in SUKIENKA:
        return [okrycie, buty, dodatek]
    k_w = [krawat] if not d and okazja == "wesele" else []
    if r_bazy in GORA:
        return [dol, buty, okrycie] + k_w + [dodatek]
    if r_bazy in DOL:
        return [gora, buty, okrycie] + k_w + [dodatek]
    if r_bazy in OKRYCIE:
        return [sukienka, buty, dodatek] if d and formalnie else [gora, dol, buty, dodatek]
    lista = [sukienka, okrycie, buty, dodatek] if d and formalnie else [gora, dol, buty, okrycie, dodatek]
    if not d and okazja == "wesele":
        lista.insert(-1, krawat)
    if r_bazy in BUTY:
        lista = [m for m in lista if m["k"] != "buty"]
    elif r_bazy in {"torebka", "pasek"}:
        lista = [m for m in lista if m["k"] != "dodatek"]
    return lista


# Hasła wyszukiwania dla miejsca: (dział, miejsce) -> {grupa okazji: hasła}. Grupy: casual, smart, formal.
HASLA = {
    ("damskie", "gora"): {"casual": ["bluzka damska", "sweter damski"], "smart": ["koszula damska", "bluzka elegancka"],
                          "formal": ["bluzka elegancka", "top satynowy"]},
    ("damskie", "dol"): {"casual": ["jeansy damskie", "spodnie damskie"], "smart": ["spodnie damskie eleganckie", "spódnica midi"],
                         "formal": ["spodnie eleganckie damskie", "spódnica midi"]},
    ("damskie", "sukienka"): {"casual": ["sukienka"], "smart": ["sukienka midi"], "formal": ["sukienka wieczorowa", "sukienka na wesele"]},
    ("damskie", "okrycie"): {"casual": ["kurtka damska", "płaszcz damski"], "smart": ["marynarka damska", "płaszcz damski"],
                             "formal": ["marynarka damska", "płaszcz elegancki damski"]},
    ("damskie", "buty"): {"casual": ["sneakersy damskie", "botki"], "smart": ["mokasyny damskie", "botki"], "formal": ["szpilki", "czółenka"]},
    ("damskie", "dodatek"): {"casual": ["torebka damska"], "smart": ["torebka damska"], "formal": ["torebka wieczorowa"]},
    ("damskie", "bizuteria"): {"casual": ["biżuteria"], "smart": ["biżuteria"], "formal": ["biżuteria"]},
    ("meskie", "gora"): {"casual": ["koszula męska", "sweter męski"], "smart": ["koszula męska", "sweter męski"],
                         "formal": ["koszula męska elegancka"]},
    ("meskie", "dol"): {"casual": ["jeansy męskie", "spodnie chino"], "smart": ["spodnie chino", "spodnie męskie eleganckie"],
                        "formal": ["spodnie garniturowe"]},
    ("meskie", "okrycie"): {"casual": ["kurtka męska", "płaszcz męski"], "smart": ["marynarka męska", "płaszcz męski"],
                            "formal": ["marynarka męska"]},
    ("meskie", "buty"): {"casual": ["sneakersy męskie", "sztyblety"], "smart": ["sztyblety", "mokasyny męskie"],
                         "formal": ["półbuty eleganckie"]},
    ("meskie", "dodatek"): {"casual": ["pasek męski"], "smart": ["pasek męski skórzany"], "formal": ["pasek męski skórzany"]},
    ("meskie", "bizuteria"): {"casual": ["zegarek męski"], "smart": ["zegarek męski"], "formal": ["krawat"]},
    ("meskie", "krawat"): {"casual": ["krawat"], "smart": ["krawat"], "formal": ["krawat jedwabny", "krawat"]},
}


def _grupa_okazji(o):
    return "formal" if o in FORMALNE else "casual" if o in ("codzien", "wyjazd") else "smart"


NAZWY_MIEJSC = {"gora": "Góra", "dol": "Dół", "sukienka": "Sukienka", "okrycie": "Okrycie", "buty": "Buty", "dodatek": "Dodatek",
                "bizuteria": "Biżuteria", "krawat": "Krawat"}


# ---------- rozmiary ----------
LITERY = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "5XL"]
NUMERY_D = {32: "XXS", 34: "XS", 36: "S", 38: "M", 40: "L", 42: "XL", 44: "XXL", 46: "3XL", 48: "4XL"}
NUMERY_M = {44: "XS", 46: "S", 48: "M", 50: "L", 52: "XL", 54: "XXL", 56: "3XL", 58: "4XL", 60: "5XL"}
KOLNIERZYK = {37: "S", 38: "S", 39: "M", 40: "M", 41: "L", 42: "L", 43: "XL", 44: "XL", 45: "XXL", 46: "XXL"}


def _norm(x):
    x = str(x).upper().replace(" ", "").replace(",", ".")
    return {"2XL": "XXL", "XXXL": "3XL", "XXXXL": "4XL", "2XS": "XXS"}.get(x, x)


def klucze_rozmiaru(r, dzial):
    if r in BUTY:
        return ["buty"]
    if dzial == "damskie":
        if r in SUKIENKA or r == "spódnica":
            return ["sukienka"]
        if r in ("spodnie", "szorty"):
            return ["spodnie"]
        if r == "jeansy":
            return ["jeansy"]
        if r in OKRYCIE:
            return ["okrycie"]
        if r in GORA:
            return ["gora"]
        return []
    if r == "koszula":
        return ["gora", "kolnierzyk"]
    if r in ("spodnie", "szorty"):
        return ["spodnie", "jeansy"]
    if r == "jeansy":
        return ["jeansy"]
    if r in ("marynarka", "garnitur", "kamizelka"):
        return ["marynarka"]
    if r in GORA or r in ("kurtka", "płaszcz"):
        return ["gora"]
    return []


def _warianty(klucz, wart, dzial):
    """Rozmiar z Ustawień i jego odpowiedniki (litera i numer)."""
    v = _norm(wart)
    w = {v}
    tab = KOLNIERZYK if klucz == "kolnierzyk" else (NUMERY_D if dzial == "damskie" else NUMERY_M)
    if v.isdigit() and int(v) in tab:
        w.add(tab[int(v)])
    if v in LITERY:
        w |= {str(n) for n, l in tab.items() if l == v and klucz != "kolnierzyk"}
    return w


def _wzrost_pasuje(token, wzrost):
    m = re.fullmatch(r"(\d{3})(?:-(\d{3}))?", token)
    if not m or not wzrost:
        return True
    a, b = int(m.group(1)), int(m.group(2) or m.group(1))
    u = [int(x) for x in re.findall(r"\d{3}", wzrost)]
    if not u:
        return True
    ua, ub = u[0], u[-1]
    return not (b < ua or a > ub)


def rozmiar_ok(p, r, dzial, rozm):
    """True/False, gdy da się sprawdzić; None, gdy sklep nie podaje rozmiarów albo w Ustawieniach brak rozmiaru."""
    klucze = [k for k in klucze_rozmiaru(r, dzial) if rozm.get(k) or (k == "jeansy" and rozm.get("jeansyW"))]
    lista = lista_rozmiarow(p.get("rozmiary"))
    if not klucze or not lista:
        return None
    wzrost = rozm.get("wzrost")
    for etyk in lista:
        e = _norm(etyk)
        tok = [t for t in re.split(r"[/|]", e) if t]
        wys = [t for t in tok if re.fullmatch(r"\d{3}(?:-\d{3})?", t)]
        if wys and not all(_wzrost_pasuje(t, wzrost) for t in wys):
            continue
        reszta = [t for t in tok if t not in wys] or tok
        for k in klucze:
            if k == "jeansy":
                W, L = _norm(rozm.get("jeansyW") or "").lstrip("W"), _norm(rozm.get("jeansyL") or "").lstrip("L")
                liczby = re.findall(r"\d{2}", e)
                if len(liczby) >= 2 and not wys:
                    if liczby[0] == W and (not L or liczby[1] == L):
                        return True
                elif len(liczby) == 1 and liczby[0] == W:
                    return True
                continue
            war = _warianty(k, rozm[k], dzial)
            if e in war or any(t in war for t in reszta):
                return True
    return False


# ---------- ocena i dobór ----------
def _trendy_listy(dzial):
    try:
        z = pamiec_czytaj(f"trendy-styl|{dzial}", 3 * 3600)
        if not z:
            z = trendy.zestawienie(dzial)
            pamiec_zapisz(f"trendy-styl|{dzial}", z)
        wyn = []
        for t in z.get("trendy") or []:
            req = trendy.cechy_pomiaru(t)
            if req:
                wyn.append((t, req))
        return wyn
    except Exception:
        traceback.print_exc()
        return []


def trend_rzeczy(k, lista):
    for t, req in lista:
        if trendy._pasuje(k, req):
            return {"nazwa": t["nazwa"], "status": t["status"]}
    return None


def _wzorzysty(k):
    return (k.get("wzor_rodzaj") or "brak") not in ("brak", "inny") or k.get("wzor") in ("wzor_wyrazisty",)


def _akcent(k):
    return (k.get("kolor") not in NEUTRALNE and k.get("kolor") not in (None, "wielokolorowy")) or _wzorzysty(k)


def ocena(p, k, baza, okazja, miejsce, styl, trend):
    s = 0.0
    lo, hi = ELEGANCJA.get(okazja, (1, 5))
    f = k.get("f") or lo
    s -= 1.5 * max(0, lo - f, f - hi)
    kol, hk = k.get("kolor"), (baza or {}).get("kolor")
    neutr = kol in NEUTRALNE
    if hk and hk not in NEUTRALNE and not neutr and kol != hk and miejsce not in ("dodatek", "bizuteria"):
        s -= 2  # dwa różne mocne kolory
    if hk and kol == hk and not neutr and miejsce in ("gora", "dol", "okrycie", "sukienka"):
        s -= 0.6
    if (baza or {}).get("material") in SKORA and k.get("material") in SKORA and miejsce in ("gora", "dol", "okrycie", "sukienka"):
        s -= 1.0  # skóra do skóry przytłacza
    if _wzorzysty(baza or {}) and _wzorzysty(k):
        s -= 2.0  # dwa wzory naraz
    if k.get("wzor") in ("duze_logo_lub_nadruk", "motyw_tematyczny"):
        s -= 3.0
    if p.get("trafnosc") == 2:
        s += 0.3
    if styl == "klasycznie":
        s += (1.0 if neutr else 0) + (0.8 if not _wzorzysty(k) else 0) + (0.5 if k.get("styl") in ("elegancki", "smart_casual") else 0)
        s += 0.4 if trend else 0
    elif styl == "modnie":
        s += 3.0 if trend else 0
        s += 0.3 if neutr else 0
    else:
        s += 0.6 if trend else 0
        s += 0.5 if neutr else 0
    return s


def powod(k, baza, trend, okazja):
    if trend:
        return f"W trendzie: {trend['nazwa']}."
    mat, kol, hk = k.get("material"), k.get("kolor"), (baza or {}).get("kolor")
    if mat == "jedwab_satyna":
        return "Satyna dodaje lekkości i połysku."
    if mat == "zamsz":
        return "Zamsz ociepla zestaw i łagodzi formę."
    if mat == "welna_kaszmir":
        return "Wełna dodaje szlachetności i ciepła."
    if hk == "czarny" and kol == "bialy_ecru":
        return "Jasny kolor rozjaśnia czerń."
    if kol in NEUTRALNE and hk and hk not in NEUTRALNE:
        return f"Spokojny kolor nie konkuruje z rzeczą wyjściową."
    if kol and kol not in NEUTRALNE and hk in NEUTRALNE:
        return f"{KOLOR_NAZWA.get(kol, 'Kolor').capitalize()} ożywia stonowaną bazę."
    if kol and kol == hk:
        return f"{KOLOR_NAZWA.get(kol, 'Kolor').capitalize()} spina zestaw w jedną całość."
    return f"Pasuje {NAZWY_OKAZJI.get(okazja, '')} według zasad ubioru."


def _okrojony(p, k, trend, ok_rozm, pow_):
    return {"id": p["id"], "sklep": p["sklep"], "nazwa": p["nazwa"], "cena": p["cena"], "stara": p.get("stara"),
            "omnibus": p.get("omnibus"), "weryf": p.get("weryf"), "url": p["url"], "zdjecie": p.get("zdjecie"), "zrodlo": p.get("zrodlo"),
            "dzial": p.get("dzial"), "plec_sklepu": p.get("plec_sklepu"), "rozmiary": p.get("rozmiary"), "kolor": p.get("kolor"),
            "klasa": k, "trend": trend, "rozmiar_ok": ok_rozm, "powod": pow_}


SCHEMAT_OPIS = {"type": "OBJECT", "properties": {"opis": {"type": "STRING"}}, "required": ["opis"]}
MODA = re.compile(r"trend|modn|na czasie|sezon|hit|must[- ]have|w tym roku|tej jesieni|tej zimy|tego lata|tej wiosny", re.I)


def _opis_z_regul(baza_nazwa, baza, okazja, uzyte):
    t = f"Do rzeczy „{baza_nazwa}” dobraliśmy zestaw {NAZWY_OKAZJI.get(okazja, '')}"
    kol = (baza or {}).get("kolor")
    if kol in NEUTRALNE:
        t += ": spokojna baza pozwala na jeden mocniejszy akcent w zestawie „Odważnie”."
    elif kol:
        t += f": przy takim kolorze ({KOLOR_NAZWA.get(kol, kol)}) reszta jest stonowana, żeby nie konkurowała."
    else:
        t += "."
    if uzyte:
        t += " Zgodnie z aktualnymi trendami: " + ", ".join(x["nazwa"] for x in uzyte[:3]) + "."
    return t


def opis_stylisty(baza_nazwa, baza, okazja, zestaw, uzyte):
    fakty = {"rzecz_wyjsciowa": {"nazwa": baza_nazwa, "rodzaj": baza.get("r"), "kolor": baza.get("kolor"), "material": baza.get("material"),
                                 "wzor": baza.get("wzor_rodzaj"), "styl": baza.get("styl")},
             "okazja": NAZWY_OKAZJI.get(okazja), "dobrane": [{"miejsce": m, "nazwa": n, "kolor": c, "material": mt} for m, n, c, mt in zestaw],
             "trendy_wolno_wspomniec": [x["nazwa"] for x in uzyte]}
    tekst = ("Jesteś stylistką sklepu z modą. Napisz po polsku 2–3 krótkie zdania (najwyżej 60 słów) dla klientki albo klienta: "
             "czym i dlaczego zestawić rzecz wyjściową na tę okazję (rodzaje rzeczy, kolory, materiały, proporcje, poziom elegancji). "
             "Dobrane rzeczy są tylko przykładem kierunku: NIE opisuj konkretnych produktów, ich nazw ani pojedynczych kolorów, "
             "bo klient może je zmieniać; pisz o zasadach zestawienia. "
             "Korzystaj WYŁĄCZNIE z faktów poniżej. Nie podawaj cen, marek ani sklepów. O modzie, trendach i sezonie wolno pisać "
             "tylko używając nazw z listy trendy_wolno_wspomniec; jeśli lista jest pusta, nie wspominaj o modzie, trendach ani sezonie. "
             "Zwracaj się bezosobowo albo w 2. osobie, ciepło i konkretnie.\nFakty: " + json.dumps(fakty, ensure_ascii=False))
    for m in [x for x in K.modele() if x not in K._martwe][:2]:
        try:
            kod, wyn = K._wywolaj(m, [{"text": tekst}], SCHEMAT_OPIS)
        except Exception:
            traceback.print_exc()
            continue
        if kod == 404:
            continue
        op = " ".join(((wyn or {}).get("opis") or "").split())
        if not op:
            break
        # kontrola: każde zdanie o modzie musi wymieniać trend z zestawu
        nazwy = [x["nazwa"].lower() for x in uzyte]
        zle = [z for z in re.split(r"(?<=[.!?])\s+", op) if MODA.search(z) and not any(n.split()[0][:5] in z.lower() for n in nazwy)]
        if not zle:
            return op, "ai"
    return _opis_z_regul(baza_nazwa, baza, okazja, uzyte), "reguly"


def _rozmiary_klucz(rozm):
    return hashlib.md5(json.dumps(rozm, sort_keys=True).encode()).hexdigest()[:10]


def zloz(baza_p, baza_q, dzial, okazja, tryb, rozm, szukaj_fn, okazje_fn, wykluczone_fn):
    """baza_p: produkt wyjściowy (słownik z bazy) albo None; baza_q: opis rzeczy wyjściowej („mam czarne spodnie”) albo ''.
    szukaj_fn(q, dzial) -> lista produktów ze sklepów; okazje_fn(p, wyk) -> okazje produktu (nadzor)."""
    klucz = f"styl{WERSJA_DOBORU}|{(baza_p or {}).get('id') or baza_q.lower()}|{dzial}|{okazja}|{tryb}|{_rozmiary_klucz(rozm)}"
    zap = pamiec_czytaj(klucz, WIEK)
    if zap:
        return zap
    k0 = K.koszt_miesiac()
    t0 = time.time()
    # rzecz wyjściowa
    baza, baza_nazwa = {}, ""
    if baza_p:
        K.klasyfikuj([baza_p], maks=1)
        baza = baza_p.get("klasa") or {}
        baza_nazwa = baza_p["nazwa"]
    elif baza_q:
        c = K.cechy_hasla(baza_q) or {}
        baza = {kk: (v if v != "dowolny" else None) for kk, v in {"r": c.get("r"), "kolor": c.get("kolor"), "material": c.get("material"),
                                                                   "wzor_rodzaj": c.get("wzor_rodzaj")}.items()}
        baza_nazwa = re.sub(r"^(mam|posiadam)\s+", "", baza_q.strip(), flags=re.I)
    r_bazy = baza.get("r")
    lista_miejsc = miejsca(dzial, okazja, tryb, r_bazy)
    sklep_bazy = baza_p["sklep"] if baza_p and baza_p.get("zrodlo") == "sklep" and baza_p["sklep"] not in POMIJANE_SKLEPY else None
    # wyszukiwania (równolegle, pamiętane 12 h w szukaj_fn)
    hasla = {m["k"]: HASLA.get((dzial, m["k"]), {}).get(_grupa_okazji(okazja), []) for m in lista_miejsc}
    zadania = [(m, q) for m, qs in hasla.items() for q in qs]
    with ThreadPoolExecutor(3) as ex:
        wyniki = list(ex.map(lambda a: (a[0], szukaj_fn(a[1], dzial)), zadania))
    pule = {m["k"]: [] for m in lista_miejsc}
    widziane = {}
    for m, lista in wyniki:
        for p in lista or []:
            if p["id"] in widziane.get(m, set()) or (baza_p and p["id"] == baza_p["id"]):
                continue
            if p.get("sklep") in POMIJANE_SKLEPY or p.get("zrodlo") != "sklep" or p.get("uzywany") or not p.get("zdjecie") or not p.get("cena"):
                continue
            if not nadzor.zgodna_plec(p, dzial):
                continue
            widziane.setdefault(m, set()).add(p["id"])
            pule[m].append(p)
    # wybór kandydatów do oceny: po kolei z każdego sklepu (różnorodność), plus sklep rzeczy wyjściowej
    do_oceny = {}
    for m, lista in pule.items():
        lista.sort(key=lambda p: -(p.get("trafnosc") or 0))
        sklepy = {}
        for p in lista:
            sklepy.setdefault(p["sklep"], []).append(p)
        wyb, i = [], 0
        while len(wyb) < NA_MIEJSCE and any(i < len(v) for v in sklepy.values()):
            for v in sklepy.values():
                if i < len(v) and len(wyb) < NA_MIEJSCE:
                    wyb.append(v[i])
            i += 1
        if sklep_bazy:
            wyb += [p for p in sklepy.get(sklep_bazy, []) if p not in wyb][:ZE_SKLEPU]
        do_oceny[m] = wyb
    wszystkie = [p for v in do_oceny.values() for p in v]
    K.klasyfikuj(wszystkie, maks=None)
    wyk = wykluczone_fn()
    tr_lista = _trendy_listy(dzial)
    # filtr: rodzaj, płeć, okazja, rozmiar
    kandydaci, odrzucone_rozm = {}, {}
    for mj in lista_miejsc:
        m = mj["k"]
        ok = []
        for p in do_oceny.get(m, []):
            k = p.get("klasa")
            if not k or k.get("r") not in mj["rodzaje"] or k.get("p") == "dzieciece" or not nadzor.zgodna_plec(p, dzial):
                continue
            if k.get("zgodne") is False:
                continue
            o = okazje_fn(p, wyk) or []
            if okazja not in o:
                continue
            rz = rozmiar_ok(p, k.get("r"), dzial, rozm)
            if rz is False:
                odrzucone_rozm.setdefault(m, set()).add(p["sklep"])
                continue
            ok.append((p, k, rz))
        kandydaci[m] = ok
    produkty = {}
    uzyte_trendy = {}

    def rankingi(tylko_sklep):
        zestawy = []
        top_wczesniej = {m["k"]: set() for m in lista_miejsc}
        braki = {}
        for styl, nazwa in (("klasycznie", "Klasycznie"), ("modnie", "Modnie"), ("odwaznie", "Odważnie")):
            sloty = {}
            akcent_miejsce = None
            if styl == "odwaznie":
                for m in ("gora", "dodatek", "buty", "sukienka", "okrycie", "dol", "bizuteria"):
                    if any(_akcent(k) and (not tylko_sklep or p["sklep"] == tylko_sklep) for p, k, _ in kandydaci.get(m, [])):
                        akcent_miejsce = m
                        break
            for mj in lista_miejsc:
                m = mj["k"]
                lista = [(p, k, rz) for p, k, rz in kandydaci.get(m, []) if not tylko_sklep or p["sklep"] == tylko_sklep]
                if not lista:
                    if tylko_sklep:
                        braki[m] = "rozmiar" if tylko_sklep in odrzucone_rozm.get(m, set()) else "sklep"
                    else:
                        braki[m] = "rozmiar" if odrzucone_rozm.get(m) else "brak"
                    continue
                ceny = sorted(p["cena"] for p, _, _ in kandydaci.get(m, []))
                mediana = ceny[len(ceny) // 2] if ceny else 0
                oc = []
                for p, k, rz in lista:
                    tr = trend_rzeczy(k, tr_lista)
                    s = ocena(p, k, baza, okazja, m, styl if styl != "odwaznie" else ("odwaznie" if m == akcent_miejsce else "klasycznie"), tr)
                    if styl == "odwaznie" and m == akcent_miejsce:
                        s += 2.5 if _akcent(k) else 0
                    elif styl == "odwaznie" and _akcent(k):
                        s -= 1.5  # jeden akcent w zestawie
                    if p["id"] in top_wczesniej[m]:
                        s -= 1.5  # różne zestawy, nie trzy podobne
                    s += (1 if rz else 0) * 0.2
                    if mediana and p["cena"] > 1.5 * mediana:
                        s -= 0.8 * math.log2(p["cena"] / mediana)  # nie podsuwamy na start rzeczy kilka razy droższej niż typowa
                    oc.append((s, p, k, rz, tr))
                oc.sort(key=lambda x: -x[0])
                ranking = []
                for s, p, k, rz, tr in oc[:W_RANKINGU]:
                    if p["id"] not in produkty:
                        produkty[p["id"]] = _okrojony(p, k, tr, rz, powod(k, baza, tr, okazja))
                    ranking.append(p["id"])
                sloty[m] = ranking
                top_wczesniej[m].add(ranking[0])
                if oc[0][4]:
                    uzyte_trendy[oc[0][4]["nazwa"]] = oc[0][4]
            zestawy.append({"styl": styl, "nazwa": nazwa, "sloty": sloty})
        return {"zestawy": zestawy, "braki": braki}

    tryby = {"wszystkie": rankingi(None)}
    if sklep_bazy:
        tryby["sklep"] = dict(rankingi(sklep_bazy), sklep=sklep_bazy)
    # opis do zestawu „Klasycznie” ze wszystkich sklepów
    z1 = tryby["wszystkie"]["zestawy"][0]["sloty"]
    zestaw = [(NAZWY_MIEJSC[m], produkty[ids[0]]["nazwa"], (produkty[ids[0]]["klasa"] or {}).get("kolor"),
               (produkty[ids[0]]["klasa"] or {}).get("material")) for m, ids in z1.items() if ids]
    uzyte = list(uzyte_trendy.values())
    opis, opis_zrodlo = opis_stylisty(baza_nazwa, baza, okazja, zestaw, uzyte) if (baza or zestaw) else ("", "brak")
    for p in produkty.values():
        p.pop("klasa", None)
    wynik = {"dzial": dzial, "okazja": okazja, "tryb": tryb, "baza": ({"id": baza_p["id"], "nazwa": baza_p["nazwa"], "sklep": baza_p["sklep"],
                                                                      "cena": baza_p["cena"], "zdjecie": baza_p.get("zdjecie"), "url": baza_p.get("url")}
                                                                     if baza_p else ({"nazwa": baza_nazwa} if baza_nazwa else None)),
             "opis": opis, "opis_zrodlo": opis_zrodlo, "trendy": uzyte,
             "miejsca": [{"k": m["k"], "nazwa": NAZWY_MIEJSC[m["k"]]} for m in lista_miejsc],
             "produkty": produkty, "tryby": tryby, "sprawdzono": int(time.time()), "czas": round(time.time() - t0, 1)}
    koszt = max(0.0, K.koszt_miesiac() - k0)
    licznik(time.strftime("styl-n-%Y-%m"), 1)
    licznik(time.strftime("styl-koszt-%Y-%m"), int(koszt * 1e6))
    if produkty:
        pamiec_zapisz(klucz, wynik)
    return wynik


def stan():
    return {"w_miesiacu": licznik(time.strftime("styl-n-%Y-%m")), "koszt_usd": round(licznik(time.strftime("styl-koszt-%Y-%m")) / 1e6, 4)}
