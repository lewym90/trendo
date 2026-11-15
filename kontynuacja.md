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

## 0.8.1 (15.11.2026): kalibracja po kodeksie
- Kontrola 0.8.0 (nowe polecenie): 4 błędy krytyczne, 61 ukrytych, zgodność 95%. 3 „błędy” = moje stare etykiety sprzeczne z kodeksem (polo w paski do pracy: Emily Post dopuszcza polo w business casual) → etykiety „?”. Ochnik bluzy z kołnierzykiem na smart casual → „?” (sporne). Prawdziwy błąd: t-shirt HUGO z emblematem na smart casual → t-shirt na smart casual wymaga elegancji ≥3.
- Nowe polecenie: AI ostrożniejsze z „wieczorem” dla gładkich koszul/golfów/spódnic. Reguły (nadzor.okazje): praca+randka, f≥3, gładkie, rodzaj z WIECZOR_RODZAJE, bez lnu/kraty/flaneli/chambray/dżinsu/sztruksu ⇒ wieczor; smart casual dla skórzanych sneakersów i kurtek, swetrów, koszul (nie flanela), sukienek dziennych; skórzane kozaki/botki (nie emu/zimowe) ⇒ smart casual, randka, wieczor; marynarki f≥3 (nie len, nie skóra) ⇒ sylwester. Zakaz „na plecach” (np. Off-White z logo na plecach).
- Kalibracja na 3 przebiegach: przebieg 3 (nowe polecenie): 0 krytycznych, 32 ukryte z 1227; przebiegi 1–2 (stare, bez pola „bialy”): 2 krytyczne = kremowe bluzki na wesele, które w nowym przebiegu łapie pole „bialy”.

## 0.9.0 (15.11.2026): cechy zamiast słów
- Użytkownik (słusznie): reguły na fragmentach słów są kruche i „podpasowane” pod pojedyncze przypadki („na plecach” odrzuci „gładka na plecach”; „krat” nie łapie „kraciasta”; t-shirt vs polo z małym H). Ma być znacznie lepiej, bez szufladkowania słowami.
- klasyfikator: AI zapisuje ujednolicone cechy ze zdjęcia i opisu: material (20 wartości), wzor_rodzaj (krata, paski, kwiaty, pepitka…), nadruk (brak, male_logo_haft, duze_logo_przod, nadruk_na_plecach, napis_haslo, grafika_postac, naszywki_aplikacje), kolor (bialy_ecru…), styl (sportowy … wieczorowy). Polecenie mówi wprost: formy słów nieistotne, opis wygrywa przy cechach niewidocznych na zdjęciu. OCENA_WERSJA=4.
- nadzor.py przepisany: zasady na cechach (nadruk zakazany, styl zakazany na okazję, materiały luźne na wieczór/wesele, skóra na wesele, cekiny do pracy/smart casual, biel = kolor bialy_ecru). Z nazwy tylko LICENCJE (pełne nazwy marek: Coca-Cola, Disney, Metallica…). Usunięte: TWARDE, NAZWA_ZAKAZ, MIEKKIE, BIEL_RE, listy rdzeni.
- Wyszukiwanie: cechy_hasla(q) (rodzaj + kolor/materiał/wzór, „dowolny” gdy nie podano), pasuje_do_hasla → trafność 2 według znaczenia. Gdy AI działa, produkty nie odpadają przez formę słowa (trafnosc 0 → 1, tylko_ai; rozstrzyga rodzaj ze zdjęcia).
- Kontrola: test_hasel (28 haseł w różnych formach: krata/kratka/kraciasta, skórzane/ze skóry, polówka/polo, dżinsy/jeansy, kaszmir…).
- Kalibracja reguł okazji do powtórzenia na nowych przebiegach (stare przebiegi nie mają nowych cech).

## 0.9.1 (15.11.2026): kalibracja na cechach
- Kontrola 0.9.0: test haseł 28/28; okazje: 4 krytyczne, 46 ukrytych, zgodność 96%.
- Poprawki ogólne (nie pod produkt): zakaz skóry/luźnych materiałów na wesele/wieczór tylko dla ubrań, nie dodatków (skórzana torebka OK); naszywki_aplikacje na rzeczach wieczorowych (styl wieczorowy lub cekiny) = ozdoby, dozwolone na wieczór/sylwestra/randkę; smart casual wyklucza „wieczorowy” tylko dla sukni/kombinezonów; skórzane sneakersy ⇒ smart casual tylko gdy AI nie oznaczyło „sport”; wniosek codzien ⇒ randka tylko dla bluzek, swetrów, sukienek, polo (nie spodnie: bojówki).
- Wzorzec wg kodeksu: #107 (kurtka biker z ekoskóry) sylwester → sporne (kodeks 17 dopuszcza skórę); #255 (t-shirt HUGO z tonalnym emblematem) smart casual → sporne.
- Wynik na przebiegu 0.9.0: 0 krytycznych, 42 ukryte, 96,6%.
- Kontrola robi teraz dwa niezależne przebiegi tego samego modelu i raportuje gorszy; każdy zapisywany do historii (kalibracja na wielu przebiegach).

