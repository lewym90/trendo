"""Klasyfikator produktów (płatne Gemini). Ocenia ZDJĘCIE i nazwę produktu ze sklepu:
rodzaj rzeczy, dla kogo, elegancję, wzór (gładki, małe logo, duży nadruk...) i okazje. Niczego nie dopisuje do oferty.
Ocena jest tylko jednym głosem: ostateczną decyzję podejmuje nadzor.py.
Każdy produkt oceniamy raz i zapisujemy na stałe (tabela klasy2).
Klucz: /root/.trendo-gemini (albo zmienna GEMINI_KEY). Budżet miesięczny: GEMINI_BUDZET_MIESIECZNY (USD, domyślnie 12, czyli trochę poniżej limitu 50 zł ustawionego w Google)."""
import base64, json, os, re, time
from concurrent.futures import ThreadPoolExecutor
from .wspolne import DB, _baza_blokada, licznik, pobierz, pobierz_json

RODZAJE = ["koszula", "bluzka", "t-shirt", "polo", "top", "sweter", "kardigan", "bluza", "marynarka", "kamizelka", "kurtka", "płaszcz",
           "sukienka", "spódnica", "spodnie", "jeansy", "szorty", "legginsy", "kombinezon", "garnitur", "dres",
           "buty", "botki", "kozaki", "sneakersy", "półbuty", "szpilki", "czółenka", "mokasyny", "baleriny", "sandały", "klapki", "kapcie",
           "torebka", "plecak", "portfel", "pasek", "biżuteria", "zegarek", "okulary", "czapka", "kapelusz", "szal", "rękawiczki",
           "krawat", "bielizna", "piżama", "strój kąpielowy", "skarpety", "rajstopy", "kosmetyk", "dom", "inne"]
OKAZJE = ["codzien", "praca", "randka", "wieczor", "wesele", "sylwester", "wyjazd", "sport", "plaza", "dom"]
PLEC = ["damskie", "meskie", "unisex", "dzieciece"]
WZORY = ["gladki", "male_logo", "duze_logo_lub_nadruk", "wzor_stonowany", "wzor_wyrazisty", "motyw_tematyczny"]
BUTY = {"botki", "kozaki", "sneakersy", "półbuty", "szpilki", "czółenka", "mokasyny", "baleriny", "sandały", "klapki", "kapcie"}

DOMYSLNE_MODELE = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash-lite"]
KANDYDACI_TESTU = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash-lite"]
# Cena USD za milion tokenów (wejście, wyjście). Nieznany model liczymy drożej, żeby budżet był bezpieczny.
CENY = [("3.8-flash", 0.75, 3.75), ("3.7-flash", 0.75, 3.75), ("3.5-flash-lite", 0.30, 2.50), ("flash-lite-latest", 0.30, 2.50),
        ("3.1-flash-lite", 0.25, 1.50), ("2.5-flash-lite", 0.10, 0.40), ("2.5-flash", 0.30, 2.50)]
BUDZET = float(os.environ.get("GEMINI_BUDZET_MIESIECZNY", "12"))
PACZKA = 10
OCENA_WERSJA = 2  # zmiana zasad = ponowna ocena produktów

