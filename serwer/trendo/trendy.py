"""Trendy z prawdziwych, darmowych źródeł (bez wymyślania).

Jak to działa:
1. Raz na dobę pobieramy nowe artykuły i raporty z listy ZRODLA (polskie i zagraniczne magazyny, raporty danych).
2. AI wypisuje z każdego tekstu wymienione w nim trendy w ujednoliconej postaci (te same cechy co ocena produktów:
   kolor, materiał, wzór, rodzaj rzeczy) i do każdego MUSI podać dosłowny fragment tekstu, który to mówi.
3. Weryfikator sprawdza, czy ten fragment naprawdę jest w artykule. Jeśli nie ma, wzmianka przepada.
4. Trend pokazujemy dopiero, gdy piszą o nim co najmniej DWA niezależne wydawnictwa. Do tego nasze liczby:
   udział cechy w nowościach sklepów tydzień po tygodniu (z ocen produktów).
W aplikacji pokazujemy tylko nazwę trendu, nasze liczby i linki do źródeł (bez przepisywania tekstów).

Uruchomienie ręczne: cd /opt/trendo && /root/trendo-scraper/bin/python -m trendo.trendy [--zbierz] [--raport]
"""
import html as html_mod, json, re, sys, time
from urllib.parse import urljoin, urlparse
from . import klasyfikator as K
from .wspolne import DB, _baza_blokada, licznik, pobierz

# typ: dane = raporty oparte na danych (zakupy, wyszukiwania, pokazy); redakcja = magazyny; branza = serwisy branżowe
# sposob: rss | linki (strona z listą artykułów) | strona (sama strona jest źródłem) | lyst
# przegladarka: True = strona blokuje zwykłe pobieranie, używamy przeglądarki na serwerze
ZRODLA = [
    {"nazwa": "Lyst Index", "typ": "dane", "kraj": "INT", "sposob": "lyst", "url": "https://www.lyst.co.uk/the-lyst-index/"},
    {"nazwa": "Tagwalk", "typ": "dane", "kraj": "INT", "sposob": "strona", "url": "https://www.tag-walk.com/en/trends/woman"},
    {"nazwa": "Pinterest Predicts", "typ": "dane", "kraj": "INT", "sposob": "strona", "url": "https://business.pinterest.com/pinterest-predicts/",
     "przegladarka": True},
    {"nazwa": "Heuritech", "typ": "dane", "kraj": "INT", "sposob": "linki", "url": "https://heuritech.com/blog/", "sciezka": r"/articles/"},
    {"nazwa": "WGSN", "typ": "dane", "kraj": "INT", "sposob": "linki", "url": "https://www.wgsn.com/en/blogs", "sciezka": r"/blog/"},
    {"nazwa": "Vogue", "typ": "redakcja", "kraj": "INT", "sposob": "rss", "url": "https://www.vogue.com/feed/rss", "sciezka": r"/article/"},
    {"nazwa": "Harper's Bazaar", "typ": "redakcja", "kraj": "INT", "sposob": "rss", "url": "https://www.harpersbazaar.com/rss/fashion.xml/"},
    {"nazwa": "Who What Wear", "typ": "redakcja", "kraj": "INT", "sposob": "rss", "url": "https://www.whowhatwear.com/rss"},
    {"nazwa": "FashionUnited", "typ": "branza", "kraj": "INT", "sposob": "rss", "url": "https://fashionunited.com/rss-news", "sciezka": r"/news/fashion/"},
    {"nazwa": "Vogue Polska", "typ": "redakcja", "kraj": "PL", "sposob": "linki", "url": "https://www.vogue.pl/", "przegladarka": True},
    {"nazwa": "Harper's Bazaar Polska", "typ": "redakcja", "kraj": "PL", "sposob": "linki", "url": "https://www.harpersbazaar.pl/", "przegladarka": True},
    {"nazwa": "Elle Polska", "typ": "redakcja", "kraj": "PL", "sposob": "linki", "url": "https://www.elle.pl/", "sciezka": r"/moda/"},
    {"nazwa": "Glamour Polska", "typ": "redakcja", "kraj": "PL", "sposob": "linki", "url": "https://www.glamour.pl/", "sciezka": r"/moda/"},
    {"nazwa": "Twój Styl", "typ": "redakcja", "kraj": "PL", "sposob": "linki", "url": "https://www.twojstyl.pl/", "sciezka": r"/artykul/"},
    {"nazwa": "fashionbiznes.pl", "typ": "branza", "kraj": "PL", "sposob": "rss", "url": "https://fashionbiznes.pl/feed/"},
    {"nazwa": "Breuninger Magazyn", "typ": "redakcja", "kraj": "PL", "sposob": "linki", "url": "https://www.breuninger.com/pl/magazyn/moda/",
     "sciezka": r"/magazyn/moda/trendy"},
]
WIEK_DNI = 150          # ile wstecz liczymy wzmianki
MAKS_NA_ZRODLO = 6      # nowych artykułów z jednego źródła na dobę
MAKS_NA_DOBE = 45
TANIE_MODELE = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]  # wyciąganie wzmianek: weryfikacja i tak jest twarda
KW = re.compile(r"trend|modn|sezon|jesie|zim[aey]|wiosn|lato|lata\b|kolor|must[- ]?have|runway|fall|winter|spring|summer|"
                r"fw\d\d|ss\d\d|aw\d\d|catwalk|pokaz|kolekcj|nosi|styl", re.I)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"