## 0.10.0 (15.11.2026): moduł trendów z darmowych źródeł
- Kontrola 0.9.1: dwa przebiegi, 0 błędów krytycznych w obu, 96%, test haseł 28/28.
- serwer/trendo/trendy.py: ZRODLA (17): dane — Lyst Index (najnowszy kwartał z lyst.co.uk), Tagwalk (najszybciej rosnące tagi tygodnia), Pinterest Predicts (przeglądarka), Heuritech (/articles/), WGSN (/blog/); redakcje INT — Vogue (RSS), Harper's Bazaar (RSS), Who What Wear (RSS), FashionUnited (RSS /news/fashion/); PL — Vogue Polska i Harper's Bazaar Polska (przeglądarka, blokują curl), Elle (/moda/), Glamour (/moda/), Twój Styl, fashionbiznes.pl (RSS), Breuninger Magazyn.
- Zbieranie raz na dobę (wątek rozgrzewki, licznik trendy-RRRR-MM-DD; instalator uruchamia python -m trendo.trendy): tytuły filtrowane przez tani model (moda, nie uroda/wnętrza), tekst artykułu (articleBody lub akapity; strony danych: cały tekst), AI (tani model) wypisuje trendy w ujednoliconych cechach (kategoria, kolor, materiał, wzór, rodzaj, dział, kierunek, kiedy, hasło) + DOSŁOWNY cytat; zweryfikowany() odrzuca wzmianki, których cytat nie występuje w tekście. Tabele tr_art, tr_wzm.
- Zestawienie: trend tylko przy ≥2 różnych wydawcach (150 dni); dane ze sklepów: udział cechy wśród produktów pierwszy raz widzianych w kolejnych tygodniach (klasy2 + ceny, próba ≥150 w 4 tyg.); status: wygasa / nadchodzi (następny sezon) / rośnie (+15% lub źródła) / na szczycie. /trendy?dzial= (pamięć 3 h). W aplikacji: nazwa, opis (kto pisze + nasze liczby), status, wykres, arkusz ze źródłami (linki), „Znajdź w sklepach” (hasło). Bez przepisywania tekstów artykułów.
- Test lokalny: zmyślone cytaty odrzucone 8/8; do zestawienia trafiają tylko trendy z ≥2 wydawców.
- Na później: Google Trends PL (SerpApi google_trends), szerszy zestaw źródeł PL, fason jako cecha produktu.

## 0.11.0 (15.11.2026): prawdziwe znaki sklepów, nowe wykresy, naprawa produktu
- Błąd: produkt Reserved (koszula ze stójką 59,99 zł) nie otwierał się. LPP czasem podaje rozmiary jako obiekt {"1": "M"} zamiast listy, ekran produktu rzucał wyjątek (p.rozmiary.map). Naprawa: serwer normalizuje rozmiary (wspolne.lista_rozmiarow), aplikacja też (listaRozmiarow), a router łapie wyjątek ekranu i pokazuje komunikat zamiast martwego ekranu.
- Znaki sklepów (serwer/trendo/logo.py, js/znak_wybierz.js, js/znak_przetworz.js): przeglądarka na serwerze otwiera stronę główną sklepu i wybiera znak z nagłówka (element na górze, w linku do strony głównej, opisany jako logo; obrazek, SVG albo tło CSS; zwinięty nagłówek przez viewBox). Plik zablokowany → zrzut elementu ×3. Strona blokuje przeglądarkę → wybór z kodu strony. Na końcu Wikidane (tylko gdy P856 = domena sklepu, logo P154). Obróbka w canvas: wycięcie tła (rogi), białe wycięcia w ciemnym kształcie (Born2Be), przycięcie, wysokość 160 px, biały napis na przezroczystym. Odrzucane: pokrycie > 0,62, proporcje < 0,8 lub > 16. Tabela `znak` (wersja 2), pamięć 30 dni, brak → ponowna próba po 3 dniach. Kolejka w tle, jedna przeglądarka naraz (wspolne.PRZEGLADARKA, wspólna z trendami), rozgrzewka 5 min po starcie. Ikonki stron (favicony) usunięte: bez znaku aplikacja pokazuje nazwę tekstem. CLI: `python -m trendo.logo Reserved Zara "H&M"` (TRENDO_GADATLIWIE=1 pokazuje kandydatów).
- Test lokalny: 25/25 sklepów ze strony (Reserved, Zara, Cropp, House, Sinsay, Mohito, Modivo, eobuwie, Showroom, Ochnik, Bialcon, Born2Be, Renee, Bizuu, Kazar, Vistula, Wólczanka, Bytom, Answear, Lancerto, Top Secret, Wittchen, Tatuum, Monnari, Quiosque, Zalando), Allegro i Mango z Wikidanych; H&M do sprawdzenia na serwerze (u nas Wikidane 429).
- Aplikacja: marka(nazwa, 'm'|'l') zamiast logoSklepu; wielkość wyrównana optycznie (pole stałe, wysokość = √(pole/proporcja), min–max); w okazjach znak nad tytułem zamiast kafla 64×64; przycisk „Nie pasuje? Zgłoś” poprawiony.
- Wykresy (js/grafika.js): wykresTrendu (krzywa monotoniczna Fritsch–Carlson, mgiełka koloru statusu, kropka „teraz”, luki zostają lukami, zakres min–max), znakStatusu (pierścień różowe złoto + strzałka, gdy < 3 tygodnie danych), wykresCeny (schodkowy, linia najniższej ceny z datą, dotyk = cena z dnia). Serwer: seria udziału zachowuje null (było 0), nowe pole tygodni_danych; klucz pamięci trendów zawiera wersję.

