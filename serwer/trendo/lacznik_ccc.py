"""Łącznik CCC. Wyszukiwarka sklepu (api/Search/Search) wymaga tokenu gościa: ciasteczka „anon”, które strona
dostaje przy pierwszym wejściu. Pobieramy je raz prawdziwą przeglądarką (ważne długo, zapisane na dysku),
a potem pytamy zwykłym, szybkim zapytaniem. Gdy sklep odrzuci token (407), pobieramy nowy."""
import json
import os
import threading
from urllib.parse import quote

from .wspolne import DANE, PRZEGLADARKA, UA, pobierz, produkt

NAZWA = "CCC"
SKLEPY = ["CCC"]
PLIK = os.path.join(DANE, "ccc-ciasteczka.json")
_blokada = threading.Lock()
DZIAL = {"damskie": ("damskie", "Kobiety"), "meskie": ("męskie", "Mężczyźni")}


def _ciasteczka(nowe=False):
    with _blokada:
        if not nowe and os.path.exists(PLIK):
            try:
                return json.load(open(PLIK))
            except Exception:
                pass
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            return None
        if not PRZEGLADARKA.acquire(timeout=25):
            return None
        try:
            with sync_playwright() as p:
                b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                try:
                    ctx = b.new_context(locale="pl-PL", user_agent=UA)
                    ctx.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image", "media", "font") else r.continue_())
                    pg = ctx.new_page()
                    pg.goto("https://ccc.eu/pl/pl/", timeout=40000, wait_until="domcontentloaded")
                    for _ in range(20):
                        if any(c["name"] == "anon" for c in ctx.cookies()):
                            break
                        pg.wait_for_timeout(500)
                    ck = {c["name"]: c["value"] for c in ctx.cookies() if "ccc" in c["domain"]}
                finally:
                    b.close()
        except Exception:
            return None
        finally:
            PRZEGLADARKA.release()
        if "anon" not in ck:
            return None
        with open(PLIK, "w") as f:
            json.dump(ck, f)
        return ck


def _zapytanie(q, ck):
    fa = quote(json.dumps({"filterAttributeOptions": []}, separators=(",", ":")))
    url = (f"https://ccc.eu/pl/api/Search/Search?searchText={quote(q)}&filterAttributes={fa}&page=1&pageSize=60"
           f"&language=pl_PL&listingName=allproducts&ClientUUID=")
    return pobierz(url, {"x-api-version": "4.0", "x-frontend-id": "44", "x-source-name": "WWW", "x-is-user-logged": "false",
                         "Accept": "application/json", "Cookie": "; ".join(f"{k}={v}" for k, v in ck.items())})


def szukaj(q, dzial):
    slowo, kat = DZIAL[dzial]
    ck = _ciasteczka()
    if not ck:
        return [], "brak tokenu sklepu"
    kod, b = _zapytanie(f"{q} {slowo}", ck)
    if kod == 407:  # token wygasł
        ck = _ciasteczka(nowe=True)
        if not ck:
            return [], "brak tokenu sklepu"
        kod, b = _zapytanie(f"{q} {slowo}", ck)
    if kod != 200:
        return [], f"brak odpowiedzi ({kod})"
    try:
        lista = (json.loads(b.decode("utf-8", "ignore")).get("data") or {}).get("products") or []
    except Exception:
        return [], "nieczytelne dane"
    wyn = []
    for x in lista:
        if ((x.get("categoryTree") or {}).get("itemCategory")) != kat or not x.get("slug"):
            continue
        c = x.get("price") or {}
        cena = c.get("priceWithDiscount") or c.get("price")
        if not cena:
            continue
        stara = c.get("price")
        om = (c.get("omnibusPrice") or {}).get("price")
        nazwa = " ".join(w for w in (x.get("name"), x.get("trademark"), (x.get("color") or "").lower()) if w)
        wyn.append(produkt("CCC", nazwa, cena, "https://ccc.eu/pl/pl/p/" + x["slug"], (x.get("photos") or [None])[0],
                           stara=(stara if stara and stara > cena + 0.01 else None), zrodlo="sklep", dzial=dzial,
                           extra={"omnibus": om if stara and stara > cena + 0.01 else None, "plec_sklepu": dzial,
                                  "kolor": x.get("color")}))
    return wyn, "ok"
