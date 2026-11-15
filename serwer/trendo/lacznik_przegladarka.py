"""Sklepy, które wpuszczają tylko prawdziwą przeglądarkę (zapora antybotowa): Vinted i C&A.
Jedna przeglądarka na oba sklepy naraz; ciasteczka zapisywane na dysku, żeby zapora sprawdzała przeglądarkę
raz na jakiś czas, a nie przy każdym wyszukiwaniu (Vinted: pierwsze wejście ok. 10 s, kolejne ok. 2 s).
Obrazki, filmy i czcionki są blokowane: szybciej i mniej pamięci."""
import html
import os
import re
from urllib.parse import quote

from .wspolne import DANE, PRZEGLADARKA, UA, liczba, pasuje_dzial, produkt

NAZWA = "Sklepy (przeglądarka)"
SKLEPY = ["Vinted", "C&A"]
STAN = os.path.join(DANE, "przegladarka-ciasteczka.json")
VINTED_KAT = {"damskie": "1904", "meskie": "5"}  # Kobiety / Mężczyźni (bez dziecięcych)
CA_HASH = "6441fc8623709091c2d6143c0df9bcdadf29db1abeafc4d2f606b73b3522bda7"  # zapytanie wyszukiwarki C&A (z ich strony)


def _vinted(ctx, q, dzial):
    pg = ctx.new_page()
    try:
        pg.goto(f"https://www.vinted.pl/catalog?search_text={quote(q)}&catalog[]={VINTED_KAT[dzial]}",
                timeout=40000, wait_until="domcontentloaded")
        try:
            pg.wait_for_selector('[data-testid$="--overlay-link"]', timeout=20000)
        except Exception:
            # pierwsze wejście: zapora sprawdza przeglądarkę i czasem nie zdąży; druga próba ma już ciasteczko
            try:
                pg.reload(timeout=40000, wait_until="domcontentloaded")
                pg.wait_for_selector('[data-testid$="--overlay-link"]', timeout=20000)
            except Exception:
                return [], "brak wyników albo zapora"
        t = pg.content()
    finally:
        pg.close()
    wyn = []
    for m in re.finditer(r'<a href="(/items/[^"?]+)[^"]*"[^>]*data-testid="product-item-id-(\d+)--overlay-link" title="([^"]+)"', t):
        href, pid_, opis = m.group(1), m.group(2), html.unescape(m.group(3))
        # „Nazwa, Marka: X, Stan: Y, Rozmiar: Z, 25.00 zł, 29.15 zł” (druga kwota: z ochroną kupującego)
        c = re.findall(r"([\d\s.,]+) zł", opis)
        if not c:
            continue
        cena = liczba(c[-1])
        nazwa = re.split(r", (?:Marka|Stan|Rozmiar): ", opis)[0].strip()
        marka = re.search(r", Marka: ([^,]+)", opis)
        stan = re.search(r", Stan: ([^,]+)", opis)
        rozm = re.search(r", Rozmiar: ([^,]+)", opis)
        img = re.search(rf'data-testid="product-item-id-{pid_}--image--img"', t)
        foto = None
        if img:
            przed = t[max(0, img.start() - 900):img.start()]
            f = re.findall(r'<img src="(https://images\d*\.vinted\.net/[^"]+)"', przed)
            foto = html.unescape(f[-1]) if f else None
        if not cena or not nazwa:
            continue
        wyn.append(produkt("Vinted", nazwa[:1].upper() + nazwa[1:] + (f" ({marka.group(1)})" if marka else ""), cena,
                           "https://www.vinted.pl" + href, foto, zrodlo="sklep", dzial=dzial,
                           extra={"uzywany": True, "stan": stan.group(1) if stan else None,
                                  "rozmiary": [rozm.group(1)] if rozm else None, "plec_sklepu": dzial,
                                  "cena_bez_oplat": liczba(c[0]) if len(c) > 1 else None}))
    return wyn, "ok"


def _ca_foto(v):
    im = v.get("modelImage") or v.get("variantImage") or {}
    plik = im.get("file") or ""
    if "/" not in plik:
        return None
    wer, nazwa = plik.split("/", 1)
    return f"https://www.c-and-a.com/img/product/q_auto:good,b_rgb:f9f8f2,c_scale,w_600/{wer}{im.get('folder') or '/productimages'}/{nazwa}"


def _ca(ctx, q, dzial):
    pg = ctx.new_page()
    try:
        with pg.expect_response(lambda r: "o=searchPageSearch" in r.url, timeout=30000) as odp:
            pg.goto(f"https://www.c-and-a.com/pl/pl/shop/search?q={quote(q)}", timeout=40000, wait_until="domcontentloaded")
        d = ((odp.value.json() or {}).get("data") or {}).get("search") or {}
    except Exception:
        return [], "brak odpowiedzi wyszukiwarki"
    finally:
        pg.close()
    cyfra = "2" if dzial == "meskie" else "1"  # kategoria: 1 = kobiety, 2 = mężczyźni, inne = dzieci
    wyn = []
    for x in d.get("products") or []:
        if not (x.get("categoryIpimId") or "").startswith(cyfra + "-"):
            continue
        v = (x.get("variants") or [{}])[0]
        c = v.get("price") or {}
        cena = c.get("grossPrice")
        if not cena or not v.get("uri") or not pasuje_dzial(x.get("name", ""), dzial):
            continue
        stara = c.get("strikePrice")
        wyn.append(produkt("C&A", x.get("name", ""), cena, "https://www.c-and-a.com" + v["uri"], _ca_foto(v),
                           stara=(stara if stara and stara > cena else None), zrodlo="sklep", dzial=dzial,
                           extra={"omnibus": c.get("lowestPrice30Days"), "plec_sklepu": dzial,
                                  "rozmiary": [s.get("label") for s in v.get("sizes") or [] if s.get("isAvailable")] or None,
                                  "kolor": (v.get("color") or {}).get("label")}))
    return wyn, "ok"


def szukaj(q, dzial):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return [], "brak przeglądarki na serwerze"
    if not PRZEGLADARKA.acquire(timeout=25):
        return [], "przeglądarka zajęta (znaki sklepów albo trendy)"
    wyn, stany = [], []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            try:
                ctx = b.new_context(locale="pl-PL", user_agent=UA, viewport={"width": 1280, "height": 900},
                                    storage_state=STAN if os.path.exists(STAN) else None)
                ctx.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image", "media", "font") else r.continue_())
                for nazwa, f in (("Vinted", _vinted), ("C&A", _ca)):
                    try:
                        lista, stan = f(ctx, q, dzial)
                    except Exception as e:
                        lista, stan = [], "błąd: " + str(e)[:50]
                    wyn += lista
                    if stan != "ok":
                        stany.append(f"{nazwa}: {stan}")
                try:
                    ctx.storage_state(path=STAN)
                except Exception:
                    pass
            finally:
                b.close()
    except Exception as e:
        return wyn, "błąd przeglądarki: " + str(e)[:60]
    finally:
        PRZEGLADARKA.release()
    return wyn, ("ok" if not stany else "; ".join(stany))
