"""Nadzór nad oceną produktów pod okazję. AI jest tu tylko jednym z głosów: decyzję podejmują sztywne zasady poniżej.
Zasada nadrzędna: lepiej ukryć dobrą rzecz niż pokazać złą.

decyzja(p, okazja) -> ("tak" | "nie", powód). Każdy produkt dostaje jednoznaczną decyzję.
Płeć: najpierw według sklepu (dział, kod produktu), dopiero gdy sklep jej nie podaje, według oceny zdjęcia.
"""
import re

FORMALNE = ("wieczor", "wesele", "sylwester", "praca", "randka", "smartcasual")  # okazje z filtrem (kodeks.md)

# Twarde zakazy (nazwa i opis ze sklepu). AI nie może ich obejść.
# UWAGA: samo słowo „logo” NIE jest zakazem. Mały haft marki na piersi (EA7, Calvin Klein, Lacoste, BOSS) nie wyklucza
# elegancji. Wyklucza dopiero duże logo albo nadruk, a to rozstrzyga ocena zdjęcia (pole „wzor”).
TWARDE = [
    "coca-cola", "coca cola", "cocacola", "pepsi", "disney", "marvel", "star wars", "harry potter", "hello kitty", "myszka miki",
    "mickey", "minnie", "snoopy", "garfield", "pokemon", "batman", "spider", "simpson", "komiks", "anime", "licencj",
    "palm", "hawaj", "flaming", "tropik", "plażow", "plazow", "kąpielow", "kapielow",
    "dres", "jogger", "piżam", "pizam", "klapk", "japonk", "crocs", "trekking", "biegow", "treningow", "do biegania",
    "na siłownię", "na silownie", "do koszykówki", "do koszykowki", "do golfa", "z kapturem", "hoodie", "bojówk", "bojowk", "cargo",
    "z dziurami", "dziury", "przetarci", "ripped", "duże logo", "dużym logo", "duzym logo", "logo na całym", "allover", "all-over",
    "moro", "kamuflaż", "kamuflaz", "na plecach",  # nadruk/logo na plecach: na zdjęciu z przodu niewidoczne
]
# Dla wesela i pracy dodatkowo (nazwa):
TWARDE_WESELE = ["jeans", "denim", "lnian", "lnu", "flanel", "sneaker", "trampk", "sportow", "t-shirt", "tshirt", "krótki rękaw",
                 "krótkim rękaw", "szorty", "polo"]
TWARDE_PRACA = ["cekin", "przezroczyst", "crop top", "kąpiel"]
# Rodzaje rzeczy rozpoznane po nazwie (wyrażenia regularne), które nie pasują do eleganckich okazji.
NAZWA_ZAKAZ = {
    "wieczor": [r"flanel", r"\bbluz(a|ę|y|ie)\b", r"sweatshirt", r"hoodie", r"\bbuty sportowe", r"sportowe buty", r"\bsneaker", r"\btrampk",
                r"\bpuchow", r"\bparka\b", r"wiatrówk", r"\bplecak"],
    "wesele": [r"\bbluz(a|ę|y|ie)\b", r"sweatshirt", r"hoodie", r"\bbuty sportowe", r"sportowe buty", r"\bpuchow", r"\bparka\b",
               r"wiatrówk", r"\bplecak", r"\bshopper", r"\bkoszulk"],
    "sylwester": [r"flanel", r"\bbluz(a|ę|y|ie)\b", r"sweatshirt", r"hoodie", r"\bbuty sportowe", r"sportowe buty", r"\bpuchow", r"\bplecak"],
    "praca": [r"\bbluz(a|ę|y|ie)\b", r"sweatshirt", r"hoodie", r"\bpuchow", r"wiatrówk"],
    "randka": [r"hoodie", r"z kapturem"],
    "smartcasual": [r"\bbluz(a|ę|y|ie)\b", r"sweatshirt", r"hoodie", r"z kapturem", r"\bpuchow", r"wiatrówk"],
}
# Kodeks, reguła 12: biel, ecru i kremowy są zarezerwowane dla panny młodej.
# Kolor rzeczy w nazwie („Biała sukienka”, „Bluzka … Biały Slim Fit”), ale nie dodatki („z białym kołnierzykiem”).
BIEL_RE = re.compile(r"(?<!z )(?<!ze )\b(biał\w*|bial[aey]\b|ecru|écru|kremow\w*|śmietankow\w*|smietankow\w*|mleczn\w*|off-white|white)")

# Nadruk w opisie, a na zdjęciu (z przodu) gładka rzecz = nadruk jest gdzie indziej (np. na plecach) → nie na eleganckie okazje.
# Gdy zdjęcie pokazuje wzór, opis „print” po prostu opisuje ten wzór i decyduje ocena zdjęcia.
MIEKKIE = ["nadruk", "napis", "graficzn", "grafik", "aplikacj", "naszyw", "print"]

