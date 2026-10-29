# Karta zgłoszenia tematu projektu

**Grupa:** L2 · **Zespół:** Z.6 · **Data:** 22.10.2026 Sztuczna inteligencja — laboratorium · Collegium Da Vinci · rok akad. 2026/2027 Oddajecie mailem do **22.10, 16:45**, temat `SI L2 · Z<nr zespołu> · karta`.

## 1\. Skład zespołu

> Rola jest wstępna — można ją zmienić w trakcie projektu bez uzgadniania.

| Imię i nazwisko | Nr albumu | Rola (wstępna) |
| :---- | :---- | :---- |
| Konrad Wawrzyniak | 31802 | dokumentacja PL/EN i prezentacja |
| Andrii Piskun | 31874 | kod rdzenia SI |
| Tymur Popovych | 31012 | dane i ewaluacja |

## 2\. Roboczy tytuł (PL) 

Dobór drużyn Counter-Strike

## 3\. Tytuł (EN)

Counter-Strike Team Selection

## 4\. Problem — co system ma robić i dla kogo (3–5 zdań)

System ma za zadanie automatycznie dobierać zawodników do jak najbardziej zbalansowanych drużyn, uwzględniając ich statystyki, role itd. W tym celu wykorzystuje algorytm genetyczny, który analizuje różne kombinacje zawodników i poszukuje najlepszego składu na podstawie określonych kryteriów i ich wag. System jest przeznaczony dla graczy, trenerów oraz organizatorów rozgrywek, którzy chcą tworzyć sprawiedliwe i konkurencyjne drużyny. 

## 5\. Technologia SI

- [ ] sieć neuronowa  
- [ ] system ekspertowy / wnioskowanie regułowe  
- [x] algorytm genetyczny  
- [ ] klasyczne uczenie maszynowe

Dlaczego ta technologia pasuje do tego problemu (2–3 zdania):  
Przy 25 zawodnikach dzielonych na 5 drużyn po 5 osób liczba możliwych podziałów wynosi około 623 miliardy.

Algorytm genetyczny pasuje, dlatego że pozwala szukać optymalnego składu na podstawie wielu kryteriów, takich jak role zawodników, statystyki, pozycje na mapach. Dzięki mechanizmom selekcji, krzyżowania i mutacji może stopniowo tworzyć coraz lepsze składy. Sprawdza się dobrze w problemach, w których istnieje wiele możliwych kombinacji rozwiązań, a wymaga uwzględnienia różnych kryteriów i ich wag. 

## 6\. Dane

- Źródło:  HLTV.org    
- Rozmiar / format: 25 \- 250 zawodników, JSON/CSV  
- Czy dane są już dostępne? tak / nie — plan pozyskania: Tak

## 7\. Stos technologiczny

Python(demoparser2, awpy), algorytm genetyczny, 

## 8\. Kryterium sukcesu

- Metryka i próg: funkcja oceny zbalansowania drużyn(F \= 0,40R \+ 0,30S \+ 0,20P \+ 0,10K) r- role, s \- statystyki, p \- pozycje, k \- komunikacja  
- Punkt odniesienia (prosta metoda, z którą porównacie wynik): dobór wężykiem

## 9\. Zakres minimalny (co powstanie na pewno)

Działający algorytm, który będzie potrafił wczytać dane, dobrać drużyny, ocenić je, przedstawić wyniki i porównać metody, repozytorium Git,  dokumentacja według szablonu, prezentacja.

## 10\. Zakres opcjonalny (co dorobimy, jeśli starczy czasu)

Strona internetowa, testowe dane dodatkowe do algorytmu

## 11\. Repozytorium

[https\://github.com/M3YSONN/CSTeamFinder-Walczaki](https://github.com/M3YSONN/CSTeamFinder-Walczaki) 

## 12\. Główne ryzyko i plan awaryjny

Problem z automatyzacją pobierania danych, plan awaryjny to ręczne zapisywanie danych  
---

*Decyzja prowadzącego:* \[ \] zatwierdzony  \[ \] do poprawy · *Uwagi:*