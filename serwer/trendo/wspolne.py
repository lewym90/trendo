"""Wspólne narzędzia zbieracza Trendo: pobieranie stron, baza (pamięć wyników, historia cen), weryfikacja promocji."""
import gzip, hashlib, json, os, re, sqlite3, subprocess, threading, time

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
DANE = os.environ.get("TRENDO_DANE", "/var/lib/trendo")
os.makedirs(DANE, exist_ok=True)
_baza_blokada = threading.Lock()
PRZEGLADARKA = threading.Lock()  # jedna przeglądarka naraz na całym serwerze (trendy, znaki sklepów)


def pobierz(url, naglowki=None, limit=8_000_000, czas=25, dane=None):
    """Pobiera adres przez curl (HTTP/2, kompresja). dane = treść POST (bajty/tekst). Zwraca (kod, bajty)."""
    cmd = ["curl", "-sS", "-L", "--compressed", "--http2", "--max-time", str(czas), "--max-filesize", str(limit),
           "-A", UA, "-H", "Accept-Language: pl-PL,pl;q=0.9,en;q=0.6"]
    for k, v in (naglowki or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if dane is not None:
        cmd += ["-X", "POST", "--data-binary", "@-"]
    cmd += ["-w", "\n%{http_code}", url]
    try:
        wej = dane.encode() if isinstance(dane, str) else dane
        r = subprocess.run(cmd, capture_output=True, timeout=czas + 10, input=wej)
        d = r.stdout
        i = d.rfind(b"\n")
        kod = int(d[i + 1:].strip() or 0)
        tresc = d[:i]
        if tresc[:2] == b"\x1f\x8b":
            try:
                tresc = gzip.decompress(tresc)
            except Exception:
                pass
        return kod, tresc
    except Exception:
        return 0, b""


def pobierz_json(url, naglowki=None, czas=25, dane=None):
    kod, b = pobierz(url, dict({"Accept": "application/json, text/plain, */*"}, **(naglowki or {})), czas=czas, dane=dane)
    if kod != 200:
        return kod, None
    try:
        return kod, json.loads(b.decode("utf-8", "ignore"))
    except Exception:
        return kod, None


def baza():
    c = sqlite3.connect(os.path.join(DANE, "trendo.db"), timeout=30, check_same_thread=False)
    c.execute("CREATE TABLE IF NOT EXISTS pamiec (klucz TEXT PRIMARY KEY, czas INTEGER, dane TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS ceny (pid TEXT, cena REAL, czas INTEGER)")
    c.execute("CREATE INDEX IF NOT EXISTS ceny_pid ON ceny(pid, czas)")
    c.execute("CREATE TABLE IF NOT EXISTS licznik (klucz TEXT PRIMARY KEY, ile INTEGER)")
    return c


DB = baza()


def pamiec_czytaj(klucz, wiek):
    with _baza_blokada:
        r = DB.execute("SELECT czas, dane FROM pamiec WHERE klucz=?", (klucz,)).fetchone()
    if r and time.time() - r[0] < wiek:
        return json.loads(r[1])
    return None


def pamiec_zapisz(klucz, dane):
    with _baza_blokada:
        DB.execute("INSERT OR REPLACE INTO pamiec VALUES (?,?,?)", (klucz, int(time.time()), json.dumps(dane, ensure_ascii=False)))
        DB.commit()


def licznik(klucz, dodaj=0):
    with _baza_blokada:
        r = DB.execute("SELECT ile FROM licznik WHERE klucz=?", (klucz,)).fetchone()
        ile = (r[0] if r else 0) + dodaj
        if dodaj:
            DB.execute("INSERT OR REPLACE INTO licznik VALUES (?,?)", (klucz, ile))
            DB.commit()
    return ile


def pid(sklep, url, nazwa=""):
    return hashlib.sha1(f"{sklep}|{url or nazwa}".encode()).hexdigest()[:16]


def _od_poprawki_cen():
    """Od kiedy ceny są czytane poprawnie (do wersji 0.13.1 parser gubił grosze i cyfry: 109,99 → 109, 2499 → 249)."""
    DB.execute("CREATE TABLE IF NOT EXISTS ustawienia (klucz TEXT PRIMARY KEY, wartosc TEXT)")
    r = DB.execute("SELECT wartosc FROM ustawienia WHERE klucz='ceny_poprawne_od'").fetchone()
    if r:
        return int(r[0])
    teraz = int(time.time())
    DB.execute("INSERT OR REPLACE INTO ustawienia VALUES ('ceny_poprawne_od', ?)", (str(teraz),))
    DB.commit()
    return teraz


def _slad_bledu(stara, nowa):
    """Czy zapisana dawniej cena to dokładnie zepsuty odczyt obecnej (obcięte grosze albo zgubiona ostatnia cyfra)."""
    return stara < nowa - 0.001 and (abs(stara - int(nowa)) < 0.001 or abs(stara - int(nowa / 10)) < 0.001)


def zapisz_cene(p):
    """Dopisuje cenę do historii (najwyżej raz na 6 godzin dla produktu)."""
    teraz = int(time.time())
    with _baza_blokada:
        od = _od_poprawki_cen()
        stare = DB.execute("SELECT rowid, cena FROM ceny WHERE pid=? AND czas<?", (p["id"], od)).fetchall()
        zle = [rid for rid, c in stare if _slad_bledu(c, p["cena"])]
        if zle:
            DB.execute(f"DELETE FROM ceny WHERE rowid IN ({','.join('?' * len(zle))})", zle)
        r = DB.execute("SELECT cena, czas FROM ceny WHERE pid=? ORDER BY czas DESC LIMIT 1", (p["id"],)).fetchone()
        if not r or teraz - r[1] > 6 * 3600 or abs(r[0] - p["cena"]) > 0.001:
            DB.execute("INSERT INTO ceny VALUES (?,?,?)", (p["id"], p["cena"], teraz))
        DB.commit()


def historia(pid_):
    with _baza_blokada:
        return DB.execute("SELECT cena, czas FROM ceny WHERE pid=? ORDER BY czas", (pid_,)).fetchall()


def weryfikuj(p):
    """Ocena promocji:
    ok       - mamy własną historię z 30 dni i przez ten czas cena była wyższa (obniżka prawdziwa),
    pozorna  - w naszej historii z ostatnich 30 dni produkt kosztował tyle samo co teraz albo mniej,
    sklep    - obniżkę deklaruje sklep, nie mamy jeszcze dość własnej historii,
    reg      - brak obniżki."""
    if not p.get("stara") or p["stara"] <= p["cena"]:
        p["stara"] = None
        return "reg"
    om = p.get("omnibus")
    if om:
        # Sklep podał najniższą cenę z 30 dni przed obniżką (dyrektywa Omnibus). Obniżkę liczymy od niej,
        # nie od „ceny regularnej”: 199,99 → 39,99 przy najniższej 69,99 to −43%, nie −80%.
        if p["cena"] < om - 0.01:
            if om < p["stara"] - 0.01:
                p["stara_sklepu"], p["stara"] = p["stara"], om
            return "ok"
        return "pozorna"
    h = historia(p["id"])
    teraz = time.time()
    przed = [c for c, t in h if teraz - t <= 30 * 86400 and teraz - t > 2 * 86400]
    if przed:
        if min(przed) <= p["cena"] + 0.01:
            return "pozorna"
        dni = (teraz - min(t for c, t in h)) / 86400
        if dni >= 28:
            return "ok"
    return "sklep"


def liczba(t):
    """Cena z dowolnego zapisu: '1 299,99 zł', '1.299,99', '1299.99', '2499', '1,299.00' -> liczba.
    Separator, po którym stoją 1–2 cyfry na końcu, jest dziesiętny; grupy po 3 cyfry to tysiące."""
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return float(t)
    t = str(t).replace("\xa0", " ").replace("\u202f", " ")
    m = re.search(r"\d+(?:(?:[.,]| (?=\d{3}(?!\d)))\d+)*", t)  # spacja tylko przed grupą 3 cyfr (tysiące)
    if not m:
        return None
    s = m.group(0).strip().rstrip(".,").replace(" ", "")
    if "," in s and "." in s:  # ostatni z nich jest dziesiętny
        dz = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dz == "," else ",", "").replace(dz, ".")
    elif "," in s or "." in s:
        sep = "," if "," in s else "."
        cz = s.split(sep)
        if len(cz) == 2 and 1 <= len(cz[1]) <= 2:
            s = cz[0] + "." + cz[1]
        elif all(len(c) == 3 for c in cz[1:]):
            s = "".join(cz)
        else:
            s = "".join(cz[:-1]) + "." + cz[-1]
    try:
        return float(s)
    except ValueError:
        return None


