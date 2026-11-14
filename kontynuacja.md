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
