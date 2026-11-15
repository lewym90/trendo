"""Klasyfikator produktów (Gemini). Ocenia WYŁĄCZNIE to, co podał sklep (nazwa, sklep, materiał, kategoria):
rodzaj rzeczy, dla kogo, poziom elegancji i okazje. Niczego nie dopisuje do oferty.
Oceny zapisujemy w bazie na stałe (produkt się nie zmienia), więc każdy produkt oceniamy raz.
Klucz: /root/.trendo-gemini (albo zmienna GEMINI_KEY)."""
import json, os, time
from concurrent.futures import ThreadPoolExecutor
from .wspolne import DB, _baza_blokada, pobierz_json, licznik

RODZAJE = ["koszula", "bluzka", "t-shirt", "top", "sweter", "kardigan", "bluza", "marynarka", "kamizelka", "kurtka", "płaszcz",
           "sukienka", "spódnica", "spodnie", "jeansy", "szorty", "legginsy", "kombinezon", "garnitur", "dres",
           "buty", "botki", "kozaki", "sneakersy", "półbuty", "szpilki", "czółenka", "mokasyny", "baleriny", "sandały", "klapki", "kapcie",
           "torebka", "plecak", "portfel", "pasek", "biżuteria", "zegarek", "okulary", "czapka", "kapelusz", "szal", "rękawiczki",
           "krawat", "bielizna", "piżama", "strój kąpielowy", "skarpety", "rajstopy", "kosmetyk", "dom", "inne"]
OKAZJE = ["codzien", "praca", "randka", "wieczor", "wesele", "sylwester", "wyjazd", "sport", "plaza", "dom"]
PLEC = ["damskie", "meskie", "unisex", "dzieciece"]
BUTY = {"botki", "kozaki", "sneakersy", "półbuty", "szpilki", "czółenka", "mokasyny", "baleriny", "sandały", "klapki", "kapcie"}
GRUPY = {"buty": BUTY, "spodnie": {"spodnie", "jeansy"}, "góra": {"koszula", "bluzka", "t-shirt", "top"},
         "sweter": {"sweter", "kardigan"}, "kurtka": {"kurtka", "płaszcz"}, "płaszcz": {"płaszcz", "kurtka"}}
MODELE = [m for m in os.environ.get("GEMINI_MODELE", "gemini-flash-lite-latest,gemini-2.5-flash-lite,gemini-flash-latest,gemini-2.5-flash").split(",") if m]
LIMIT_DZIENNY = int(os.environ.get("GEMINI_LIMIT_DZIENNY", "900"))

ZASADY = """Jesteś doświadczonym stylistą. Oceniasz produkty ze sklepów odzieżowych WYŁĄCZNIE na podstawie podanej nazwy,
sklepu i opisu. Nie zgaduj ponad to, co wynika z nazwy. Dla każdego produktu zwróć:
r = rodzaj rzeczy (jedna wartość z listy),
p = dla kogo: damskie / meskie / unisex / dzieciece (gdy nazwa nie mówi, oceń po fasonie i sklepie; „unisex” tylko gdy naprawdę pasuje obu płciom),
f = elegancja od 1 do 5 (1 = plaża, sport, dom, śmieszne nadruki; 2 = luźna codzienność; 3 = smart casual; 4 = elegancko; 5 = gala, smoking, suknia wieczorowa),
o = lista okazji, na które ta rzecz NAPRAWDĘ się nadaje według dobrego stylisty:
  codzien, praca (biuro, schludnie, bez krzykliwych nadruków), randka, wieczor (wyjście do restauracji, teatru, na drinka: elegancko lub smart, bez nadruków z logo i postaciami, bez motywów plażowych, sportowych, krzykliwych wzorów), wesele (strój wizytowy), sylwester (elegancko, błysk, cekiny), wyjazd, sport, plaza, dom.
Rzeczy z nadrukami marek (np. Coca-Cola), postaci, napisów, motywów plażowych (palmy, flamingi), hawajskie, dresowe, sportowe NIE nadają się na wieczor, wesele, praca ani sylwester.
Koszule z krótkim rękawem NIE nadają się na wesele."""


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


def _tabela():
    with _baza_blokada:
        DB.execute("CREATE TABLE IF NOT EXISTS klasy (pid TEXT PRIMARY KEY, dane TEXT, czas INTEGER)")
        DB.commit()


_tabela()
_model_ok = {"nazwa": None}


