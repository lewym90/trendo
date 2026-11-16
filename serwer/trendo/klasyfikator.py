"""Klasyfikator produktów (płatne Gemini). Ocenia ZDJĘCIE i nazwę produktu ze sklepu:
rodzaj rzeczy, dla kogo, elegancję, wzór (gładki, małe logo, duży nadruk...) i okazje. Niczego nie dopisuje do oferty.
Ocena jest tylko jednym głosem: ostateczną decyzję podejmuje nadzor.py.
Każdy produkt oceniamy raz i zapisujemy na stałe (tabela klasy2).
Klucz: /root/.trendo-gemini (albo zmienna GEMINI_KEY). Bez własnych limitów kosztów (decyzja użytkownika 15.11): granicą są środki wpłacone na konto klucza.
Koszt liczymy tylko do wglądu (/zdrowie)."""
import base64, json, os, re, time, unicodedata
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from .wspolne import DB, _baza_blokada, licznik, pobierz, pobierz_json

RODZAJE = ["koszula", "bluzka", "t-shirt", "polo", "top", "sweter", "kardigan", "bluza", "marynarka", "kamizelka", "kurtka", "płaszcz",
           "sukienka", "spódnica", "spodnie", "jeansy", "szorty", "legginsy", "kombinezon", "garnitur", "dres",
           "buty", "botki", "kozaki", "sneakersy", "półbuty", "szpilki", "czółenka", "mokasyny", "baleriny", "sandały", "klapki", "kapcie",
           "torebka", "plecak", "portfel", "pasek", "biżuteria", "zegarek", "okulary", "czapka", "kapelusz", "szal", "rękawiczki",
           "krawat", "bielizna", "piżama", "strój kąpielowy", "skarpety", "rajstopy", "kosmetyk", "dom", "inne"]
OKAZJE = ["codzien", "smartcasual", "praca", "randka", "wieczor", "wesele", "sylwester", "wyjazd", "sport", "plaza", "dom"]
PLEC = ["damskie", "meskie", "unisex", "dzieciece"]
WZORY = ["gladki", "male_logo", "duze_logo_lub_nadruk", "wzor_stonowany", "wzor_wyrazisty", "motyw_tematyczny"]
MATERIALY = ["bawelna", "len", "welna_kaszmir", "dzianina", "jedwab_satyna", "wiskoza_szyfon", "koronka", "aksamit_welur",
             "dzins", "flanela", "sztruks", "skora", "skora_ekologiczna", "zamsz", "powlekany_woskowany", "cekiny_brokat_metaliczny",
             "puch_pikowany", "techniczny_sportowy", "syntetyk", "inny"]
WZORY_RODZAJ = ["brak", "krata", "paski", "kropki", "kwiaty", "zwierzecy", "moro", "geometryczny", "etniczny_paisley",
                "jodelka_pepitka", "inny"]
NADRUKI = ["brak", "male_logo_haft", "duze_logo_przod", "nadruk_na_plecach", "napis_haslo", "grafika_postac", "naszywki_aplikacje"]
KOLORY = ["czarny", "bialy_ecru", "szary", "granatowy", "niebieski", "bezowy_brazowy", "zielony", "czerwony_bordo", "rozowy",
          "fioletowy", "zolty_pomaranczowy", "zloty_srebrny", "wielokolorowy"]
STYLE = ["sportowy", "plazowy_domowy", "casual", "smart_casual", "elegancki", "wieczorowy"]
BUTY = {"botki", "kozaki", "sneakersy", "półbuty", "szpilki", "czółenka", "mokasyny", "baleriny", "sandały", "klapki", "kapcie"}

DOMYSLNE_MODELE = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash-lite"]
KANDYDACI_TESTU = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash-lite"]
# Cena USD za milion tokenów (wejście, wyjście). Nieznany model liczymy drożej, żeby budżet był bezpieczny.
CENY = [("3.8-flash", 0.75, 3.75), ("3.7-flash", 0.75, 3.75), ("3.5-flash-lite", 0.30, 2.50), ("flash-lite-latest", 0.30, 2.50),
        ("3.1-flash-lite", 0.25, 1.50), ("2.5-flash-lite", 0.10, 0.40), ("2.5-flash", 0.30, 2.50)]
PACZKA = 10
OCENA_WERSJA = 4  # zmiana zasad = ponowna ocena produktów

