"""Ocena produktów pod okazję przez Gemini: model ogląda zdjęcie i czyta nazwę, jak stylistka.
Klucz: /root/.trendo-gemini (albo zmienna GEMINI_KEY). Oceny zapamiętujemy na stałe (produkt + okazja)."""
import base64, json, os, re, time
from concurrent.futures import ThreadPoolExecutor
from .wspolne import DB, _baza_blokada, pobierz, pobierz_json

MODELE = [m for m in os.environ.get("GEMINI_MODELE", "gemini-flash-lite-latest,gemini-2.5-flash-lite,gemini-flash-latest,gemini-2.5-flash").split(",") if m]
PACZKA = 15

OPISY = {
    "wieczor": "eleganckie wieczorne wyjście: kolacja w dobrej restauracji, teatr, koncert, drink w eleganckim lokalu",
    "wesele": "wesele jako gość: strój wizytowy, elegancki, odpowiedni do garnituru albo eleganckiej sukienki",
    "sylwester": "sylwester, impreza wieczorowa: elegancko i efektownie, dozwolony błysk, cekiny, satyna",
    "randka": "randka: zadbany, stylowy i atrakcyjny wygląd, może być smart casual, ale nie sportowo ani niechlujnie",
    "praca": "praca w biurze: stonowany, profesjonalny styl smart / business casual",
}
ZASADY = """Bądź surowa jak doświadczona stylistka. NIE pasuje (pasuje=false), jeśli rzecz ma: nadruki, logo, napisy, grafiki,
motywy z marek, filmów czy bajek (np. Coca-Cola), wzory plażowe/hawajskie/palmy, krzykliwe lub zabawne wzory,
charakter sportowy, dresowy, plażowy, roboczy albo typowo luźny (flanela w kratę, bluzy, t-shirty z grafiką),
przetarcia, dziury, efekt zniszczenia, albo gdy po prostu nie wyglądałaby dobrze na tej okazji.
Pasuje (pasuje=true) tylko to, w czym rozsądna, dobrze ubrana osoba czułaby się właściwie na tej okazji.
ocena 0-10: jak dobrze rzecz pasuje do okazji i jak elegancko/stylowo wygląda (10 = idealnie)."""


def klucz():
    k = os.environ.get("GEMINI_KEY")
    if k:
        return k.strip()
    for p in ("/root/.trendo-gemini", os.path.expanduser("~/.trendo-gemini")):
        try:
            return open(p).read().strip()
        except OSError:
            pass
    return None


with _baza_blokada:
    DB.execute("CREATE TABLE IF NOT EXISTS ocena (pid TEXT, okazja TEXT, pasuje INTEGER, ocena INTEGER, czas INTEGER, PRIMARY KEY (pid, okazja))")
    DB.commit()


def _z_pamieci(pids, okazja):
    if not pids:
        return {}
    with _baza_blokada:
        r = DB.execute(f"SELECT pid, pasuje, ocena FROM ocena WHERE okazja=? AND pid IN ({','.join('?' * len(pids))})",
                       [okazja, *pids]).fetchall()
    return {a: (bool(b), c) for a, b, c in r}


def _zapisz(wyniki, okazja):
    t = int(time.time())
    with _baza_blokada:
        DB.executemany("INSERT OR REPLACE INTO ocena VALUES (?,?,?,?,?)", [(p, okazja, int(a), int(b), t) for p, (a, b) in wyniki.items()])
        DB.commit()


def _miniatura(url):
    if not url:
        return None
    u = url.replace("w=750", "w=400").replace("&w=750", "&w=400")
    kod, b = pobierz(u, czas=15, limit=3_000_000)
    if kod != 200 or len(b) < 800:
        return None
    typ = "image/png" if b[:4] == b"\x89PNG" else "image/webp" if b[8:12] == b"WEBP" else "image/jpeg"
    return {"inline_data": {"mime_type": typ, "data": base64.b64encode(b).decode()}}


def _paczka(produkty, okazja, dzial, q, k):
    obrazy = list(ThreadPoolExecutor(max_workers=8).map(lambda p: _miniatura(p.get("zdjecie")), produkty))
    czesci = [{"text": f"Okazja: {OPISY[okazja]}. Dział: {'odzież damska' if dzial == 'damskie' else 'odzież męska'}. "
                       f"Klientka/klient szuka: „{q}”.\n{ZASADY}\n"
                       f"Oceń każdy z {len(produkty)} produktów poniżej. Zwróć wyłącznie JSON: lista obiektów "
                       f'{{"i": numer, "pasuje": true/false, "ocena": 0-10}} dla każdego numeru.'}]
    for i, (p, obr) in enumerate(zip(produkty, obrazy)):
        czesci.append({"text": f"Produkt {i}: {p['nazwa']} (sklep {p['sklep']}){'' if obr else ' [brak zdjęcia, oceń po nazwie]'}"})
        if obr:
            czesci.append(obr)
    cialo = json.dumps({"contents": [{"role": "user", "parts": czesci}],
                        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}})
    for model in MODELE:
        kod, d = pobierz_json(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={k}",
                              naglowki={"Content-Type": "application/json"}, dane=cialo, czas=60)
        if kod in (404, 400) and not d:
            continue
        if not d:
            if kod == 429:
                time.sleep(4)
                continue
            return None
        try:
            tekst = d["candidates"][0]["content"]["parts"][0]["text"]
            lista = json.loads(re.search(r"\[.*\]", tekst, re.S).group(0))
        except Exception:
            continue
        out = {}
        for x in lista:
            try:
                i = int(x["i"])
                out[produkty[i]["id"]] = (bool(x.get("pasuje")), max(0, min(10, int(x.get("ocena", 0)))))
            except Exception:
                pass
        return out
    return None


def ocen(produkty, okazja, dzial, q):
    """Zwraca (słownik pid -> (pasuje, ocena), stan). Produkty bez oceny nie trafiają do słownika."""
    if okazja not in OPISY:
        return {}, "bez okazji"
    k = klucz()
    if not k:
        return {}, "brak klucza Gemini"
    wynik = _z_pamieci([p["id"] for p in produkty], okazja)
    nowe = [p for p in produkty if p["id"] not in wynik]
    paczki = [nowe[i:i + PACZKA] for i in range(0, len(nowe), PACZKA)]
    bledy = 0
    with ThreadPoolExecutor(max_workers=3) as ex:
        for w in ex.map(lambda pk: _paczka(pk, okazja, dzial, q, k), paczki):
            if w is None:
                bledy += 1
                continue
            _zapisz(w, okazja)
            wynik.update(w)
    return wynik, ("ok" if not bledy else f"nie ocenione paczki: {bledy} z {len(paczki)}")
