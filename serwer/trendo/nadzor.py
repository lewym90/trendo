"""Nadzór nad oceną produktów pod okazję (zasady: serwer/kontrola/kodeks.md).
AI jest tu jednym z głosów: decyzję podejmują stałe zasady poniżej.

Od 0.9.0 zasady NIE opierają się na kawałkach słów z nazwy (polska odmiana: „krata”, „kratka”, „kraciasta”…).
Działają na cechach, które AI rozpoznaje ze zdjęcia i opisu i zapisuje w ujednoliconej postaci:
rodzaj (r), elegancja (f), material, wzor_rodzaj, nadruk, kolor, styl, natężenie wzoru (wzor), okazje (o).
Z nazwy sprawdzamy tylko jednoznaczne nazwy własne marek licencyjnych (Coca-Cola, Disney…).

decyzja(p, okazja) -> ("tak" | "nie", powód). Każdy produkt dostaje jednoznaczną decyzję.
Płeć: najpierw według sklepu (dział, kod produktu), dopiero gdy sklep jej nie podaje, według oceny zdjęcia.
"""
import re

FORMALNE = ("wieczor", "wesele", "sylwester", "praca", "randka", "smartcasual")  # okazje z filtrem (kodeks.md)

# Nazwy własne marek i licencji niemodowych (kodeks 2). Pełne nazwy, nie fragmenty słów.
LICENCJE = re.compile(r"\b(coca[ -]?cola|pepsi|disney|marvel|star wars|harry potter|hello kitty|myszk\w* miki|mickey|minnie|"
                      r"snoopy|garfield|pok[eé]mon|batman|spider[ -]?man|simpson\w*|looney tunes|scooby|barbie|metallica|"
                      r"ac/dc|nirvana|rolling stones|ayrton senna|formula 1|nasa)\b", re.I)

# Cechy (wartości z klasyfikator.py)
NADRUK_ZAKAZANY = {"duze_logo_przod", "nadruk_na_plecach", "napis_haslo", "grafika_postac", "naszywki_aplikacje"}
WZOR_ZAKAZANY = {"duze_logo_lub_nadruk", "motyw_tematyczny"}
SKORA = {"skora", "skora_ekologiczna", "zamsz", "powlekany_woskowany"}
LUZNE_MATERIALY = {"len", "dzins", "flanela", "sztruks"}  # kodeks 10 i 16: nie na wieczór ani na wesele (len: wyjątek garnitur)

MIN_ELEGANCJA = {"wesele": 4, "wieczor": 3, "sylwester": 2, "praca": 3, "randka": 2, "smartcasual": 2}  # sylwester 2: gdy AI go wypisało
RODZAJ_ZAKAZANY = {
    "wesele": {"t-shirt", "polo", "bluza", "dres", "jeansy", "szorty", "legginsy", "sneakersy", "klapki", "kapcie", "plecak",
               "piżama", "strój kąpielowy", "czapka", "kurtka"},
    "wieczor": {"bluza", "dres", "szorty", "legginsy", "klapki", "kapcie", "plecak", "piżama", "strój kąpielowy"},
    "sylwester": {"bluza", "dres", "szorty", "klapki", "kapcie", "plecak", "piżama", "strój kąpielowy"},
    "praca": {"dres", "szorty", "klapki", "kapcie", "piżama", "strój kąpielowy", "bluza"},
    "randka": {"dres", "klapki", "kapcie", "piżama", "strój kąpielowy"},
    "smartcasual": {"dres", "legginsy", "szorty", "klapki", "kapcie", "piżama", "strój kąpielowy", "plecak"},
}
# Styl zakazany na okazję (kodeks 6–7, 9, 14)
STYL_ZAKAZANY = {
    "wesele": {"sportowy", "plazowy_domowy", "casual"},
    "wieczor": {"sportowy", "plazowy_domowy"},
    "sylwester": {"sportowy", "plazowy_domowy"},
    "praca": {"sportowy", "plazowy_domowy", "wieczorowy"},
    "randka": {"sportowy", "plazowy_domowy"},
    "smartcasual": {"sportowy", "plazowy_domowy"},  # suknie wieczorowe: osobno w decyzja()
}
DODATKI = {"buty", "botki", "kozaki", "sneakersy", "półbuty", "szpilki", "czółenka", "mokasyny", "baleriny", "sandały",
           "torebka", "plecak", "portfel", "pasek", "biżuteria", "zegarek", "okulary", "czapka", "kapelusz", "szal", "rękawiczki", "krawat"}
