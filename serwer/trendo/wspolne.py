"""Wspólne narzędzia zbieracza Trendo: pobieranie stron, baza (pamięć wyników, historia cen), weryfikacja promocji."""
import gzip, hashlib, json, os, re, sqlite3, subprocess, threading, time

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
DANE = os.environ.get("TRENDO_DANE", "/var/lib/trendo")
os.makedirs(DANE, exist_ok=True)
_baza_blokada = threading.Lock()


def pobierz(url, naglowki=None, limit=8_000_000, czas=25):
    """Pobiera adres przez curl (HTTP/2, kompresja). Zwraca (kod, bajty)."""
    cmd = ["curl", "-sS", "-L", "--compressed", "--http2", "--max-time", str(czas), "--max-filesize", str(limit),
           "-A", UA, "-H", "Accept-Language: pl-PL,pl;q=0.9,en;q=0.6"]
    for k, v in (naglowki or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    cmd += ["-w", "\n%{http_code}", url]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=czas + 10)
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


def pobierz_json(url, naglowki=None, czas=25):
    kod, b = pobierz(url, dict({"Accept": "application/json, text/plain, */*"}, **(naglowki or {})), czas=czas)
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


def zapisz_cene(p):
    """Dopisuje cenę do historii (najwyżej raz na 6 godzin dla produktu)."""
    teraz = int(time.time())
    with _baza_blokada:
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
        # sklep podał najniższą cenę z 30 dni przed obniżką (dyrektywa Omnibus)
        return "ok" if p["cena"] < om - 0.01 else "pozorna"
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
    """'1 299,99 zł' -> 1299.99"""
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return float(t)
    t = str(t).replace("\xa0", " ")
    m = re.search(r"(\d{1,3}(?:[ .]\d{3})*(?:,\d{1,2})?|\d+(?:\.\d{1,2})?)", t)
    if not m:
        return None
    s = m.group(1)
    if "," in s:
        s = s.replace(" ", "").replace(".", "").replace(",", ".")
    else:
        s = s.replace(" ", "")
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
    return p


MESKIE = re.compile(r"męsk|meski|meskie|mężczy|mezczy|\bmen\b|\bman\b", re.I)
DAMSKIE = re.compile(r"damsk|kobiet|\bwomen\b|\bwoman\b|\blady\b", re.I)


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