ZASADY = """Jesteś doświadczoną, surową stylistką. Stosujesz zasady ubioru według Emily Post, Debrett's i polskiego protokołu
(Orłowski, PISM). Oceniasz produkty ze sklepów na podstawie ZDJĘCIA i nazwy. Zdjęcie jest ważniejsze niż nazwa, bo sklepy
nadają mylące nazwy. Oceniasz WYŁĄCZNIE produkt z nazwy, a nie resztę stylizacji modela. Marka nie podnosi ani nie obniża oceny.

Dla każdego produktu zwróć:
r = rodzaj rzeczy (jedna wartość z listy).
p = dla kogo: damskie / meskie / unisex / dzieciece (po zdjęciu, kroju i nazwie). Gdy zdjęcie pokazuje sam produkt bez osoby
    i z wyglądu nie da się rozstrzygnąć, wybierz unisex. Nie zgaduj płci po kolorze.
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
Cechy rzeczy (opisz to, co widzisz na zdjęciu ORAZ to, co mówi nazwa i opis sklepu; opis wygrywa, gdy mówi o czymś
niewidocznym na zdjęciu, np. o nadruku na plecach albo o materiale). Słowa mogą mieć dowolną formę: „kraciasta”, „w kratę”,
„w kratkę” to ta sama krata; „ze skóry”, „skórzana” to skóra; „gładka na plecach” znaczy BRAK nadruku.
material = główny materiał (z listy). Sztuczna skóra, ekoskóra, imitacja skóry = skora_ekologiczna.
wzor_rodzaj = rodzaj wzoru (z listy), brak = jednolity.
nadruk = brak / male_logo_haft (mały znaczek, haft, logo kilka cm) / duze_logo_przod / nadruk_na_plecach / napis_haslo /
  grafika_postac / naszywki_aplikacje. Mała litera, monogram albo logo marki wyhaftowane na piersi to male_logo_haft.
kolor = dominujący kolor (z listy). Biel, ecru, kremowy, złamana biel, śmietankowy = bialy_ecru.
styl = ogólny charakter rzeczy: sportowy / plazowy_domowy / casual / smart_casual / elegancki / wieczorowy.
o = okazje, na które ta rzecz NAPRAWDĘ się nadaje (może być pusta lista). Oceniasz rzecz jako ELEMENT stroju: zakładasz,
  że reszta stroju zostanie dobrana właściwie. Wypisz WSZYSTKIE okazje, na które rzecz pasuje, nie tylko najlepszą.
  codzien = na co dzień (casual).
  smartcasual = smart casual: elegancja połączona ze swobodą, luźniej niż biuro, dozwolone kolory i ciekawsze wzory.
    TAK: koszule (także casualowe i overshirt), polówki, swetry, golfy, marynarki, chinosy, spodnie materiałowe, ciemne
    dżinsy, bluzki, spódnice, sukienki dzienne, skórzane kurtki, płaszcze, mokasyny, sztyblety, botki, czyste
    minimalistyczne skórzane sneakersy. NIE: dresy, bluzy z kapturem, legginsy, koszulki z nadrukiem, buty sportowe
    (biegowe, do koszykówki, na siłownię), klapki, sportowe kurtki puchowe, rzeczy podarte, suknie wieczorowe i cekiny.
  praca = business casual w biurze: spodnie, chinosy lub spódnica z koszulą, bluzką, polo lub swetrem, sukienki, marynarki.
    NIE: sneakersy, głębokie dekolty, ramiączka-spaghetti, cekiny, rzeczy prześwitujące, nadruki.
  randka = smart casual lub dressy casual: zadbanie i styl, nie sportowo ani niechlujnie. Wszystko, co pasuje na
    wieczor albo do pracy, pasuje też na randkę.
  wieczor = kolacja w dobrej restauracji, teatr, drink w eleganckim lokalu (cocktail / semi-formal). Mężczyźni: ciemny
    garnitur lub marynarka, koszula z długim rękawem, elegancki sweter lub golf z cienkiej dzianiny, spodnie materiałowe,
    skórzane półbuty, mokasyny, sztyblety. Kobiety: sukienka koktajlowa, mała czarna, elegancka bluzka (satyna, jedwab,
    koronka), spódnica, eleganckie spodnie, szpilki, czółenka, botki, kozaki, mała elegancka torebka. Czerń jest kolorem
    wieczoru.
  wesele = gość weselny (strój wizytowy / cocktail): garnitur, marynarka, koszula z długim rękawem, eleganckie spodnie,
    skórzane buty wizytowe; sukienka (zwykle do kolana lub midi), kombinezon, elegancka spódnica z bluzką, szpilki,
    czółenka, mała torebka. Kobiety NIGDY na biało, ecru ani kremowo (to kolory panny młodej). Czerń jest dozwolona.
    NIE: dżins, t-shirty, polówki, swetry codzienne, sneakersy, skóra, duże torby, zbyt odważne lub balowe kreacje.
  sylwester = impreza (festive / cocktail z błyskiem): cekiny, satyna, aksamit, metaliczne tkaniny, skóra, czerń,
    eleganckie marynarki, koszule i spodnie.
  wyjazd, sport, plaza, dom.
Nigdy na wieczor, wesele, sylwester ani praca: bluzy (zwłaszcza z kapturem), dresy, legginsy, t-shirty z nadrukiem,
flanela i kolorowa krata, moro, rzeczy plażowe i hawajskie, sneakersy sportowe, biegowe i do koszykówki, kurtki puchowe,
parki, wiatrówki, plecaki, duże torby na zakupy, rzeczy z dziurami i przetarciami."""