ZASADY = """Jesteś doświadczoną, surową stylistką. Oceniasz produkty ze sklepów odzieżowych na podstawie ZDJĘCIA i nazwy.
Zdjęcie jest ważniejsze niż nazwa, bo sklepy nadają mylące nazwy. Oceniasz WYŁĄCZNIE produkt z nazwy, a nie resztę
stylizacji modela (przy spodniach nie oceniaj koszuli modela). Marka nie podnosi ani nie obniża oceny.

Dla każdego produktu zwróć:
r = rodzaj rzeczy (jedna wartość z listy).
p = dla kogo: damskie / meskie / unisex / dzieciece (po zdjęciu, kroju i nazwie). Gdy zdjęcie pokazuje sam produkt bez osoby
    (np. buty sportowe, kurtka, sweter) i z wyglądu nie da się rozstrzygnąć, wybierz unisex. Nie zgaduj płci po kolorze.
f = elegancja 1-5: 1 = sport, dres, plaża, dom, zabawne nadruki; 2 = luźna codzienność (t-shirty, bluzy, jeansy, sneakersy);
    3 = smart casual (gładkie bluzki i koszule, golfy i topy z cienkiej dzianiny, chinosy, swetry, skórzane botki);
    4 = elegancko (satyna, jedwab, koronka, koszule wizytowe, marynarki, spodnie w kant, szpilki); 5 = wizytowo, gala.
wzor = jak wygląda powierzchnia rzeczy:
  gladki: jeden kolor, ewentualnie faktura, splot, prążek, jodełka, drobna pepitka;
  male_logo: rzecz gładka z MAŁYM logo lub haftem marki (np. na piersi, kołnierzu, mankiecie, kilka centymetrów;
    EA7, Calvin Klein, Lacoste, Ralph Lauren, BOSS, Tommy Hilfiger). MAŁE LOGO NIE OBNIŻA ELEGANCJI I NIE WYKLUCZA
    ŻADNEJ OKAZJI. Oceniaj taką rzecz dokładnie tak, jakby logo nie było;
  duze_logo_lub_nadruk: duże logo lub napis (np. przez pół klatki), grafika, nadruk, naszywki, aplikacje;
  wzor_stonowany: klasyczne wzory: paski, krata garniturowa, kropki, drobne kwiaty, stonowany paisley;
  wzor_wyrazisty: duże, kolorowe lub krzykliwe wzory: zwierzęce, moro, duże kwiaty, kolorowa krata, etniczne;
  motyw_tematyczny: postaci, bajki, marki niemodowe (np. Coca-Cola), motywy świąteczne, zwierzątka, żartobliwe napisy.
zgodne = true, gdy zdjęcie pokazuje rzecz z nazwy; false, gdy zdjęcie pokazuje wyraźnie co innego.
o = okazje, na które ta rzecz NAPRAWDĘ się nadaje według dobrej stylistki (może być pusta lista).
  Oceniasz rzecz jako ELEMENT stroju: zakładasz, że reszta stroju zostanie dobrana właściwie. Pytanie brzmi: czy ta rzecz
  może być częścią dobrego stroju na tę okazję? Przykłady: satynowa bluzka + elegancka spódnica = wesele, wieczor, sylwester;
  gładki dopasowany golf z cienkiej dzianiny + skórzane spodnie = wieczor, praca, randka; czarne skórzane kozaki + sukienka =
  wieczor, randka; koszula wizytowa + garnitur = wesele, wieczor, praca.
  codzien = na co dzień;
  praca = biuro, smart lub business casual: stonowanie i schludnie;
  randka = zadbanie i stylowo, smart casual dozwolony, ale nie sportowo ani niechlujnie;
  wieczor = kolacja w dobrej restauracji, teatr, drink w eleganckim lokalu: elegancko lub dopracowany smart casual.
    Mężczyźni: koszula z długim rękawem, marynarka, elegancki sweter lub golf z cienkiej dzianiny, spodnie materiałowe
    lub eleganckie ciemne, skórzane półbuty, mokasyny, sztyblety. Gładka polówka z dobrego materiału najwyżej jako smart casual.
    Kobiety: sukienka, elegancka bluzka (satyna, jedwab, koronka), spódnica, eleganckie spodnie, szpilki, czółenka, botki,
    mała elegancka torebka. Satynowe, jedwabne, koronkowe i szyfonowe bluzki oraz koszule nadają się na wieczor, wesele,
    sylwester i randkę. Gładkie dopasowane golfy i topy z cienkiej dzianiny: wieczor, praca, randka;
  wesele = gość na weselu: garnitur, marynarka, koszula z długim rękawem, eleganckie spodnie, skórzane buty wizytowe;
    sukienka, kombinezon, elegancka spódnica i bluzka, szpilki, czółenka, mała torebka. Kobiety NIE na biało;
  sylwester = impreza: elegancko i efektownie, cekiny, satyna, skóra, błysk, czerń;
  wyjazd, sport, plaza, dom.
Nigdy na wieczor, wesele, sylwester ani praca: bluzy (zwłaszcza z kapturem), dresy, legginsy, t-shirty z nadrukiem,
flanela i kolorowa krata, moro, rzeczy plażowe i hawajskie, sneakersy sportowe, biegowe i do koszykówki, kurtki puchowe,
parki, wiatrówki, plecaki, duże torby na zakupy, rzeczy z dziurami i przetarciami.
Na wesele nigdy: dżins, len, t-shirty, polówki, swetry codzienne, sneakersy, krótki rękaw w koszulach męskich."""

