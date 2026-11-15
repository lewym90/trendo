"""Trendo: serwer zbieracza. Uruchomienie: python -m trendo.api (port w zmiennej PORT, domyślnie 18890).
Endpointy (za Caddy pod /trendo-api/):
  GET /zdrowie                    stan łączników i konta Google Shopping
  GET /szukaj?q=...&dzial=damskie produkty ze wszystkich łączników naraz
  GET /historia?id=...            historia ceny produktu z naszej bazy
  GET /zglos?id=&okazja=&...      zgłoszenie „Nie pasuje” (od razu ukrywa produkt na tę okazję)
  GET /zgloszenia                 ostatnie zgłoszenia (do poprawiania zasad)
  GET /logo?sklep=...             logo sklepu pobrane z jego strony (pamięć 14 dni)
"""
import json, os, re, time, traceback
from concurrent.futures import ThreadPoolExecutor, wait
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote_plus, urlparse

import threading
from . import klasyfikator, lacznik_google, lacznik_lpp, lacznik_modivo, lacznik_strony, lacznik_zara, logo, nadzor
from .wspolne import DB, _baza_blokada, historia, licznik, pamiec_czytaj, pamiec_zapisz, plec_ze_sklepu, weryfikuj, zapisz_cene

WERSJA = "0.7.2"
LACZNIKI = [lacznik_zara, lacznik_lpp, lacznik_modivo, lacznik_strony, lacznik_google]
PULA = ThreadPoolExecutor(max_workers=8)
WIEK_PAMIECI = 12 * 3600


POMIJANE = {"damskie", "damski", "damska", "męskie", "męski", "męska", "meskie", "meski", "dla", "modne", "modny", "nowe", "tanie"}


def tokeny(q):
    return [w[:4] for w in re.findall(r"\w+", q.lower()) if len(w) >= 4 and w not in POMIJANE]


RZECZY = ("spod", "jean", "kosz", "bluz", "swet", "kurt", "płas", "suki", "spód", "buty", "botk", "szpi", "sand", "tore",
          "plec", "pask", "szal", "czap", "ręka", "mary", "kami", "golf", "kard", "dres", "legg", "szor", "koza", "tramp",
          "snea", "moka", "okul", "kolc", "nasz", "bran", "zega", "garn", "trencz", "parka", "bomb", "kombi", "body", "top",
          "półb", "glan", "worker", "kopert", "nerk", "beret", "rękaw", "apasz", "chust", "rajst", "skar", "piża", "szla",
          "pase", "kolcz", "zesta", "pług", "kosm", "brel")


def rzecz(w):
    w = w[:5]
    return len(w) >= 4 and any(w.startswith(r[:4]) for r in RZECZY)


def trafnosc(p, tok):
    """2 = pasuje całe hasło, 1 = pasuje sama rzecz (np. płaszcz bez koloru), 0 = nie pasuje."""
    t = (p["nazwa"] + " " + (p.get("material") or "")).lower()
    glowne = [x for x in tok if rzecz(x)]
    pierwsza = next((w[:4] for w in re.findall(r"\w+", p["nazwa"].lower()) if rzecz(w)), None)
    if glowne and pierwsza and pierwsza not in glowne:
        return 0  # np. „Pasek do spodni”, gdy szukamy spodni
    if all(x in t for x in tok):
        return 2
    if glowne and all(x in t for x in glowne):
        return 1
    return 0


OKAZJE = {"wieczor": "Wieczór", "wesele": "Wesele", "sylwester": "Sylwester", "randka": "Randka", "praca": "Praca"}

with _baza_blokada:
    DB.execute("CREATE TABLE IF NOT EXISTS zgloszenia (czas INTEGER, pid TEXT, okazja TEXT, q TEXT, dzial TEXT, powod TEXT, nazwa TEXT, sklep TEXT, zdjecie TEXT)")
    DB.commit()


def wykluczone():
    with _baza_blokada:
        return {(a, b) for a, b in DB.execute("SELECT pid, okazja FROM zgloszenia WHERE okazja != ''")}


def pobierz_produkty(q, dzial, laczniki):
    zad = {PULA.submit(l.szukaj, q, dzial): l.NAZWA for l in laczniki}
    gotowe, _ = wait(zad, timeout=55)
    sklepy, produkty, widziane = [], [], set()
    tok = tokeny(q)
    wlasne = {s.lower() for l in LACZNIKI if l is not lacznik_google for s in getattr(l, "SKLEPY", [l.NAZWA])}
    for f, nazwa in zad.items():
        if f not in gotowe:
            sklepy.append({"nazwa": nazwa, "stan": "za długo", "ile": 0}); continue
        try:
            lista, stan = f.result()
        except Exception as e:
            traceback.print_exc()
            lista, stan = [], "błąd: " + str(e)[:60]
        ile = 0
        for p in lista:
            k = (p["sklep"].lower(), p["nazwa"].lower(), p["cena"])
            if k in widziane or not p.get("url") or (p["zrodlo"] == "google" and p["sklep"].lower() in wlasne):
                continue
            p["trafnosc"] = trafnosc(p, tok) if tok else 2
            if not p["trafnosc"]:
                continue
            widziane.add(k)
            p["plec_sklepu"] = plec_ze_sklepu(p, dzial)
            logo.poznaj(p)
            zapisz_cene(p)
            p["weryf"] = weryfikuj(p)
            produkty.append(p); ile += 1
        sklepy.append({"nazwa": nazwa, "stan": stan, "ile": ile})
    return sklepy, produkty