def produkt(sklep, nazwa, cena, url, zdjecie, stara=None, zrodlo="", dzial="", extra=None):
    p = {"id": pid(sklep, url, nazwa), "sklep": sklep, "nazwa": re.sub(r"\s+", " ", (nazwa or "")).strip(),
         "cena": round(float(cena), 2), "stara": round(float(stara), 2) if stara else None,
         "url": url, "zdjecie": zdjecie, "zrodlo": zrodlo, "dzial": dzial, "sprawdzono": int(time.time())}
    if extra:
        p.update(extra)
    if "rozmiary" in p:
        p["rozmiary"] = lista_rozmiarow(p["rozmiary"])
    return p


def lista_rozmiarow(r):
    """Rozmiary zawsze jako lista napisów. Sklepy podają je jako listę, obiekt {"1": "M"} albo napis "S, M, L"."""
    if not r:
        return None
    if isinstance(r, dict):
        r = [r[k] for k in sorted(r, key=lambda k: (not str(k).isdigit(), int(k) if str(k).isdigit() else 0, str(k)))]
    elif isinstance(r, str):
        r = re.split(r"[,;/|]", r)
    elif not isinstance(r, (list, tuple)):
        return None
    wyn = []
    for x in r:
        if isinstance(x, dict):
            x = x.get("name") or x.get("label") or x.get("size") or x.get("value")
        x = str(x).strip() if x is not None else ""
        if x and x not in wyn:
            wyn.append(x)
    return wyn or None