SCHEMAT_PROD = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "i": {"type": "INTEGER"}, "r": {"type": "STRING", "enum": RODZAJE}, "p": {"type": "STRING", "enum": PLEC},
    "f": {"type": "INTEGER"}, "wzor": {"type": "STRING", "enum": WZORY}, "zgodne": {"type": "BOOLEAN"},
    "material": {"type": "STRING", "enum": MATERIALY}, "wzor_rodzaj": {"type": "STRING", "enum": WZORY_RODZAJ},
    "nadruk": {"type": "STRING", "enum": NADRUKI}, "kolor": {"type": "STRING", "enum": KOLORY}, "styl": {"type": "STRING", "enum": STYLE},
    "o": {"type": "ARRAY", "items": {"type": "STRING", "enum": OKAZJE}}},
    "required": ["i", "r", "p", "f", "wzor", "zgodne", "material", "wzor_rodzaj", "nadruk", "kolor", "styl", "o"]}}


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


def _wywolaj(model, czesci, schemat):
    """Zwraca (kod, odpowiedź JSON albo None)."""
    k = _klucz()
    if not k:
        return 0, None
    for cfg in _konfiguracje(model):
        cfg = dict(cfg, responseSchema=schemat)
        cialo = json.dumps({"contents": [{"role": "user", "parts": czesci}], "generationConfig": cfg})
        for proba in range(3):
            kod, b = pobierz(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                             {"Content-Type": "application/json", "Accept": "application/json", "x-goog-api-key": k}, czas=90, dane=cialo)
            try:
                d = json.loads(b.decode("utf-8", "ignore")) if b else None
            except Exception:
                d = None
            if kod != 200:
                blad, d = (d or {}).get("error") if isinstance(d, dict) else None, None
            if kod in (429, 500, 503) and proba < 2:
                time.sleep(4 * (proba + 1)); continue
            break
        if kod == 404:
            _martwe.add(model)
            return 404, None
        if kod in (403, 429):
            # treść od Google rozróżnia chwilowy limit na minutę od limitu wydatków albo braku środków
            ustawienie("ai_ostatni_blad", json.dumps({"kod": kod, "czas": int(time.time()), "model": model,
                                                     "status": (blad or {}).get("status"), "opis": ((blad or {}).get("message") or "")[:300]}))
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
                                       "zgodne": bool(x.get("zgodne", True)), "material": x.get("material", "inny"),
                                       "wzor_rodzaj": x.get("wzor_rodzaj", "brak"), "nadruk": x.get("nadruk", "brak"),
                                       "kolor": x.get("kolor", "wielokolorowy"), "styl": x.get("styl", "casual"),
                                       "bialy": x.get("kolor") == "bialy_ecru", "o": [o for o in (x.get("o") or []) if o in OKAZJE],
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