WIECZOR_RODZAJE = {"koszula", "bluzka", "spódnica", "spodnie", "sweter", "top", "sukienka"}
RANDKA_RODZAJE = {"sweter", "kardigan", "polo", "sukienka", "bluzka", "top", "kombinezon"}  # przy spodniach o charakterze decyduje krój


def _tekst(p):
    return (p.get("nazwa", "") + " " + (p.get("material") or "")).lower()


def skorzane(p, k=None):
    k = k or p.get("klasa") or {}
    return k.get("material") in SKORA


def zakaz_slowny(p, okazja):
    """Jedyny zakaz oparty na nazwie: marki i licencje niemodowe (pełne nazwy własne)."""
    if okazja not in FORMALNE:
        return None
    m = LICENCJE.search(_tekst(p))
    return m.group(0) if m else None


def okazje(p, k):
    """Okazje według AI uzupełnione o oczywiste wnioski stylistki (AI wypisuje okazje zbyt oszczędnie i przy kolejnym
    pytaniu potrafi lekko zmienić listę). Liczone tylko z odpowiedzi AI, bez łańcuchów. Kalibracja: kontrola/kalibracja.py."""
    o0 = set(k.get("o") or [])
    o, f, r, wz = set(o0), k.get("f") or 0, k.get("r"), k.get("wzor")
    mat, wr, styl = k.get("material"), k.get("wzor_rodzaj"), k.get("styl")
    sk = mat in SKORA
    elegancki = styl in ("smart_casual", "elegancki", "wieczorowy")
    if "wieczor" in o0 and f >= 4 and r not in ("sweter", "kardigan"):
        o.add("sylwester")  # elegancko na wieczór = także na sylwestra
    if "wieczor" in o0 and f >= 4 and not sk:
        o.add("wesele")  # bardzo elegancko na wieczór = także na wesele (ale nie skóra)
    if r == "sukienka" and f >= 3 and "wieczor" in o0 and not sk and wz != "wzor_wyrazisty":
        o.add("wesele")
    if "praca" in o0 or ({"wieczor", "sylwester"} & o0 and f >= 3):
        o.add("randka")
    if "codzien" in o0 and f >= 2 and wz in ("gladki", "male_logo") and r in RANDKA_RODZAJE:
        o.add("randka")
    if r in ("marynarka", "garnitur") and f >= 3 and wz != "wzor_wyrazisty" and not sk:
        o |= {"wieczor", "randka", "praca", "smartcasual"}  # marynarka to zawsze strój na wyjście
        if mat != "len":
            o.add("sylwester")
    if ("praca" in o0 or {"randka", "codzien"} <= o0) and 2 <= f <= 4 and wz not in WZOR_ZAKAZANY:
        o.add("smartcasual")  # kodeks 5–6
    if styl == "smart_casual":
        o.add("smartcasual")
    # gładka koszula, golf, spódnica, spodnie do pracy i na randkę = także na kolację (nie len, dżins, flanela, sztruks, krata)
    if ({"praca", "randka"} <= o0 and f >= 3 and wz in ("gladki", "male_logo") and r in WIECZOR_RODZAJE
            and mat not in LUZNE_MATERIALY and wr != "krata"):
        o |= {"wieczor", "randka"}
    # kodeks 6: smart casual obejmuje skórzane sneakersy i kurtki, swetry, koszule, sukienki dzienne
    if r == "sneakersy" and sk and wz in ("gladki", "male_logo") and styl != "sportowy" and "sport" not in o0:
        o.add("smartcasual")
    if r == "kurtka" and sk:
        o.add("smartcasual")
    if r in ("sweter", "kardigan") and f >= 2 and wz in ("gladki", "male_logo", "wzor_stonowany"):
        o.add("smartcasual")
    if r == "koszula" and f >= 2 and wz in ("gladki", "male_logo", "wzor_stonowany") and mat != "flanela":
        o.add("smartcasual")
    if r == "sukienka" and f >= 2 and wz in ("gladki", "male_logo", "wzor_stonowany") and "codzien" in o0:
        o.add("smartcasual")
    # kodeks 10: skórzane kozaki i botki o eleganckim charakterze pasują do sukienki na wieczór
    if r in ("kozaki", "botki") and sk and wz in ("gladki", "male_logo") and elegancki:
        o |= {"smartcasual", "randka", "wieczor"}
    return o