MESKIE = re.compile(r"męsk|mesk|mężczy|mezczy|\bmen\b|\bman\b", re.I)
DAMSKIE = re.compile(r"damsk|kobiet|\bwomen\b|\bwoman\b|\blady\b", re.I)


# Sklepy, w których szukamy wprost w dziale damskim albo męskim: płeć produktu = dział wyszukiwania.
DZIAL_ZE_SKLEPU = {"Zara", "Modivo", "eobuwie", "Born2Be", "Renee", "Reserved", "House", "Cropp", "Sinsay", "Mohito"}
TYLKO_DAMSKIE_SKLEPY = {"Bizuu", "Mohito", "Top Secret", "Molton", "Moodo", "Quiosque", "Monnari"}


def plec_ze_sklepu(p, dzial):
    """Płeć produktu według sklepu (dział, kod produktu, opis). None, gdy sklep jej nie podaje."""
    if p.get("plec_sklepu"):
        return p["plec_sklepu"]
    sklep, nazwa = p.get("sklep", ""), p.get("nazwa", "")
    if sklep in TYLKO_DAMSKIE_SKLEPY:
        return "damskie"
    if sklep in DZIAL_ZE_SKLEPU and p.get("zrodlo") != "google":
        return dzial
    if sklep == "Ochnik":
        # kody Ochnika: KOSMT = koszula męska, KURDS = kurtka damska, BUTYM = buty męskie, SUKDT = sukienka damska
        m = re.search(r"\b([A-Z]{4,5})-[0-9A-Z]", nazwa)
        if m:
            k = m.group(1)
            z = k[3] if len(k) == 5 and k[4] in "TS" else k[-1]
            if z in "MD":
                return "meskie" if z == "M" else "damskie"
    if sklep in ("Kazar", "Bialcon"):  # sklepy głównie damskie: męskie tylko z opisem „męskie”
        return "meskie" if MESKIE.search(nazwa) else "damskie"
    m, d = bool(MESKIE.search(nazwa)), bool(DAMSKIE.search(nazwa))
    if m != d:
        return "meskie" if m else "damskie"
    return None


def pasuje_dzial(tekst, dzial):
    """Odrzuca produkty wprost opisane jako przeznaczone dla drugiej płci."""
    t = tekst or ""
    if dzial == "damskie":
        return not (MESKIE.search(t) and not DAMSKIE.search(t))
    return not (DAMSKIE.search(t) and not MESKIE.search(t))


def rownolegle(funkcja, lista, watki=6):
    """Uruchamia funkcję dla każdego elementu naraz, zwraca listę wyników (błędy pomija)."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=watki) as ex:
        out = []
        for f in [ex.submit(funkcja, x) for x in lista]:
            try:
                out.append(f.result(timeout=40))
            except Exception:
                out.append(None)
        return out
