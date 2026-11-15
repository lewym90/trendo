# Trendo: kontynuacja

Stan na 14.11.2026, wersja 0.1.0.

## Zrobione
- Szata graficzna według wzoru użytkownika: ciemny bakłażan, różowe złoto, Cormorant Garamond + Jost. Ikona od użytkownika (litera T z wieszakiem), przycięta bez ramki do icons/.
- Ekrany: powitanie, start, nowe wyszukiwanie (dział, dwa budżety, tryby, okazje), analiza, wyniki (stylizacje i sklepy ze strefami cenowymi i second-handem), stylizacja (kolaż, elementy, dlaczego, suma), produkt (weryfikacja promocji, wykres ceny 30 dni, rozmiary, alert), trendy, okazje, zakupy (koszyk zbiorczy per sklep, progi darmowej dostawy), alerty, ustawienia.
- Wszystko na danych przykładowych z js/demo.js, oznaczonych w interfejsie.

## Grafiki, na które czekamy (nazwy plików w img/)
- hero.jpg: ekran powitalny
- sezon-jz.jpg, sezon-wl.jpg: okładki raportu trendów
Dopóki ich nie ma, w tych miejscach jest tło z gradientem.

## Test sklepów z serwera (14.11.2026)
Bezpośrednio działają między innymi: H&M, COS, Arket, & Other Stories, Weekday, C&A, Zalando, Born2Be, Renee, Showroom, Vistula, Bytom, Wólczanka, Top Secret, Quiosque, CCC, Deichmann, Nike, Adidas, Sizeer, 50style, Levi's.
Twarda blokada: grupa Inditex (Zara, Bershka, Stradivarius, Pull&Bear, Massimo Dutti, Oysho), Mango (429), Answear, Vitkac, Medicine, Tatuum, Lancerto, Decathlon, Guess, Allegro (403), Pako Lorente, 4F.
Pozostałe oznaczone jako BLOKADA odpowiadają pełną stroną (100+ KB); test był zbyt czuły (słowo captcha w kodzie strony), do ponownego sprawdzenia na stronach produktów.
Błąd połączenia: Diverse, Monnari, Badura (sprawdzić adresy).

## Następne kroki
1. Drugi, dokładniejszy test: pobranie listy produktów z wyszukiwarki każdego sklepu.
2. Serwer: zbieranie katalogów, historia cen, Google Shopping przez płatne API dla sklepów z blokadą.
3. Podłączenie aplikacji do serwera zamiast js/demo.js.

## Testy 2 i 3 z serwera (14.11.2026)
Przeglądarka (Playwright + Chromium) zainstalowana: ~/trendo-scraper (venv), uruchamianie ~/trendo-scraper/bin/python. Serwer: 3,8 GB RAM (ok. 2,3 GB wolne), 2 CPU, 14 GB wolnego dysku. Przeglądarka: jedna karta naraz.

Najlepsza droga dla każdego sklepu:
- A. Bezpośrednio (curl + dane strukturalne): Sinsay, Arket, Weekday, C&A, eobuwie, Born2Be, Renee, Moliera2, Vistula, Recman, Kazar, Adidas, 50style.
- B. Łącznik (strona produktu dostępna, cenę trzeba wyciągnąć z API sklepu lub przeglądarką): Zara, Bershka, Stradivarius, Pull&Bear, Massimo Dutti, Oysho (curl 200 na stronach produktów, przeglądarka 403), Reserved, Mohito, House, Cropp, H&M (adresy z mapy dają 404), CCC, Deichmann, 4F, Nike, Top Secret, Big Star, Molton, Ryłko, Wólczanka, Vinted, Modivo, About You, Ochnik, Wittchen, Bytom, Diverse, Bialcon, Quiosque, Showroom, Bizuu, Pako Lorente, Tatuum, Zalando.
- C. Google Shopping (płatne API): Answear i Medicine (serwer blokowany curl i przeglądarką), Vitkac, Lancerto, Decathlon, Guess, Allegro, Mango, COS, & Other Stories, Levi's, Sizeer, Tommy Hilfiger, Calvin Klein.
- Adresy do poprawy: Monnari sprzedaje online na emonnari.pl; Badura nie odpowiada (sprawdzić).