OKAZJE_HASLA = ["dowolna", "codzien", "smartcasual", "praca", "randka", "wieczor", "wesele", "sylwester", "wyjazd"]
SCHEMAT_HASLO = {"type": "OBJECT", "properties": {
    "r": {"type": "STRING", "enum": RODZAJE}, "kolor": {"type": "STRING", "enum": ["dowolny"] + KOLORY},
    "material": {"type": "STRING", "enum": ["dowolny"] + MATERIALY}, "wzor_rodzaj": {"type": "STRING", "enum": ["dowolny"] + WZORY_RODZAJ},
    "styl": {"type": "STRING", "enum": ["dowolny"] + STYLE}, "okazja": {"type": "STRING", "enum": OKAZJE_HASLA},
    "marka": {"type": "STRING"}, "marka_warianty": {"type": "ARRAY", "items": {"type": "STRING"}}, "model": {"type": "STRING"},
    "bez_marki": {"type": "STRING"},
    "wymagane": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "cecha": {"type": "STRING"}, "slowa": {"type": "ARRAY", "items": {"type": "STRING"}}}, "required": ["cecha", "slowa"]}}},
    "required": ["r", "kolor", "material", "wzor_rodzaj", "styl", "okazja", "marka", "marka_warianty", "model", "bez_marki", "wymagane"]}
_haslo_pamiec = {}
PYTANIE_HASLO = """Klientka lub klient wpisał w wyszukiwarkę sklepu odzieżowego: „{q}”. Ustal, czego dokładnie szuka.
r = rodzaj rzeczy (jedna wartość z listy).
kolor, material, wzor_rodzaj = cechy, o które hasło WPROST prosi; jeśli nie prosi, „dowolny”. Słowa mogą mieć dowolną formę:
  „kraciasta”, „w kratkę”, „w kratę” = krata; „ze skóry”, „skórzane” = skora; „ekoskóra”, „sztuczna skóra” = skora_ekologiczna;
  „czarna”, „czarne” = czarny.
styl = tylko gdy hasło wprost go podaje: „elegancka”, „wizytowa” = elegancki; „wieczorowa” = wieczorowy; „sportowa” = sportowy;
  „casualowa” = casual; „smart casual” = smart_casual. Inaczej „dowolny”.
okazja = tylko gdy hasło wprost ją podaje: „na wesele” = wesele, „do pracy”, „do biura” = praca, „na sylwestra” = sylwester,
  „na randkę” = randka, „na co dzień” = codzien. Inaczej „dowolna”.
marka = marka, jeśli hasło ją zawiera (np. „torebka guess” = Guess, „buty nike air max” = Nike, „koszula helikon” = Helikon-Tex),
  w poprawnej pisowni. Inaczej pusty napis. Nie zgaduj marki, której w haśle nie ma.
marka_warianty = inne zapisy tej marki spotykane w nazwach produktów w sklepach (np. Helikon-Tex: „Helikon”; Michael Kors:
  „MICHAEL Michael Kors”; Tommy Hilfiger: „Tommy Jeans”). Pusta lista, gdy nie ma marki.
model = nazwa modelu lub linii, jeśli hasło ją podaje (np. „Air Max 90”, „Jet Set”, „Speedy”). Inaczej pusty napis.
bez_marki = to samo hasło bez marki i modelu, w mianowniku, jako hasło do wyszukiwarki (np. „brązowa torebka michael kors jet set”
  = „brązowa torebka”). Gdy marka wyraźnie określa charakter rzeczy, zachowaj go słowem (np. „koszula texar” = „koszula
  taktyczna”, „kurtka the north face” = „kurtka outdoorowa”). Pusty napis, gdy w haśle nie ma marki.
wymagane = INNE cechy, o które hasło wprost prosi, a których nie opisują pola powyżej: przeznaczenie i charakter (taktyczna,
  wojskowa, trekkingowa, do biegania, ciążowa, narciarska, przeciwdeszczowa), krój i fason (oversize, slim, maxi, midi, mini,
  z wysokim stanem, szerokie nogawki, dwurzędowa, kopertowa), detale (z kapturem, na obcasie, na platformie, z frędzlami,
  na łańcuszku, z kieszeniami, bez rękawów, z golfem). NIE wpisuj płci, rodzaju rzeczy, koloru, materiału, wzoru, stylu, okazji,
  marki ani ogólników (modna, ładna, tania, nowa, damska). Zwykle lista jest pusta albo ma jedną cechę.
  cecha = krótko, tak jak w haśle (np. „taktyczna”).
  slowa = 3 do 10 rdzeni słów (małe litery, bez końcówek, po polsku i po angielsku), które w NAZWIE produktu w sklepie oznaczają
  tę cechę, np. taktyczna: taktyczn, tactical, militar, wojskow, bojow, combat; z kapturem: kaptur, hood; oversize: oversiz,
  luzn, loose; na obcasie: obcas, heel, szpil.
Rodzaje: {rodzaje}"""