def szukaj(q, dzial, okazja=""):
    q = " ".join(q.split())[:80]
    okazja = okazja if okazja in OKAZJE else ""
    klucz = f"szukaj|{WERSJA}|{q.lower()}|{dzial}|{okazja}"
    zap = pamiec_czytaj(klucz, WIEK_PAMIECI)
    if zap:
        zap["z_pamieci"] = True
        return zap
    t0 = time.time()
    sklepy, produkty = pobierz_produkty(q, dzial, LACZNIKI)
    # Ocena każdego produktu (zdjęcie + nazwa), raz na zawsze. Rodzaj hasła równolegle.
    klasyfikacja, nieocenione = "slowa", 0
    if produkty and klasyfikator.dostepny():
        f_haslo = PULA.submit(klasyfikator.rodzaj_hasla, q)
        ocenione = klasyfikator.klasyfikuj(produkty, maks=400)
        try:
            r_hasla = f_haslo.result(timeout=40)
        except Exception:
            r_hasla = None
        nieocenione = len(produkty) - ocenione
        if ocenione:
            klasyfikacja = "ai"
            produkty = [p for p in produkty if nadzor.zgodna_plec(p, dzial)
                        and (not p.get("klasa") or klasyfikator.zgodny_rodzaj(r_hasla, p["klasa"]["r"]))]
    else:
        produkty = [p for p in produkty if nadzor.zgodna_plec(p, dzial)]
    pominiete = 0
    if okazja:
        wyk = wykluczone()
        zostaja = []
        for p in produkty:
            if klasyfikacja == "ai" and not p.get("klasa"):
                continue  # jeszcze nieoceniona: nie pokazujemy (wynik nie trafi do pamięci, następne wyszukiwanie oceni resztę)
            werdykt, powod = nadzor.decyzja(p, okazja, wyk)
            if werdykt == "nie":
                pominiete += 1
                continue
            p["punkty"] = nadzor.punkty(p, okazja)
            zostaja.append(p)
        produkty = zostaja
    wynik = {"zapytanie": q, "dzial": dzial, "czas": round(time.time() - t0, 1), "sprawdzono": int(time.time()),
             "sklepy": sklepy, "produkty": sorted(produkty, key=lambda p: -p.get("punkty", 0)),
             "okazja": OKAZJE.get(okazja, ""), "pominiete": pominiete, "nieocenione": nieocenione,
             "klasyfikacja": klasyfikacja}
    # Bez pełnej oceny nie zapamiętujemy wyniku na 12 godzin, żeby następne wyszukiwanie spróbowało ocenić resztę.
    if produkty and (nieocenione == 0 or not klasyfikator.dostepny()):
        pamiec_zapisz(klucz, wynik)
    return wynik


# Ocena w tle: raz na dobę popularne hasła (bez Google Shopping, żeby nie zużywać kredytów), żeby wyszukiwania były szybkie.
# Tylko rozgrzewka ma własny hamulec (do 0,1 USD na noc i do 30% budżetu miesięcznego), wyszukiwania użytkowników nie mają limitu dziennego.
ROZGRZEWKA = {
    "damskie": ["sukienka", "bluzka", "koszula", "spódnica", "spodnie", "jeansy", "marynarka", "sweter", "płaszcz", "kurtka",
                "kombinezon", "szpilki", "botki", "kozaki", "sneakersy", "torebka", "t-shirt", "kardigan", "sukienka wieczorowa",
                "sukienka na wesele", "bluzka satynowa", "spodnie skórzane", "czółenka", "baleriny"],
    "meskie": ["koszula", "marynarka", "garnitur", "spodnie", "jeansy", "sweter", "golf", "płaszcz", "kurtka", "polo", "t-shirt",
               "bluza", "półbuty", "mokasyny", "sneakersy", "sztyblety", "chinosy", "kamizelka"],
}


