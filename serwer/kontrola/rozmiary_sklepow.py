"""Buduje serwer/trendo/rozmiary-sklepow.json: ogólne tabele rozmiarów sklepów, przepisane z ich stron „tabele rozmiarów”.
Każda tabela ma adres źródła i datę sprawdzenia. Wybór tabel (numer tabeli na stronie, dział, rodzaj rzeczy) jest ręczny,
po obejrzeniu strony; skrypt odczytuje liczby i sprawdza, czy tabela ma oczekiwane pomiary.
Uruchomienie (z katalogu serwer): python3 kontrola/rozmiary_sklepow.py
Gdy sklep zmieni stronę, skrypt wypisze, której tabeli nie znalazł, i jej nie zapisze."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("TRENDO_DANE", "/tmp/trendo-rozmiary")
os.makedirs(os.environ["TRENDO_DANE"], exist_ok=True)
from trendo import rozmiary as R
from trendo.wspolne import pobierz

# sklep: (adresy stron, [(numer strony, numer tabeli, dział d/m, grupa, nazwa tabeli, wymagane pomiary, pomiary do pominięcia)])
# grupa: ubrania (góra, sukienki, okrycia, ogólna), dol (spodnie, spódnice, szorty), jeansy, marynarki, buty
SPEC = {
    "Reserved": (["https://www.reserved.com/pl/pl/help-size-guide"], [
        (0, 1, "d", "ubrania", "Odzież damska (XS–XL)", {"klatka", "talia", "biodra"}, ()),
        (0, 0, "d", "ubrania", "Odzież damska (32–54)", {"klatka", "talia", "biodra"}, ()),
        (0, 2, "d", "dol", "Spodnie i spódnice damskie", {"talia", "biodra"}, ()),
        (0, 19, "d", "buty", "Buty damskie", {"stopa"}, ()),
        (0, 20, "m", "ubrania", "Odzież męska", {"klatka", "talia"}, ()),
        (0, 22, "m", "buty", "Buty męskie", {"stopa"}, ()),
    ]),
    "Mohito": (["https://www.mohito.com/pl/pl/help-tabele-rozmiarowe"], [
        (0, 1, "d", "ubrania", "Odzież (XXS–XXL)", {"talia", "biodra"}, ()),
        (0, 0, "d", "ubrania", "Odzież (32–44)", {"talia", "biodra"}, ()),
    ]),
    "House": (["https://www.housebrand.com/pl/pl/help-tabele-rozmiarowe"], [
        (0, 4, "d", "ubrania", "Odzież damska", {"klatka", "talia", "biodra"}, ()),
        (0, 5, "d", "dol", "Spodnie, szorty i spódnice damskie", {"talia", "biodra"}, ()),
        (0, 6, "d", "jeansy", "Jeansy damskie", {"talia", "biodra"}, ()),
        (0, 13, "d", "buty", "Obuwie damskie", {"wkladka"}, ()),
        (0, 0, "m", "ubrania", "Góra męska (koszule, t-shirty, kurtki)", {"klatka"}, ()),
        (0, 1, "m", "dol", "Spodnie i szorty męskie", {"talia", "biodra"}, ()),
        (0, 2, "m", "jeansy", "Jeansy męskie", {"biodra"}, ()),
        (0, 14, "m", "buty", "Obuwie męskie", {"wkladka"}, ()),
    ]),
    "Cropp": (["https://www.cropp.com/pl/pl/help-tabele-rozmiarowe"], [
        (0, 0, "d", "ubrania", "Topy damskie", {"klatka", "talia", "biodra"}, ()),
        (0, 1, "d", "dol", "Spodnie, szorty i spódnice damskie", {"talia", "biodra"}, ()),
        (0, 2, "d", "jeansy", "Jeansy damskie", {"talia", "biodra"}, ("rekaw",)),  # sklep opisuje nogawkę jako „długość rękawa”
        (0, 7, "m", "ubrania", "Kurtki, bluzy, t-shirty, swetry, koszule", {"klatka", "talia"}, ()),
        (0, 8, "m", "jeansy", "Jeansy i spodnie męskie", {"talia", "biodra"}, ()),
    ]),
    "Sinsay": (["https://www.sinsay.com/pl/pl/help-tabele-rozmiarowe"], [
        (0, 0, "d", "ubrania", "Odzież damska", {"klatka", "talia", "biodra"}, ()),
        (0, 1, "d", "ubrania", "Odzież damska, większe rozmiary", {"klatka", "talia", "biodra"}, ()),
        (0, 2, "d", "buty", "Buty damskie", {"stopa"}, ()),
        (0, 12, "m", "ubrania", "Odzież męska", {"klatka", "talia", "biodra"}, ()),
        (0, 13, "m", "dol", "Spodnie męskie", {"talia", "biodra"}, ()),
        (0, 17, "m", "buty", "Buty męskie", {"stopa"}, ()),
    ]),
    "Quiosque": (["https://www.quiosque.pl/tabela-rozmiarow,13.html"], [
        (0, 1, "d", "ubrania", "Odzież (S–5XL)", {"klatka", "talia", "biodra"}, ()),
        (0, 0, "d", "ubrania", "Odzież (36–52)", {"klatka", "talia", "biodra"}, ()),
    ]),
    "Monnari": (["https://emonnari.pl/tabela-rozmiarow,13.html"], [
        (0, 1, "d", "ubrania", "Odzież (S–5XL)", {"klatka", "talia", "biodra"}, ()),
        (0, 0, "d", "ubrania", "Odzież (36–52)", {"klatka", "talia", "biodra"}, ()),
        (0, 3, "d", "buty", "Obuwie damskie", {"stopa"}, ()),
    ]),
    "Kazar": (["https://kazar.com/tabele-rozmiarow"], [
        (0, 0, "d", "buty", "Obuwie damskie", {"stopa"}, ()),
        (0, 1, "m", "buty", "Obuwie męskie", {"stopa"}, ()),
    ]),
    "Bytom": (["https://bytom.com.pl/tabela-rozmiarow-1", "https://bytom.com.pl/tabela-rozmiarow-2",
               "https://bytom.com.pl/tabela-rozmiarow-3"], [
        (0, 0, "m", "ubrania", "Wymiary ciała (S–XXXL)", {"klatka", "talia"}, ()),
        (1, 0, "m", "marynarki", "Garnitury i marynarki", {"klatka", "talia"}, ()),
        (2, 0, "m", "dol", "Spodnie", {"talia"}, ()),
    ]),
}


def buduj():
    dzis = time.strftime("%Y-%m-%d")
    wyn, bledy = {}, []
    for sklep, (adresy, tabele) in SPEC.items():
        strony = []
        for u in adresy:
            kod, b = pobierz(u, czas=30)
            strony.append(R.siatki(b.decode("utf-8", "ignore")) if kod == 200 else [])
        lista = []
        for nr, ti, dz, gr, naz, wymagane, pomin in tabele:
            g = strony[nr][ti] if ti < len(strony[nr]) else None
            t = R._z_siatki(g) if g else None
            if not t or not wymagane <= set(t["wymiary"]):
                bledy.append(f"{sklep}: nie znalazłem tabeli „{naz}” (strona {adresy[nr]}, tabela {ti})")
                continue
            for k in pomin:
                t["wymiary"].pop(k, None)
            zostaw = [j for j, r in enumerate(t["rozmiary"]) if r not in t["rozmiary"][:j]]  # powtórzony rozmiar: zostaje pierwszy
            t["rozmiary"] = [t["rozmiary"][j] for j in zostaw]
            for v in list(t["wymiary"].values()) + t["inne"]:
                v["wartosci"] = [v["wartosci"][j] for j in zostaw]
            for a in t.get("aliasy", []):
                a["rozmiary"] = [a["rozmiary"][j] for j in zostaw]
            lista.append({"dzial": dz, "grupa": gr, "nazwa": naz, "url": adresy[nr], **t})
        if lista:
            wyn[sklep] = {"url": adresy[0], "sprawdzono": dzis, "tabele": lista}
    return wyn, bledy


if __name__ == "__main__":
    wyn, bledy = buduj()
    cel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "trendo", "rozmiary-sklepow.json")
    with open(cel, "w", encoding="utf-8") as f:
        json.dump({"opis": "Ogólne tabele rozmiarów sklepów (wymiary ciała w cm), przepisane z ich stron. Budowa: kontrola/rozmiary_sklepow.py.",
                   "sklepy": wyn}, f, ensure_ascii=False, indent=1)
    print("Zapisane sklepy:", ", ".join(f"{k} ({len(v['tabele'])})" for k, v in wyn.items()))
    for b in bledy:
        print("UWAGA:", b)
