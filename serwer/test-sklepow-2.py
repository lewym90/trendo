#!/usr/bin/env python3
"""Trendo: drugi test sklepów. Niczego nie instaluje i niczego nie zmienia na serwerze.
Dla każdego sklepu sprawdza trzy drogi do produktów:
  1. robots.txt i mapa strony (sitemap) - lista adresów produktów,
  2. strona pojedynczego produktu - czy widać cenę (dane strukturalne),
  3. wynik ogólny: TAK (czytamy bezpośrednio) / CZESC / NIE (trzeba innej drogi).
Wynik zapisuje też do ~/trendo-test2.txt.
"""
import gzip, json, os, re, subprocess, sys, time

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
NAGL = ["-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H", "Accept-Language: pl-PL,pl;q=0.9,en;q=0.7",
        "-H", "Upgrade-Insecure-Requests: 1",
        "-H", 'sec-ch-ua: "Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "-H", "sec-ch-ua-mobile: ?0", "-H", 'sec-ch-ua-platform: "Windows"',
        "-H", "Sec-Fetch-Dest: document", "-H", "Sec-Fetch-Mode: navigate", "-H", "Sec-Fetch-Site: none", "-H", "Sec-Fetch-User: ?1"]

SKLEPY = [
 ("Zara", ["https://www.zara.com"]), ("H&M", ["https://www2.hm.com"]), ("Reserved", ["https://www.reserved.com"]),
 ("Mohito", ["https://www.mohito.com"]), ("Sinsay", ["https://www.sinsay.com"]), ("House", ["https://www.housebrand.com"]),
 ("Cropp", ["https://www.cropp.com"]), ("Mango", ["https://shop.mango.com"]), ("Bershka", ["https://www.bershka.com"]),
 ("Stradivarius", ["https://www.stradivarius.com"]), ("Pull&Bear", ["https://www.pullandbear.com"]), ("Massimo Dutti", ["https://www.massimodutti.com"]),
 ("Oysho", ["https://www.oysho.com"]), ("COS", ["https://www.cos.com"]), ("Arket", ["https://www.arket.com"]),
 ("& Other Stories", ["https://www.stories.com"]), ("Weekday", ["https://www.weekday.com"]), ("C&A", ["https://www.c-and-a.com"]),
 ("Zalando", ["https://www.zalando.pl"]), ("Answear", ["https://answear.com"]), ("Modivo", ["https://modivo.pl"]),
 ("eobuwie", ["https://www.eobuwie.com.pl"]), ("About You", ["https://www.aboutyou.pl"]), ("Born2Be", ["https://born2be.pl"]),
 ("Renee", ["https://renee.pl"]), ("Showroom", ["https://www.showroom.pl"]), ("Vitkac", ["https://www.vitkac.com"]),
 ("Moliera2", ["https://www.moliera2.com"]), ("Ochnik", ["https://ochnik.com"]), ("Wittchen", ["https://www.wittchen.com"]),
 ("Vistula", ["https://vistula.pl"]), ("Bytom", ["https://bytom.com.pl"]), ("Wolczanka", ["https://wolczanka.pl"]),
 ("Pako Lorente", ["https://pakolorente.pl", "https://www.pakolorente.pl"]), ("Recman", ["https://recman.pl"]), ("Medicine", ["https://wearmedicine.com"]),
 ("Top Secret", ["https://www.topsecret.pl"]), ("Diverse", ["https://www.diverse.pl", "https://diverse.pl", "https://www.diverse.com.pl"]),
 ("Big Star", ["https://www.bigstar.pl", "https://bigstar.pl"]), ("Tatuum", ["https://tatuum.com"]),
 ("Monnari", ["https://www.monnari.pl", "https://monnari.pl", "https://www.monnari.com"]), ("Molton", ["https://molton.pl"]),
 ("Bialcon", ["https://www.bialcon.pl"]), ("Quiosque", ["https://www.quiosque.pl"]), ("Kazar", ["https://www.kazar.com"]),
 ("Rylko", ["https://rylko.com"]), ("Badura", ["https://www.badura.pl", "https://badura.pl", "https://www.badura.com.pl"]),
 ("Lancerto", ["https://lancerto.com"]), ("Bizuu", ["https://bizuu.com"]), ("CCC", ["https://ccc.eu"]),
 ("Deichmann", ["https://www.deichmann.com"]), ("4F", ["https://4f.com.pl"]), ("Nike", ["https://www.nike.com"]),
 ("Adidas", ["https://www.adidas.pl"]), ("Sizeer", ["https://sizeer.com"]), ("50style", ["https://50style.pl"]),
 ("Decathlon", ["https://www.decathlon.pl"]), ("Levi's", ["https://www.levi.com"]), ("Tommy Hilfiger", ["https://pl.tommy.com"]),
 ("Calvin Klein", ["https://www.calvinklein.pl"]), ("Guess", ["https://www.guess.eu"]), ("Vinted", ["https://www.vinted.pl"]),
 ("Allegro", ["https://allegro.pl"]), ("Ceneo", ["https://www.ceneo.pl"]),
]

