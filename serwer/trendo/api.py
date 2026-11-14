"""Trendo: serwer zbieracza. Uruchomienie: python -m trendo.api (port w zmiennej PORT, domyślnie 18890).
Endpointy (za Caddy pod /trendo-api/):
  GET /zdrowie                    stan łączników i konta Google Shopping
  GET /szukaj?q=...&dzial=damskie produkty ze wszystkich łączników naraz
  GET /historia?id=...            historia ceny produktu z naszej bazy
"""
import json, os, time, traceback
from concurrent.futures import ThreadPoolExecutor, wait
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import lacznik_google, lacznik_zara
from .wspolne import historia, pamiec_czytaj, pamiec_zapisz, weryfikuj, zapisz_cene

WERSJA = "0.3.1"
LACZNIKI = [lacznik_zara, lacznik_google]
PULA = ThreadPoolExecutor(max_workers=8)
WIEK_PAMIECI = 6 * 3600


def szukaj(q, dzial):
    q = " ".join(q.split())[:80]
    klucz = f"szukaj|{WERSJA}|{q.lower()}|{dzial}"
    zap = pamiec_czytaj(klucz, WIEK_PAMIECI)
    if zap:
        zap["z_pamieci"] = True
        return zap
    t0 = time.time()
    zad = {PULA.submit(l.szukaj, q, dzial): l.NAZWA for l in LACZNIKI}
    gotowe, _ = wait(zad, timeout=50)
    sklepy, produkty, widziane = [], [], set()
    wlasne = {l.NAZWA.lower() for l in LACZNIKI if l is not lacznik_google}
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
            widziane.add(k)
            zapisz_cene(p)
            p["weryf"] = weryfikuj(p)
            produkty.append(p); ile += 1
        sklepy.append({"nazwa": nazwa, "stan": stan, "ile": ile})
    wynik = {"zapytanie": q, "dzial": dzial, "czas": round(time.time() - t0, 1), "sprawdzono": int(time.time()),
             "sklepy": sklepy, "produkty": produkty}
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
                return self._wyslij(200, {"ok": True, "wersja": WERSJA, "laczniki": [l.NAZWA for l in LACZNIKI],
                                          "google": lacznik_google.stan()})
            if u.path == "/szukaj":
                q = a.get("q", "").strip()
                if len(q) < 2:
                    return self._wyslij(400, {"blad": "Wpisz, czego szukasz."})
                dzial = "meskie" if a.get("dzial") == "meskie" else "damskie"
                return self._wyslij(200, szukaj(q, dzial))
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