def _zapytaj(tresc, schemat):
    k = _klucz()
    if not k:
        return None
    dzien = time.strftime("gemini-%Y-%m-%d")
    if licznik(dzien) >= LIMIT_DZIENNY:
        return None
    modele = ([_model_ok["nazwa"]] if _model_ok["nazwa"] else []) + [m for m in MODELE if m != _model_ok["nazwa"]]
    for model in modele:
        for myslenie in (True, False):
            cfg = {"temperature": 0, "responseMimeType": "application/json", "responseSchema": schemat}
            if myslenie:
                cfg["thinkingConfig"] = {"thinkingBudget": 0}
            licznik(dzien, 1)
            kod, d = pobierz_json(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                  naglowki={"Content-Type": "application/json", "x-goog-api-key": k}, czas=45,
                                  dane=json.dumps({"contents": [{"role": "user", "parts": [{"text": tresc}]}],
                                                   "generationConfig": cfg}))
            if d and d.get("candidates"):
                try:
                    tekst = d["candidates"][0]["content"]["parts"][0]["text"]
                    _model_ok["nazwa"] = model
                    return json.loads(tekst)
                except Exception:
                    return None
            if kod == 404:
                break  # nie ma takiego modelu, następny
            if kod == 429:
                return None  # limit
    return None


SCHEMAT_PROD = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "i": {"type": "INTEGER"}, "r": {"type": "STRING", "enum": RODZAJE}, "p": {"type": "STRING", "enum": PLEC},
    "f": {"type": "INTEGER"}, "o": {"type": "ARRAY", "items": {"type": "STRING", "enum": OKAZJE}}},
    "required": ["i", "r", "p", "f", "o"]}}
SCHEMAT_HASLO = {"type": "OBJECT", "properties": {"r": {"type": "STRING", "enum": RODZAJE}}, "required": ["r"]}


def _partia(lista):
    linie = "\n".join(f"{i}|{p['sklep']}|{p['nazwa'][:140]}|{(p.get('material') or '')[:60]}" for i, p in enumerate(lista))
    wyn = _zapytaj(f"{ZASADY}\n\nRodzaje: {', '.join(RODZAJE)}\n\nProdukty (numer|sklep|nazwa|opis):\n{linie}", SCHEMAT_PROD)
    out = {}
    for x in wyn or []:
        try:
            i = int(x["i"])
            if 0 <= i < len(lista):
                out[lista[i]["id"]] = {"r": x["r"], "p": x["p"], "f": max(1, min(5, int(x["f"]))), "o": list(x.get("o") or [])}
        except Exception:
            continue
    return out


def klasyfikuj(produkty, maks=260):
    """Uzupełnia p['klasa'] = {r, p, f, o}. Najpierw z bazy, brakujące przez Gemini (partiami równolegle)."""
    ids = [p["id"] for p in produkty]
    znane = {}
    with _baza_blokada:
        for i in range(0, len(ids), 500):
            cz = ids[i:i + 500]
            for pid, dane in DB.execute(f"SELECT pid, dane FROM klasy WHERE pid IN ({','.join('?' * len(cz))})", cz):
                znane[pid] = json.loads(dane)
    brak = [p for p in produkty if p["id"] not in znane][:maks]
    if brak and dostepny():
        partie = [brak[i:i + 45] for i in range(0, len(brak), 45)]
        with ThreadPoolExecutor(max_workers=4) as ex:
            for wynik in ex.map(_partia, partie):
                if not wynik:
                    continue
                znane.update(wynik)
                with _baza_blokada:
                    DB.executemany("INSERT OR REPLACE INTO klasy VALUES (?,?,?)",
                                   [(pid, json.dumps(v, ensure_ascii=False), int(time.time())) for pid, v in wynik.items()])
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
    wyn = _zapytaj(f"Jaki rodzaj rzeczy (jedna wartość z listy) opisuje hasło wyszukiwania w sklepie odzieżowym: „{q}”?\n"
                   f"Rodzaje: {', '.join(RODZAJE)}", SCHEMAT_HASLO)
    r = (wyn or {}).get("r")
    if r:
        _haslo_pamiec[q] = r
    return r


def zgodny_rodzaj(r_hasla, r_produktu):
    """Czy produkt jest tym rodzajem rzeczy, którego szukamy."""
    if not r_hasla or r_hasla == "inne" or r_hasla == r_produktu:
        return True
    pary = {("spodnie", "jeansy"), ("koszula", "bluzka"), ("bluzka", "koszula"), ("sweter", "kardigan"),
            ("t-shirt", "top"), ("top", "t-shirt"), ("szpilki", "czółenka"), ("czółenka", "szpilki")}
    if (r_hasla, r_produktu) in pary:
        return True
    return r_hasla == "buty" and r_produktu in BUTY
