# Dobór drużyn Counter-Strike

**Zespół:** Z6 · grupa L2 · **Repozytorium:**  Sztuczna inteligencja — laboratorium · Collegium Da Vinci · rok akad. 2026/2027

> 

## 1\. Problem *(rubryka A)*

> Z problemem mierzy się organizator mixów, inhouse’ów lub turniejów amatorskich, który musi podzielić zawodników na drużyny. Zwykle robi losowanie lub wybiera kapitanów drużyn, którzy sami wybierają składy np. wężykiem. Często dochodzi do sytuacji, w których drużyny są mocno niezbalansowane. Nasz system wykorzystuje algorytm genetyczny i dobiera wszystkie drużyny jednocześnie, biorąc pod uwagę role, statystyki i pokrycie pozycji. Na wejściu dostaje bazę danych z graczami oraz parametry algorytmu. Na wyjściu zwraca podział drużyn z oceną dla każdej z nich i porównuje te wyniki z doborem wężykiem.

## 2\. Dlaczego SI i dlaczego ta technika *(B · 7 pkt)*

> Zwykły algorytm nie wystarcza, ponieważ dokładny przepis jest za drogi. Podziałów 75 graczy na 15 piątek jest około 1,2 × 10⁶⁶, więc sprawdzenie wszystkich, nawet przy miliardzie podziałów na sekundę, trwałoby około 10⁴⁹ lat. 

## 3\. Dane *(B · 8 pkt)*

> Źródło: https\://www\.hltv.org/stats/players   
> Rozmiar: 75 graczy, 7 map, 35 pozycji, 525 przypisań gracz-pozycja  
> Format: skrypt SQL z czterema tabelami połączonymi kluczami obcymi

## 4\. Rozwiązanie *(A · 10 pkt, B · 5 pkt)*

> Ocena pojedynczej drużyny: F(d) \= 0,4·R \+ 0,3·S \+ 0,2·P \+ 0,1·K, gdzie F ∈ \[0, 1\]    
>   
> (R \- role, S \- statystyki, P \- pokrycie pozycji, K \- komunikacja (odsetek graczy w drużynie pochodzących z tego samego kraju))   
>   
>   
>   
>   
>   
> Schemat działania:  
> 

1. Wczytanie danych.   
2. Przygotowanie oceny  
3. Dobór wężykiem \- sortuje graczy po ratingu i rozdaje wężykiem do 15 drużyn  
4. Algorytm genetyczny szuka najlepszego podziału:  
- Osobnik: permutacja numerów 75 graczy  
- Populacja początkowa: 150 losowych permutacji  
- W każdym pokoleniu: ocenia każdego osobnika funkcją fitness, 2 najlepsze osobniki przechodzą bez zmian, robi selekcję turniejową, krzyżowanie, mutacja. Warunek stopu to 800 pokoleń

## 5\. Ewaluacja *(B · 8 pkt)*

> Co tu wpisać: metryka (ta z karty, pkt 8), punkt odniesienia (prosta metoda z karty), wyniki na kilku przypadkach — w tabeli albo na wykresie. Jedno–dwa zdania wniosku: czy system jest lepszy od punktu odniesienia i o ile.

| Przypadek / zbiór | Punkt odniesienia | Nasz system |
| :---- | :---- | :---- |
| Funkcja oceny, fitness | Dobór wężykiem \- 0,39 | Algorytm genetyczny \- 0,71 |

## System jest prawie dwa razy lepszy od punktu odniesienia.

## 6\. Wymagania niefunkcjonalne *(A · 5 pkt)*

> Algorytm genetyczny dzieli 75 graczy na 15 drużyn w 12,9 sekund na procesorze Intel Core i7-13700K. Przed obliczeniami program sprawdza dane i wypisuje ostrzeżenia jeśli coś się nie zgadza. Mimo to kontynuuje działanie, a brakujące wartości zamieniają się na 0\. Algorytm genetyczny jest losowy, natomiast w 10 uruchomieniach fitness był powtarzalny i wynosił między 0,696 \- 0,713.

## 7\. Ograniczenia *(E · 4 pkt)*

> Kiedy system się myli \- drużyna może dostać wysoką ocenę za komunikację w przypadku gdy np. 4 graczy jest z tego samego kraju i posługuję się tym samym językiem, mimo że piąty gracz z innego kraju jest prowadzącym i to on musi się komunikować najwięcej.  Kiedy system nie zadziała lub da zły wynik \- gdy w bazie jest mniej graczy, niż wymaga liczba drużyn, gdy brakuje ratingu \- przyjmowana wartość 0 zaburza ocenę drużyny. Mając więcej czasu zgromadzilibyśmy więcej danych, nowe zmienne, interfejs graficzny.

## 8\. Zastosowania w praktyce *(E · 4 pkt)*

> FACEIT (CS2 MATCHMAKING PLATFORM) \- Wskaźnik zbalansowania meczu na platformie opiera się na „Team Rating”, który uwzględnia poziom umiejętności graczy w drużynie, to, czy drużyna składa się z graczy solo czy z całego zgranego składu, liczbę rozegranych meczów każdego gracza oraz rozrzut umiejętności w drużynie. To bardzo podobne do naszej funkcji oceny: nie liczy się tylko średnia, ale też skład i rozrzut. 

## 9\. Zespół *(D · 8 pkt)*

> Co tu wpisać: kto za co odpowiadał. Jeśli role się zmieniały — napiszcie kiedy i dlaczego. Wkład powinien zgadzać się z historią repozytorium.

| Osoba | Za co odpowiadała |
| :---- | :---- |
| Andrii Piskun Tymur Popovych Konrad Wawrzyniak | Kod, pozyskanie danych Baza danych, pozyskanie danych Dokumentacja, prezentacja, pozyskanie danych, założenia algorytmu |

## 10\. Uruchomienie *(C · 4 pkt)*

```
git clone https://github.com/M3YSONN/CSTeamFinder-Walczaki
cd DoborDruzynCS
python -c "import sqlite3; c=sqlite3.connect('cs2.db'); c.executescript(open('ctf_db_poprawiony.sql', encoding='utf-8').read()); c.commit()" 
python main.py --typ sqlite
```

## 11\. Narzędzia AI

> Claude \- wspomaganie przy kodzie, narzędzie do prezentacji.