WZOR_ZAKAZANY = {"duze_logo_lub_nadruk", "motyw_tematyczny"}
MIN_ELEGANCJA = {"wesele": 4, "wieczor": 3, "sylwester": 2, "praca": 3, "randka": 2, "smartcasual": 2}  # sylwester 2: tylko gdy AI sam go wypisał
WIECZOR_RODZAJE = {"koszula", "bluzka", "spódnica", "spodnie", "sweter", "top", "sukienka"}
NIE_WIECZOR = ["lnian", "lnu", " len", "krat", "flanel", "chambray", "jeans", "denim", "dżins", "sztruks", "bojówk", "cargo"]
RANDKA_RODZAJE = {"sweter", "kardigan", "polo", "sukienka", "bluzka", "spódnica", "spodnie", "top", "kombinezon"}
# Rzeczy, które nigdy nie pasują do danej okazji (rodzaj z klasyfikacji).
RODZAJ_ZAKAZANY = {
    "wesele": {"t-shirt", "bluza", "dres", "jeansy", "szorty", "legginsy", "sneakersy", "klapki", "kapcie", "plecak", "piżama",
               "strój kąpielowy", "czapka", "kurtka"},
    "wieczor": {"bluza", "dres", "szorty", "legginsy", "klapki", "kapcie", "plecak", "piżama", "strój kąpielowy"},
    "sylwester": {"bluza", "dres", "szorty", "klapki", "kapcie", "plecak", "piżama", "strój kąpielowy"},
    "praca": {"dres", "szorty", "klapki", "kapcie", "piżama", "strój kąpielowy", "bluza"},
    "randka": {"dres", "klapki", "kapcie", "piżama", "strój kąpielowy"},
    "smartcasual": {"dres", "bluza", "legginsy", "szorty", "klapki", "kapcie", "piżama", "strój kąpielowy", "plecak"},
}


def _tekst(p):
    return (p.get("nazwa", "") + " " + (p.get("material") or "")).lower()


def _ma(t, slowa):
    return next((s for s in slowa if s in t), None)


def zakaz_slowny(p, okazja):
    """Zwraca słowo, które wyklucza produkt na tę okazję, albo None."""
    if okazja not in FORMALNE:
        return None
    t = _tekst(p)
    s = _ma(t, TWARDE)
    if s:
        return s
    for wz in NAZWA_ZAKAZ.get(okazja, ()):
        m = re.search(wz, t)
        if m:
            return m.group(0)
    if okazja == "wesele":
        s = _ma(t, TWARDE_WESELE)
        if s in ("lnian", "lnu") and (p.get("klasa") or {}).get("r") in ("garnitur", "marynarka"):
            return None  # lniany garnitur latem jest dopuszczalny (kodeks, reguła 16)
        return s
    if okazja == "praca":
        return _ma(t, TWARDE_PRACA)
    return None


def skorzane(p):
    return _ma(_tekst(p), ["skór", "skor", "lateks", "woskow", "winyl"]) is not None