SCHEMAT_PROD = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "i": {"type": "INTEGER"}, "r": {"type": "STRING", "enum": RODZAJE}, "p": {"type": "STRING", "enum": PLEC},
    "f": {"type": "INTEGER"}, "wzor": {"type": "STRING", "enum": WZORY}, "zgodne": {"type": "BOOLEAN"},
    "o": {"type": "ARRAY", "items": {"type": "STRING", "enum": OKAZJE}}},
    "required": ["i", "r", "p", "f", "wzor", "zgodne", "o"]}}
SCHEMAT_HASLO = {"type": "OBJECT", "properties": {"r": {"type": "STRING", "enum": RODZAJE}}, "required": ["r"]}


def _klucz():
    k = os.environ.get("GEMINI_KEY")
    if k:
        return k.strip()
    for p in ("/root/.trendo-gemini", os.path.expanduser("~/.trendo-gemini")):
        try:
            return open(p).read().strip()
        except OSError:
            pass
    return None


def dostepny():
    return bool(_klucz())


with _baza_blokada:
    DB.execute("CREATE TABLE IF NOT EXISTS klasy2 (pid TEXT PRIMARY KEY, dane TEXT, model TEXT, czas INTEGER)")
    DB.execute("CREATE TABLE IF NOT EXISTS ustawienia (klucz TEXT PRIMARY KEY, wartosc TEXT)")
    DB.commit()


def ustawienie(k, v=None):
    with _baza_blokada:
        if v is not None:
            DB.execute("INSERT OR REPLACE INTO ustawienia VALUES (?,?)", (k, v)); DB.commit()
            return v
        r = DB.execute("SELECT wartosc FROM ustawienia WHERE klucz=?", (k,)).fetchone()
    return r[0] if r else None


def modele():
    wyb = ustawienie("model_ai")
    return ([wyb] if wyb else []) + [m for m in DOMYSLNE_MODELE if m != wyb]


def _cena(model):
    for k, a, b in CENY:
        if k in model:
            return a, b
    return 1.0, 6.0


def koszt_dzis():
    return licznik(time.strftime("ai-koszt-%Y-%m-%d")) / 1e6


def koszt_miesiac():
    return licznik(time.strftime("ai-koszt-m-%Y-%m")) / 1e6


def _dolicz(model, uz):
    a, b = _cena(model)
    wej = uz.get("promptTokenCount", 0)
    wyj = uz.get("candidatesTokenCount", 0) + uz.get("thoughtsTokenCount", 0)
    usd = wej * a / 1e6 + wyj * b / 1e6
    licznik(time.strftime("ai-koszt-%Y-%m-%d"), int(usd * 1e6) + 1)
    licznik(time.strftime("ai-koszt-m-%Y-%m"), int(usd * 1e6) + 1)
    return usd


def _konfiguracje(model):
    baza = {"temperature": 0, "responseMimeType": "application/json"}
    m = dict(baza, mediaResolution="MEDIA_RESOLUTION_MEDIUM")
    if model.startswith("gemini-2.5"):
        return [dict(m, thinkingConfig={"thinkingBudget": 0}), baza]
    return [dict(m, thinkingConfig={"thinkingLevel": "low"}), m, baza]


_martwe = set()