## 0.11.1 (15.11.2026): trendy męskie, medaliony, grafiki trendów bez zgadywania
- Medaliony statusu od użytkownika: img/status/{rosnie,nadchodzi,szczyt,wygasa}.webp (wycięte z arkusza 2×2), zamiast znaków z kodu.
- Trendy męskie (było 11, prawie wszystkie z 2 źródeł, bo źródła piszą głównie o modzie damskiej): nowe darmowe źródła z działem „meskie”: Tagwalk /trends/man, GQ (RSS /story/), British GQ (RSS /article/), Esquire (RSS style, /mens-fashion/), Highsnobiety (RSS), Permanent Style (RSS, pełna treść z content:encoded, bo strony artykułów dają 403), Mr Vintage (PL, RSS); K MAG (PL, RSS, dział rozpoznaje AI). Odrzucone: MaleMEN (treści sponsorowane), Men's Health/Fitness PL (zdrowie), FashionBeans (403 na artykułach, w kanale tylko zajawki), Esquire PL i Logo (nie istnieją). Flaga "modowy": bez wstępnego filtra słów KW (tytuły ocenia AI). Kolejność zbierania na przemian (damskie/wspólne i męskie), limit 90 artykułów na dobę. Prompt: męskie przykłady nazw i wymóg polskich znaków.
- Grafiki trendów: koniec zgadywania po kategorii (było: zawsze pierwsza grafika kategorii, np. czarne skórzane spodnie przy „Białych jeansach”, torebka przy „Wzorach zwierzęcych”, m-torebki-1 nie istnieje). Teraz img/trendy/mapa.json: grafika przypisana ręcznie po kluczu nazwy (małe litery, bez polskich znaków; d/m), opcjonalnie próbka wzoru (cechy.wzor) dla trendów o wzorze; inaczej kafel z monogramem „T”. Z 126 starych grafik uczciwie pasuje 15 trendów. img/trendy/plan.json: 4 arkusze 3×3 do wygenerowania (29 grafik trendów + 7 próbek wzorów), komórka → plik → klucze trendów. CLI `python -m trendo.trendy` wypisuje trendy bez własnej grafiki (czyta mapa.json z GitHuba).
- Udział w nowościach sklepów tylko dla trendów mierzalnych w całości (trendy.mierzalny): wszystkie cechy naraz (kolor, materiał, wzór, rodzaj); fason/detal/styl, zestawienia kolorów („i”) i rzeczy z przymiotnikami (np. „Spodnie Capri” → było 51,2% = wszystkie spodnie) bez liczby. Serwer podaje material/wzor/rodzaj trendu, pole img usunięte.

## 0.11.2 (15.11.2026): kafelki trendów od użytkownika
- 4 arkusze 3×3 wycięte narzędziem (skrypt serwer/kontrola/tnij_arkusz.py (uruchamiany lokalnie): tło = mediana ramki, maska odległości od tła, składowe spójne przypisane do komórek po środku ciężkości, miękka przezroczystość, przycięcie z marginesem 3 px jak img/wzorce, maks. 420 px). 36 plików w img/trendy/, wpisane do mapa.json według plan.json.
- Pokrycie: 30/30 trendów damskich i 15/15 męskich ma własną, trafną grafikę; 7 próbek wzorów na trendy o wzorze.

## 0.11.3 (15.11.2026): okazje z grafikami, ilustracje pustych ekranów
- Arkusze 5 (damskie) i 6 (męskie) od użytkownika: 16 stylizacji okazji (img/okazje/okazja-<d|m>-<okazja>.webp) + pusty koszyk i dzwonek (img/puste/). tnij_arkusz.py obsługuje pole "katalog" w planie i większy rozmiar (560 px) dla zestawów.
- Wyszukiwanie: okazje jako karuzela kafelków z grafiką stylizacji (zależną od działu), zaznaczenie w różowym złocie, wybór bez przerysowania ekranu, karuzela przewija się do wybranej okazji. Pusty koszyk i brak alertów z ilustracjami.

## 0.11.4 (15.11.2026): powitanie w 3 slajdach, przedmioty w różowym złocie
- Arkusz 7 (img/ikony/): tryby wyszukiwania (manekin, wieszak, torebka, aparat) zamiast cienkich ikon; puste ekrany: obserwowane (serce), brak wyników (lupa), trendy (klepsydra), brak promocji (metka); Ustawienia z miarą krawiecką.
- Powitanie: 3 przesuwane slajdy (scroll-snap) z img/hero.jpg, img/powitanie-2.jpg (promocje), img/powitanie-3.jpg (trendy); przycisk „Dalej” → „Zacznijmy” na ostatnim, kropki klikalne.

## 0.11.5 (15.11.2026): ekran analizy z przedmiotami
- Arkusz 8 (2×2, tnij_arkusz.py rozpoznaje siatkę po liczbie plików): krok-trendy (magazyny), krok-sklepy (butik), krok-promocje (waga), krok-stylizacje (nożyczki z nicią) w img/ikony/. Każdy krok analizy ma swój przedmiot, a środek pierścienia płynnie zmienia przedmiot na aktywny krok.