## Zbieracz na serwerze (15.11.2026, wersja 0.3.x)
- Zainstalowany przez `curl -fsSL https://raw.githubusercontent.com/lewym90/trendo/main/serwer/install.sh | bash` (ten sam skrypt aktualizuje).
- Kod: /opt/trendo (pobierany z GitHuba), dane: /var/lib/trendo/trendo.db (pamięć wyników 6 h, historia cen), ustawienia: /etc/trendo.env, klucz SerpApi: /root/.trendo-serpapi.
- Usługa systemd `trendo` (python z ~/trendo-scraper, port 127.0.0.1:18890, limit 1200 MB), trasa Caddy /etc/caddy/conf.d/trendo.caddy → https://188-68-247-201.sslip.io/trendo-api/ (zdrowie, szukaj, historia).
- Lekcja: plik w conf.d musi być czytelny dla konta caddy (chmod 644); instalator sam wycofuje trasę, gdy reload się nie uda. Pierwsza próba 14.11 nie przeładowała Caddy (permission denied), aplikacje użytkownika działały cały czas na starej konfiguracji.
- Łączniki: Zara (itxrest search, store 11725), Google Shopping (SerpApi, plan Free 250/mies., limit 8 dziennie). Linki z Google prowadzą do karty oferty w Google, nie prosto do sklepu.
- Aplikacja: wyniki „W sklepach” prawdziwe; stylizacje, trendy i okazje nadal przykładowe (oznaczone). API można przestawić do testów: localStorage `trendo-api`.
- Następne łączniki: siostry Inditex, LPP (Reserved, Mohito, House, Cropp, Sinsay), H&M, sklepy grupy A (ld+json), przeglądarka dla reszty.

## 0.4.0 (15.11.2026)
- Łączniki bezpośrednie: Zara (itxrest), LPP przez Algolię (Reserved, Mohito, House, Cropp, Sinsay; klucz/indeks czytany ze strony głównej marki, history_price = Omnibus), Modivo i eobuwie (search-service.modivo.io, kanały modivo/eobuwie, zdjęcia img.modivo.cloud/product(ścieżka,jpg), omnibus_price), strony wyszukiwania: Ochnik i Bialcon (ld+json ItemList, /products/search?query=), Born2Be i Renee (kafle data-dl-*), Bizuu (Searchanise getresults, klucz 1r4h1n5E9I).
- Weryfikacja promocji: jeśli sklep podaje cenę Omnibus → ok/pozorna od razu; inaczej własna historia.
- Trafność (api.py): tokeny 4-literowe; „rzecz” (spodnie, płaszcz…) musi się zgadzać i być pierwszą rzeczą w nazwie (odrzuca „pasek do spodni”); trafnosc 2 = całe hasło, 1 = sama rzecz (sekcja „Podobne” w aplikacji).
- Zablokowane także u mnie: siostry Inditex (strony z zabezpieczeniem), grupa H&M (403). Wittchen: wyszukiwarka Synerise wymaga autoryzacji (401). C&A: POST /api?o=searchPageSearch (do zrobienia). Vinted: /catalog?search_text= (do zrobienia, second-hand).

