"""Trendo: serwer zbieracza. Uruchomienie: python -m trendo.api (port w zmiennej PORT, domyślnie 18890).
Endpointy (za Caddy pod /trendo-api/):
  GET /zdrowie                    stan łączników i konta Google Shopping
  GET /szukaj?q=...&dzial=damskie produkty ze wszystkich łączników naraz
  GET /historia?id=...            historia ceny produktu z naszej bazy
"""
import json, os, re, time, traceback
from concurrent.futures import ThreadPoolExecutor, wait
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote_plus, urlparse

from . import klasyfikator, lacznik_google, lacznik_lpp, lacznik_modivo, lacznik_strony, lacznik_zara, ocena_ai
from .wspolne import historia, pamiec_czytaj, pamiec_zapisz, weryfikuj, zapisz_cene

WERSJA = "0.6.0"
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


# Okazje: czego na pewno nie pokazywać i co premiować. Słowa szukane w nazwie i opisie produktu (małe litery).
NIEFORMALNE = ["coca", "cola", "pepsi", "disney", "marvel", "star wars", "harry potter", "hello kitty", "z motywem", "motyw ",
               "logo", "napis", "retro print", "palm", "hawaj", "plaż", "plaz", "tropik", "flaming", "dres", "sportow", "jogger", "bojówk", "cargo",
               "z kapturem", "kapturem", "nadruk", "print", "graficzn", "dziur", "przetarc", "ripped", "kąpiel", "piżam",
               "polar", "trekking", "biegow", "treningow", "kraciaste szorty", "szorty", "klapk", "japonk", "crocs",
               "coca", "cola", "logo", "disney", "marvel", "myszk", "licencj", "napis", "motyw", "komiks", "anime", "pepsi"]
ELEGANCKIE = ["elegan", "wizytow", "satyn", "jedwab", "smoking", "garnitur", "koronk", "aksamit", "welur", "wełn",
              "kaszmir", "slim", "gładk", "klasycz", "taliowan", "marynar", "szpilk", "lakierk", "oxford", "derby"]
OKAZJE = {
    "wieczor": {"nazwa": "Wieczór", "nie": NIEFORMALNE + ["krótkim rękaw", "krótki rękaw", "lnian", "lnu", "flanel", "jeans", "denim", "krat", "wzorzyst", "kolorow", "w paski", "workowat"],
                "tak": ELEGANCKIE + ["cekin", "brokat", "czarn"]},
    "wesele": {"nazwa": "Wesele", "nie": NIEFORMALNE + ["krótkim rękaw", "krótki rękaw", "lnian", "lnu", "flanel", "jeans", "denim", "sneaker", "trampk", "krat", "wzorzyst", "w paski", "workowat"],
               "tak": ELEGANCKIE},
    "sylwester": {"nazwa": "Sylwester", "nie": NIEFORMALNE + ["lnian", "flanel"], "tak": ELEGANCKIE + ["cekin", "brokat", "metaliczn", "złot", "srebrn"]},
    "randka": {"nazwa": "Randka", "nie": NIEFORMALNE, "tak": ELEGANCKIE + ["koronk"]},
    "praca": {"nazwa": "Praca", "nie": NIEFORMALNE + ["cekin", "brokat", "prześwit", "crop", "mini "], "tak": ["biur", "klasycz", "wizytow", "oxford", "garnitur", "marynar", "gładk", "slim", "taliowan"]},
}


def ocen_okazje(p, okazja):
    """Zwraca None, gdy produkt nie pasuje do okazji, inaczej liczbę punktów (więcej = lepiej)."""
    o = OKAZJE.get(okazja)
    if not o:
        return 0
    t = (p["nazwa"] + " " + (p.get("material") or "")).lower()
    if any(x in t for x in o["nie"]):
        return None
    return sum(1 for x in o["tak"] if x in t)


def szukaj(q, dzial, okazja=""):
    q = " ".join(q.split())[:80]
    okazja = okazja if okazja in OKAZJE else ""
    klucz = f"szukaj|{WERSJA}|{q.lower()}|{dzial}|{okazja}"
    zap = pamiec_czytaj(klucz, WIEK_PAMIECI)
    if zap:
        zap["z_pamieci"] = True
        return zap
    t0 = time.time()
    zad = {PULA.submit(l.szukaj, q, dzial): l.NAZWA for l in LACZNIKI}
    gotowe, _ = wait(zad, timeout=55)
    sklepy, produkty, widziane, pominiete = [], [], set(), 0
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
            pkt = ocen_okazje(p, okazja)
            if pkt is None:
                pominiete += 1
                continue
            p["punkty"] = pkt
            widziane.add(k)
            zapisz_cene(p)
            p["weryf"] = weryfikuj(p)
            produkty.append(p); ile += 1
        sklepy.append({"nazwa": nazwa, "stan": stan, "ile": ile})
    ocena_stan = ""
    if okazja and produkty:
        kandydaci = sorted(produkty, key=lambda p: -p.get("trafnosc", 2))[:150]
        oceny, ocena_stan = ocena_ai.ocen(kandydaci, okazja, dzial, q)
        if oceny:
            zostaw = []
            for p in kandydaci:
                w = oceny.get(p["id"])
                if w is None:
                    continue  # bez oceny nie pokazujemy w trybie okazji
                if not w[0]:
                    pominiete += 1
                    continue
                p["punkty"] = w[1]
                zostaw.append(p)
            pominiete += len(produkty) - len(kandydaci)
            produkty = zostaw
    # Ocena AI (rodzaj, dla kogo, elegancja, okazje) na podstawie tego, co podał sklep.
    klasyfikacja = "slowa"
    if produkty and klasyfikator.dostepny():
        f_haslo = PULA.submit(klasyfikator.rodzaj_hasla, q)
        ocenione = klasyfikator.klasyfikuj(produkty)
        try:
            r_hasla = f_haslo.result(timeout=30)
        except Exception:
            r_hasla = None
        if ocenione:
            klasyfikacja = "ai"
            zostaja = []
            for p in produkty:
                k = p.get("klasa")
                if not k:
                    zostaja.append(p); continue
                if k["p"] == "dzieciece" or (dzial == "damskie" and k["p"] == "meskie") or (dzial == "meskie" and k["p"] == "damskie"):
                    continue
                if not klasyfikator.zgodny_rodzaj(r_hasla, k["r"]):
                    continue
                if okazja:
                    if okazja not in k["o"]:
                        pominiete += 1
                        continue
                    p["punkty"] = k["f"] if okazja in ("wieczor", "wesele", "sylwester", "praca", "randka") else 0
                zostaja.append(p)
            produkty = zostaja
    wynik = {"zapytanie": q, "dzial": dzial, "ocena_ai": ocena_stan, "czas": round(time.time() - t0, 1), "sprawdzono": int(time.time()),
             "sklepy": sklepy, "produkty": sorted(produkty, key=lambda p: -p.get("punkty", 0)),
             "okazja": OKAZJE[okazja]["nazwa"] if okazja else "", "pominiete": pominiete, "klasyfikacja": klasyfikacja}
    if produkty:
        pamiec_zapisz(klucz, wynik)
    return wynik


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
                                          "google": lacznik_google.stan()})
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
    ThreadingHTTPServer(("127.0.0.1", port), Obsluga).serve_forever()


if __name__ == "__main__":
    main()