def rozgrzewka():
    time.sleep(120)
    while True:
        if klasyfikator.dostepny():
            dzien = time.strftime("rozgrzewka-%Y-%m-%d")
            if not licznik(dzien):
                licznik(dzien, 1)
                bez_google = [l for l in LACZNIKI if l is not lacznik_google]
                for dzial, hasla in ROZGRZEWKA.items():
                    for q in hasla:
                        if klasyfikator.koszt_miesiac() >= klasyfikator.BUDZET * 0.3 or klasyfikator.koszt_dzis() >= 0.1:
                            break
                        try:
                            _, produkty = pobierz_produkty(q, dzial, bez_google)
                            klasyfikator.klasyfikuj(produkty, maks=400)
                        except Exception:
                            traceback.print_exc()
        time.sleep(1800)


class Obsluga(BaseHTTPRequestHandler):
    def _wyslij(self, kod, dane):
        b = json.dumps(dane, ensure_ascii=False).encode()
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        a = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path in ("/", "/zdrowie"):
                return self._wyslij(200, {"ok": True, "wersja": WERSJA, "laczniki": [l.NAZWA for l in LACZNIKI], "ai": klasyfikator.dostepny(),
                                      "sklepy_bezposrednio": sorted({s for l in LACZNIKI if l is not lacznik_google for s in getattr(l, "SKLEPY", [l.NAZWA])}),
                                          "google": lacznik_google.stan(), "ocena": klasyfikator.stan()})
            if u.path == "/szukaj":
                q = a.get("q", "").strip()
                if len(q) < 2:
                    return self._wyslij(400, {"blad": "Wpisz, czego szukasz."})
                dzial = "meskie" if a.get("dzial") == "meskie" else "damskie"
                return self._wyslij(200, szukaj(q, dzial, a.get("okazja", "")))
            if u.path == "/link":
                nazwa, sklep = a.get("nazwa", "")[:200], a.get("sklep", "")[:80]
                klucz = f"link|{nazwa.lower()}|{sklep.lower()}"
                zap = pamiec_czytaj(klucz, 7 * 86400)
                if zap:
                    return self._wyslij(200, zap)
                url, pewny = lacznik_google.link_do_sklepu(nazwa, sklep)
                wyn = {"url": url, "pewny": pewny} if url else {
                    "url": "https://www.google.com/search?q=" + quote_plus(f"{nazwa} {sklep}"), "pewny": False, "wyszukiwanie": True}
                if url:
                    pamiec_zapisz(klucz, wyn)
                return self._wyslij(200, wyn)
            if u.path == "/zglos":
                if licznik(time.strftime("zgloszenia-%Y-%m-%d"), 1) > 500:
                    return self._wyslij(429, {"blad": "Za dużo zgłoszeń dzisiaj."})
                ok = a.get("okazja", "") if a.get("okazja", "") in OKAZJE else ""
                with _baza_blokada:
                    DB.execute("INSERT INTO zgloszenia VALUES (?,?,?,?,?,?,?,?,?)", (int(time.time()), a.get("id", "")[:40], ok,
                               a.get("q", "")[:80], a.get("dzial", "")[:10], a.get("powod", "")[:80], a.get("nazwa", "")[:200],
                               a.get("sklep", "")[:80], a.get("zdjecie", "")[:400]))
                    DB.execute("DELETE FROM pamiec WHERE klucz LIKE 'szukaj|%'")  # wyniki od razu bez tej rzeczy
                    DB.commit()
                return self._wyslij(200, {"ok": True})
            if u.path == "/kontrola":
                return self._wyslij(200, {"wynik": json.loads(klasyfikator.ustawienie("kontrola_wynik") or "null"),
                                          "szczegoly": json.loads(klasyfikator.ustawienie("kontrola_szczegoly") or "[]")})
            if u.path == "/zgloszenia":
                with _baza_blokada:
                    r = DB.execute("SELECT * FROM zgloszenia ORDER BY czas DESC LIMIT 300").fetchall()
                pola = ["czas", "id", "okazja", "q", "dzial", "powod", "nazwa", "sklep", "zdjecie"]
                return self._wyslij(200, {"zgloszenia": [dict(zip(pola, x)) for x in r]})
            if u.path == "/logo":
                typ, dane = logo.logo(a.get("sklep", "")[:80])
                if not dane:
                    return self._wyslij(404, {"blad": "Brak logo."})
                self.send_response(200)
                self.send_header("Content-Type", typ)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "public, max-age=604800")
                self.send_header("Content-Length", str(len(dane)))
                self.end_headers()
                self.wfile.write(dane)
                return
            if u.path == "/historia":
                return self._wyslij(200, {"id": a.get("id"), "ceny": historia(a.get("id", ""))})
            return self._wyslij(404, {"blad": "Nie ma takiej ścieżki."})
        except Exception as e:
            traceback.print_exc()
            return self._wyslij(500, {"blad": str(e)[:120]})

    def log_message(self, fmt, *args):
        pass


def main():
    port = int(os.environ.get("PORT", "18890"))
    print(f"Trendo {WERSJA} nasłuchuje na 127.0.0.1:{port}", flush=True)
    threading.Thread(target=rozgrzewka, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", port), Obsluga).serve_forever()


if __name__ == "__main__":
    main()
