"""Kontrola jakości oceny produktów na zestawie wzorcowym (serwer/kontrola/zloty.json, produkty ocenione ręcznie).
Uruchomienie na serwerze:  cd /opt/trendo && /root/trendo-scraper/bin/python -m trendo.kontrola [--wybierz] [--model NAZWA]
  --wybierz  sprawdza kilka modeli Gemini i ustawia najlepszy (najmniej błędów, przy remisie tańszy),
  bez opcji sprawdza model, którego serwer używa teraz.
Błąd krytyczny = rzecz, która na daną okazję NIE pasuje, a trafiła do głównych wyników."""
import hashlib, json, os, sys, time
from . import klasyfikator, nadzor
from .wspolne import plec_ze_sklepu

PLIK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kontrola", "zloty.json")


def produkty_wzorcowe():
    lista = json.load(open(PLIK, encoding="utf-8"))
    for e in lista:
        e["zrodlo"] = "sklep"
        e["plec_sklepu"] = plec_ze_sklepu(e, e["dzial"])
        e["id"] = "k-" + hashlib.sha1(f"{e['sklep']}|{e['nazwa']}|{e['zdjecie']}".encode()).hexdigest()[:14]
    return lista


def ocen_model(model, lista):
    for p in lista:
        p.pop("klasa", None)
    przed = klasyfikator.koszt_dzis()
    t0 = time.time()
    ile = klasyfikator.klasyfikuj(lista, maks=len(lista), swiezo=True, model=model, zapisuj=False)
    koszt = klasyfikator.koszt_dzis() - przed
    return podsumuj(model, lista, ile, koszt, round(time.time() - t0))


def podsumuj(model, lista, ile, koszt=0.0, czas=0):
    """Porównanie decyzji (aktualne zasady nadzoru) z wzorcem dla produktów z gotową oceną AI w p["klasa"]."""
    r = {"model": model, "ocenione": ile, "wszystkie": len(lista), "czas_s": czas, "koszt_usd": round(koszt, 3),
         "krytyczne": [], "ukryte_dobre": [], "plec": [], "trafione": 0, "sprawdzen": 0}
    for p in lista:
        k = p.get("klasa")
        if not k:
            continue
        dobra_plec = p["plec"] == p["dzial"] or p["plec"] == "unisex"
        pokazana = nadzor.zgodna_plec(p, p["dzial"])
        if dobra_plec != pokazana:
            zr = "sklep" if p.get("plec_sklepu") else "AI"
            r["plec"].append(f"{p['nazwa']} ({p['sklep']}): {zr} {nadzor.plec(p)}, powinno {p['plec']}"
                             f" ({'pokazane w złym dziale' if pokazana else 'ukryte'})")
        for okazja, ma_pasowac in p["oczekiwane"].items():
            w, powod = nadzor.decyzja(p, okazja)
            if not pokazana:
                w = "nie"
            if not dobra_plec:
                ma_pasowac = False
            r["sprawdzen"] += 1
            opis = f"{okazja}: {p['nazwa']} ({p['sklep']}) [{powod or 'AI: ' + ','.join(k['o'])}; wzór {k.get('wzor')}; f={k.get('f')}]"
            if not ma_pasowac and w == "tak":
                r["krytyczne"].append(opis)
            elif ma_pasowac and w == "nie":
                r["ukryte_dobre"].append(opis)
            else:
                r["trafione"] += 1
    nieocenione = len(lista) - ile
    r["punkty_karne"] = len(r["krytyczne"]) * 5 + len(r["plec"]) * 3 + len(r["ukryte_dobre"]) + nieocenione * 2
    r["szczegoly"] = [{"nr": p["nr"], "klasa": p.get("klasa")} for p in lista]
    return r