with _baza_blokada:
    DB.execute("CREATE TABLE IF NOT EXISTS tr_art (url TEXT PRIMARY KEY, zrodlo TEXT, tytul TEXT, czas INTEGER, stan TEXT)")
    DB.execute("CREATE TABLE IF NOT EXISTS tr_wzm (url TEXT, zrodlo TEXT, typ TEXT, kraj TEXT, czas INTEGER, dzial TEXT, kategoria TEXT,"
               " nazwa TEXT, kolor TEXT, material TEXT, wzor TEXT, rodzaj TEXT, kierunek TEXT, kiedy TEXT, haslo TEXT, cytat TEXT)")
    DB.execute("CREATE INDEX IF NOT EXISTS tr_wzm_czas ON tr_wzm(czas)")
    DB.commit()


# ---------- pobieranie ----------
def _strona(z, url):
    if z.get("przegladarka"):
        return pobierz_przegladarka(url)
    kod, b = pobierz(url, naglowki={"User-Agent": UA}, czas=30, limit=6_000_000)
    return b.decode("utf-8", "ignore") if kod == 200 and b else ""


_przegladarka = {"ok": None}


def pobierz_przegladarka(url):
    """Strony blokujące zwykłe pobieranie: przeglądarka Chromium na serwerze (Playwright). Pusty tekst, gdy się nie da."""
    if _przegladarka["ok"] is False:
        return ""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        _przegladarka["ok"] = False
        return ""
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            s = b.new_page(user_agent=UA, locale="pl-PL")
            s.goto(url, timeout=45000, wait_until="domcontentloaded")
            s.wait_for_timeout(2500)
            h = s.content()
            b.close()
            _przegladarka["ok"] = True
            return h
    except Exception:
        return ""


def _tytul_z_adresu(u):
    slug = urlparse(u).path.rstrip("/").split("/")[-1]
    return " ".join(w for w in re.split(r"[-_]+", slug) if not re.fullmatch(r"\d+|[a-z]\d+", w)).capitalize()


def _linki(z, h):
    dom = urlparse(z["url"]).netloc.replace("www.", "")
    tytuly = {}
    for href, txt in re.findall(r'<a\b[^>]*?href="([^"#]+)"[^>]*>(.*?)</a>', h, re.S | re.I):
        u = urljoin(z["url"], href).split("?")[0]
        if dom not in urlparse(u).netloc or (z.get("sciezka") and not re.search(z["sciezka"], u)):
            continue
        t = " ".join(html_mod.unescape(re.sub(r"<[^>]+>", " ", txt)).split())
        if "->" in t or "#" in t or "{" in t or len(t) < 25:
            t = ""  # tekst z atrybutów, nie tytuł
        if len(t) > len(tytuly.get(u, "")):
            tytuly[u] = t
        tytuly.setdefault(u, "")
    out = []
    for u, t in tytuly.items():
        t = t or _tytul_z_adresu(u)
        if len(t) >= 20 and KW.search(t + " " + u):
            out.append((u, t[:200]))
    return out