## 0.4.1 (15.11.2026)
- Google Shopping: Serper (POST https://google.serper.dev/shopping, nagłówek X-API-KEY, klucz /root/.trendo-serper, limit 300 dziennie; darmowe 2500 na start, potem pakiet 50 000 za 50 USD ważny 6 miesięcy), SerpApi jako zapas (limit 8 dziennie). Serper zwraca ok. 15 wyników na zapytanie, linki do karty oferty w Google.
- Wspólna pamięć wyników: 12 godzin.

## 0.5.0 (15.11.2026)
- Okazja z ekranu wyszukiwania wreszcie trafia do serwera (wcześniej była tylko przyciskiem — zgłoszenie użytkownika: koszula w palmy na wieczór). api.py: OKAZJE (wieczor, wesele, sylwester, randka, praca) — lista „nie” (plażowe, sportowe, nadruki, krata, len, krótki rękaw na wieczór/wesele…) wyklucza, lista „tak” (elegancka, satyna, jedwab, wełna, slim…) daje punkty i kolejność. Odpowiedź ma okazja i pominiete. codzien/wyjazd = bez filtra.
- Linki z Google Shopping (karta Google pokazuje „Szczegółowe informacje o tym produkcie są niedostępne” poza Google): /link?nazwa=&sklep= szuka strony produktu w sklepie przez Serper (wyszukiwanie zwykłe, 1 kredyt, pamięć 7 dni); gdy nie znajdzie domeny sklepu → zwykłe wyszukiwanie Google. Aplikacja: akcja doSklepu.

## 0.6.0 (15.11.2026)
- Zgłoszenie użytkownika: na „wieczór” dalej koszule z nadrukiem Coca-Cola — listy słów nie wystarczą. Dodany klasyfikator AI (serwer/trendo/klasyfikator.py, Gemini, klucz /root/.trendo-gemini): dla każdego produktu na podstawie nazwy/sklepu/opisu: r (rodzaj z listy), p (damskie/meskie/unisex/dzieciece), f (elegancja 1–5), o (okazje). Oceny w tabeli klasy (na stałe). Rodzaj hasła też przez AI (rodzaj_hasla). Filtr: dzieciece i druga płeć odpadają, rodzaj musi pasować (zgodny_rodzaj), okazja musi być na liście o, punkty = elegancja. Bez klucza / przy limicie: dawne reguły słów (klasyfikacja „slowa”).
- Nowe sklepy w łączniku stron: Kazar (Magento, w dziale męskim tylko jawnie męskie), Showroom (__PLP_PRELOADED_STATE__, płeć z kategorii).
- C&A: zapytanie GraphQL (persisted query) zwraca indeks DE i 0 produktów — do dopracowania. Vinted: 403 dla curl. Vistula/Bytom/Wólczanka: wyniki renderowane w przeglądarce, bez widocznego API — do zrobienia przeglądarką.

## 0.7.0 (15.11.2026): nadzór nad oceną, płatne Gemini, loga sklepów
- Użytkownik nie ufa darmowemu Gemini (limity, błędy). Klucz przeszedł na płatny plan (doładowanie 50 zł, limit miesięczny 50 zł w AI Studio). Użytkownik NIE chce limitu dziennego (używanie bywa nierówne, np. weekend). Serwer ma tylko limit miesięczny GEMINI_BUDZET_MIESIECZNY=12 USD (koszt z usageMetadata, liczniki ai-koszt-m-RRRR-MM i ai-koszt-RRRR-MM-DD do statystyk). Własny hamulec ma tylko rozgrzewka w tle (0,3 USD dziennie, do 50% budżetu miesiąca).
- klasyfikator.py: jedna ocena na produkt ze ZDJĘCIEM (miniatura w=400, mediaResolution MEDIUM) + nazwa: r, p, f, wzor (gladki/male_logo/duze_logo_lub_nadruk/wzor_stonowany/wzor_wyrazisty/motyw_tematyczny), zgodne, o. Tabela klasy2 (na stałe). Paczki po 10, 8 równolegle. Model z ustawienia model_ai (wybiera kontrola), inaczej lista DOMYSLNE_MODELE. ocena_ai.py usunięty.
- Zasada użytkownika: małe logo marki na piersi (EA7, CK, BOSS) NIE wyklucza elegancji. Słowo „logo” zdjęte z zakazów; wyklucza dopiero duże logo/nadruk widoczne na zdjęciu.
- nadzor.py: decyzja tak/moze/nie. Twarde zakazy słów (Coca-Cola, palmy, dres, bluza, sneakersy, kaptur…), rodzaje zakazane na okazję, wzór ze zdjęcia, min. elegancja (wesele 4, wieczór/sylwester/praca 3, randka 2). Niezgodność (sklep pisze „nadruk”, zdjęcie gładkie; brak zdjęcia; krata; wyrazisty wzór) → „Może pasować”. Nieocenione w trybie okazji ukryte.
- Kontrola jakości: serwer/kontrola/zloty.json = 271 prawdziwych produktów ocenionych ręcznie (wieczór/wesele/praca/randka/sylwester, „?” nie liczone). python -m trendo.kontrola [--wybierz] [--model X]; instalator uruchamia ją po każdej aktualizacji; pierwszy raz porównuje modele i ustawia najlepszy (błąd krytyczny = zła rzecz w głównych wynikach, waga 5).
- „Nie pasuje”: /zglos (od razu ukrywa produkt na tę okazję, czyści pamięć wyników), /zgloszenia do przeglądu.
- Rozgrzewka: raz na dobę popularne hasła (bez Google Shopping) oceniane w tle.
- Loga sklepów: logo.py, /logo?sklep= (apple-touch-icon/ikona ze strony sklepu, zapas: favicony Google i DuckDuckGo), pamięć 14 dni, domeny poznawane z adresów produktów. Pliki logo nie są w repozytorium.

## 0.7.1 (15.11.2026): po pierwszej kontroli
- Kontrola 0.7.0 (271 produktów, 1016 sprawdzeń): gemini-3.5-flash-lite 2 błędy krytyczne / 114 ukrytych dobrych / 0,111 USD; gemini-3.1-flash-lite 4 / 85 / 0,108 USD; gemini-3.8-flash 0 / 93 / 0,222 USD (wybrany, zgodność 91%); gemini-2.5-flash-lite niedostępny. Koszt 3.8-flash ≈ 0,82 USD za 1000 produktów.
- Poprawki: zasady oceniają rzecz jako ELEMENT stroju (satynowa bluzka = wesele/wieczór; gładki golf = wieczór/praca), doprecyzowana skala elegancji, płeć „unisex”, gdy ze zdjęcia nie da się rozstrzygnąć. OCENA_WERSJA=2 (stare oceny liczone od nowa).
- Płeć według AI sprzeczna z działem → „Może pasować” zamiast ukrycia (błędy AI dotyczyły głównie butów sportowych i kurtek).
- Showroom: zdjęcia z parametrami width=600&height=900 dawały 404 (ocena bez zdjęcia, w aplikacji pusty obraz) → pełny adres bez parametrów.
- Rozgrzewka: do 0,1 USD na noc i do 30% budżetu miesięcznego.

## 0.7.2 (15.11.2026): bez „Może pasować”, płeć ze sklepu
- Użytkownik: nie chce sekcji „Może pasować” ani odrzucania z niepewności, nie chce tracić ofert; płeć ma być ustalona precyzyjnie.
- Płeć produktu: najpierw sklep (wspolne.plec_ze_sklepu): sklepy szukane w dziale (Zara, Modivo, eobuwie, Born2Be, Renee, LPP) = dział; LPP pole sex; Showroom z kategorii; Ochnik z kodu produktu (KOSMT = męska, KURDS = damska, BUTYM = męskie buty: wyszukiwarka Ochnika zwraca też męskie przy damskich); Kazar i Bialcon damskie, chyba że opis „męsk”; Bizuu, Mohito damskie; opis „damsk/męsk”. AI decyduje tylko, gdy sklep nie podaje (ok. 15 z 271 we wzorcu).
- Wzorzec: 3 pary butów Ochnika BUTYM poprawione na męskie (AI miało rację).
- Decyzja tylko tak/nie. Opis „nadruk/napis/grafika/print”, a na zdjęciu gładko → nadruk poza zdjęciem → nie (poza randką). Wyrazisty wzór → nie tylko do pracy. Krata, brak zdjęcia, niezgodne zdjęcie → decyduje ocena zdjęcia/AI.
- Klasyfikacja ponawiana: paczki po 10, potem po 4, potem model zapasowy; zdjęcie: w=400 → oryginał → bez parametrów.
- AI niedostępne (np. budżet) → decyzja_slowna: tylko jednoznacznie eleganckie z opisu.
- Kontrola zapisuje szczegóły ocen wzorca (/kontrola) → kalibracja zasad u mnie na prawdziwych odpowiedziach modelu bez kolejnych kosztów.

## 0.7.3 (15.11.2026): kalibracja na prawdziwych odpowiedziach modelu
- Po 0.7.2: 0 błędów krytycznych, 68 dobrych ukrytych, 1 błąd płci (Amazon „T-shirt z mężczyzn”, nazwa sklepu myląca). Odpowiedzi modelu dla wzorca pobrane z /kontrola, reguły testowane lokalnie (serwer/kontrola/kalibracja.py) bez kosztów.
- Wszystkie 68 pominięć: AI zbyt oszczędnie wypisuje okazje. nadzor.okazje(): wieczor (f≥3, nie sweter) ⇒ sylwester; wieczor f≥4 i nie skóra ⇒ wesele; sukienka f≥3 z wieczorem ⇒ wesele (min. elegancja 3 dla sukienek na wesele); praca+randka f≥3 ⇒ wieczor (nie torebka/kurtka/wyrazisty wzór); praca albo wieczor/sylwester f≥3 ⇒ randka; codzien f≥2 dla ubrań gładkich/stonowanych ⇒ randka. Sylwester min. elegancja 2 (gdy AI go wypisało). Usunięty zakaz wyrazistego wzoru do pracy (AI i wzorzec się zgadzały).
- Wynik na wzorcu: 0 błędów krytycznych, ukryte dobre 68 → 20, zgodność 98% (996/1016). Uwaga: reguły dobrane na tym samym zestawie — kolejny krok to drugi, nowy zestaw sprawdzający (żeby wykluczyć dopasowanie „pod test”) i zgłoszenia „Nie pasuje”.

## 0.7.4 (15.11.2026): reguły odporne na zmienność modelu
- Kontrola po 0.7.3 (nowy przebieg modelu) dała 3 błędy krytyczne (emu na randkę, flanelowa koszula na randkę, bawełniana koszula relaxed na sylwestra), a lista „koszula na wieczór” urosła do 135 (len, chambray, krata). Przyczyna: model przy ponownym pytaniu zmienia odpowiedź w 104 z 271 produktów (pojedyncze pola stabilne w 92–99%), a reguły 0.7.3 dobrałem na jednym przebiegu.
- Nowe reguły sprawdzane na DWÓCH przebiegach naraz: wieczor f≥4 (nie sweter) ⇒ sylwester; wieczor f≥4 nie skóra ⇒ wesele; sukienka f≥3 z wieczorem ⇒ wesele; praca albo wieczor/sylwester f≥3 ⇒ randka; codzien f≥2, gładkie/małe logo, ubrania (sweter, polo, sukienka, bluzka, spódnica, spodnie, top) ⇒ randka; marynarka/garnitur f≥3 (nie wyrazisty, nie skóra) ⇒ wieczor, randka, praca. Usunięte: praca+randka ⇒ wieczor (wpuszczało len i kratę), wieczor f3 ⇒ sylwester.
- Wynik: przebieg 1: 0 krytycznych / 27 ukrytych; przebieg 2: 0 / 32 (z 1016). Kontrola zapisuje teraz do 6 ostatnich przebiegów (/kontrola → przebiegi), kalibracja.py liczy każdy osobno.
- Ocena w aplikacji jest stała: każdy produkt oceniony raz i zapamiętany, więc wyniki się nie „przełączają”.

## 0.8.0 (15.11.2026): kodeks ubioru ze źródłami + Smart casual
- Użytkownik: zasady okazji i trendy mają opierać się na profesjonalnych źródłach, nie na naszych pomysłach; więcej źródeł, także polskie; tylko darmowe; dodać okazję Smart casual.
- serwer/kontrola/kodeks.md: kodeks ubioru Trendo z regułami i źródłami (Emily Post Institute, Debrett's, T. Orłowski „Protokół dyplomatyczny” PISM, A. Szteliga UŚ, I. Kamińska-Radomska, A. Pakuła, Forbes PL; pomocniczo Breuninger PL, C&A PL, Suitsupply). Sporne: czerń na weselu (przyjęto: dozwolona). Biel/ecru/kremowy dla kobiet na wesele: zakaz (pole AI „bialy” + kolor w nazwie, bez „z białym …”).
- Polecenie dla AI przepisane według kodeksu (definicje okazji, smart casual, wypisywać WSZYSTKIE pasujące okazje), nowe pole bialy, OCENA_WERSJA=3 (ponowna ocena wszystkich produktów).
- Okazja smartcasual: w aplikacji (kafelek „Smart casual”), serwerze i nadzorze (min. elegancja 2, zakazy: dres, bluza, kaptur, legginsy, szorty, klapki, puchowe; wyprowadzenie: praca albo randka+codzien, f 2–4).
- Wzorzec: kolumna smartcasual (141 tak / 70 nie), poprawki wg kodeksu (kremowe/ecru bluzki i zamszowa marynarka nie na wesele). Kalibracja na starych przebiegach: zostały 2 błędy (kremowe bluzki), które wyłapie dopiero nowe pole „bialy” — do sprawdzenia po instalacji.
- Lniany garnitur/marynarka dozwolone na wesele (kodeks 16).