# Ta sama rzecz wpisana różnymi słowami musi dać to samo (rodzaj i cechy). Pola nieustawione = dowolne.
HASLA = [
    ("koszula w kratę", {"r": "koszula", "wzor_rodzaj": "krata"}),
    ("koszula w kratkę", {"r": "koszula", "wzor_rodzaj": "krata"}),
    ("kraciasta koszula", {"r": "koszula", "wzor_rodzaj": "krata"}),
    ("koszula w paski", {"r": "koszula", "wzor_rodzaj": "paski"}),
    ("koszula w paseczki", {"r": "koszula", "wzor_rodzaj": "paski"}),
    ("skórzane spodnie", {"r": "spodnie", "material": "skora"}),
    ("spodnie ze skóry", {"r": "spodnie", "material": "skora"}),
    ("spodnie skóra", {"r": "spodnie", "material": "skora"}),
    ("spodnie z ekoskóry", {"r": "spodnie", "material": "skora_ekologiczna"}),
    ("czarna polówka", {"r": "polo", "kolor": "czarny"}),
    ("polo czarne", {"r": "polo", "kolor": "czarny"}),
    ("koszulka polo czarna", {"r": "polo", "kolor": "czarny"}),
    ("sukienka w kwiaty", {"r": "sukienka", "wzor_rodzaj": "kwiaty"}),
    ("kwiecista sukienka", {"r": "sukienka", "wzor_rodzaj": "kwiaty"}),
    ("sukienka w kwiatki", {"r": "sukienka", "wzor_rodzaj": "kwiaty"}),
    ("biała koszula", {"r": "koszula", "kolor": "bialy_ecru"}),
    ("koszula biała", {"r": "koszula", "kolor": "bialy_ecru"}),
    ("dżinsy", {"r": "jeansy"}),
    ("jeansy", {"r": "jeansy"}),
    ("spodnie jeansowe", {"r": "jeansy"}),
    ("marynarka w pepitkę", {"r": "marynarka", "wzor_rodzaj": "jodelka_pepitka"}),
    ("sweter z kaszmiru", {"r": "sweter", "material": "welna_kaszmir"}),
    ("kaszmirowy sweter", {"r": "sweter", "material": "welna_kaszmir"}),
    ("satynowa sukienka", {"r": "sukienka", "material": "jedwab_satyna"}),
    ("sukienka z satyny", {"r": "sukienka", "material": "jedwab_satyna"}),
    ("botki", {"r": "botki"}),
    ("szpilki", {"r": "szpilki"}),
    ("trencz", {"r": "płaszcz"}),
]


def test_hasel(swiezo=True):
    bledy = []
    for q, oczek in HASLA:
        c = klasyfikator.cechy_hasla(q, swiezo=swiezo) or {}
        zle = {pole: (c.get(pole), w) for pole, w in oczek.items()
               if not (c.get(pole) == w or (pole == "r" and klasyfikator.zgodny_rodzaj(w, c.get(pole)) and klasyfikator.zgodny_rodzaj(c.get(pole), w)))}
        if zle:
            bledy.append(f"„{q}”: " + ", ".join(f"{p} = {a} (powinno {b})" for p, (a, b) in zle.items()))
    print(f"\n=== Rozumienie haseł (różne formy słów) ===\n  Zgodne: {len(HASLA) - len(bledy)} z {len(HASLA)}")
    for b in bledy:
        print("    -", b)
    return len(bledy)


def zapisz_przebieg(r):
    """Kolejne przebiegi (do 6) do kalibracji zasad na wielu odpowiedziach modelu naraz."""
    przebiegi = json.loads(klasyfikator.ustawienie("kontrola_przebiegi") or "[]")
    przebiegi = (przebiegi + [{"czas": int(time.time()), "model": r["model"], "szczegoly": r["szczegoly"]}])[-6:]
    klasyfikator.ustawienie("kontrola_przebiegi", json.dumps(przebiegi, ensure_ascii=False))