def _wywolaj(model, czesci, schemat, budzet=True):
    """Zwraca (kod, odpowiedź JSON albo None)."""
    k = _klucz()
    if not k:
        return 0, None
    if budzet and koszt_miesiac() >= BUDZET:
        return 402, None
    for cfg in _konfiguracje(model):
        cfg = dict(cfg, responseSchema=schemat)
        cialo = json.dumps({"contents": [{"role": "user", "parts": czesci}], "generationConfig": cfg})
        for proba in range(3):
            kod, d = pobierz_json(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                  naglowki={"Content-Type": "application/json", "x-goog-api-key": k}, czas=90, dane=cialo)
            if kod in (429, 500, 503) and proba < 2:
                time.sleep(3 * (proba + 1)); continue
            break
        if kod == 404:
            _martwe.add(model)
            return 404, None
        if kod == 400:
            continue  # model nie zna któregoś ustawienia, próbujemy prostszej konfiguracji
        if not d:
            return kod, None
        _dolicz(model, d.get("usageMetadata") or {})
        try:
            return 200, json.loads(d["candidates"][0]["content"]["parts"][0]["text"])
        except Exception:
            return 200, None
    return 400, None


def miniatura(url):
    if not url:
        return None
    for u in dict.fromkeys([re.sub(r"([?&])w=\d+", r"\1w=400", url), url, url.split("?")[0]]):
        kod, b = pobierz(u, czas=15, limit=4_000_000)
        if kod == 200 and b and len(b) >= 800 and (b[:4] == b"\x89PNG" or b[8:12] == b"WEBP" or b[:3] == b"\xff\xd8\xff"):
            break
    else:
        return None
    if b[:4] == b"\x89PNG":
        typ = "image/png"
    elif b[8:12] == b"WEBP":
        typ = "image/webp"
    elif b[:3] == b"\xff\xd8\xff":
        typ = "image/jpeg"
    else:
        return None  # np. AVIF albo strona błędu: oceniamy wtedy bez zdjęcia
    return {"inline_data": {"mime_type": typ, "data": base64.b64encode(b).decode()}}


_POBIERANIE = ThreadPoolExecutor(max_workers=12)


def _partia(lista, model):
    obrazy = list(_POBIERANIE.map(lambda p: miniatura(p.get("zdjecie")), lista))
    czesci = [{"text": f"{ZASADY}\n\nRodzaje: {', '.join(RODZAJE)}\n\nOceń {len(lista)} produktów (numery 0-{len(lista) - 1}). "
                       "Zwróć listę z oceną dla każdego numeru."}]
    for i, (p, obr) in enumerate(zip(lista, obrazy)):
        czesci.append({"text": f"Produkt {i}: {p['nazwa'][:160]} | sklep: {p['sklep']} | opis: {(p.get('material') or '')[:80]}"
                               f"{'' if obr else ' | BRAK ZDJĘCIA, oceń ostrożnie po nazwie'}"})
        if obr:
            czesci.append(obr)
    kod, wyn = _wywolaj(model, czesci, SCHEMAT_PROD)
    if kod != 200 or not isinstance(wyn, list):
        return kod, {}
    out = {}
    for x in wyn:
        try:
            i = int(x["i"])
            if 0 <= i < len(lista) and lista[i]["id"] not in out:
                out[lista[i]["id"]] = {"v": OCENA_WERSJA, "r": x["r"], "p": x["p"], "f": max(1, min(5, int(x["f"]))), "wzor": x.get("wzor", "gladki"),
                                       "zgodne": bool(x.get("zgodne", True)), "o": [o for o in (x.get("o") or []) if o in OKAZJE],
                                       "zdj": obrazy[i] is not None}
        except Exception:
            continue
    return 200, out