def _rss(z, h):
    out = []
    for it in re.findall(r"<item>(.*?)</item>", h, re.S):
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
        l = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", it, re.S)
        if not (t and l):
            continue
        tyt = " ".join(html_mod.unescape(t.group(1)).split())
        u = l.group(1).strip()
        if z.get("sciezka") and not re.search(z["sciezka"], u):
            continue
        if KW.search(tyt + " " + u):
            out.append((u, tyt[:200]))
    return out


def _lyst(z, h):
    """Strona Lyst Index ma listę kwartałów (Q3-26, q2-26…): bierzemy najnowszy raport."""
    q = sorted(set(re.findall(r"the-lyst-index/[qQ](\d)-(\d\d)", h)), key=lambda x: (x[1], x[0]), reverse=True)
    return [(f"https://www.lyst.co.uk/the-lyst-index/q{q[0][0]}-{q[0][1]}/", f"The Lyst Index Q{q[0][0]} 20{q[0][1]}")] if q else []


def tekst_artykulu(h):
    """Czysty tekst artykułu (bez skryptów, menu i stopki)."""
    for m in re.findall(r'"articleBody"\s*:\s*"((?:[^"\\]|\\.)*)"', h):
        try:
            t = json.loads('"' + m + '"')
            if len(t) > 500:
                return " ".join(html_mod.unescape(re.sub(r"<[^>]+>", " ", t)).split())[:24000]
        except Exception:
            pass
    h = re.sub(r"(?is)<(script|style|nav|footer|header|noscript|svg|form)\b.*?</\1>", " ", h)
    czesci = re.findall(r"(?is)<(?:p|h1|h2|h3|li|blockquote)\b[^>]*>(.*?)</(?:p|h1|h2|h3|li|blockquote)>", h)
    zdania = [" ".join(html_mod.unescape(re.sub(r"<[^>]+>", " ", c)).split()) for c in czesci]
    return " ".join(z for z in zdania if len(z) > 25)[:24000]


def tekst_strony(h):
    h = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", h)
    return " ".join(html_mod.unescape(re.sub(r"<[^>]+>", " ", h)).split())[:24000]


def _norm(t):
    t = (t or "").lower().replace("\u00ad", "")
    t = re.sub(r"[\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\"'`´«»]", "", t)
    t = re.sub(r"[^\w%]+", " ", t)
    return " ".join(t.split())


def zweryfikowany(cytat, tekst):
    """Twarda weryfikacja: cytat (min. 3 słowa, np. „colour Gold 4%” z Tagwalk) musi naprawdę występować w tekście (bez znaczenia interpunkcja i wielkość liter)."""
    c = _norm(cytat)
    return len(c.split()) >= 3 and c in _norm(tekst)


# ---------- AI: które tytuły dotyczą trendów w modzie ----------
SCHEMAT_TYTULY = {"type": "ARRAY", "items": {"type": "INTEGER"}}


def _modele_tanie():
    return [m for m in TANIE_MODELE if m not in K._martwe] + [m for m in K.modele() if m not in TANIE_MODELE and m not in K._martwe]


def wybierz_tytuly(lista):
    """lista [(url, tytul)] → indeksy artykułów o trendach w ubraniach, butach i dodatkach (nie uroda, dom, jedzenie)."""
    if not lista:
        return []
    tresc = ("Zwróć numery tylko tych tytułów, które dotyczą TRENDÓW w ubraniach, butach, torebkach lub biżuterii "
             "(co jest modne, kolory i fasony sezonu, pokazy mody, raporty o modzie). Pomiń urodę, kosmetyki, fryzury, wnętrza, "
             "jedzenie, podróże, plotki i zwykłe reklamy produktów.\n" + "\n".join(f"{i}: {t}" for i, (_, t) in enumerate(lista)))
    for m in _modele_tanie():
        kod, wyn = K._wywolaj(m, [{"text": tresc}], SCHEMAT_TYTULY)
        if kod == 404:
            continue
        return [i for i in (wyn or []) if isinstance(i, int) and 0 <= i < len(lista)]
    return []