## 0.11.6 (15.11.2026): porządki na serwerze (koszty, trendy męskie, procenty, nazwy)
- Koszt AI 15.11: 6,05 USD w jeden dzień (połowa budżetu 12 USD), głównie kontrola jakości (2 × ok. 0,3 USD przy każdej instalacji). Teraz kontrola tylko przy zmianie zasad: kontrola.odcisk_zasad() = skrót polecenia AI, cech, nadzor.py, plec_ze_sklepu, kontrola.py, zloty.json i modelu, zapisany w ustawieniu kontrola_odcisk; bez zmian → wypisuje ostatni wynik. Wymuszenie: `python -m trendo.kontrola --wymus`.
- Wzorzec #145 (polo Sinsay z wakacyjnym wzorem): etykieta smartcasual usunięta jako sporna (kodeks reguły 5–6 dopuszczają polo i ciekawsze wzory), powód w polu „sporne”.
- Trendy męskie: redakcje o profilu damskim (Vogue, Harper's Bazaar, Who What Wear, Vogue PL, Harper's Bazaar PL, Elle PL, Glamour PL, Twój Styl) z dzial="oba" nie zasilają działu męskiego (filtr w zestawienie, działa też na zapisane dane). Polecenie: „oba” tylko, gdy tekst wprost mówi o obu płciach lub unisex.
- Udział w nowościach: trendy.cechy_pomiaru() — mierzymy cechę definiującą trend (wzór/materiał/kolor) plus rodzaj tylko, gdy nazwa go wymienia (RODZAJ_Z_SLOWA, grupy „odzież wierzchnia” = kurtka/płaszcz). Było: AND wszystkich cech z AI (np. „Krata” liczona tylko jako beżowa krata → 0,0%).
- Nazwy trendów: popraw_nazwy() — korekta pisowni przez tani model raz na nazwę (tabela tr_nazwy), nowe nazwy przed zapisem, zapisane jednorazowo na starcie zbierania (UPDATE tr_wzm). Klucze grafik w mapa.json są bez polskich znaków, więc poprawki typu „skory” → „skóry” nie gubią grafik.