def cechy_hasla(q, swiezo=False):
    """Co klientka/klient naprawdę wpisał(a): rodzaj rzeczy, cechy, marka, model, okazja i inne wymagane cechy (np. „taktyczna”),
    niezależnie od formy słów („kraciasta koszula” = „koszula w kratę”). Wynik pamiętany na stałe."""
    q = " ".join(q.lower().split())
    if q in _haslo_pamiec and not swiezo:
        return _haslo_pamiec[q]
    zap = None if swiezo else ustawienie("hasloV5|" + q)
    if zap:
        _haslo_pamiec[q] = json.loads(zap)
        return _haslo_pamiec[q]
    for m in [x for x in modele() if x not in _martwe]:
        kod, wyn = _wywolaj(m, [{"text": PYTANIE_HASLO.format(q=q, rodzaje=", ".join(RODZAJE))}], SCHEMAT_HASLO)
        if kod == 404:
            continue
        if isinstance(wyn, dict) and wyn.get("r"):
            wyn = _popraw_haslo(wyn, q)
            _haslo_pamiec[q] = wyn
            ustawienie("hasloV5|" + q, json.dumps(wyn, ensure_ascii=False))
            return wyn
        return None
    return None


def _popraw_haslo(c, q):
    """Porządek w odpowiedzi modelu: marka tylko taka, której ślad jest w haśle (nie zgadujemy), krótkie listy słów."""
    c = dict(c)
    hq = scisle(q)
    marka = (c.get("marka") or "").strip()
    warianty = [w.strip() for w in c.get("marka_warianty") or [] if w and w.strip()]
    model = (c.get("model") or "").strip()
    model_ok = bool(scisle(model)) and scisle(model) in hq  # „air max” wskazuje markę, choć jej nie wpisano
    slad = any(len(scisle(x)) >= 2 and scisle(x) in hq for x in [marka] + warianty) or \
        any(len(scisle(x)) >= 4 and scisle(x) in hq for x in marka.replace("-", " ").split())
    if marka and not (slad or model_ok):
        marka, warianty = "", []
    c["marka"], c["marka_warianty"] = marka, warianty[:6]
    c["model"] = model if marka and model_ok else ""
    c["bez_marki"] = " ".join((c.get("bez_marki") or "").split())[:80] if marka else ""
    wym = []
    for w in c.get("wymagane") or []:
        cecha = " ".join((w.get("cecha") or "").lower().split())[:40]
        slowa = list(dict.fromkeys(bez_ogonkow(s).strip() for s in w.get("slowa") or [] if len(bez_ogonkow(s).strip()) >= 3))[:12]
        if cecha:
            wym.append({"cecha": cecha, "slowa": slowa})
    c["wymagane"] = wym[:4]
    return c


def bez_ogonkow(s):
    s = unicodedata.normalize("NFKD", (s or "").lower().replace("ł", "l"))
    return " ".join("".join(ch for ch in s if not unicodedata.combining(ch)).split())


def scisle(s):
    """Do porównywania marek i modeli: bez wielkich liter, ogonków, spacji i znaków („Helikon-Tex” = „helikontex”)."""
    return re.sub(r"[^a-z0-9]", "", bez_ogonkow(s))


def _tekst_produktu(p):
    sciezka = re.sub(r"[-_/.+]", " ", urlparse(p.get("url") or "").path)
    return " ".join([p.get("nazwa") or "", p.get("material") or "", p.get("marka") or "", sciezka])


def _jest(wariant, tekst_sc, tekst_sl):
    v = scisle(wariant)
    if len(v) < 2:
        return False
    if len(v) >= 5:
        return v in tekst_sc
    return re.search(r"(?<![a-z0-9])" + re.escape(bez_ogonkow(wariant)) + r"(?![a-z0-9])", tekst_sl) is not None