# ---------- AI: wzmianki o trendach ----------
KATEGORIE = ["kolor", "material", "wzor", "rzecz", "fason", "styl", "detal"]
SCHEMAT_WZM = {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
    "nazwa": {"type": "STRING"}, "kategoria": {"type": "STRING", "enum": KATEGORIE},
    "kolor": {"type": "STRING", "enum": ["brak"] + K.KOLORY}, "material": {"type": "STRING", "enum": ["brak"] + K.MATERIALY},
    "wzor": {"type": "STRING", "enum": ["brak"] + K.WZORY_RODZAJ}, "rodzaj": {"type": "STRING", "enum": ["brak"] + K.RODZAJE},
    "dzial": {"type": "STRING", "enum": ["damskie", "meskie", "oba"]},
    "kierunek": {"type": "STRING", "enum": ["rosnie", "utrzymuje_sie", "wraca", "wygasa"]},
    "kiedy": {"type": "STRING", "enum": ["teraz", "nastepny_sezon"]},
    "haslo": {"type": "STRING"}, "cytat": {"type": "STRING"}},
    "required": ["nazwa", "kategoria", "kolor", "material", "wzor", "rodzaj", "dzial", "kierunek", "kiedy", "haslo", "cytat"]}}


def znane_nazwy():
    with _baza_blokada:
        r = DB.execute("SELECT nazwa, COUNT(*) c FROM tr_wzm WHERE czas > ? GROUP BY nazwa ORDER BY c DESC LIMIT 200",
                       (int(time.time()) - WIEK_DNI * 86400,)).fetchall()
    return [x[0] for x in r]


def wyciagnij(zrodlo, tytul, tekst):
    nazwy = znane_nazwy()
    tresc = (f"Źródło: {zrodlo}. Tytuł: {tytul}\n\nTEKST ARTYKUŁU:\n{tekst[:16000]}\n\n"
             "Wypisz trendy w modzie (ubrania, buty, torebki, biżuteria), które TEN TEKST wprost przedstawia jako modne teraz "
             "albo w najbliższym sezonie. Nie dopisuj niczego od siebie. Pomiń reklamy pojedynczych produktów bez mowy o trendzie, "
             "urodę, fryzury i wnętrza. Najwyżej 8 trendów.\n"
             "nazwa = krótka polska nazwa trendu (2-5 słów, mianownik, np. „Królewski fiolet”, „Spódnice midi z satyny”, "
             "„Baleriny”, „Kożuchy”). Jeśli trend jest na tej liście znanych nazw, użyj DOKŁADNIE tej nazwy: "
             f"{'; '.join(nazwy) if nazwy else '(brak)'}\n"
             "kategoria, kolor, material, wzor, rodzaj = ujednolicone cechy trendu (brak, gdy nie dotyczy).\n"
             "dzial = dla kogo (oba, gdy tekst nie rozróżnia). kierunek = co tekst mówi o trendzie. "
             "kiedy = teraz (obecny sezon) albo nastepny_sezon (zapowiedź z pokazów na kolejny sezon).\n"
             "haslo = polskie hasło do wyszukania takich rzeczy w sklepie (np. „fioletowy sweter”, „spódnica midi satynowa”).\n"
             "cytat = DOSŁOWNY fragment tekstu (3-30 słów, w oryginalnym języku, skopiowany znak w znak), który mówi o tym trendzie. "
             "Bez cytatu z tekstu nie wypisuj trendu.")
    for m in _modele_tanie():
        kod, wyn = K._wywolaj(m, [{"text": tresc}], SCHEMAT_WZM)
        if kod == 404:
            continue
        return wyn if isinstance(wyn, list) else []
    return []