def okazje(p, k):
    """Okazje według AI uzupełnione o oczywiste wnioski stylistki. AI wypisuje okazje zbyt oszczędnie, a przy kolejnym
    pytaniu potrafi lekko zmienić listę. Reguły sprawdzone na zestawie wzorcowym w DWÓCH niezależnych przebiegach modelu
    (0.7.4: 0 błędów krytycznych w obu, ukryte dobre 64 → 27–32 z 1016). Liczone tylko z odpowiedzi AI, bez łańcuchów."""
    o0 = set(k.get("o") or [])
    o, f, r, wz = set(o0), k.get("f") or 0, k.get("r"), k.get("wzor")
    if "wieczor" in o0 and f >= 4 and r not in ("sweter", "kardigan"):
        o.add("sylwester")  # elegancko na wieczór = także na sylwestra
    if "wieczor" in o0 and f >= 4 and not skorzane(p):
        o.add("wesele")  # bardzo elegancko na wieczór = także na wesele (ale nie skóra)
    if r == "sukienka" and f >= 3 and "wieczor" in o0 and not skorzane(p) and wz != "wzor_wyrazisty":
        o.add("wesele")
    if "praca" in o0 or ({"wieczor", "sylwester"} & o0 and f >= 3):
        o.add("randka")
    if "codzien" in o0 and f >= 2 and wz in ("gladki", "male_logo") and r in RANDKA_RODZAJE:
        o.add("randka")  # gładki sweter, polo, sukienka, bluzka, spodnie = smart casual na randkę
    if r in ("marynarka", "garnitur") and f >= 3 and wz != "wzor_wyrazisty" and not skorzane(p):
        o |= {"wieczor", "randka", "praca", "smartcasual"}  # marynarka to zawsze strój na wyjście
    if ("praca" in o0 or {"randka", "codzien"} <= o0) and f >= 2 and f <= 4 and wz not in WZOR_ZAKAZANY:
        o.add("smartcasual")  # kodeks 5–6: smart casual = elegancja ze swobodą (bez rzeczy typowo imprezowych)
    t = _tekst(p)
    sk = skorzane(p)
    # 0.8.1 (kalibracja na 3 przebiegach): gładka koszula, golf, spódnica, spodnie do pracy i na randkę = także na kolację,
    # ale nie len, krata, flanela, chambray, dżins, sztruks, bojówki (kodeks 10)
    if {"praca", "randka"} <= o0 and f >= 3 and wz in ("gladki", "male_logo") and r in WIECZOR_RODZAJE and not _ma(t, NIE_WIECZOR):
        o |= {"wieczor", "randka"}
    # kodeks 6: smart casual obejmuje skórzane sneakersy i kurtki, swetry, koszule, sukienki dzienne
    if r == "sneakersy" and sk and wz in ("gladki", "male_logo"):
        o.add("smartcasual")
    if r == "kurtka" and sk:
        o.add("smartcasual")
    if r in ("sweter", "kardigan") and f >= 2 and wz in ("gladki", "male_logo", "wzor_stonowany"):
        o.add("smartcasual")
    if r == "koszula" and f >= 2 and wz in ("gladki", "male_logo", "wzor_stonowany") and not _ma(t, ["flanel"]):
        o.add("smartcasual")
    if r == "sukienka" and f >= 2 and wz in ("gladki", "male_logo", "wzor_stonowany") and "codzien" in o0:
        o.add("smartcasual")
    # kodeks 10: skórzane kozaki i botki pasują do sukienki na wieczór (ale nie buty zimowe typu emu)
    if r in ("kozaki", "botki") and sk and wz in ("gladki", "male_logo") and not _ma(t, ["emu", "ugg", "śniegow", "sniegow", "zimow", "trapery", "trekking"]):
        o |= {"smartcasual", "randka", "wieczor"}
    # kodeks 17: eleganckie marynarki na sylwestra (nie lniane, nie skórzane)
    if r in ("marynarka", "garnitur") and f >= 3 and wz != "wzor_wyrazisty" and not sk and not _ma(t, ["lnian", "lnu", " len", "lnem"]):
        o.add("sylwester")
    return o


def decyzja(p, okazja, wykluczone=()):
    """p['klasa'] = wynik klasyfikatora (albo brak). Zwraca (werdykt, powód)."""
    if okazja not in FORMALNE:
        return "tak", ""
    if (p.get("id"), okazja) in wykluczone:
        return "nie", "zgłoszone: nie pasuje"
    s = zakaz_slowny(p, okazja)
    if s:
        return "nie", f"zakaz: {s}"
    k = p.get("klasa")
    if not k:
        return decyzja_slowna(p, okazja)
    if k.get("r") in RODZAJ_ZAKAZANY.get(okazja, ()):
        return "nie", f"rodzaj: {k.get('r')}"
    if okazja not in okazje(p, k):
        return "nie", "AI: nie na tę okazję"
    wz = k.get("wzor") or "gladki"
    if wz in WZOR_ZAKAZANY:
        return "nie", f"zdjęcie: {wz}"
    minimum = 3 if (okazja == "wesele" and k.get("r") == "sukienka") else MIN_ELEGANCJA[okazja]
    if okazja == "smartcasual" and k.get("r") == "t-shirt":
        minimum = 3  # zwykły t-shirt to casual, nie smart casual (kodeks 7)
    if (k.get("f") or 0) < minimum:
        return "nie", f"elegancja {k.get('f')}"
    # kolor z oceny zdjęcia albo z początku nazwy („Biała sukienka…”, „Kremowy sweter…”), nie z dodatków („…z białym kołnierzykiem”)
    if okazja == "wesele" and plec(p) == "damskie" and (k.get("bialy") or BIEL_RE.search(p.get("nazwa", "").lower())):
        return "nie", "biel zarezerwowana dla panny młodej"
    m = _ma(_tekst(p), MIEKKIE)
    if m and wz in ("gladki", "male_logo") and okazja != "randka":
        return "nie", f"opis: {m}, nadruk poza zdjęciem"
    return "tak", ""


ELEGANCKIE = ["elegan", "wizytow", "satyn", "jedwab", "smoking", "garnitur", "koronk", "aksamit", "welur", "wełn", "kaszmir",
              "taliowan", "marynar", "szpilk", "lakierk", "oxford", "derby", "cekin", "czółen", "w kant"]
LUZNE = ["wzorzyst", "kolorow", "krat", "jeans", "denim", "lnian", "workowat", "oversize", "t-shirt", "koszulk", "bluz"]


def decyzja_slowna(p, okazja):
    """Gdy stylista AI jest niedostępny (np. wyczerpany miesięczny budżet): tylko rzeczy jednoznacznie eleganckie z opisu."""
    t = _tekst(p)
    if _ma(t, MIEKKIE) or _ma(t, LUZNE):
        return "nie", "opis (bez AI)"
    if okazja == "randka" or _ma(t, ELEGANCKIE):
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