def ma_marke(p, c):
    """Czy produkt jest marki, o którą prosi hasło (nazwa, opis, adres strony albo sam sklep, np. Zara w Zarze)."""
    if not c or not c.get("marka"):
        return None
    t = _tekst_produktu(p) + " " + (p.get("sklep") or "")
    sc, sl = scisle(t), bez_ogonkow(re.sub(r"[-_/.+]", " ", t))
    return any(_jest(w, sc, sl) for w in [c["marka"]] + list(c.get("marka_warianty") or []))


def ten_model(p, c):
    if not c or not c.get("model"):
        return False
    t = _tekst_produktu(p)
    return _jest(c["model"], scisle(t), bez_ogonkow(re.sub(r"[-_/.+]", " ", t)))


def pasuje_styl(c, k):
    """Styl lub okazja, o które hasło prosi wprost (np. „elegancka sukienka”), według oceny zdjęcia. None = brak danych."""
    if not c or not k:
        return None
    s = c.get("styl")
    if s and s != "dowolny":
        ks, f = k.get("styl"), k.get("f") or 0
        ok = {"elegancki": ks in ("elegancki", "wieczorowy") or f >= 4, "wieczorowy": ks == "wieczorowy" or "wieczor" in (k.get("o") or []),
              "smart_casual": ks in ("smart_casual", "elegancki") or "smartcasual" in (k.get("o") or []),
              "casual": ks in ("casual", "smart_casual", "sportowy"), "sportowy": ks == "sportowy" or "sport" in (k.get("o") or []),
              "plazowy_domowy": ks == "plazowy_domowy"}.get(s, True)
        if not ok:
            return False
    return True


with _baza_blokada:
    DB.execute("CREATE TABLE IF NOT EXISTS cechy_prod (klucz TEXT PRIMARY KEY, ok INTEGER)")
    DB.commit()
SCHEMAT_CECHY = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "i": {"type": "INTEGER"}, "ma": {"type": "ARRAY", "items": {"type": "INTEGER"}}}, "required": ["i", "ma"]}}


def _cechy_partia(lista, cechy, model):
    opis = "\n".join(f"{j}) {c}" for j, (c, _) in enumerate(cechy))
    czesci = [{"text": "Klientka lub klient szuka w sklepie odzieżowym rzeczy, która ma WSZYSTKIE te cechy:\n" + opis +
               "\n\nDla każdego produktu wypisz numery cech, które ten produkt ma. Cechę ma, gdy wynika to z nazwy, opisu, "
               "cech ze zdjęcia albo z Twojej pewnej wiedzy o marce i modelu (np. Helikon-Tex, Texar, M-Tac i Mil-Tec szyją "
               "odzież taktyczną). Gdy nic na to nie wskazuje, cechy nie ma: nie zgaduj. Zwróć wpis dla każdego numeru produktu."}]
    for i, p in enumerate(lista):
        k = p.get("klasa") or {}
        zdj = f" | ze zdjęcia: {k.get('kolor')}, {k.get('material')}, styl {k.get('styl')}, wzór {k.get('wzor_rodzaj')}" if k else ""
        czesci.append({"text": f"Produkt {i}: {p['nazwa'][:160]} | sklep: {p['sklep']} | opis: {(p.get('material') or '')[:80]}{zdj}"})
    kod, wyn = _wywolaj(model, czesci, SCHEMAT_CECHY)
    if kod != 200 or not isinstance(wyn, list):
        return None
    out = {i: set() for i in range(len(lista))}
    for x in wyn:
        try:
            i = int(x["i"])
            if i in out:
                out[i] |= {int(j) for j in x.get("ma") or [] if 0 <= int(j) < len(cechy)}
        except Exception:
            continue
    return out