# ---------- zbieranie ----------
def zbierz(maks=MAKS_NA_DOBE, wypisuj=False):
    """Pobiera nowe artykuły, wyciąga i weryfikuje wzmianki. Zwraca statystykę."""
    stat = {"zrodla": {}, "artykuly": 0, "wzmianki": 0, "odrzucone_cytaty": 0}
    for z in ZRODLA:
        if stat["artykuly"] >= maks:
            break
        h = _strona(z, z["url"])
        if not h:
            stat["zrodla"][z["nazwa"] + (" " + z.get("dzial", "") if z.get("dzial") else "")] = "brak dostępu"
            continue
        if z["sposob"] == "strona":
            kandydaci = [(z["url"], z["nazwa"])]
        elif z["sposob"] == "lyst":
            kandydaci = _lyst(z, h)
        elif z["sposob"] == "rss":
            kandydaci = _rss(z, h)
        else:
            kandydaci = _linki(z, h)
        with _baza_blokada:
            znane = {r[0] for r in DB.execute(f"SELECT url FROM tr_art WHERE url IN ({','.join('?' * len(kandydaci))})",
                                               [u for u, _ in kandydaci])} if kandydaci else set()
        # strony z danymi (Tagwalk, Pinterest) czytamy ponownie co tydzień, bo zmieniają treść
        if z["sposob"] == "strona":
            with _baza_blokada:
                r = DB.execute("SELECT czas FROM tr_art WHERE url=?", (z["url"],)).fetchone()
            if r and time.time() - r[0] < 7 * 86400:
                kandydaci = []
            znane = set()
        nowe = [k for k in kandydaci if k[0] not in znane][:25]
        if z["sposob"] in ("rss", "linki") and nowe:
            nowe = [nowe[i] for i in wybierz_tytuly(nowe)]
            with _baza_blokada:  # pominięte tytuły zapamiętujemy, żeby nie pytać o nie ponownie
                DB.executemany("INSERT OR IGNORE INTO tr_art VALUES (?,?,?,?,?)",
                               [(u, z["nazwa"], t, int(time.time()), "pominiety") for u, t in kandydaci if (u, t) not in nowe and u not in znane])
                DB.commit()
        ile = 0
        for url, tytul in nowe[:MAKS_NA_ZRODLO]:
            if stat["artykuly"] >= maks:
                break
            h2 = h if url == z["url"] else _strona(z, url)
            # strony z danymi (Lyst, Tagwalk, Pinterest) to tabele i kafelki, nie akapity: bierzemy cały tekst strony
            tekst = (tekst_strony(h2) if z["sposob"] in ("strona", "lyst") else tekst_artykulu(h2)) if h2 else ""
            stan = "pusty"
            if len(tekst) > 400:
                wzm = wyciagnij(z["nazwa"], tytul, tekst)
                dobre = []
                for w in wzm or []:
                    if not w.get("nazwa") or not zweryfikowany(w.get("cytat", ""), tekst):
                        stat["odrzucone_cytaty"] += 1
                        continue
                    dobre.append(w)
                with _baza_blokada:
                    DB.executemany("INSERT INTO tr_wzm VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
                        (url, z["nazwa"], z["typ"], z["kraj"], int(time.time()), z.get("dzial") or w["dzial"], w["kategoria"],
                         w["nazwa"].strip()[:60], w["kolor"], w["material"], w["wzor"], w["rodzaj"], w["kierunek"], w["kiedy"],
                         w["haslo"].strip()[:60], w["cytat"][:300]) for w in dobre])
                    DB.commit()
                stat["wzmianki"] += len(dobre)
                stan = f"ok:{len(dobre)}"
                if wypisuj:
                    print(f"  {z['nazwa']}: {tytul[:70]} → {len(dobre)} trendów" + (f" ({', '.join(w['nazwa'] for w in dobre[:5])})" if dobre else ""))
            with _baza_blokada:
                DB.execute("INSERT OR REPLACE INTO tr_art VALUES (?,?,?,?,?)", (url, z["nazwa"], tytul, int(time.time()), stan))
                DB.commit()
            stat["artykuly"] += 1
            ile += 1
        stat["zrodla"][z["nazwa"] + (" " + z.get("dzial", "") if z.get("dzial") else "")] = f"ok, nowe: {ile}"
    return stat


# ---------- nasze dane ze sklepów ----------
def _pasuje(dane, t):
    if t["kategoria"] == "kolor" and t["kolor"] != "brak":
        return dane.get("kolor") == t["kolor"]
    if t["kategoria"] == "material" and t["material"] != "brak":
        return dane.get("material") in K.ZGODNE_MATERIALY.get(t["material"], {t["material"]})
    if t["kategoria"] == "wzor" and t["wzor"] != "brak":
        return dane.get("wzor_rodzaj") == t["wzor"]
    if t["rodzaj"] != "brak":
        return dane.get("r") == t["rodzaj"]
    return None