def decyzja(p, okazja, wykluczone=()):
    """p['klasa'] = wynik klasyfikatora (albo brak). Zwraca (werdykt, powód)."""
    if okazja not in FORMALNE:
        return "tak", ""
    if (p.get("id"), okazja) in wykluczone:
        return "nie", "zgłoszone: nie pasuje"
    s = zakaz_slowny(p, okazja)
    if s:
        return "nie", f"licencja: {s}"
    k = p.get("klasa")
    if not k:
        return decyzja_slowna(p, okazja)
    r, mat, styl = k.get("r"), k.get("material"), k.get("styl")
    if r in RODZAJ_ZAKAZANY.get(okazja, ()):
        return "nie", f"rodzaj: {r}"
    nd = k.get("nadruk")
    ozdoby_wieczorowe = nd == "naszywki_aplikacje" and (styl == "wieczorowy" or mat == "cekiny_brokat_metaliczny")
    if nd in NADRUK_ZAKAZANY and not (ozdoby_wieczorowe and okazja in ("wieczor", "sylwester", "randka")):
        return "nie", f"nadruk: {nd}"  # cyrkonie, frędzle, cekiny na rzeczy wieczorowej to ozdoby, nie naszywki
    if (k.get("wzor") or "gladki") in WZOR_ZAKAZANY:
        return "nie", f"wzór: {k.get('wzor')}"
    if styl in STYL_ZAKAZANY.get(okazja, ()):
        if not (okazja == "wesele" and styl == "casual" and r == "sukienka" and (k.get("f") or 0) >= 3):
            return "nie", f"styl: {styl}"
    if k.get("wzor_rodzaj") == "moro":
        return "nie", "moro"
    ubranie = r not in DODATKI  # kodeks 16 dotyczy ubrań; skórzana torebka czy buty na weselu są w porządku
    if ubranie and okazja in ("wieczor", "wesele") and mat in LUZNE_MATERIALY and not (mat == "len" and r in ("garnitur", "marynarka")):
        return "nie", f"materiał: {mat}"
    if ubranie and okazja == "wesele" and mat in SKORA:
        return "nie", "skóra na wesele"
    if okazja == "smartcasual" and styl == "wieczorowy" and r in ("sukienka", "kombinezon"):
        return "nie", "suknia wieczorowa"  # kodeks 7
    if okazja in ("praca", "smartcasual") and mat == "cekiny_brokat_metaliczny":
        return "nie", "cekiny"
    if okazja not in okazje(p, k):
        return "nie", "AI: nie na tę okazję"
    minimum = 3 if (okazja == "wesele" and r == "sukienka") else MIN_ELEGANCJA[okazja]
    if (k.get("f") or 0) < minimum:
        return "nie", f"elegancja {k.get('f')}"
    # kodeks 12: biel, ecru i kremowy zarezerwowane dla panny młodej (kolor ze zdjęcia i opisu)
    if okazja == "wesele" and plec(p) == "damskie" and k.get("kolor") == "bialy_ecru":
        return "nie", "biel zarezerwowana dla panny młodej"
    return "tak", ""


ELEGANCKIE = ["elegan", "wizytow", "satyn", "jedwab", "smoking", "garnitur", "koronk", "aksamit", "welur", "wełn", "kaszmir",
              "taliowan", "marynar", "szpilk", "lakierk", "oxford", "derby", "cekin", "czółen", "w kant"]


def decyzja_slowna(p, okazja):
    """Gdy stylista AI jest niedostępny (np. wyczerpany miesięczny budżet): tylko rzeczy jednoznacznie eleganckie z opisu,
    bez nadruków. To wyjątkowy tryb awaryjny; w normalnej pracy każdy produkt ma ocenę AI."""
    t = _tekst(p)
    if re.search(r"nadruk|napis|grafik|print|dres|bluz[aęy]\b|t-?shirt|koszulk", t):
        return "nie", "opis (bez AI)"
    if any(x in t for x in ELEGANCKIE):
        return "tak", "opis (bez AI)"
    return "nie", "opis (bez AI): brak cech eleganckich"


def plec(p):
    """Ostateczna płeć produktu: sklep ma pierwszeństwo, ocena zdjęcia tylko gdy sklep jej nie podaje."""
    k = p.get("klasa") or {}
    if k.get("p") == "dzieciece":
        return "dzieciece"
    return p.get("plec_sklepu") or k.get("p")


def zgodna_plec(p, dzial):
    pl = plec(p)
    if pl == "dzieciece":
        return False
    return not ((dzial == "damskie" and pl == "meskie") or (dzial == "meskie" and pl == "damskie"))


def punkty(p, okazja):
    k = p.get("klasa") or {}
    return (k.get("f") or 0) if okazja in FORMALNE else 0
