/* DANE PRZYKŁADOWE: tylko do pokazania wyglądu, zanim serwer zacznie zbierać prawdziwe dane ze sklepów.
   Każdy ekran z tymi danymi pokazuje oznaczenie „Dane przykładowe”. */
window.DEMO = (function () {
  const P = [
    { id: 'p1', sklep: 'Zara', nazwa: 'Spodnie z ekoskóry, prosty krój', typ: 'spodnie', k: ['#1F1B1D', '#2E292B'], cena: 99, stara: 139, omnibus: 139, weryf: 'ok', strefa: 'budzet', material: '100% poliuretan', rozmiary: ['34', '36', '38', '40', '42'], brak: ['38'], historia: [139, 139, 139, 139, 139, 139, 139, 139, 99, 99], dostawa: { prog: 229, koszt: 9.95 }, url: 'https://www.zara.com/pl/' },
    { id: 'p2', sklep: 'Mohito', nazwa: 'Spodnie typu flare z ekoskóry', typ: 'flare', k: ['#4A2F22', '#5A3B2C'], cena: 249.99, stara: null, weryf: 'reg', strefa: 'budzet', material: '95% poliuretan, 5% elastan', rozmiary: ['XS', 'S', 'M', 'L'], brak: [], historia: [249.99, 249.99, 249.99, 249.99, 249.99, 249.99, 249.99, 249.99, 249.99, 249.99], url: 'https://www.mohito.com/pl/pl/' },
    { id: 'p3', sklep: 'Medicine', nazwa: 'Skórzane spodnie z wysokim stanem', typ: 'szerokie', k: ['#4E1820', '#5E2129'], cena: 279, stara: 399, omnibus: 279, weryf: 'pozorna', strefa: 'budzet', material: 'Skóra naturalna jagnięca', rozmiary: ['34', '36', '38', '40'], brak: ['34'], historia: [279, 279, 279, 279, 279, 279, 279, 279, 279, 279], url: 'https://wearmedicine.com/' },
    { id: 'p4', sklep: 'H&M', nazwa: 'Szeroka nogawka, ekoskóra', typ: 'szerokie', k: ['#1F1B1D', '#2E292B'], cena: 129.99, stara: null, weryf: 'reg', strefa: 'budzet', material: '100% poliuretan', rozmiary: ['34', '36', '38', '40', '42', '44'], brak: [], historia: [129.99, 129.99, 129.99, 129.99, 129.99, 129.99, 129.99, 129.99, 129.99, 129.99], url: 'https://www2.hm.com/pl_pl/index.html' },
    { id: 'p5', sklep: 'Reserved', nazwa: 'Spodnie z ekoskóry z kantem', typ: 'spodnie', k: ['#3B2A22', '#4A372D'], cena: 159.99, stara: 199.99, omnibus: 199.99, weryf: 'ok', strefa: 'budzet', material: '100% poliuretan', rozmiary: ['34', '36', '38', '40'], brak: [], historia: [199.99, 199.99, 199.99, 199.99, 199.99, 199.99, 199.99, 159.99, 159.99, 159.99], url: 'https://www.reserved.com/pl/pl/' },
    { id: 'p6', sklep: 'Ochnik', nazwa: 'Spodnie ze skóry naturalnej, slim', typ: 'spodnie', k: ['#16120F', '#2A2420'], cena: 449, stara: 599, omnibus: 599, weryf: 'ok', strefa: 'wiecej', material: 'Skóra naturalna owcza', rozmiary: ['34', '36', '38', '40'], brak: [], historia: [599, 599, 599, 599, 599, 599, 599, 599, 449, 449], url: 'https://ochnik.com/' },
    { id: 'p7', sklep: 'Massimo Dutti', nazwa: 'Spodnie ze skóry nappa', typ: 'flare', k: ['#2B1D18', '#3A2A23'], cena: 399, stara: null, weryf: 'reg', strefa: 'wiecej', material: 'Skóra naturalna nappa', rozmiary: ['34', '36', '38', '40'], brak: ['40'], historia: [399, 399, 399, 399, 399, 399, 399, 399, 399, 399], url: 'https://www.massimodutti.com/pl/' },
    { id: 'p8', sklep: 'Sinsay', nazwa: 'Spodnie z ekoskóry, gumka w pasie', typ: 'spodnie', k: ['#1F1B1D', '#2E292B'], cena: 59.99, stara: null, weryf: 'reg', strefa: 'tanio', material: '100% poliester, powłoka PU', rozmiary: ['XS', 'S', 'M', 'L', 'XL'], brak: [], historia: [59.99, 59.99, 59.99, 59.99, 59.99, 59.99, 59.99, 59.99, 59.99, 59.99], url: 'https://www.sinsay.com/pl/pl/' },
    { id: 'p9', sklep: 'Vinted', nazwa: 'Skórzane spodnie Zara, rozmiar 36, stan bardzo dobry', typ: 'spodnie', k: ['#1F1B1D', '#2E292B'], cena: 70, stara: null, weryf: 'second', strefa: 'second', material: 'Wg opisu sprzedającej: ekoskóra', rozmiary: ['36'], brak: [], historia: [70, 70, 70, 70, 70, 70, 70, 70, 70, 70], url: 'https://www.vinted.pl/' },
    { id: 'p10', sklep: 'Vinted', nazwa: 'Spodnie ze skóry naturalnej, rozmiar 38', typ: 'szerokie', k: ['#4A2F22', '#5A3B2C'], cena: 140, stara: null, weryf: 'second', strefa: 'second', material: 'Wg opisu sprzedającej: skóra naturalna', rozmiary: ['38'], brak: [], historia: [140, 140, 140, 140, 140, 140, 140, 140, 140, 140], url: 'https://www.vinted.pl/' },

    { id: 'd1', sklep: 'Mango', nazwa: 'Płaszcz wełniany, camel', typ: 'plaszcz', k: ['#B98552', '#9E6E40'], cena: 399, stara: null, weryf: 'reg', material: '70% wełna, 30% poliamid', rozmiary: ['XS', 'S', 'M', 'L'], brak: [], historia: [399, 399, 399, 399, 399, 399, 399, 399, 399, 399], url: 'https://shop.mango.com/pl' },
    { id: 'd2', sklep: 'H&M', nazwa: 'Koszula flanelowa w kratę', typ: 'koszula', k: ['#66705F', '#3A4437'], cena: 89.99, stara: null, weryf: 'reg', material: '100% bawełna', rozmiary: ['XS', 'S', 'M', 'L'], brak: [], historia: [89.99, 89.99, 89.99, 89.99, 89.99, 89.99, 89.99, 89.99, 89.99, 89.99], url: 'https://www2.hm.com/pl_pl/index.html' },
    { id: 'd3', sklep: 'CCC', nazwa: 'Botki typu chelsea', typ: 'botki', k: ['#2A211D', '#3D332D'], cena: 179.99, stara: 229.99, omnibus: 229.99, weryf: 'ok', material: 'Skóra naturalna, podeszwa TPU', rozmiary: ['36', '37', '38', '39', '40'], brak: [], historia: [229.99, 229.99, 229.99, 229.99, 229.99, 229.99, 179.99, 179.99, 179.99, 179.99], url: 'https://ccc.eu/pl' },
    { id: 'd4', sklep: 'Sinsay', nazwa: 'Torebka kuferek', typ: 'torebka', k: ['#5A3B2C', '#4A2F22'], cena: 59.99, stara: null, weryf: 'reg', material: 'Ekoskóra', rozmiary: ['Uniwersalny'], brak: [], historia: [59.99, 59.99, 59.99, 59.99, 59.99, 59.99, 59.99, 59.99, 59.99, 59.99], url: 'https://www.sinsay.com/pl/pl/' },
    { id: 'd5', sklep: 'Mohito', nazwa: 'Marynarka oversize', typ: 'marynarka', k: ['#2A2A30', '#1C1C22'], cena: 229.99, stara: 279.99, omnibus: 279.99, weryf: 'ok', material: '64% poliester, 33% wiskoza, 3% elastan', rozmiary: ['XS', 'S', 'M', 'L'], brak: [], historia: [279.99, 279.99, 279.99, 279.99, 279.99, 279.99, 279.99, 229.99, 229.99, 229.99], url: 'https://www.mohito.com/pl/pl/' },
    { id: 'd6', sklep: 'Reserved', nazwa: 'Bluzka satynowa', typ: 'bluzka', k: ['#E9D9CF', '#D7C2B5'], cena: 99.99, stara: null, weryf: 'reg', material: '100% poliester', rozmiary: ['XS', 'S', 'M', 'L'], brak: [], historia: [99.99, 99.99, 99.99, 99.99, 99.99, 99.99, 99.99, 99.99, 99.99, 99.99], url: 'https://www.reserved.com/pl/pl/' },
    { id: 'd7', sklep: 'Apart', nazwa: 'Złote kolczyki koła', typ: 'kolczyki', k: ['#D8B48E', '#B8925F'], cena: 149, stara: null, weryf: 'reg', material: 'Srebro pozłacane', rozmiary: ['Uniwersalny'], brak: [], historia: [149, 149, 149, 149, 149, 149, 149, 149, 149, 149], url: 'https://www.apart.pl/' },
    { id: 'd8', sklep: 'House', nazwa: 'Sweter z grubej dzianiny', typ: 'sweter', k: ['#D9CBB8', '#C4B49E'], cena: 119.99, stara: null, weryf: 'reg', material: '60% akryl, 40% bawełna', rozmiary: ['XS', 'S', 'M', 'L'], brak: [], historia: [119.99, 119.99, 119.99, 119.99, 119.99, 119.99, 119.99, 119.99, 119.99, 119.99], url: 'https://www.housebrand.com/pl/pl/' },
    { id: 'd9', sklep: 'Deichmann', nazwa: 'Sneakersy skórzane, białe', typ: 'botki', k: ['#EDE6E0', '#D8CEC6'], cena: 149.9, stara: null, weryf: 'reg', material: 'Skóra naturalna', rozmiary: ['36', '37', '38', '39', '40'], brak: [], historia: [149.9, 149.9, 149.9, 149.9, 149.9, 149.9, 149.9, 149.9, 149.9, 149.9], url: 'https://www.deichmann.com/pl-pl/' }
  ];

  const S = [
    { id: 's1', nazwa: 'Miejska', opis: 'Skóra ocieplona camelem i kratą', el: ['p1', 'd1', 'd2', 'd3', 'd4'],
      uklad: [['d1', 4, 4, 44, 50, -7], ['d2', 52, 6, 44, 40, 6], ['p1', 30, 40, 30, 46, -2], ['d4', 64, 44, 28, 26, -8], ['d3', 58, 72, 38, 25, 0]],
      dlaczego: ['Płaszcz w kolorze camel łagodzi surowość czarnej skóry. To jedno z najczęściej pokazywanych zestawień w tym sezonie.', 'Krata wraca w zielonych tonach. W sklepach przybywa jej z tygodnia na tydzień.', 'Botki typu chelsea zostają klasykiem do skórzanych spodni.'] },
    { id: 's2', nazwa: 'Wieczorowa', opis: 'Satyna, złoto i ostra marynarka', el: ['p1', 'd5', 'd6', 'd7', 'd3'],
      uklad: [['d5', 4, 4, 46, 52, -6], ['d6', 50, 8, 42, 40, 5], ['p1', 30, 42, 30, 46, 0], ['d7', 70, 50, 22, 20, 0], ['d3', 56, 72, 40, 25, 0]],
      dlaczego: ['Satyna przy skórze daje kontrast faktur, który dobrze wygląda w sztucznym świetle.', 'Złote dodatki zastępują srebrne. Ten kierunek wyraźnie rośnie.', 'Marynarka oversize dodaje formy wieczorowi bez sukienki.'] },
    { id: 's3', nazwa: 'Swobodna', opis: 'Gruba dzianina i białe sneakersy', el: ['p1', 'd8', 'd9', 'd4'],
      uklad: [['d8', 6, 6, 50, 46, -5], ['p1', 34, 38, 30, 48, 2], ['d4', 66, 18, 28, 26, 8], ['d9', 58, 72, 38, 25, 0]],
      dlaczego: ['Gruba dzianina przełamuje skórę na co dzień.', 'Białe sneakersy obniżają formalność całego zestawu.'] }
  ];

  const TR = {
    damskie: [
      { nazwa: 'Skóra w kolorze bordo', opis: 'Spodnie, płaszcze i torebki w odcieniu wina.', status: 'rosnie', zrodla: 12, seria: [3, 4, 5, 6, 9, 12, 15, 19], probka: ['gladka', '#4E1820', ''] },
      { nazwa: 'Zamsz w odcieniach brązu', opis: 'Kurtki i botki w czekoladzie i karmelu.', status: 'szczyt', zrodla: 18, seria: [8, 13, 16, 18, 19, 19, 18, 18], probka: ['zamsz', '#7A5236', ''] },
      { nazwa: 'Krata w zielonych tonach', opis: 'Flanela i wełna w butelkowej zieleni.', status: 'rosnie', zrodla: 9, seria: [2, 2, 3, 4, 6, 7, 10, 12], probka: ['krata', '#66705F', '#3A4437'] },
      { nazwa: 'Srebrna biżuteria', opis: 'Ustępuje miejsca złotu i mieszanym metalom.', status: 'wygasa', zrodla: 7, seria: [16, 15, 13, 12, 10, 8, 7, 5], probka: ['metal', '#DADDE0', '#8D949B'] }
    ],
    meskie: [
      { nazwa: 'Kurtki skórzane typu bomber', opis: 'Krótkie, w czerni i brązie.', status: 'rosnie', zrodla: 10, seria: [4, 5, 6, 8, 10, 12, 14, 16], probka: ['gladka', '#2A211D', ''] },
      { nazwa: 'Swetry z grubej dzianiny', opis: 'Golfy i kardigany w kolorach ziemi.', status: 'szczyt', zrodla: 14, seria: [9, 12, 15, 17, 18, 18, 18, 17], probka: ['zamsz', '#9C8468', ''] },
      { nazwa: 'Krata na płaszczach', opis: 'Szara i brązowa krata na dłuższych fasonach.', status: 'rosnie', zrodla: 8, seria: [2, 3, 3, 5, 6, 8, 9, 11], probka: ['krata', '#6B6258', '#3F3832'] },
      { nazwa: 'Logo na całej koszulce', opis: 'Duże nadruki marek tracą na popularności.', status: 'wygasa', zrodla: 6, seria: [14, 13, 12, 10, 9, 7, 6, 5], probka: ['gladka', '#3A3A44', ''] }
    ]
  };

  const OK = [
    { sklep: 'Zara', tytul: 'Do −40% na wybraną kolekcję', opis: 'Sprawdziliśmy 312 produktów: obniżki są prawdziwe.', rabat: 40, weryf: 'ok', typ: 'promocje' },
    { sklep: 'H&M', tytul: 'Swetry i kardigany −25%', opis: 'Obniżki potwierdzone: wcześniej przez 30 dni ceny były wyższe.', rabat: 25, weryf: 'ok', typ: 'promocje' },
    { sklep: 'Reserved', tytul: 'Nowa kolekcja −20% z kodem', opis: 'Kod podany na stronie sklepu, ważny do niedzieli.', rabat: 20, weryf: 'ok', typ: 'promocje' },
    { sklep: 'Medicine', tytul: '„Wyprzedaż” do −30%', opis: 'Część produktów miała tę samą cenę przez ostatnie 30 dni.', rabat: 30, weryf: 'pozorna', typ: 'promocje' },
    { sklep: 'Mango', tytul: 'Wyprzedaż do −50%', opis: 'Głównie letnie modele, rozmiary szybko znikają.', rabat: 50, weryf: 'ok', typ: 'wyprzedaze' },
    { sklep: 'Answear', tytul: 'Outlet marek do −60%', opis: 'Kolekcje z poprzednich sezonów.', rabat: 60, weryf: 'ok', typ: 'wyprzedaze' }
  ];

  return { P, S, TR, OK, sklepow: 64 };
})();