def dane_sklepow(dzial, cechy, tygodni=8):
    """Udział rzeczy o danej cesze wśród produktów, które pojawiły się w sklepach (pierwszy raz u nas) w kolejnych tygodniach.
    Zwraca (seria procentów od najstarszego tygodnia, liczebność ostatnich 4 tygodni) albo (None, 0), gdy za mało danych."""
    teraz = int(time.time())
    with _baza_blokada:
        wiersze = DB.execute("SELECT k.dane, MIN(c.czas) FROM klasy2 k JOIN ceny c ON c.pid = k.pid "
                             "WHERE c.czas > ? GROUP BY k.pid", (teraz - tygodni * 7 * 86400 - 86400,)).fetchall()
    tyg = [[0, 0] for _ in range(tygodni)]
    for dane, pierwszy in wiersze:
        try:
            d = json.loads(dane)
        except Exception:
            continue
        if d.get("p") not in (dzial, "unisex"):
            continue
        i = tygodni - 1 - (teraz - pierwszy) // (7 * 86400)
        if 0 <= i < tygodni:
            p = _pasuje(d, cechy)
            if p is None:
                return None, 0
            tyg[i][1] += 1
            tyg[i][0] += 1 if p else 0
    proba = sum(t[1] for t in tyg[-4:])
    if proba < 150:
        return None, proba
    return [round(100 * a / b, 1) if b >= 30 else None for a, b in tyg], proba


# ---------- zestawienie ----------
IMG = {"spodnie": "spodnie", "jeansy": "spodnie", "koszula": "koszule", "bluzka": "koszule", "sweter": "swetry", "kardigan": "swetry",
       "kurtka": "okrycia", "płaszcz": "okrycia", "marynarka": "okrycia", "sukienka": "sukienki", "spódnica": "sukienki",
       "torebka": "torebki", "botki": "buty", "kozaki": "buty", "szpilki": "buty", "baleriny": "buty", "mokasyny": "buty",
       "sneakersy": "buty", "półbuty": "buty", "biżuteria": "dodatki", "pasek": "dodatki", "szal": "dodatki", "czapka": "dodatki"}


