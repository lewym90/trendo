"""Łącznik Wittchen. Wyszukiwarka sklepu (Synerise) wymaga tokenu gościa ważnego godzinę, który wydaje skrypt strony.
Token przechwytujemy prawdziwą przeglądarką (ok. 5 s) i zapisujemy na dysku; dopóki jest ważny, pytamy zwykłym,
szybkim zapytaniem. Odnawiamy go dopiero przy wyszukiwaniu po wygaśnięciu."""
import base64
import json
import os
import threading
import time
from urllib.parse import quote

from .wspolne import DANE, PRZEGLADARKA, UA, liczba, pasuje_dzial, pobierz, produkt

NAZWA = "Wittchen"
SKLEPY = ["Wittchen"]
PLIK = os.path.join(DANE, "wittchen-token.json")
_blokada = threading.Lock()
PLEC = {"damskie": "female", "meskie": "male"}


def _wygasa(t):
    try:
        e = json.loads(base64.urlsafe_b64decode(t.split(".")[1] + "=="))["exp"]
        return e / 1000 if e > 1e11 else e
    except Exception:
        return 0


def _token(nowy=False):
    with _blokada:
        if not nowy and os.path.exists(PLIK):
            try:
                z = json.load(open(PLIK))
                if _wygasa(z["token"]) - time.time() > 120:
                    return z
            except Exception:
                pass
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            return None
        if not PRZEGLADARKA.acquire(timeout=25):
            return None
        z = {}
        try:
            with sync_playwright() as p:
                b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                try:
                    ctx = b.new_context(locale="pl-PL", user_agent=UA)
                    ctx.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image", "media", "font") else r.continue_())
                    pg = ctx.new_page()

                    def zad(r):
                        a = r.headers.get("authorization", "")
                        if "/ai/search/" in r.url and "/indices/" in r.url and a.startswith("Bearer "):
                            z["token"], z["indeks"] = a[7:], r.url.split("/indices/")[1].split("/")[0]
                    pg.on("request", zad)
                    pg.goto("https://www.wittchen.com/search?q=torebka", timeout=40000, wait_until="domcontentloaded")
                    for _ in range(40):
                        if z:
                            break
                        pg.wait_for_timeout(500)
                finally:
                    b.close()
        except Exception:
            return None
        finally:
            PRZEGLADARKA.release()
        if not z:
            return None
        with open(PLIK, "w") as f:
            json.dump(z, f)
        return z


def _zapytanie(q, z):
    url = f"https://smcr.wittchen.com/ai/search/v2/indices/{z['indeks']}/query?query={quote(q)}&limit=48&includeMeta=true&page=1"
    return pobierz(url, {"Authorization": "Bearer " + z["token"], "Accept": "application/json"})


def szukaj(q, dzial):
    z = _token()
    if not z:
        return [], "brak tokenu sklepu"
    kod, b = _zapytanie(q, z)
    if kod in (401, 403):
        z = _token(nowy=True)
        if not z:
            return [], "brak tokenu sklepu"
        kod, b = _zapytanie(q, z)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    try:
        lista = json.loads(b.decode("utf-8", "ignore")).get("data") or []
    except Exception:
        return [], "nieczytelne dane"
    wyn = []
    for x in lista:
        pl = x.get("gender") or ""
        if pl in ("female", "male") and pl != PLEC[dzial] or x.get("ageGroup") not in (None, "adult"):
            continue
        cena = liczba(x.get("effectivePrice")) or liczba((x.get("salePrice") or {}).get("value")) or liczba((x.get("price") or {}).get("value"))
        nazwa = x.get("title") or ""
        if not cena or not x.get("link") or not nazwa or not pasuje_dzial(nazwa, dzial):
            continue
        stara = liczba((x.get("price") or {}).get("value"))
        at = x.get("attributes") or {}
        om = liczba(at.get("omnibus"))
        wyn.append(produkt("Wittchen", nazwa, cena, x["link"], (x.get("imageLink") or "").replace("?s=2000", "?s=600") or None,
                           stara=(stara if stara and stara > cena + 0.01 else None), zrodlo="sklep", dzial=dzial,
                           extra={"omnibus": om if stara and stara > cena + 0.01 else None, "kolor": x.get("color"),
                                  "plec_sklepu": "damskie" if pl == "female" else "meskie" if pl == "male" else None}))
    return wyn, "ok"
