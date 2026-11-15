"""Kalibracja zasad nadzoru BEZ ponownego pytania AI: odtwarza zapisane odpowiedzi modelu dla zestawu wzorcowego
(GET /trendo-api/kontrola zapisane do pliku) i liczy błędy dla aktualnych zasad w nadzor.py.
Użycie: curl -s https://HOST/trendo-api/kontrola > k.json; TRENDO_DANE=/tmp/x python3 serwer/kontrola/kalibracja.py k.json [k2.json ...]
Liczy każdy przebieg osobno (pole „przebiegi” albo „szczegoly” z każdego pliku): reguła jest dobra dopiero, gdy daje 0 błędów
krytycznych we WSZYSTKICH przebiegach."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from trendo import kontrola, nadzor

przebiegi = []
for plik in sys.argv[1:]:
    d = json.load(open(plik))
    for pr in d.get("przebiegi") or [{"szczegoly": d["szczegoly"]}]:
        przebiegi.append({x["nr"]: x["klasa"] for x in pr["szczegoly"]})
L = kontrola.produkty_wzorcowe()
for nr, kl in enumerate(przebiegi, 1):
    kr, uk, ok = [], [], 0
    for p in L:
        p["klasa"] = kl.get(p["nr"])
        dobra = p["plec"] in (p["dzial"], "unisex")
        pok = nadzor.zgodna_plec(p, p["dzial"])
        for o, ma in p["oczekiwane"].items():
            w, pw = nadzor.decyzja(p, o)
            w = w if pok else "nie"
            ma = ma and dobra
            k = p["klasa"] or {}
            opis = f"{o:9} #{p['nr']:3} {p['nazwa'][:55]:55} | {pw} | r={k.get('r')} f={k.get('f')} wz={k.get('wzor')} o={','.join(k.get('o') or [])}"
            if not ma and w == "tak":
                kr.append(opis)
            elif ma and w == "nie":
                uk.append(opis)
            else:
                ok += 1
    print(f"Przebieg {nr}: błędy krytyczne {len(kr)}, ukryte dobre {len(uk)}, zgodne {ok}")
    for x in kr:
        print("  !!", x)