def sprawdz_cechy(produkty, wymagane):
    """Wymagane cechy z hasła (np. „taktyczna”, „z kapturem”). Najpierw słowa w nazwie i opisie (bez kosztów), potem zapamiętane
    oceny, a resztę rozstrzyga model z samego tekstu (bez zdjęć, kilka groszy na wyszukiwanie; każda para cecha + produkt raz).
    Ustawia p['cechy_ok']: True (ma wszystkie), False (czegoś na pewno nie ma), None (nie udało się sprawdzić)."""
    cechy = [(w["cecha"], w.get("slowa") or []) for w in wymagane or [] if w.get("cecha")]
    if not cechy:
        return
    wynik, do_ai = {}, []
    klucze = {(p["id"], j): f"{bez_ogonkow(c)}|{p['id']}" for p in produkty for j, (c, _) in enumerate(cechy)}
    with _baza_blokada:
        zn = {}
        kl = list(set(klucze.values()))
        for i in range(0, len(kl), 500):
            cz = kl[i:i + 500]
            zn.update(dict(DB.execute(f"SELECT klucz, ok FROM cechy_prod WHERE klucz IN ({','.join('?' * len(cz))})", cz).fetchall()))
    for p in produkty:
        t = bez_ogonkow(re.sub(r"[-_/.+]", " ", _tekst_produktu(p)))
        brak = False
        for j, (c, slowa) in enumerate(cechy):
            if any(s in t for s in slowa) or bez_ogonkow(c) in t:
                wynik[(p["id"], j)] = True
            elif klucze[(p["id"], j)] in zn:
                wynik[(p["id"], j)] = bool(zn[klucze[(p["id"], j)]])
            else:
                brak = True
        if brak:
            do_ai.append(p)
    if do_ai and dostepny():
        m = next((x for x in modele() if x not in _martwe), None)
        partie = [do_ai[i:i + 40] for i in range(0, min(len(do_ai), 240), 40)]
        with ThreadPoolExecutor(max_workers=6) as ex:
            odp = list(ex.map(lambda pa: (pa, _cechy_partia(pa, cechy, m)), partie)) if m else []
        zapis = []
        for pa, w in odp:
            if w is None:
                continue
            for i, p in enumerate(pa):
                for j in range(len(cechy)):
                    if (p["id"], j) not in wynik:
                        wynik[(p["id"], j)] = j in w.get(i, set())
                        zapis.append((klucze[(p["id"], j)], int(wynik[(p["id"], j)])))
        if zapis:
            with _baza_blokada:
                DB.executemany("INSERT OR REPLACE INTO cechy_prod VALUES (?,?)", zapis)
                DB.commit()
    for p in produkty:
        v = [wynik.get((p["id"], j)) for j in range(len(cechy))]
        p["cechy_ok"] = False if False in v else None if None in v else True


def rodzaj_hasla(q):
    c = cechy_hasla(q)
    return c.get("r") if c else None


ZGODNE_MATERIALY = {"skora": {"skora", "skora_ekologiczna"}, "skora_ekologiczna": {"skora", "skora_ekologiczna"},
                    "jedwab_satyna": {"jedwab_satyna", "wiskoza_szyfon"}, "welna_kaszmir": {"welna_kaszmir", "dzianina"}}


def pasuje_do_hasla(c, k):
    """Czy cechy produktu (ocena zdjęcia) spełniają cechy, o które prosi hasło. None = brak danych."""
    if not c or not k:
        return None
    for pole in ("kolor", "material", "wzor_rodzaj"):
        chce = c.get(pole)
        if not chce or chce == "dowolny":
            continue
        ma = k.get(pole)
        if ma is None:
            return None
        if pole == "material":
            if ma not in ZGODNE_MATERIALY.get(chce, {chce}):
                return False
        elif ma != chce:
            return False
    return True


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
            "koszt_dzis_usd": round(koszt_dzis(), 4), "koszt_miesiac_usd": round(koszt_miesiac(), 3), "limit": "brak (granicą są środki na koncie klucza)",
            "ostatni_blad": json.loads(ustawienie("ai_ostatni_blad") or "null"),
            "kontrola": json.loads(ustawienie("kontrola_wynik") or "null")}


SCHEMAT_ZDJECIE = {"type": "OBJECT", "properties": {
    "rzeczy": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "q": {"type": "STRING"}, "r": {"type": "STRING", "enum": RODZAJE}, "marka": {"type": "STRING"}, "model": {"type": "STRING"},
        "znak": {"type": "STRING"}, "dzial": {"type": "STRING", "enum": ["damskie", "meskie", "nieznany"]}},
        "required": ["q", "r", "marka", "model", "znak", "dzial"]}}},
    "required": ["rzeczy"]}