def zestawienie(dzial):
    od = int(time.time()) - WIEK_DNI * 86400
    with _baza_blokada:
        w = DB.execute("SELECT w.url, w.zrodlo, w.typ, w.kraj, w.czas, w.dzial, w.kategoria, w.nazwa, w.kolor, w.material, w.wzor, "
                       "w.rodzaj, w.kierunek, w.kiedy, w.haslo, a.tytul FROM tr_wzm w LEFT JOIN tr_art a ON a.url = w.url "
                       "WHERE w.czas > ? AND w.dzial IN (?, 'oba')", (od, dzial)).fetchall()
    grupy = {}
    for r in w:
        grupy.setdefault(r[7].lower(), []).append(r)
    out = []
    for _, rr in grupy.items():
        wydawcy = sorted({r[1] for r in rr})
        if len(wydawcy) < 2:
            continue  # zasada: co najmniej dwa niezależne wydawnictwa
        def najczestsze(i, pomin=("brak",)):
            v = [r[i] for r in rr if r[i] and r[i] not in pomin]
            return max(set(v), key=v.count) if v else "brak"
        t = {"nazwa": najczestsze(7), "kategoria": najczestsze(6), "kolor": najczestsze(8), "material": najczestsze(9),
             "wzor": najczestsze(10), "rodzaj": najczestsze(11), "haslo": najczestsze(14)}
        kier = [r[12] for r in rr]
        kiedy = [r[13] for r in rr]
        seria, proba = dane_sklepow(dzial, t)
        zmiana = None
        if seria and seria[-1] is not None:
            stare = [x for x in seria[:4] if x is not None]
            if stare and sum(stare) / len(stare) > 0:
                zmiana = round(100 * (seria[-1] - sum(stare) / len(stare)) / (sum(stare) / len(stare)))
        if kier.count("wygasa") > len(kier) / 2:
            status = "wygasa"
        elif kiedy.count("nastepny_sezon") > len(kiedy) / 2:
            status = "nadchodzi"
        elif (zmiana is not None and zmiana >= 15) or kier.count("rosnie") + kier.count("wraca") > len(kier) / 2:
            status = "rosnie"
        else:
            status = "szczyt"
        linki = {}
        for r in sorted(rr, key=lambda x: -x[4]):
            linki.setdefault(r[1], {"wydawca": r[1], "url": r[0], "tytul": (r[15] or "")[:120], "data": r[4], "kraj": r[3]})
        dane_opis = ""
        if seria and seria[-1] is not None:
            dane_opis = f" W nowościach sklepów: {str(seria[-1]).replace('.', ',')}%" + (f" ({'+' if zmiana >= 0 else ''}{zmiana}% w miesiąc)." if zmiana is not None else ".")
        pl = [x for x in wydawcy if linki[x]["kraj"] == "PL"]
        opis = "Piszą o tym: " + ", ".join(wydawcy[:4]) + (f" i {len(wydawcy) - 4} innych" if len(wydawcy) > 4 else "") + "." + dane_opis
        wynik = {"nazwa": t["nazwa"], "opis": opis, "status": status, "zrodla": len(wydawcy), "wydawcy": wydawcy, "polskie": len(pl),
                 "dane_rynkowe": sum(1 for r in rr if r[2] == "dane"), "linki": list(linki.values())[:8], "haslo": t["haslo"],
                 "kategoria": t["kategoria"], "kolor": t["kolor"], "seria": [x if x is not None else 0 for x in seria] if seria else None,
                 "udzial": seria[-1] if seria else None, "zmiana": zmiana, "proba": proba,
                 "wzmianek_w_tygodniach": [sum(1 for r in rr if (int(time.time()) - r[4]) // (7 * 86400) == 7 - i) for i in range(8)],
                 "img": None}
        k = IMG.get(t["rodzaj"])
        if k:
            wynik["img"] = f"{'d' if dzial == 'damskie' else 'm'}-{k}-1"
        wynik["punkty"] = len(wydawcy) * 3 + wynik["dane_rynkowe"] * 2 + len(pl) * 2 + (2 if (zmiana or 0) > 15 else 0)
        out.append(wynik)
    out.sort(key=lambda x: -x["punkty"])
    with _baza_blokada:
        art = DB.execute("SELECT COUNT(*) FROM tr_art WHERE stan LIKE 'ok%'").fetchone()[0]
        wz = DB.execute("SELECT COUNT(*) FROM tr_wzm WHERE czas > ?", (od,)).fetchone()[0]
    return {"dzial": dzial, "trendy": out[:30], "artykulow": art, "wzmianek": wz,
            "zrodla": sorted({z["nazwa"] for z in ZRODLA}), "aktualizacja": int(time.time())}


def main():
    arg = sys.argv[1:]
    if not K.dostepny():
        print("Trendy: brak klucza Gemini.")
        return
    if "--zbierz" in arg or not arg:
        licznik(time.strftime("trendy-%Y-%m-%d"), 1)  # dzisiejsze zbieranie zrobione (usługa nie powtórzy)
        print("Zbieram artykuły i raporty o trendach...")
        s = zbierz(wypisuj=True)
        print(f"\nŹródła: " + "; ".join(f"{k}: {v}" for k, v in s["zrodla"].items()))
        print(f"Przeczytane artykuły: {s['artykuly']}, potwierdzone wzmianki: {s['wzmianki']}, odrzucone (cytat nie z tekstu): {s['odrzucone_cytaty']}")
    if "--raport" in arg or not arg:
        for dz in ("damskie", "meskie"):
            z = zestawienie(dz)
            print(f"\n=== Trendy {dz} (co najmniej 2 niezależne źródła): {len(z['trendy'])} ===")
            for t in z["trendy"][:15]:
                print(f"  {t['nazwa']} [{t['status']}] — {', '.join(t['wydawcy'])}" + (f"; sklepy {t['udzial']}%" if t["udzial"] is not None else ""))


if __name__ == "__main__":
    main()
