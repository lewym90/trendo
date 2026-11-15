"""Kontrola jakości oceny produktów na zestawie wzorcowym (serwer/kontrola/zloty.json, produkty ocenione ręcznie).
Uruchomienie na serwerze:  cd /opt/trendo && /root/trendo-scraper/bin/python -m trendo.kontrola [--wybierz] [--model NAZWA]
  --wybierz  sprawdza kilka modeli Gemini i ustawia najlepszy (najmniej błędów, przy remisie tańszy),
  bez opcji sprawdza model, którego serwer używa teraz.
Błąd krytyczny = rzecz, która na daną okazję NIE pasuje, a trafiła do głównych wyników."""
import hashlib, json, os, sys, time
from . import klasyfikator, nadzor

PLIK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kontrola", "zloty.json")


def produkty_wzorcowe():
    lista = json.load(open(PLIK, encoding="utf-8"))
    for e in lista:
        e["id"] = "k-" + hashlib.sha1(f"{e['sklep']}|{e['nazwa']}|{e['zdjecie']}".encode()).hexdigest()[:14]
    return lista


def ocen_model(model, lista):
    for p in lista:
        p.pop("klasa", None)
    przed = klasyfikator.koszt_dzis()
    t0 = time.time()
    ile = klasyfikator.klasyfikuj(lista, maks=len(lista), swiezo=True, model=model, zapisuj=False)
    koszt = klasyfikator.koszt_dzis() - przed
    r = {"model": model, "ocenione": ile, "wszystkie": len(lista), "czas_s": round(time.time() - t0), "koszt_usd": round(koszt, 3),
         "krytyczne": [], "w_moze_pasowac": [], "ukryte_dobre": [], "plec": [], "trafione": 0, "sprawdzen": 0}
    for p in lista:
        k = p.get("klasa")
        if not k:
            continue
        dobra_plec = p["plec"] == p["dzial"] or p["plec"] == "unisex"
        if nadzor.zgodna_plec(k, p["dzial"]) != dobra_plec:
            r["plec"].append(f"{p['nazwa']} ({p['sklep']}): AI {k['p']}, powinno {p['plec']}")
        for okazja, ma_pasowac in p["oczekiwane"].items():
            w, powod = nadzor.decyzja(p, okazja)
            if not dobra_plec:
                w = "nie"
            r["sprawdzen"] += 1
            opis = f"{okazja}: {p['nazwa']} ({p['sklep']}) [{powod or 'AI: ' + ','.join(k['o'])}; wzór {k.get('wzor')}; f={k.get('f')}]"
            if not ma_pasowac and w == "tak":
                r["krytyczne"].append(opis)
            elif not ma_pasowac and w == "moze":
                r["w_moze_pasowac"].append(opis)
            elif ma_pasowac and w == "nie":
                r["ukryte_dobre"].append(opis)
            else:
                r["trafione"] += 1
    nieocenione = len(lista) - ile
    r["punkty_karne"] = len(r["krytyczne"]) * 5 + len(r["plec"]) * 3 + len(r["w_moze_pasowac"]) + len(r["ukryte_dobre"]) + nieocenione * 2
    return r


def drukuj(r):
    print(f"\n=== {r['model']} ===")
    if not r["ocenione"]:
        print("  Model nie odpowiada (brak dostępu albo nie istnieje).")
        return
    print(f"  Ocenione produkty: {r['ocenione']} z {r['wszystkie']}, czas {r['czas_s']} s, koszt {r['koszt_usd']} USD")
    print(f"  Zgodne z wzorcem: {r['trafione']} z {r['sprawdzen']} sprawdzeń")
    print(f"  BŁĘDY KRYTYCZNE (zła rzecz w głównych wynikach): {len(r['krytyczne'])}")
    for x in r["krytyczne"][:25]:
        print("    -", x)
    print(f"  Złe rzeczy tylko w „Może pasować”: {len(r['w_moze_pasowac'])}")
    print(f"  Dobre rzeczy ukryte: {len(r['ukryte_dobre'])}")
    for x in r["ukryte_dobre"][:12]:
        print("    -", x)
    print(f"  Błędy płci: {len(r['plec'])}")
    for x in r["plec"][:8]:
        print("    -", x)
    print(f"  Punkty karne: {r['punkty_karne']} (mniej = lepiej)")


def main():
    if not klasyfikator.dostepny():
        print("Kontrola: brak klucza Gemini, pomijam.")
        return
    klasyfikator.BUDZET = max(klasyfikator.BUDZET, klasyfikator.koszt_miesiac() + 3.0)  # kontrola zawsze może się wykonać
    arg = sys.argv[1:]
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
    for m in modele:
        r = ocen_model(m, [dict(p) for p in lista])
        drukuj(r)
        if r["ocenione"]:
            wyniki.append(r)
    if not wyniki:
        print("\nKONTROLA: żaden model nie odpowiedział. Sprawdź, czy płatności w Google AI Studio są aktywne.")
        return
    naj = min(wyniki, key=lambda r: (r["punkty_karne"], klasyfikator._cena(r["model"])))
    if len(modele) > 1 or not klasyfikator.ustawienie("model_ai"):
        klasyfikator.ustawienie("model_ai", naj["model"])
    klasyfikator.ustawienie("kontrola_wynik", json.dumps({
        "czas": int(time.time()), "model": naj["model"], "krytyczne": len(naj["krytyczne"]), "sprawdzen": naj["sprawdzen"],
        "trafione": naj["trafione"], "ukryte_dobre": len(naj["ukryte_dobre"]), "plec": len(naj["plec"])}))
    print(f"\nKONTROLA: model w użyciu: {naj['model']}. Błędy krytyczne: {len(naj['krytyczne'])}, "
          f"zgodność z wzorcem {round(100 * naj['trafione'] / max(1, naj['sprawdzen']))}%.")


if __name__ == "__main__":
    main()