## 0.12.0 (15.11.2026): dwie drogi — szukanie rzeczy i stylizacja (decyzja użytkownika)
- Problem (audyt z użytkownikiem): okazja działała jak ukryty, zapamiętany filtr wyszukiwania (np. raz wybrane „Wesele” chowało potem skórzane spodnie przy każdym szukaniu), tryby „Cały outfit / Jedna rzecz / Dodatki / Ze zdjęcia” zmieniały tylko napis, wyniki otwierały się na strefie „W budżecie”.
- Droga 1 „Szukaj rzeczy” (#/szukaj → #/analiza → #/wyniki): hasło, dział, maksymalna cena (b1; 3000 = bez limitu). Serwer /szukaj niczego nie ukrywa pod okazję: każdy produkt ma pole okazje (api.okazje_produktu: formalne przez nadzor.decyzja, codzien/wyjazd z nadzor.okazje; None = jeszcze bez oceny AI). Klucz pamięci bez okazji. Wyniki: filtry widoczne i odwracalne (Do X zł ✕, Tylko promocje, Z drugiej ręki, okazja z licznikami liczonymi przed filtrem okazji), kolejność Polecane/Najtaniej/Najdrożej, przycisk „Pokaż też droższe”, komunikat, gdy nic nie pasuje na okazję (z przykładami reguł kodeksu). Okazja nie jest zapamiętywana między wyszukiwaniami.
- Karta produktu: „Pasuje na” (kafelki okazji z grafikami) i „Dobierz stylizację” (most do drogi 2).
- Droga 2 „Stylizacja” (#/komponuj → #/stylizacje): okazja (kafelki), Całą stylizację / Tylko dodatki, rzecz startowa (z karty produktu albo wpisana), budżet na całość (b2). Wynik: na razie przykładowe stylizacje z uczciwą informacją (silnik stylizacji to następny etap).
- Start: cztery kafelki to wejścia (Jedna rzecz → droga 1, Cały outfit / Dodatki → droga 2, Ze zdjęcia → wybór zdjęcia).
- Instalator: próbne wyszukiwanie pokazuje wszystkie wyniki i liczbę pasujących na wieczór. Zgłoszenie „Nie pasuje na okazję” działa z filtra okazji i usuwa okazję z produktu.

## 0.12.1 (15.11.2026): kontrola bez kosztów, dwie poprawki zasad
- Instalacja 0.12.0 OK. Ostatnia płatna kontrola (z 0.11.6) miała 2 błędy krytyczne w 1 z 6 przebiegów: buty do koszykówki Reebok na smart casual (model raz dał styl casual zamiast sportowy) i czarna mini spódnica z cyrkoniami na wesele (wnioskowanie „wieczór f≥4 → wesele” przy cekinach/brokacie).
- nadzor: sneakersy na smart casual z wnioskowania tylko w stonowanym kolorze (STONOWANE; kodeks 6 „minimalistyczne”); wesele z wnioskowania „wieczór f≥4” nie dla błyszczących pojedynczych części (cekiny_brokat_metaliczny i r ≠ sukienka; kodeks 14). Kalibracja na 6 przebiegach: 0 krytycznych we wszystkich, ukryte dobre bez zmian (42–52). Kodeks uzupełniony o te interpretacje.
- kontrola: zamiast odcisku — gdy są ≥2 zapisane przebiegi tego modelu z aktualną OCENA_WERSJA i kompletem produktów wzorca, instalator odtwarza je z aktualnymi zasadami i wzorcem (0 USD, test haseł z pamięci). Płatna kontrola tylko po zmianie polecenia AI (OCENA_WERSJA), modelu albo z --wymus.
- Koszt AI do 15.11: 7,49 z 12 USD miesięcznie (głównie kontrole przy instalacjach); od teraz instalacje nie kosztują.

## 0.12.2 (15.11.2026): kafelki brakujących trendów
- Instalacja 0.12.1: kontrola bez kosztów na 6 przebiegach, 0 krytycznych, hasła 28/28.
- Arkusze 9 (3×3) i 10 (2×2) wycięte: 10 męskich trendów + Broszki + na zapas Dzianinowa estetyka (d) i Buty z noskiem w szpic (d). Pokrycie: 30/30 damskich i 20/20 męskich.

## 0.13.0 (15.11.2026): dwa światy (damski i męski)
- styles.css: wszystkie kolory przez zmienne (rgb jako --*-rgb do rgba()), paleta damska bez zmian, html[data-swiat="m"]: mosiądz (#D9B77E, gradient #F0DDB0→#CFA866→#8F6A36), koniak (--wino #4A2E1C), grafit (tło #0C0B0A). Atrybut na <html>, bo zmienne zależne od zmiennych liczą się na elemencie, gdzie je zdefiniowano.
- app.js: ustawSwiat() przy każdym renderze (powitanie zawsze damskie), theme-color; przełącznik działu w trendach i ustawieniach zmienia świat; ostatni slajd powitania: „Dla niej / Dla niego”.
- Grafiki męskie: img/m/<ta sama ścieżka> + GOTOWE_M (lista gotowych) + podmienGrafikiSwiata() po renderze (klasa wlasna-m wyłącza przemalowanie). Do czasu grafik: --przemaluj (hue-rotate 24°, saturate .62) na przedmiotach w różowym złocie. Wykresy biorą kolory ze zmiennych (grafika.js kol()).
- tnij_arkusz.py: dowolna siatka z plan.json „siatki”: {"12": [2,3]}. Plan arkuszy 11 (3×3 tryby+puste), 12 (2×3 kroki analizy+koszyk+alerty), 13 (2×2 medaliony), okładki sezonu m/sezon-jz.jpg i m/sezon-wl.jpg.

## 0.13.1 (15.11.2026): męskie grafiki
- Arkusze 11 (3×3) i 12 (2×3) wycięte do img/m/ikony i img/m/puste, medaliony (2×2, wycięcie kołowe) do img/m/status, okładki sezonu img/m/sezon-jz.jpg i sezon-wl.jpg (1024 px). 21 ścieżek w GOTOWE_M.
- Poprawka: ustawSwiat() przed budową ekranu (okładka i grafiki zależą od świata już w szablonie).
- W świecie męskim przemalowywana filtrem zostaje tylko moneta w menu (ikona użytkownika).

## 0.14.0 (15.11.2026): pełny audyt — sklepy, ceny, okazje, alerty, zdjęcie
- **Błąd cen (poważny):** wspolne.liczba() gubiła grosze i cyfry („179.99” → 179, „2499” → 249, „1299,00 zł” → 129). Dotyczyło Born2Be, Renee, Bizuu, części Google. Nowy parser (separator z 1–2 cyframi na końcu = dziesiętny, grupy po 3 = tysiące, spacja tylko przed grupą 3 cyfr), 17 przypadków testowych. Historia cen: przy pierwszym ponownym odczycie produktu usuwane są wpisy sprzed poprawki, które są dokładnie śladem błędu (obcięte grosze albo zgubiona cyfra); ustawienie ceny_poprawne_od.
- **Renee nie działał po cichu** (zmiana klasy linku na r-dl-product-click): _kafle szuka teraz po atrybutach data-dl-*. **Showroom** dla samego „sukienka” dawał pustą stronę: ponowienie ze słowem działu.
- **LPP męskie**: Algolia filtruje płeć (facetFilters sex:Kobieta / sex:Mężczyzna). Koszula męska: 7 → 160 produktów; przy okazji odpadają dziecięce.
- **Nowe sklepy bezpośrednio (21 razem):** Top Secret (kafle2, Omnibus z kafla), Molton i Moodo (szablon IdoSell, data-omniprice), Quiosque i Monnari (formularz POST, data-product), Kappahl (JSON stanu strony, businessArea; słowo działu w zapytaniu). Nie da się bez przeglądarki: Vistula/Wólczanka/Bytom (SPA), CCC, Deichmann, 4F, Big Star, Wittchen, Inditex poza Zarą (wyszukiwarka wymaga sesji), Answear, Zalando, Vinted, Levi's, Apart (403) — zostają przez Google Shopping. simple-cp.com przekierowuje na podejrzaną domenę: pominięty.
- **Omnibus uczciwie:** gdy sklep podaje najniższą cenę z 30 dni niższą od „regularnej”, rabat liczymy od niej (stara_sklepu zachowana). Moodo 199,99 → 39,99 przy najniższej 69,99 = −43%, nie −80%.
- **Naprawa awarii w aplikacji:** „Promocja pozorna” i „Obniżka prawdziwa” bez ceny Omnibus (z własnej historii) wywoływały zl(undefined) i wywalały listę wyników. zl() odporna na brak liczby.
- **serwer/trendo/obserwowane.py:** tabela produkty (ostatni stan każdego produktu z wyszukiwań), obserwowane (alerty + serca). /okazje (sprawdzone obniżki z 48 h, maks. 6 na sklep), /produkty?ids=, /obserwuj?ids=. Wątek odświeżania: obserwowane co 12 h w ich własnym sklepie (Google pomijane). Nocny przegląd sklepów pobiera produkty zawsze (darmowe), ocenę AI tylko w ramach hamulca.
- **POST /zdjecie:** Gemini opisuje rzecz na zdjęciu hasłem (2–5 słów, bez marki); limit 200 zdjęć na dobę, budżet miesięczny. Aplikacja zmniejsza zdjęcie do 1280 px JPEG.
- **Aplikacja:** Okazje dnia i ekran Okazji z serwera (zakładki: Sprawdzone obniżki / Obserwowane), alerty: odświeżenie przy otwarciu, „Cena spadła poniżej …”, kropka na dzwonku tylko przy spadku, powiadomienie (za zgodą, po otwarciu aplikacji; sw.js notificationclick → #/alerty). Usunięta nieprawdziwa obietnica „damy znać, gdy wróci rozmiar”. „Wersja próbna” zastąpiona informacją, że stylizacje są przykładowe.
- install.sh: tabela sklepów (damskie/męskie), okazje dnia, próba zdjęcia na zdjęciu produktu z wyników.
- Koszt AI: ok. 0,0007 USD za nowo oceniany produkt (raz na zawsze). Więcej sklepów = więcej pierwszych ocen; limit miesięczny chroni budżet.

## 0.14.1 (15.11.2026): bez własnych limitów (decyzja użytkownika)
- Użytkownik: granicą budżetu są środki wpłacone na klucz, aplikacja nie ogranicza. Usunięte: budżet miesięczny AI (BUDZET, 402), hamulec oceny nocnej (0,1 USD/noc, 30% miesiąca), limit 400 ocen na wyszukiwanie (teraz wszystkie), limit 200 zdjęć/dobę, dzienne limity Serper (300) i SerpApi (8), limit 90 artykułów trendów/dobę. Koszty nadal liczone do wglądu w /zdrowie; błąd 403/429 od Gemini zapisywany jako ocena.ostatni_blad (np. brak środków).
- Test przeglądarką (z IP centrum danych): Zalando, H&M, Mango, Bershka, Massimo Dutti, Answear, Allegro blokują ochroną antybotową nawet prawdziwą przeglądarkę → tylko Google. Do podłączenia (dane widać albo trzeba znaleźć wewnętrzne API): Vinted (przeglądarka: 312 cen), CCC, Deichmann, C&A, About You, Vistula/Wólczanka/Bytom, 4F, Big Star, Wittchen.

## 0.15.0 (15.11.2026): 26 sklepów
- Instalacja 0.14.1 OK (serwer pokazywał 0.14.0, bo nie podbito WERSJA w api.py; od teraz 0.15.0).
- Vistula, Wólczanka, Bytom (grupa VRG): wyszukiwarka działa pod /search?query= (nie ?q=), zwykłe pobranie; _vrg w lacznik_strony (płeć z data-filter-gender, Omnibus „Najniższa cena”, „Cena regularna”; nazwy Bytomia z wielkich liter → zdanie).
- serwer/trendo/lacznik_przegladarka.py: Vinted (kategorie 1904 kobiety / 5 mężczyźni, dane z atrybutu title kafelka, cena z ochroną kupującego, uzywany=True → weryf „second”) i C&A (odpowiedź searchPageSearch przechwycona z nawigacji; kategoria 1-/2- = kobiety/mężczyźni; API wprost zwraca 403 nawet z ciasteczkami). Jedna przeglądarka na oba, wspólna blokada PRZEGLADARKA (czeka do 25 s), ciasteczka w DANE/przegladarka-ciasteczka.json, obrazki/czcionki blokowane. Ok. 6 s na wyszukiwanie.
- Nadal tylko przez Google: Zalando, H&M, Mango, Bershka, Massimo Dutti, Answear, Allegro (zapory), Wittchen (Synerise z tokenem), CCC, Deichmann, 4F, Big Star, About You (wyszukiwarka tylko w skrypcie; do rozpracowania w przeglądarce).

## 0.15.1 (15.11.2026): 28 sklepów
- Instalacja 0.15.0 OK: 26 sklepów na serwerze, Vinted 96/96 i C&A 41/41 przez przeglądarkę, 19 okazji męskich.
- Deichmann: /pl-pl/search/{q}?gendersFilter=1887164 (kobiety) / 1887165 (mężczyźni); wyniki w <script id="ng-state"> jako base64+gzip (klucz z „search%2F”), 24 na stronę → dwie strony (&page=2). Ceny w groszach (priceRange.min.withTax), beforeSaleWithTax, lowestPriorPrice (Omnibus). Zdjęcie: asset.deichmann.com/images/f_auto,q_auto/w_600/{public_id}/zdjecie (bez końcowego członu 404).
- Big Star: API bigstar.pl/api/v2/products/?q= (parametr query={…} jest ignorowany), 63 na stronę; płeć i dzieci z category_path; link bigstar.pl/p-{slug}; regular_price, omnibus_price.
- Zostają: CCC (wyszukiwanie przekierowuje na stronę główną — do rozpracowania w przeglądarce), 4F (strona nie odpowiada z mojego środowiska), About You (bez danych w odpowiedziach), Wittchen (Synerise z tokenem).

## 0.16.0 (15.11.2026): 30 sklepów (CCC, Wittchen)
- Instalacja 0.15.1 OK (28 sklepów). Deichmann 0/0 w teście instalatora, bo to sklep z butami: test sprawdza teraz buty (botki / sneakersy), gdy sklep nie ma sukienek ani koszul.
- Grafika damskiego trendu „Płaszcz o ponadczasowym kroju”: wzorce/d-okrycia-1 (camelowy płaszcz).
- serwer/trendo/lacznik_ccc.py: api/Search/Search?searchText=…&filterAttributes={"filterAttributeOptions":[]}&page=1&pageSize=60&language=pl_PL&listingName=allproducts, nagłówki x-api-version 4.0, x-frontend-id 44, x-source-name WWW, ciasteczko „anon” (token gościa, ważny długo) pobrane raz przeglądarką do DANE/ccc-ciasteczka.json; przy 407 nowe. Do hasła dopisujemy „damskie”/„męskie”, płeć z categoryTree.itemCategory (Kobiety/Mężczyźni). Link ccc.eu/pl/pl/p/{slug}.
- serwer/trendo/lacznik_wittchen.py: Synerise smcr.wittchen.com/ai/search/v2/indices/{indeks}/query?query=…&limit=48; token Bearer ważny 1 h przechwytywany przeglądarką (ok. 5 s) do DANE/wittchen-token.json, odnawiany po wygaśnięciu. gender female/male, effectivePrice, price, attributes.omnibus.
- Zostają przez Google: 4F (strona nie odpowiada z mojego środowiska), About You.

## 0.16.1 (15.11.2026): test instalatora
- Instalacja 0.16.0 OK: 30 sklepów, Wittchen 48/30. CCC w tabeli „ok” = 0 na sukienkę/koszulę (sklep obuwniczy); test sprawdza teraz buty dla każdego sklepu bez wyników, także w łącznikach wielu sklepów (eobuwie męskie: sneakersy). Dodane próbne wyszukiwanie damskie (sukienka) przez serwer — od razu zasila damskie okazje dnia.

## 0.17.0 (15.11.2026): Rozmiarówka na stronie produktu (decyzja użytkownika)
- Użytkownik NIE chce zapisywać swoich wymiarów (zmienia sylwetkę). Chce widzieć rozmiarówkę produktu. Zaakceptowane: rząd rozmiarów z dostępnością, szkic rzeczy z liniami pomiarów dla wybranego rozmiaru, oznaczenie źródła, krój. Odrzucone: wskazówka „zmierz koszulę”, porównanie z innymi sklepami.
- Grafiki od użytkownika: 2 arkusze 3×3 (damski: bluzka, sweter, sukienka, spódnica, spodnie, marynarka, płaszcz, botek, wkładka; męski: koszula, t-shirt, sweter, marynarka, płaszcz, spodnie, jeansy, but, wkładka) → img/rozmiary/{d,m}-*.webp. Linie pomiarów: data/szkice-rozmiarow.json (ułamki szerokości/wysokości, krawędzie korpusu dobrane ręcznie, bez rękawów).
- serwer/trendo/rozmiary.py: czytnik tabel HTML (rowspan/colspan, tabele zakodowane w JSON strony), rozpoznaje rozmiary (XS…3XL, 32–54, W/L, „XS/34”) i pomiary (biust/klatka, talia, biodra, nogawka, stopa, wkładka, rękaw, kołnierzyk, wzrost, długość…) w obu układach; odpowiedniki rozmiarów (EU, IT, numery garniturów) jako aliasy. /rozmiary?id=: 1) tabela ze strony produktu (pamięć 7 dni; działa m.in. Top Secret, Moodo, Born2Be, Renee, Bizuu, Ochnik, Bialcon), 2) ogólna tabela sklepu z serwer/trendo/rozmiary-sklepow.json, 3) „sklep nie podaje tabeli”.
- serwer/kontrola/rozmiary_sklepow.py buduje bazę ogólnych tabel (ręczny wybór tabel ze stron pomocy, sprawdzenie wymaganych pomiarów): Reserved 6, Mohito 2, House 8, Cropp 5, Sinsay 6, Quiosque 2, Monnari 3, Kazar 2, Bytom 3. Błędy źródeł: Cropp „długość rękawa” w jeansach to nogawka (pomijana), House „79-73” w nogawce (nie wchodzi).
- Brak tabel (do zrobienia): Zara (okienko tylko w skrypcie), C&A, Kappahl, Vistula/Wólczanka (doradca interaktywny), Big Star, Molton, Modivo/eobuwie/Showroom (wielomarkowe), CCC, Deichmann, Vinted (rozmiar od sprzedającego).
- Produkty w bazie mają „rodzaj” z oceny AI (szkic i grupa tabeli). Poprawka: karta historii ceny nie obiecuje „oceny po 30 dniach”, gdy sklep podał cenę z 30 dni.

## 0.18.0 (15.11.2026): tabele rozmiarów dla kolejnych sklepów
- Prośba użytkownika: dorobić tabelę zgodną z każdym produktem tam, gdzie jej nie było. Rozwiązanie: odczyt tabeli przy otwarciu produktu (nie przy wyszukiwaniu, żeby nie mnożyć zapytań), pamięć 7 dni na adres produktu (klucz „rozmA|url”), w razie porażki dawna ścieżka (strona produktu, tabela ogólna, brak).
- serwer/trendo/rozmiary.py ADAPTERY: Vistula/Wólczanka/Bytom (GET strony → meta csrf-token i .product-size-info data-id → POST /product/sizeTable/{id} z X-CSRF-TOKEN; w „view” tablica dataSizes: chest/waist/available/result_size/result_size_alternative, garnitury i koszule pogrupowane wzrostem), CCC (api/Product/GetProduct?slug=…, nagłówki x-api-version 5.0, x-frontend-id 44, ciasteczko anon; tableSize + itemSizes), Big Star (api/v2/product/sizedetails/{variation_id}; łącznik zapisuje rozm_ref {war, mapa variation_id→„W29 L32”}, pole w POLA; to wymiary UBRANIA na płasko → rodzaj „rzecz”), Kappahl (stan strony „sizeGuide”, drzewo {tag, attr, children} → HTML → z_html; układ B scala literę i UE w „S/36”), Modivo/eobuwie (searchgcp.modivo.io/api/v5/products/{slug}?channel=…: tabela_producent marki, inaczej domyślna tabela kategorii z kategorie_filtr_b → zrodlo „sklep”), Showroom (stan strony „sizeGuide”: sam przelicznik EU/IT/FR/ES/UK/US, rodzaj „przelicznik”).
- C&A: ogólne tabele z ich API (POST /api?o=sizeGuide, persistedQuery 73fa97a3…, klucze 1-top, 1-bottom, 2-top, 2-bottom) pobierane przeglądarką w kontrola/rozmiary_sklepow.py (curl dostaje 403). Baza ma teraz 41 tabel.
- Aplikacja: wybór grupy przed rozmiarem (Wzrost 164–170/176–182/188–194 w koszulach VRG, wzrost w garniturach Bytom, Długość L30/L32/L34 w Big Star; serwer podaje t.grupy {nazwa, lista[, klucze, etykiety]}), dostępność z tabeli (t.dostepne), etykiety linii z nazw sklepu przy wymiarach ubrania, opis „wymiary ubrania mierzone na płasko” / „wymiary ciała”, karta przelicznika dla Showroom (odpowiedniki wybranego rozmiaru, rozmiary w sklepie).
- Bez tabeli dalej: Zara (okienko tylko w skrypcie, strona za zaporą), Deichmann (okienko nie otwiera się poza prawdziwą przeglądarką, dane produktu bez długości), Molton (brak tabeli na stronach produktów), Wittchen (paski „S/M 90 cm”, niewarte), Vinted (z założenia). Google Shopping bez zmian.

## 0.18.1 (15.11.2026): poprawki po instalacji 0.18.0
- Instalacja 0.18.0 OK (inne aplikacje 200/200/200/400). Tabele działają: Vistula, Wólczanka, Bytom (wybór wzrostu), CCC, eobuwie, Big Star, Kappahl, Modivo (ogólna), C&A (ogólna), Showroom (przelicznik).
- Renee i Born2Be zmieniły stronę: komórka rozmiaru ma dwie etykiety („S S”, „XXL 2XL”) → rozmiary._bez_dubla. Brak tabeli był pamiętany 7 dni → teraz klucz „rozm2|” (tabela 7 dni) i „rozm2n|” (brak tylko dobę).
- Zdjęcie po instalacji: Gemini 403/429 (zaraz po setkach ocen z próbnych wyszukiwań). klasyfikator._wywolaj zapisuje teraz w ai_ostatni_blad status i treść błędu Google (rozróżnienie limitu na minutę od limitu wydatków); instalator ponawia próbę zdjęcia po minucie i wypisuje odpowiedź Google. Uwaga: koszt listopada 11,54 USD, a w AI Studio użytkownik miał ustawiony limit miesięczny 50 zł — możliwe, że to on.
- Test rozmiarówki w instalatorze tylko dla sklepów podłączonych bezpośrednio. Kazar: tabela ubrań nie istnieje (paski 80–125 pominięte, rozmiary trzycyfrowe).
- Bytom 500 w próbie sklepów: chwilowa awaria po stronie sklepu.

## 0.18.2 (15.11.2026): instalacja bez kosztów AI (prośba użytkownika)
- Użytkownik: „wydałem sporo na same testy”. Instalacja 0.18.1 kosztowała ok. 1,7 USD (próbne wyszukiwania oceniały ~1600 nowych produktów; listopad 13,27 USD).
- /szukaj?test=1: wyszukiwanie bez oceny AI (bez cechy hasła), bez zapisu w pamięci wyszukiwań; produkty trafiają do bazy (rozmiarówka po id działa). Instalator używa test=1 we wszystkich próbnych wyszukiwaniach. Jakość oceny nadal sprawdza darmowa kontrola na zapisanych przebiegach. Pozostały koszt instalacji: zdjęcie próbne (~0,001 USD) i nowe artykuły trendów (zwykle 0).
- Do decyzji użytkownika: nocny przegląd (ceny 42 haseł bez Google — darmowe; ocena AI nowych produktów — płatna).

## 0.18.3 (15.11.2026): tańsza noc (DECYZJA użytkownika)
- Użytkownik pytał o sens nocnego zbierania. Ustalone: sprawdzanie promocji zostaje (Omnibus ze sklepu i własna historia cen są darmowe; chroni przed napompowanymi rabatami w okazjach dnia). Nocny przegląd cen 42 haseł zostaje (bez AI, darmowy). Wyłączona nocna ocena AI wszystkich nowych produktów; AI ocenia w nocy tylko okazje dnia (do 60+60, każdy produkt raz). Szacunek: 0,02–0,10 USD/noc, 1–3 USD/mies.
- Udziały trendów w sklepach (dane_sklepow) i tak pokazywane tylko przy próbie ≥150 (tydzień ≥30); bez nocnej oceny będą rzadsze. O trendzie decydują źródła (≥2 wydawców); udział wpływa tylko na status „rośnie” (zmiana ≥15%).
- /okazje: „pasuje na” liczone z zapisanych ocen (klasyfikuj maks=0, bez kosztów).
- Koszt nocy: ustawienie noc_koszt {data, koszt_usd, okazje, artykuly} → /zdrowie „noc” i wiersz w instalatorze. Użytkownik: licznik tylko dla niego, NIE w aplikacji.