def drukuj(r):
    print(f"\n=== {r.get('model_opis', r['model'])} ===")
    if not r["ocenione"]:
        print("  Model nie odpowiada (brak dostępu albo nie istnieje).")
        return
    print(f"  Ocenione produkty: {r['ocenione']} z {r['wszystkie']}, czas {r['czas_s']} s, koszt {r['koszt_usd']} USD")
    print(f"  Zgodne z wzorcem: {r['trafione']} z {r['sprawdzen']} sprawdzeń")
    print(f"  BŁĘDY KRYTYCZNE (zła rzecz w głównych wynikach): {len(r['krytyczne'])}")
    for x in r["krytyczne"][:25]:
        print("    -", x)
    print(f"  Dobre rzeczy ukryte: {len(r['ukryte_dobre'])}")
    for x in r["ukryte_dobre"][:6]:
        print("    -", x)
    print(f"  Błędy płci: {len(r['plec'])}")
    for x in r["plec"][:8]:
        print("    -", x)
    print(f"  Punkty karne: {r['punkty_karne']} (mniej = lepiej)")


def zapisane_przebiegi(model):
    """Zapisane odpowiedzi modelu z poprzednich kontroli, aktualne dla obecnego polecenia (wersja oceny) i modelu."""
    try:
        przebiegi = json.loads(klasyfikator.ustawienie("kontrola_przebiegi") or "[]")
    except Exception:
        return []
    nr_wzorca = {p["nr"] for p in produkty_wzorcowe()}
    dobre = []
    for pr in przebiegi:
        kl = {x["nr"]: x["klasa"] for x in pr.get("szczegoly", []) if x.get("klasa")}
        if pr.get("model") == model and nr_wzorca <= set(kl) and all(k.get("v") == klasyfikator.OCENA_WERSJA for k in kl.values()):
            dobre.append(kl)
    return dobre


def odtworz(model, przebiegi):
    """Kontrola bez kosztów: zapisane odpowiedzi modelu + aktualne zasady nadzoru i wzorzec."""
    wyniki = []
    for kl in przebiegi:
        lista = [dict(p) for p in produkty_wzorcowe()]
        for p in lista:
            p["klasa"] = kl.get(p["nr"])
        wyniki.append(podsumuj(model, lista, sum(1 for p in lista if p.get("klasa"))))
    return wyniki


