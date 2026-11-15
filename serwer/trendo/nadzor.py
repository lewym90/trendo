"""Nadzór nad oceną produktów pod okazję. AI jest tu tylko jednym z głosów: decyzję podejmują sztywne zasady poniżej.
Zasada nadrzędna: lepiej ukryć dobrą rzecz niż pokazać złą.

decyzja(p, okazja) -> ("tak" | "moze" | "nie", powód)
  tak  - główne wyniki,
  moze - sekcja „Może pasować” (coś się nie zgadza albo brak pewności),
  nie  - nie pokazujemy.
"""
import re

FORMALNE = ("wieczor", "wesele", "sylwester", "praca", "randka")

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
    "moro", "kamuflaż", "kamuflaz",
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
}

# Słowa, które każą sprawdzić zdjęcie: jeśli AI na zdjęciu widzi gładką rzecz, a sklep pisze „z nadrukiem”, to niezgodność.
MIEKKIE = ["nadruk", "print", "napis", "graficzn", "grafik", "motyw", "aplikacj", "naszyw"]

WZOR_ZAKAZANY = {"duze_logo_lub_nadruk", "motyw_tematyczny"}
MIN_ELEGANCJA = {"wesele": 4, "wieczor": 3, "sylwester": 3, "praca": 3, "randka": 2}
# Rzeczy, które nigdy nie pasują do danej okazji (rodzaj z klasyfikacji).
RODZAJ_ZAKAZANY = {
    "wesele": {"t-shirt", "bluza", "dres", "jeansy", "szorty", "legginsy", "sneakersy", "klapki", "kapcie", "plecak", "piżama",
               "strój kąpielowy", "czapka", "kurtka"},
    "wieczor": {"bluza", "dres", "szorty", "legginsy", "klapki", "kapcie", "plecak", "piżama", "strój kąpielowy"},
    "sylwester": {"bluza", "dres", "szorty", "klapki", "kapcie", "plecak", "piżama", "strój kąpielowy"},
    "praca": {"dres", "szorty", "klapki", "kapcie", "piżama", "strój kąpielowy", "bluza"},
    "randka": {"dres", "klapki", "kapcie", "piżama", "strój kąpielowy"},
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
        return _ma(t, TWARDE_WESELE)
    if okazja == "praca":
        return _ma(t, TWARDE_PRACA)
    return None


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
        return "moze", "brak oceny"
    if k.get("r") in RODZAJ_ZAKAZANY.get(okazja, ()):
        return "nie", f"rodzaj: {k.get('r')}"
    if okazja not in (k.get("o") or []):
        return "nie", "AI: nie na tę okazję"
    wz = k.get("wzor") or "gladki"
    if wz in WZOR_ZAKAZANY:
        return "nie", f"zdjęcie: {wz}"
    if (k.get("f") or 0) < MIN_ELEGANCJA[okazja]:
        return "nie", f"elegancja {k.get('f')}"
    # Od tego miejsca rzecz przeszła wszystkie zakazy. Sprawdzamy pewność.
    if not k.get("zdj"):
        return "moze", "ocena bez zdjęcia"
    if k.get("zgodne") is False:
        return "moze", "zdjęcie nie zgadza się z nazwą"
    if wz == "wzor_wyrazisty":
        return "moze", "wyrazisty wzór"
    if okazja in ("wieczor", "wesele", "sylwester") and "krat" in _tekst(p) and k.get("r") not in ("marynarka", "garnitur", "spodnie", "płaszcz"):
        return "moze", "krata"
    m = _ma(_tekst(p), MIEKKIE)
    if m and wz in ("gladki", "male_logo"):
        return "moze", f"sklep pisze „{m}”, zdjęcie pokazuje gładką rzecz"
    return "tak", ""


def zgodna_plec(k, dzial):
    if not k:
        return True
    if k.get("p") == "dzieciece":
        return False
    return not ((dzial == "damskie" and k.get("p") == "meskie") or (dzial == "meskie" and k.get("p") == "damskie"))


def punkty(p, okazja):
    k = p.get("klasa") or {}
    return (k.get("f") or 0) if okazja in FORMALNE else 0