def pobierz(url, limit=4_000_000):
    """Zwraca (kod, bajty). Kod 0 = brak połączenia."""
    try:
        r = subprocess.run(["curl", "-sS", "-L", "--compressed", "--http2", "--max-time", "25", "--max-filesize", str(limit),
                            "-A", UA, *NAGL, "-w", "\n%{http_code}", url], capture_output=True, timeout=40)
        dane = r.stdout
        i = dane.rfind(b"\n")
        kod = int(dane[i + 1:].strip() or 0)
        tresc = dane[:i]
        if tresc[:2] == b"\x1f\x8b":
            try: tresc = gzip.decompress(tresc)
            except Exception: pass
        return kod, tresc
    except Exception:
        return 0, b""

BLOKADY = re.compile(rb"(px-captcha|_Incapsula_|datadome|cf-chl|Pardon Our Interruption|Access Denied|Request unsuccessful|challenge-platform|/_sec/cp_challenge|akamai-bm|bm-verify)", re.I)
PROD_URL = re.compile(r"(product|produkt|/p/|-p\d|/\d{6,}|\.html$|/prod)", re.I)

def ma_cene(html):
    t = html.decode("utf-8", "ignore")
    for blok in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', t, re.S | re.I):
        if re.search(r'"@type"\s*:\s*"Product"', blok) and re.search(r'"price"\s*:', blok):
            return "ld+json"
    if re.search(r'property="(product:price:amount|og:price:amount)"', t): return "meta"
    if re.search(r'itemprop="price"', t): return "microdata"
    if re.search(r'"price"\s*:\s*"?\d', t) and re.search(r'(PLN|zł)', t): return "json"
    return ""

def mapa(baza):
    """Szuka adresów produktów w sitemapach."""
    kod, robots = pobierz(baza + "/robots.txt", 500_000)
    mapy = re.findall(rb"(?im)^\s*sitemap:\s*(\S+)", robots) if kod == 200 else []
    mapy = [m.decode() for m in mapy] or [baza + "/sitemap.xml"]
    # najpierw mapy polskie / produktowe
    mapy.sort(key=lambda u: (0 if re.search(r"(pl|polska|poland)", u, re.I) else 1, 0 if re.search(r"prod", u, re.I) else 1))
    for m in mapy[:6]:
        k, x = pobierz(m)
        if k != 200 or not x: continue
        loc = re.findall(rb"<loc>\s*([^<\s]+)\s*</loc>", x)
        if not loc: continue
        loc = [l.decode("utf-8", "ignore") for l in loc]
        if b"<sitemapindex" in x[:3000] or all(l.endswith((".xml", ".xml.gz")) for l in loc[:20]):
            loc.sort(key=lambda u: (0 if re.search(r"(/pl|pl[_-]|_pl|poland)", u, re.I) else 1, 0 if re.search(r"prod", u, re.I) else 1))
            for pod in loc[:5]:
                k2, y = pobierz(pod)
                if k2 != 200: continue
                l2 = [l.decode("utf-8", "ignore") for l in re.findall(rb"<loc>\s*([^<\s]+)\s*</loc>", y)]
                prod = [u for u in l2 if PROD_URL.search(u)]
                if prod: return kod, len(l2), prod
        else:
            prod = [u for u in loc if PROD_URL.search(u)]
            if prod: return kod, len(loc), prod
    return kod, 0, []

def main():
    wyniki = []
    print("Sprawdzam %d sklepów, to potrwa kilka minut...\n" % len(SKLEPY))
    print("%-16s %-7s %-7s %-9s %s" % ("SKLEP", "ROBOTS", "MAPA", "PRODUKT", "WYNIK"))
    for nazwa, adresy in SKLEPY:
        rob, ile, prod, kodp, cena, baza = 0, 0, [], 0, "", adresy[0]
        for baza in adresy:
            rob, ile, prod = mapa(baza)
            if rob: break
        if prod:
            for u in prod[:3]:
                kodp, html = pobierz(u)
                if kodp == 200 and not BLOKADY.search(html[:200000]) and len(html) > 5000:
                    cena = ma_cene(html)
                    if cena: break
        if cena: wynik = "TAK (" + cena + ")"
        elif prod: wynik = "CZESC (mapa jest, strona produktu %s)" % (kodp or "bez odpowiedzi")
        elif rob: wynik = "NIE (brak mapy produktów)"
        else: wynik = "NIE (brak połączenia)"
        linia = "%-16s %-7s %-7s %-9s %s" % (nazwa[:16], rob or "-", ile or "-", kodp or "-", wynik)
        print(linia, flush=True); wyniki.append(linia)
        time.sleep(0.5)
    tak = sum(1 for w in wyniki if " TAK " in w); cz = sum(1 for w in wyniki if " CZESC " in w)
    podsum = "---\nRAZEM: %d | TAK: %d | CZESC: %d | NIE: %d" % (len(wyniki), tak, cz, len(wyniki) - tak - cz)
    print(podsum)
    with open(os.path.expanduser("~/trendo-test2.txt"), "w") as f:
        f.write("\n".join(wyniki) + "\n" + podsum + "\n")

if __name__ == "__main__":
    main()