def main():
    if not klasyfikator.dostepny():
        print("Kontrola: brak klucza Gemini, pomijam.")
        return
    arg = sys.argv[1:]
    model_teraz = klasyfikator.ustawienie("model_ai")
    # Zasady nadzoru działają na zapisanych cechach, więc ich zmianę sprawdzamy za darmo na zapisanych odpowiedziach modelu.
    # Za model płacimy tylko, gdy zmieniło się to, co model dostaje (wersja polecenia albo model) albo na życzenie (--wymus).
    if model_teraz and not any(a in arg for a in ("--wymus", "--model", "--wybierz")):
        zap = zapisane_przebiegi(model_teraz)
        if len(zap) >= 2:
            wyniki = odtworz(model_teraz, zap)
            print(f"Kontrola jakości bez kosztów: aktualne zasady sprawdzone na {len(wyniki)} zapisanych przebiegach modelu {model_teraz}.")
            for i, r in enumerate(wyniki, 1):
                print(f"  Przebieg {i}: błędy krytyczne {len(r['krytyczne'])}, ukryte dobre {len(r['ukryte_dobre'])}, "
                      f"zgodne {r['trafione']} z {r['sprawdzen']}")
            naj = max(wyniki, key=lambda x: (len(x["krytyczne"]), x["punkty_karne"]))
            for x in sorted({o for r in wyniki for o in r["krytyczne"]})[:10]:
                print(f"    - {x}")
            bledy_hasel = test_hasel(swiezo=False)  # z pamięci: polecenie się nie zmieniło
            klasyfikator.ustawienie("kontrola_wynik", json.dumps({
                "czas": int(time.time()), "model": model_teraz, "krytyczne": len(naj["krytyczne"]), "sprawdzen": naj["sprawdzen"],
                "trafione": naj["trafione"], "ukryte_dobre": len(naj["ukryte_dobre"]), "plec": len(naj["plec"]),
                "hasla_bledy": bledy_hasel, "odtworzona": len(wyniki)}))
            if naj["krytyczne"]:
                print("\nUWAGA: są błędy krytyczne. Wklej ten wynik, poprawię zasady.")
            print(f"\nKONTROLA: najgorszy przebieg: błędy krytyczne {len(naj['krytyczne'])}, "
                  f"zgodność z wzorcem {round(100 * naj['trafione'] / max(1, naj['sprawdzen']))}%, hasła z błędami {bledy_hasel}.")
            return
    klasyfikator.BUDZET = max(klasyfikator.BUDZET, klasyfikator.koszt_miesiac() + 3.0)  # kontrola zawsze może się wykonać
    if "--model" in arg:
        modele = [arg[arg.index("--model") + 1]]
    elif "--wybierz" in arg or not klasyfikator.ustawienie("model_ai"):
        dostepne = set(klasyfikator.lista_modeli())
        modele = []
        for c in klasyfikator.KANDYDACI_TESTU:
            if not dostepne or c in dostepne:
                modele.append(c); continue
            podobne = sorted((m for m in dostepne if m.startswith(c) and not any(x in m for x in ("image", "tts", "audio", "live"))), key=len)
            if podobne:
                modele.append(podobne[0])
        if dostepne and not modele:
            modele = sorted((m for m in dostepne if "flash" in m and not any(x in m for x in ("image", "tts", "audio", "live"))), reverse=True)[:3]
    else:
        modele = [klasyfikator.ustawienie("model_ai")]
    lista = produkty_wzorcowe()
    print(f"Kontrola jakości: {len(lista)} produktów wzorcowych, modele: {', '.join(modele)}")
    wyniki = []
    # Model przy każdym pytaniu odpowiada odrobinę inaczej, więc sprawdzamy dwa niezależne przebiegi i liczymy gorszy.
    ile_przebiegow = 1 if len(modele) > 1 else 2
    for m in modele:
        przebiegi = []
        for nr in range(ile_przebiegow):
            r = ocen_model(m, [dict(p) for p in lista])
            if ile_przebiegow > 1:
                r["model_opis"] = f"{m}, przebieg {nr + 1}"
            drukuj(r)
            if r["ocenione"]:
                przebiegi.append(r)
                zapisz_przebieg(r)
        if przebiegi:
            wyniki.append(max(przebiegi, key=lambda x: (len(x["krytyczne"]), x["punkty_karne"])))
    if not wyniki:
        print("\nKONTROLA: żaden model nie odpowiedział. Sprawdź, czy płatności w Google AI Studio są aktywne.")
        return
    bledy_hasel = test_hasel()
    naj = min(wyniki, key=lambda r: (r["punkty_karne"], klasyfikator._cena(r["model"])))
    if len(modele) > 1 or not klasyfikator.ustawienie("model_ai"):
        klasyfikator.ustawienie("model_ai", naj["model"])
    klasyfikator.ustawienie("kontrola_szczegoly", json.dumps(naj["szczegoly"], ensure_ascii=False))
    klasyfikator.ustawienie("kontrola_wynik", json.dumps({
        "czas": int(time.time()), "model": naj["model"], "krytyczne": len(naj["krytyczne"]), "sprawdzen": naj["sprawdzen"],
        "trafione": naj["trafione"], "ukryte_dobre": len(naj["ukryte_dobre"]), "plec": len(naj["plec"]), "hasla_bledy": bledy_hasel}))
    if naj["krytyczne"]:
        print("\nUWAGA: są błędy krytyczne. Wklej ten wynik, poprawię zasady.")
    print(f"\nKONTROLA: model w użyciu: {naj['model']}. Błędy krytyczne: {len(naj['krytyczne'])}, "
          f"zgodność z wzorcem {round(100 * naj['trafione'] / max(1, naj['sprawdzen']))}%.")


if __name__ == "__main__":
    main()