def klasyfikuj(produkty, maks=240, swiezo=False, model=None, zapisuj=True):
    """Uzupełnia p['klasa']. Najpierw z bazy, brakujące przez Gemini (paczkami równolegle).
    Zwraca liczbę ocenionych produktów."""
    znane = {}
    if not swiezo:
        ids = [p["id"] for p in produkty]
        with _baza_blokada:
            for i in range(0, len(ids), 500):
                cz = ids[i:i + 500]
                for pid_, dane in DB.execute(f"SELECT pid, dane FROM klasy2 WHERE pid IN ({','.join('?' * len(cz))})", cz):
                    d = json.loads(dane)
                    if d.get("v") == OCENA_WERSJA:
                        znane[pid_] = d
    brak, widziane = [], set()
    for p in produkty:
        if p["id"] not in znane and p["id"] not in widziane:
            widziane.add(p["id"]); brak.append(p)
    brak = brak[:maks]
    if brak and dostepny():
        kolejka = [model] if model else [m for m in modele() if m not in _martwe]
        # Podejścia: główny model paczkami po 10, ponownie po 4 (gdy paczka się nie udała), potem model zapasowy.
        proby = [(kolejka[0], PACZKA), (kolejka[0], 4)] + [(m, PACZKA) for m in kolejka[1:2]] if kolejka else []
        for m, wielkosc in proby:
            brak = [p for p in brak if p["id"] not in znane]
            if not brak:
                break
            partie = [brak[i:i + wielkosc] for i in range(0, len(brak), wielkosc)]
            with ThreadPoolExecutor(max_workers=8) as ex:
                wyniki = list(ex.map(lambda pa: _partia(pa, m), partie))
            for _, w in wyniki:
                if not w:
                    continue
                znane.update(w)
                if zapisuj:
                    with _baza_blokada:
                        DB.executemany("INSERT OR REPLACE INTO klasy2 VALUES (?,?,?,?)",
                                       [(pid_, json.dumps(v, ensure_ascii=False), m, int(time.time())) for pid_, v in w.items()])
                        DB.commit()
    for p in produkty:
        if p["id"] in znane:
            p["klasa"] = znane[p["id"]]
    return sum(1 for p in produkty if "klasa" in p)


_haslo_pamiec = {}


def rodzaj_hasla(q):
    q = q.lower().strip()
    if q in _haslo_pamiec:
        return _haslo_pamiec[q]
    zap = ustawienie("haslo|" + q)
    if zap:
        _haslo_pamiec[q] = zap
        return zap
    for m in [x for x in modele() if x not in _martwe]:
        kod, wyn = _wywolaj(m, [{"text": f"Jaki rodzaj rzeczy (jedna wartość z listy) opisuje hasło wyszukiwania w sklepie "
                                         f"odzieżowym: „{q}”?\nRodzaje: {', '.join(RODZAJE)}"}], SCHEMAT_HASLO)
        if kod == 404:
            continue
        r = (wyn or {}).get("r") if isinstance(wyn, dict) else None
        if r:
            _haslo_pamiec[q] = r
            ustawienie("haslo|" + q, r)
        return r
    return None


def zgodny_rodzaj(r_hasla, r_produktu):
    """Czy produkt jest tym rodzajem rzeczy, którego szukamy."""
    if not r_hasla or r_hasla == "inne" or r_hasla == r_produktu:
        return True
    pary = {("spodnie", "jeansy"), ("koszula", "bluzka"), ("bluzka", "koszula"), ("sweter", "kardigan"), ("t-shirt", "top"),
            ("top", "t-shirt"), ("t-shirt", "polo"), ("polo", "t-shirt"), ("szpilki", "czółenka"), ("czółenka", "szpilki"),
            ("marynarka", "garnitur"), ("garnitur", "marynarka"), ("kurtka", "płaszcz"), ("płaszcz", "kurtka"), ("bluzka", "top"),
            ("top", "bluzka"), ("sweter", "golf")}
    if (r_hasla, r_produktu) in pary:
        return True
    return r_hasla == "buty" and r_produktu in BUTY


def lista_modeli():
    k = _klucz()
    if not k:
        return []
    kod, d = pobierz_json("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", naglowki={"x-goog-api-key": k})
    return [m["name"].split("/", 1)[1] for m in (d or {}).get("models", []) if "generateContent" in (m.get("supportedGenerationMethods") or [])]


def stan():
    with _baza_blokada:
        ile = DB.execute("SELECT COUNT(*) FROM klasy2").fetchone()[0]
    return {"klucz": dostepny(), "model": modele()[0], "ocenione_produkty": ile,
            "koszt_dzis_usd": round(koszt_dzis(), 4), "koszt_miesiac_usd": round(koszt_miesiac(), 3), "budzet_miesieczny_usd": BUDZET,
            "kontrola": json.loads(ustawienie("kontrola_wynik") or "null")}