PYTANIE_ZDJECIE = """Na zdjęciu (zrzut ekranu z internetu, kadr z filmu, zdjęcie z ulicy) są ubrania, buty albo dodatki, które ktoś chce kupić.
Wypisz WSZYSTKIE rzeczy do kupienia, które dobrze widać (najwyżej 6), od najbardziej widocznej. Pomiń rzeczy ledwo widoczne.{prosba}
Dla każdej rzeczy:
q = hasło do wyszukiwarki polskiego sklepu odzieżowego: 2 do 5 słów, po polsku, w mianowniku, tak jak wpisałby je człowiek,
  BEZ marki, np. „czarne skórzane spodnie”, „brązowa skórzana torebka na ramię”, „białe sneakersy na grubej podeszwie”.
  Podaj rodzaj rzeczy, kolor i najważniejszą cechę (materiał, krój albo wzór).
r = rodzaj rzeczy (jedna wartość z listy).
marka = marka TYLKO wtedy, gdy na tej rzeczy WYRAŹNIE widać jej logo, napis z nazwą albo jednoznaczny znak firmowy (monogram LV,
  GG Gucci, krata Burberry, logo Michael Kors, „swoosh” Nike, trzy paski i trójliść adidas, napis GUESS). Nigdy nie zgaduj marki
  z kształtu, koloru ani stylu rzeczy; gdy znak jest nieczytelny albo niepewny, wpisz pusty napis.
model = nazwa modelu lub linii, gdy jest wyraźnie widoczna albo pewna po znaku i charakterystycznym kształcie (np. „Jet Set”,
  „Air Force 1”, „Speedy”). Gdy nie masz pewności, pusty napis.
znak = co dokładnie widać, gdy podajesz markę (np. „logo MK na klapie”, „napis GUESS na pasku”); inaczej pusty napis.
dzial = damskie albo meskie, gdy rzecz jest wyraźnie dla jednej płci, inaczej nieznany.
Gdy na zdjęciu nie ma żadnej rzeczy do kupienia, zwróć pustą listę.
Rodzaje: {rodzaje}"""


def opis_zdjecia(b, typ="image/jpeg", szukam=""):
    """Zdjęcie (np. zrzut z Instagrama) -> lista rzeczy do wyszukania: hasło po polsku, rodzaj, marka i model tylko z widocznego znaku.
    szukam: opcjonalna podpowiedź („torebka”, „szukam tych butów”): ta rzecz trafia na pierwsze miejsce.
    Zwraca (kod, {"rzeczy": [...], "rzecz": bool, "q": str, "dzial": str}) albo (kod, None). rzecz/q/dzial: dla starszej aplikacji."""
    szukam = " ".join((szukam or "").split())[:80]
    prosba = (f"\nKlient napisał, czego szuka na tym zdjęciu: „{szukam}”. Tę rzecz podaj jako PIERWSZĄ (także gdy jest mała), "
              "a pozostałe po niej.") if szukam else ""
    czesci = [{"inline_data": {"mime_type": typ, "data": base64.b64encode(b).decode()}},
              {"text": PYTANIE_ZDJECIE.format(prosba=prosba, rodzaje=", ".join(RODZAJE))}]
    for m in [x for x in modele() if x not in _martwe]:
        kod, wyn = _wywolaj(m, czesci, SCHEMAT_ZDJECIE)
        if kod == 404:
            continue
        if not isinstance(wyn, dict):
            return kod, None
        rzeczy, widziane = [], set()
        for x in wyn.get("rzeczy") or []:
            q = " ".join((x.get("q") or "").split())[:60]
            if not q or q.lower() in widziane:
                continue
            widziane.add(q.lower())
            marka = " ".join((x.get("marka") or "").split())[:40]
            model = " ".join((x.get("model") or "").split())[:40] if marka else ""
            if marka and scisle(marka) in scisle(q):
                q = re.sub(re.escape(marka), "", q, flags=re.I).strip() or q
            rzeczy.append({"q": q, "r": x.get("r") or "inne", "marka": marka, "model": model,
                           "znak": " ".join((x.get("znak") or "").split())[:80] if marka else "",
                           "dzial": x.get("dzial") if x.get("dzial") in ("damskie", "meskie") else "nieznany",
                           "szukaj": " ".join([q, marka, model]).strip()})
        rzeczy = rzeczy[:6]
        g = rzeczy[0] if rzeczy else {}
        return 200, {"rzeczy": rzeczy, "rzecz": bool(rzeczy), "q": g.get("szukaj", ""), "dzial": g.get("dzial", "nieznany")}
    return 0, None
